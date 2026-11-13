"""
Minimal stand-in for Grafana's GET /api/annotations with demo data.

Times are relative to now, so the demo always has a past, an ongoing and an
upcoming maintenance window. Filters like Grafana: tags (all, or any with
matchAny=true), from/to overlap, newest first, limit.

    python mock_grafana.py [port]
"""
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

H = 3_600_000
D = 24 * H


def now():
    return int(time.time() * 1000)


def data():
    n = now(); day = n - n % D
    G = "https://grafana.example.com"
    SD = "https://servicedesk.example.com/ticket"
    return [
        {"id": 1, "time": day - 1 * D + 7 * H, "timeEnd": day - 1 * D + 9 * H, "tags": ["maintenance", "firewall"],
         "text": "Firewall cluster reboot",
         "data": {"title": "Firewall cluster reboot", "impact": "No impact expected (HA)", "contact": "Security team", "url": f"{G}/d/maintenance"}},
        {"id": 2, "time": n - 1 * H, "timeEnd": n + 2 * H, "tags": ["maintenance", "metrics"],
         "text": "Metrics storage migration",
         "data": {"title": "Metrics storage migration", "summary": "Moving the time series database to new nodes.",
                  "impact": "Dashboards may show short gaps", "contact": "Platform team", "url": f"{G}/d/maintenance"}},
        {"id": 3, "time": day + 1 * D + 6 * H, "timeEnd": day + 1 * D + 8 * H, "tags": ["maintenance", "network", "core"],
         "text": "Core switch firmware upgrade",
         "data": {"title": "Core switch firmware upgrade", "summary": "Rolling upgrade, one chassis at a time.",
                  "impact": "Brief failover per site", "contact": "Network operations", "url": f"{G}/d/maintenance",
                  "jira": ["[OPS-1423](https://jira.example.com/browse/OPS-1423)"]}},
        {"id": 21, "time": n - 5 * H, "timeEnd": n + 6 * H, "tags": ["incident", "tier3", "wifi"],
         "text": "Access points dropping clients",
         "data": {"title": "Access points dropping clients", "summary": "Clients on floor 3 lose the connection every few minutes.",
                  "status": "Investigating", "ticket": f"[INC0041872]({SD}/INC0041872)", "url": f"{G}/d/wifi"}},
        # created by hand in Grafana: plain text, no data, attached to a dashboard panel
        {"id": 23, "time": day - 1 * D + 14 * H, "timeEnd": day - 1 * D + 15 * H + 30 * 60_000,
         "tags": ["incident", "tier3", "firewall"], "dashboardUID": "firewalls", "panelId": 2,
         "text": "Firewall in conserve mode\nMemory exhausted, new sessions dropped until failover", "data": {}},
        {"id": 22, "time": day - 2 * D + 9 * H, "timeEnd": day - 2 * D + 15 * H, "tags": ["incident", "tier3", "wan"],
         "text": "Packet loss on WAN uplink",
         "data": {"title": "Packet loss on WAN uplink", "summary": "Carrier replaced a faulty line card.",
                  "status": "Resolved", "ticket": f"[PRB0003318]({SD}/PRB0003318)", "url": f"{G}/d/wan"}},
        {"id": 11, "time": day - 1 * D + 10 * H, "tags": ["changelog", "netbox"],
         "text": "Interface severity",
         "data": {"title": "Interface alerts by severity", "summary": "Set a severity per interface in NetBox; empty means no alert.",
                  "url": f"{G}/d/changelog", "jira": ["[OPS-1388](https://jira.example.com/browse/OPS-1388)"],
                  "docs": "[Severity guide](https://wiki.example.com/severity)"}},
        {"id": 12, "time": day - 3 * D + 10 * H, "tags": ["changelog", "grafana"],
         "text": "Grafana 13", "data": {"title": "Grafana 13", "summary": "Security update, new panel options.", "url": f"{G}/d/changelog"}},
        {"id": 13, "time": day - 8 * D + 10 * H, "tags": ["changelog", "monitoring", "wifi"],
         "text": "Access point monitoring", "data": {"title": "Access point monitoring", "summary": "All access points with client counts and radio status.", "url": f"{G}/d/changelog"}},
    ]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path != "/api/annotations":
            self.send_error(404)
            return
        q = parse_qs(url.query)
        tags = q.get("tags", [])
        start = int(q.get("from", ["0"])[0])
        end = int(q.get("to", [str(10**15)])[0])
        match = any if q.get("matchAny", ["false"])[0] == "true" else all
        out = [
            a for a in data()
            if (not tags or match(t in a["tags"] for t in tags))
            and a["time"] <= end and (a.get("timeEnd") or a["time"]) >= start
        ]
        out.sort(key=lambda a: a["time"], reverse=True)
        body = json.dumps(out[: int(q.get("limit", ["100"])[0])]).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    print(f"mock grafana on :{port}", flush=True)
    HTTPServer(("", port), Handler).serve_forever()
