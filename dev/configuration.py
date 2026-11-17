PLUGINS = ["netbox_grafana_annotations"]

PLUGINS_CONFIG = {
    "netbox_grafana_annotations": {
        "grafana_url": "http://mock-grafana:3000",
        "grafana_public_url": "https://grafana.example.com",
        "cache_timeout": 0,
        "pinned": [
            {"title": "Maintenance", "color": "pink", "width": 6, "tags": "maintenance", "days_back": 1, "days_ahead": 14,
             "max_entries": 5, "hint": "Maintenance windows: yesterday, ongoing and planned"},
            {"title": "Current T3 Investigations", "color": "red", "width": 6, "tags": "incident,tier3", "days_back": 7,
             "days_ahead": 0, "max_entries": 5, "hint": "These are current Problem/Incident cases from the desk"},
        ],
    },
}
