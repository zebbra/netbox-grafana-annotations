PLUGINS = ["netbox_grafana_annotations"]

PLUGINS_CONFIG = {
    "netbox_grafana_annotations": {
        "grafana_url": "http://mock-grafana:3000",
        "grafana_public_url": "https://grafana.example.com",
        "cache_timeout": 0,
        "pinned_message": "**Welcome to the demo.** Feeds below are pinned in `configuration.py`; see [README](https://github.com/zebbra/netbox-grafana-annotations).",
        "pinned": [
            {"title": "Maintenance", "color": "pink", "tags": "maintenance", "days_back": 1, "days_ahead": 14,
             "max_entries": 5, "hint": "Maintenance windows: yesterday, ongoing and planned"},
            {"title": "Current T3 Investigations", "color": "red", "tags": "incident,tier3", "days_back": 7,
             "days_ahead": 0, "max_entries": 5, "hint": "These are current Problem/Incident cases from the desk"},
            {"title": "Preview", "color": "teal", "tags": "preview", "days_back": 0, "days_ahead": 0,
             "hint": "Features in acceptance testing on dev"},
            {"title": "Empty feed (hidden)", "tags": "nothing-here", "days_back": 30, "days_ahead": 30},
        ],
    },
}
