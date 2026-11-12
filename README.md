# netbox-grafana-annotations

A NetBox dashboard widget that lists Grafana annotations filtered by tags: upcoming maintenance windows, a changelog, deployments, incidents.

NetBox fetches the annotations server-side (the Grafana token never reaches the browser) and caches them briefly. Each widget has its own tags, so a dashboard can show «Maintenance» (upcoming) next to «Changelog» (recent).

## Install

```sh
pip install git+https://github.com/zebbra/netbox-grafana-annotations.git@v0.1.1
```

```python
PLUGINS = ["netbox_grafana_annotations"]

PLUGINS_CONFIG = {
    "netbox_grafana_annotations": {
        "grafana_url": "http://grafana.monitoring.svc",        # used for API calls
        "grafana_public_url": "https://grafana.example.com",  # used for links, defaults to grafana_url
    },
}
```

| Setting | Default | |
|---|---|---|
| `grafana_url` | – | Grafana base URL for API calls (required) |
| `grafana_public_url` | `grafana_url` | Base URL for links in the widget |
| `token` | – | Grafana service account token |
| `token_env` | `GRAFANA_ANNOTATIONS_TOKEN` | Environment variable read when `token` is not set |
| `timeout` | `5` | Request timeout in seconds |
| `verify_ssl` | `True` | TLS verification for the API call |
| `cache_timeout` | `300` | Cache lifetime in seconds, `0` disables caching |

Proxies follow NetBox's `HTTP_PROXIES`.

## Grafana token

Create a service account with role **Viewer** and a token for it. Viewer can read organization annotations; nothing else is needed.

## Widget

Add «Grafana Annotations» on the NetBox dashboard and configure:

- **Tags**: comma-separated; by default an annotation must carry all of them, «Match any tag» relaxes that
- **Show**: «Upcoming and ongoing» (from now, oldest first, ongoing regions marked) or «Recent» (newest first)
- **Days**: how far ahead or back to look
- **Max entries**, **Show tags** (the filter tags themselves are never shown)

## Annotation format

Any annotation works: the first line of its text becomes the title, further lines become details, HTML is stripped. Links point to the annotation's dashboard and panel if it has one.

Annotations written by automation can carry structured fields in `data`, which take precedence:

```json
{
  "time": 1794812400000,
  "timeEnd": 1794819600000,
  "tags": ["maintenance", "aci"],
  "text": "<b>ACI exporter deployment</b><br>…",
  "data": {
    "title": "ACI exporter deployment",
    "url": "https://grafana.example.com/d/maintenance/maintenance",
    "impact": "Short gaps in ACI metrics",
    "contact": "Jane Doe",
    "jira": [{"key": "OPS-123", "url": "https://jira.example.com/browse/OPS-123"}]
  }
}
```

Only `http(s)` URLs are rendered as links.

## Development

```sh
PYTHONPATH=. uvx pytest tests
```

## License

MIT
