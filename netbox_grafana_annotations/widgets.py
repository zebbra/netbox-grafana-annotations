import json
import os
import time
from hashlib import sha256

import requests
from django import forms
from django.conf import settings
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from extras.dashboard.utils import register_widget
from extras.dashboard.widgets import DashboardWidget, WidgetConfigForm

from . import grafana

try:
    from utilities.proxy import resolve_proxies
except ImportError:
    def resolve_proxies(url=None, protocol=None, context=None):
        return getattr(settings, "HTTP_PROXIES", None)


def plugin_settings():
    return settings.PLUGINS_CONFIG.get("netbox_grafana_annotations", {})


@register_widget
class GrafanaAnnotationsWidget(DashboardWidget):
    default_title = _("Grafana Annotations")
    description = _("Grafana annotations filtered by tags, e.g. maintenance windows, a changelog or incidents.")
    template_name = "netbox_grafana_annotations/widget.html"
    default_config = {
        "tags": "",
        "match_any": False,
        "days_back": 7,
        "days_ahead": 14,
        "max_entries": 10,
        "show_tags": True,
        "show_fields": True,
    }
    width = 4
    height = 4

    class ConfigForm(WidgetConfigForm):
        tags = forms.CharField(
            label=_("Tags"),
            required=False,
            help_text=_("Comma-separated Grafana annotation tags"),
        )
        match_any = forms.BooleanField(
            label=_("Match any tag"),
            required=False,
            help_text=_("Default: an annotation must carry all tags"),
        )
        days_back = forms.IntegerField(
            label=_("Days back"),
            min_value=0,
            max_value=3650,
            help_text=_("Past entries to include, 0 for none"),
        )
        days_ahead = forms.IntegerField(
            label=_("Days ahead"),
            min_value=0,
            max_value=3650,
            help_text=_("Upcoming entries to include, 0 for none"),
        )
        max_entries = forms.IntegerField(label=_("Max entries"), min_value=1, max_value=100)
        show_tags = forms.BooleanField(label=_("Show tags"), required=False)
        show_fields = forms.BooleanField(
            label=_("Show fields"),
            required=False,
            help_text=_("Further fields of the annotation data as key: value"),
        )
        hint = forms.CharField(
            label=_("Hint"),
            required=False,
            help_text=_("Shown on hover over the info icon, e.g. what this widget lists"),
        )

    def render(self, request):
        return render_to_string(self.template_name, self.get_context())

    def get_context(self):
        conf = plugin_settings()
        api_url = conf.get("grafana_url")
        if not api_url:
            return {"error": _("grafana_url is not configured for netbox_grafana_annotations")}
        public_url = conf.get("grafana_public_url") or api_url

        config = {**self.default_config, **self.config}
        tags = grafana.parse_tags(config["tags"])
        days_back, days_ahead = grafana.window(config)
        now_ms = int(time.time() * 1000)

        try:
            annotations = self.fetch(conf, api_url, tags, config, days_back, days_ahead, now_ms)
        except (requests.exceptions.RequestException, ValueError) as e:
            return {"error": e}

        items = grafana.entries(
            annotations, now_ms, config["max_entries"], public_url,
            hide_tags=set(tags), show_fields=config.get("show_fields", True),
        )
        return {
            "entries": items,
            "only_upcoming": days_back == 0,
            "dim_past": days_back > 0 and days_ahead > 0,
            "show_tags": config.get("show_tags"),
            "hint": config.get("hint"),
        }

    def fetch(self, conf, api_url, tags, config, days_back, days_ahead, now_ms):
        ttl = conf.get("cache_timeout", 300)
        bucket = now_ms // (ttl * 1000) if ttl else now_ms
        key_src = json.dumps([api_url, tags, config, bucket], sort_keys=True, default=str)
        key = "netbox_grafana_annotations_" + sha256(key_src.encode()).hexdigest()
        if ttl and (cached := cache.get(key)) is not None:
            return cached

        limit = config["max_entries"] if days_ahead == 0 else 100
        params = grafana.query_params(tags, config.get("match_any"), days_back, days_ahead, limit, now_ms)
        headers = {"Accept": "application/json", "User-Agent": f"NetBox/{settings.RELEASE.version}"}
        token = conf.get("token") or os.environ.get(conf.get("token_env", "GRAFANA_ANNOTATIONS_TOKEN"))
        if token:
            headers["Authorization"] = f"Bearer {token}"
        url = api_url.rstrip("/") + "/api/annotations"
        response = requests.get(
            url,
            params=params,
            headers=headers,
            proxies=resolve_proxies(url=url, context={"client": self}),
            timeout=conf.get("timeout", 5),
            verify=conf.get("verify_ssl", True),
        )
        response.raise_for_status()
        annotations = response.json()
        if not isinstance(annotations, list):
            raise ValueError("unexpected response from Grafana")
        if ttl:
            cache.set(key, annotations, ttl)
        return annotations
