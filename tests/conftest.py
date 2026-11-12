import sys
import types

try:
    import netbox.plugins  # noqa: F401
except ImportError:
    plugins = types.ModuleType("netbox.plugins")
    plugins.PluginConfig = object
    sys.modules.setdefault("netbox", types.ModuleType("netbox"))
    sys.modules["netbox.plugins"] = plugins
