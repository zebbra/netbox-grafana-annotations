from django.urls import reverse
from netbox.plugins import PluginTemplateExtension

from . import grafana
from .widgets import GrafanaAnnotationsWidget


class PinnedFeeds(PluginTemplateExtension):
    """Feeds from PLUGINS_CONFIG["pinned"], shown above every user's dashboard."""

    def head(self):
        request = self.context["request"]
        cards = grafana.pinned_cards(self.context["config"].get("pinned"))
        if not cards or request.path != reverse("home"):
            return ""
        for card in cards:
            widget = GrafanaAnnotationsWidget(
                title=card["title"], config={**GrafanaAnnotationsWidget.default_config, **card["config"]},
            )
            card["body"] = widget.render(request)
        return self.render("netbox_grafana_annotations/pinned.html", {"cards": cards})


template_extensions = [PinnedFeeds]
