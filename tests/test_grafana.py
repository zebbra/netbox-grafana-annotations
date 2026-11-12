from netbox_grafana_annotations import grafana

NOW = 1_794_800_000_000
BASE = "https://grafana.example.com"


def test_query_params_upcoming():
    p = dict(grafana.query_params(["maintenance"], False, grafana.UPCOMING, 14, 50, NOW))
    assert p["from"] == NOW and p["to"] == NOW + 14 * grafana.DAY_MS
    assert p["tags"] == "maintenance" and "matchAny" not in p


def test_query_params_recent_multi_tag_any():
    p = grafana.query_params(["a", "b"], True, grafana.RECENT, 7, 50, NOW)
    assert ("tags", "a") in p and ("tags", "b") in p and ("matchAny", "true") in p
    assert dict(p)["to"] == NOW


def test_structured_data():
    e = grafana.normalize({
        "time": NOW - 1000, "timeEnd": NOW + 1000, "tags": ["maintenance", "aci"],
        "text": "<b>ignored</b>",
        "data": {"title": "ACI Exporter", "url": f"{BASE}/d/x", "impact": "Gaps",
                 "contact": "Ops", "jira": [{"key": "T-1", "url": "https://jira/T-1"}]},
    }, NOW, BASE, hide_tags={"maintenance"})
    assert e["title"] == "ACI Exporter" and e["active"]
    assert e["details"] == ["Impact: Gaps", "Contact: Ops"]
    assert e["summary"] == ""
    assert e["links"] == [{"label": "T-1", "url": "https://jira/T-1"}]
    assert e["tags"] == ["aci"]


def test_text_fallback_and_relative_url():
    e = grafana.normalize({
        "time": NOW, "tags": [], "dashboardUID": "abc", "panelId": 3,
        "text": "Deploy &amp; restart<br>second line<br><a href='/x'>Details</a>",
    }, NOW, BASE)
    assert e["title"] == "Deploy & restart"
    assert e["details"] == ["second line"]
    assert e["url"] == f"{BASE}/d/abc?viewPanel=3"
    assert e["end"] is None and not e["active"]


def test_unsafe_urls_dropped():
    e = grafana.normalize({
        "time": NOW, "data": {"title": "x", "url": "javascript:alert(1)",
                              "jira": [{"key": "k", "url": "javascript:x"}]},
    }, NOW, None)
    assert e["url"] is None and e["links"] == []


def test_entries_order():
    a = [{"time": NOW + i, "text": str(i)} for i in (2, 1, 3)]
    assert [e["title"] for e in grafana.entries(a, grafana.UPCOMING, NOW, 2)] == ["1", "2"]
    assert [e["title"] for e in grafana.entries(a, grafana.RECENT, NOW, 2)] == ["3", "2"]


def test_summary_and_extra_fields():
    data = {"title": "t", "summary": "one line", "prio": "high", "owner": ["A", "B"],
            "nested": {"x": 1}, "contact": "Ops", "on_call": True}
    e = grafana.normalize({"time": NOW, "data": data}, NOW)
    assert e["summary"] == "one line"
    assert e["details"] == ["Contact: Ops", "On call: yes", "Owner: A, B", "Prio: high"]
    assert grafana.normalize({"time": NOW, "data": data}, NOW, show_fields=False)["details"] == []
