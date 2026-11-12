import re
from datetime import datetime, timezone
from html import unescape
from urllib.parse import urljoin, urlparse

UPCOMING = "upcoming"
RECENT = "recent"

DAY_MS = 86_400_000

_BR = re.compile(r"<br\s*/?>|\n", re.IGNORECASE)
_TAG = re.compile(r"<[^>]*>")


def query_params(tags, match_any, mode, days, limit, now_ms):
    """Query string for GET /api/annotations as a list of pairs."""
    if mode == UPCOMING:
        start, end = now_ms, now_ms + days * DAY_MS
    else:
        start, end = now_ms - days * DAY_MS, now_ms
    params = [("type", "annotation"), ("from", start), ("to", end), ("limit", limit)]
    params += [("tags", t) for t in tags]
    if match_any:
        params.append(("matchAny", "true"))
    return params


def parse_tags(value):
    return [t.strip() for t in (value or "").split(",") if t.strip()]


def safe_url(url, base=None):
    """Absolute http(s) URL, or None. Relative URLs are resolved against base."""
    if not url or not isinstance(url, str):
        return None
    if base and not urlparse(url).scheme:
        url = urljoin(base.rstrip("/") + "/", url.lstrip("/"))
    if urlparse(url).scheme not in ("http", "https"):
        return None
    return url


def plain_lines(html):
    """Text of an annotation as plain lines, tags stripped."""
    parts = (unescape(_TAG.sub("", p)).strip() for p in _BR.split(html or ""))
    return [p for p in parts if p]


def _ts(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc) if ms else None


def normalize(annotation, now_ms, base_url=None, hide_tags=()):
    """
    Turn a Grafana annotation into a display entry.

    Structured fields in annotation["data"] win (title, url, impact, contact,
    jira: [{key, url}]); otherwise the first text line is the title and the
    rest are details.
    """
    data = annotation.get("data") or {}
    if not isinstance(data, dict):
        data = {}
    lines = plain_lines(annotation.get("text"))

    title = data.get("title") or (lines[0] if lines else "")
    if data.get("title"):
        details = []
        for key, label in (("impact", "Impact"), ("contact", "Contact")):
            if data.get(key):
                details.append(f"{label}: {data[key]}")
    else:
        details = [line for line in lines[1:] if line != "Details" and " · " not in line]

    url = safe_url(data.get("url"), base_url)
    if not url and annotation.get("dashboardUID"):
        path = f"/d/{annotation['dashboardUID']}"
        if annotation.get("panelId"):
            path += f"?viewPanel={annotation['panelId']}"
        url = safe_url(path, base_url)

    links = []
    for item in data.get("jira") or []:
        if isinstance(item, dict) and safe_url(item.get("url")):
            links.append({"label": item.get("key") or item["url"], "url": item["url"]})

    start = annotation.get("time")
    end = annotation.get("timeEnd")
    if end == start:
        end = None
    return {
        "id": annotation.get("id"),
        "title": title,
        "details": details,
        "url": url,
        "links": links,
        "tags": [t for t in annotation.get("tags") or [] if t not in hide_tags],
        "start": _ts(start),
        "end": _ts(end),
        "active": bool(end and start <= now_ms < end),
        "_start_ms": start or 0,
    }


def entries(annotations, mode, now_ms, max_entries, base_url=None, hide_tags=()):
    items = [normalize(a, now_ms, base_url, hide_tags) for a in annotations]
    items.sort(key=lambda e: e["_start_ms"], reverse=(mode != UPCOMING))
    return items[:max_entries]
