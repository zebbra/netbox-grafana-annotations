from netbox_grafana_annotations import grafana

NOW = 1_794_800_000_000
BASE = "https://grafana.example.com"


def test_query_params_window():
    p = dict(grafana.query_params(["maintenance"], False, 1, 14, 50, NOW))
    assert p["from"] == NOW - grafana.DAY_MS and p["to"] == NOW + 14 * grafana.DAY_MS
    assert p["tags"] == "maintenance" and "matchAny" not in p


def test_query_params_recent_multi_tag_any():
    p = grafana.query_params(["a", "b"], True, 7, 0, 50, NOW)
    assert ("tags", "a") in p and ("tags", "b") in p and ("matchAny", "true") in p
    assert dict(p)["to"] == NOW


def test_structured_data():
    e = grafana.normalize({
        "time": NOW - 1000, "timeEnd": NOW + 1000, "tags": ["maintenance", "aci"],
        "text": "<b>ignored</b>",
        "data": {"title": "ACI Exporter", "url": f"{BASE}/d/x", "impact": "Gaps",
                 "contact": "Ops", "jira": ["[T-1](https://jira/T-1)"]},
    }, NOW, BASE, hide_tags={"maintenance"})
    assert e["title"] == "ACI Exporter" and e["active"]
    assert [d["label"] for d in e["details"]] == ["Impact", "Contact", "Jira"]
    assert e["details"][2]["parts"] == [{"text": "T-1", "url": "https://jira/T-1"}]
    assert e["summary"] == ""
    assert e["tags"] == ["aci"]


def test_text_fallback_and_relative_url():
    e = grafana.normalize({
        "time": NOW, "tags": [], "dashboardUID": "abc", "panelId": 3,
        "text": "Deploy &amp; restart<br>second line<br><a href='/x'>Details</a>",
    }, NOW, BASE)
    assert e["title"] == "Deploy & restart"
    assert [d["parts"][0]["text"] for d in e["details"]] == ["second line"]
    assert e["url"] == f"{BASE}/d/abc?viewPanel=3"
    assert e["end"] is None and not e["active"]


def test_unsafe_urls_dropped():
    e = grafana.normalize({
        "time": NOW, "data": {"title": "x", "url": "javascript:alert(1)", "ref": "[k](javascript:x)"},
    }, NOW, None)
    assert e["url"] is None
    assert e["details"][0]["parts"] == [{"text": "[k](javascript:x)", "url": None}]


def test_entries_order():
    a = [
        {"time": NOW - 5, "text": "past-old"},
        {"time": NOW + 9, "text": "later"},
        {"time": NOW - 1, "text": "past-new"},
        {"time": NOW - 3, "timeEnd": NOW + 3, "text": "ongoing"},
        {"time": NOW + 2, "text": "soon"},
    ]
    assert [e["title"] for e in grafana.entries(a, NOW, 10)] == ["ongoing", "soon", "later", "past-new", "past-old"]
    assert [e["title"] for e in grafana.entries(a, NOW, 2)] == ["ongoing", "soon"]


def test_window_compat():
    assert grafana.window({"days_back": 3, "days_ahead": 0}) == (3, 0)
    assert grafana.window({"mode": "upcoming", "days": 14}) == (0, 14)
    assert grafana.window({"mode": "recent", "days": 30}) == (30, 0)


def test_summary_and_extra_fields():
    data = {"title": "t", "summary": "one line", "prio": "high", "owner": ["A", "B"],
            "nested": {"x": 1}, "contact": "Ops", "on_call": True}
    e = grafana.normalize({"time": NOW, "data": data}, NOW)
    assert e["summary"] == "one line"
    assert [(d["label"], d["parts"][0]["text"]) for d in e["details"]] == [
        ("Contact", "Ops"), ("On call", "yes"), ("Owner", "A, B"), ("Prio", "high")]
    assert grafana.normalize({"time": NOW, "data": data}, NOW, show_fields=False)["details"] == []


def test_parts_links():
    p = grafana.parts("see [Overview](/d/abc), https://x.example/a and text", BASE)
    assert p == [
        {"text": "see ", "url": None},
        {"text": "Overview", "url": f"{BASE}/d/abc"},
        {"text": ", ", "url": None},
        {"text": "https://x.example/a", "url": "https://x.example/a"},
        {"text": " and text", "url": None},
    ]
