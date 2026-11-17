"""Dashboard of user admin with two example widgets (maintenance and incidents are pinned in configuration.py) (run via the seed service)."""
from extras.models import Dashboard
from users.models import User

WIDGET = "netbox_grafana_annotations.GrafanaAnnotationsWidget"


def config(tags, back, ahead, entries=5, fields=True, hint=""):
    return {
        "tags": tags, "match_any": False, "days_back": back, "days_ahead": ahead,
        "max_entries": entries, "show_tags": True, "show_fields": fields, "hint": hint,
    }


widgets = [
    ("Changelog", "purple", config("changelog", 30, 0, hint="What changed in NetBox, Grafana and monitoring")),
    ("Past maintenance", "gray", config("maintenance", 30, 0, entries=10, fields=False)),
]
ids = [f"{i}{i}{i}{i}{i}{i}{i}{i}-{i}{i}{i}{i}-4{i}{i}{i}-8{i}{i}{i}-{i * 12}" for i in "12"]
layout = [
    {"id": wid, "x": 6 * (n % 2), "y": 5 * (n // 2), "w": 6, "h": 5}
    for n, wid in enumerate(ids)
]
cfg = {wid: {"class": WIDGET, "title": t, "color": c, "config": conf} for wid, (t, c, conf) in zip(ids, widgets)}

user = User.objects.get(username="admin")
Dashboard.objects.update_or_create(user=user, defaults={"layout": layout, "config": cfg})
print("dashboard seeded")
