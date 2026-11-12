from netbox.plugins import PluginConfig

__version__ = "0.1.0"


class GrafanaAnnotationsConfig(PluginConfig):
    name = "netbox_grafana_annotations"
    verbose_name = "Grafana Annotations"
    description = "Dashboard widget showing Grafana annotations, e.g. maintenance windows or a changelog"
    version = __version__
    base_url = "grafana-annotations"
    min_version = "4.0.0"
    default_settings = {
        "grafana_url": None,
        "grafana_public_url": None,
        "token": None,
        "token_env": "GRAFANA_ANNOTATIONS_TOKEN",
        "timeout": 5,
        "verify_ssl": True,
        "cache_timeout": 300,
    }

    def ready(self):
        super().ready()
        from . import widgets  # noqa: F401


config = GrafanaAnnotationsConfig
