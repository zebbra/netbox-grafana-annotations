# netbox-grafana-annotations

A NetBox dashboard widget that lists Grafana annotations filtered by tags: upcoming maintenance windows, a changelog, deployments, incidents.

![Widgets for maintenance, changelog and incidents](docs/screenshot.png)

NetBox fetches the annotations server-side (the Grafana token never reaches the browser) and caches them briefly. Each widget has its own tags and time window, so a dashboard can show upcoming maintenance next to a changelog and current incidents.

## Install

```sh
pip install git+https://github.com/zebbra/netbox-grafana-annotations.git@v0.4.1
```

```python
PLUGINS = ["netbox_grafana_annotations"]

PLUGINS_CONFIG = {
    "netbox_grafana_annotations": {
        "grafana_url": "http://grafana.monitoring.svc",        # used for API calls
        "grafana_public_url": "https://grafana.example.com",  # used for links, defaults to grafana_url
    },
}
```

| Setting | Default | |
|---|---|---|
| `grafana_url` | – | Grafana base URL for API calls (required) |
| `grafana_public_url` | `grafana_url` | Base URL for links in the widget |
| `token` | – | Grafana service account token |
| `token_env` | `GRAFANA_ANNOTATIONS_TOKEN` | Environment variable read when `token` is not set |
| `timeout` | `5` | Request timeout in seconds |
| `verify_ssl` | `True` | TLS verification for the API call |
| `cache_timeout` | `300` | Cache lifetime in seconds, `0` disables caching |
| `pinned` | `[]` | Feeds shown above every user's dashboard, see below |
| `pinned_message` | – | Markdown text shown above the pinned feeds, e.g. a message of the day |

Proxies follow NetBox's `HTTP_PROXIES`.

## Grafana token

Create a service account with role **Viewer** and a token for it. Viewer can read organization annotations; nothing else is needed.

## Widget

Add «Grafana Annotations» on the NetBox dashboard and configure:

<img src="docs/config.png" alt="Widget configuration" width="420">

- **Tags**: comma-separated; by default an annotation must carry all of them, «Match any tag» relaxes that
- **Days back** / **Days ahead**: time window around now; e.g. 0/14 for upcoming maintenance, 30/0 for a changelog, 1/14 to keep yesterday's window visible. Ongoing entries come first, then upcoming (soonest first), then past (newest first, dimmed when the window also looks ahead)
- **Hint**: optional text shown when hovering the info icon, e.g. what the widget lists
- **Max entries**, **Show tags** (the filter tags themselves are never shown), **Show fields**

## Pinned feeds

Feeds that every user should see, e.g. maintenance and incidents, can be pinned above the dashboard. They come from the configuration, so users cannot remove or change them; the dashboard below stays theirs.

```python
"pinned": [
    {"title": "Planned work", "color": "purple", "tags": "maintenance", "days_back": 0, "days_ahead": 7},
    {"title": "Incidents", "color": "red", "tags": "incident", "days_back": 5, "hint": "Current cases"},
    {"title": "Preview", "color": "teal", "tags": "preview", "days_back": 0, "days_ahead": 0},
],
"pinned_message": "**Release 4.6** on Monday, see [notes](https://wiki.example.com/release).",
```

Feeds share one row in equal widths and are hidden while they have no entries. `title`, `color`, `width` (of 12 columns, overrides the equal split) and `height` (max height in units of 100px, default 4) shape the card; every other key is a widget setting as above (`tags`, `days_back`, `days_ahead`, `max_entries`, `hint`, …). NetBox has no hook for the home page, so the plugin adds the feeds via its `<head>` content and a few lines of JavaScript placed before `#dashboard`; if a NetBox release changes that element, the feeds just do not show.

With `days_back` and `days_ahead` both 0 a feed lists only annotations running now, e.g. region annotations from the rollout of a feature on a test system to its release.

## Annotation format

**Created by hand in Grafana**, e.g. an engineer marks an incident on a graph (Ctrl+click, text and tags), the API returns something like:

```json
{
  "time": 1794812400000,
  "timeEnd": 1794817800000,
  "tags": ["incident", "tier3", "firewall"],
  "dashboardUID": "firewalls",
  "panelId": 2,
  "text": "Firewall in conserve mode\nMemory exhausted, new sessions dropped until failover",
  "data": {}
}
```

The widget shows the first line as title, linked to the dashboard panel, and the following lines as details. HTML in the text is stripped.

**Written by automation**, an annotation can carry structured fields in `data`, which take precedence:

```json
{
  "time": 1794812400000,
  "timeEnd": 1794819600000,
  "tags": ["maintenance", "aci"],
  "text": "<b>ACI exporter deployment</b><br>…",
  "data": {
    "title": "ACI exporter deployment",
    "summary": "New exporter image with APIC fault metrics",
    "url": "https://grafana.example.com/d/maintenance/maintenance",
    "impact": "Short gaps in ACI metrics",
    "contact": "Jane Doe",
    "jira": ["[OPS-123](https://jira.example.com/browse/OPS-123)"],
    "runbook": "https://wiki.example.com/runbook/aci"
  }
}
```

`title` is the linked title (`url`), `summary` a grey line below it. Every further field with a plain value or a list of plain values is listed as `Key: value` (`impact` and `contact` first, nested objects skipped), unless «Show fields» is off. Markdown links (`[text](url)`) and bare URLs in values become links; relative ones are resolved against `grafana_public_url`. Only `http(s)` URLs are rendered as links.

`text` stays what Grafana shows in its own tooltips. Writing `data` needs the HTTP API (`POST /api/annotations`), the Grafana UI only sets text and tags.

## Demo

`dev/` runs NetBox with the plugin from this checkout and a mock Grafana with demo data relative to now (yesterday's, an ongoing and tomorrow's maintenance, a changelog, incidents incl. one created by hand):

```sh
cd dev && docker compose up -d
```

After a minute or two, http://localhost:8000 (login `admin` / `admin`) shows a message and three pinned feeds above a dashboard with two widgets. `NETBOX_PORT=8080 docker compose up -d` for another port, `docker compose down -v` to clean up. Plugin code changes: `docker compose restart netbox`.

## Development

```sh
PYTHONPATH=. uvx pytest tests
```

## License

MIT
