from django.template.loader import render_to_string
from django.urls import reverse
from netbox.plugins import PluginTemplateExtension

from . import grafana
from .widgets import GrafanaAnnotationsWidget


class PinnedFeeds(PluginTemplateExtension):
    """Message and feeds from PLUGINS_CONFIG, shown above every user's dashboard. Empty feeds are hidden."""

    def head(self):
        config = self.context["config"]
        if self.context["request"].path != reverse("home"):
            return ""
        cards = []
        for card in grafana.pinned_cards(config.get("pinned")):
            widget = GrafanaAnnotationsWidget(
                title=card["title"], config={**GrafanaAnnotationsWidget.default_config, **card["config"]},
            )
            context = widget.get_context()
            if context.get("error") or context.get("entries"):
                card["body"] = render_to_string(widget.template_name, context)
                cards.append(card)
        message = config.get("pinned_message")
        if not cards and not message:
            return ""
        return self.render("netbox_grafana_annotations/pinned.html", {"cards": cards, "message": message})


template_extensions = [PinnedFeeds]
