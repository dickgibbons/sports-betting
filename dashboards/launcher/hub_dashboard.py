#!/usr/bin/env python3
"""
Sports dashboard hub: landing tile -> sport-specific links (same host, different ports).

Does not start other processes over HTTP (security); run soccer/hockey/streamlit via nohup/systemd
as today, then open the links from this page.
"""

import os
from flask import Flask, render_template, request

_ROOT = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, root_path=_ROOT, template_folder="templates")
app.config["TEMPLATES_AUTO_RELOAD"] = True


def _link_base() -> str:
    """Build http(s)://hostname for links to sibling services on other ports."""
    # Prefer X-Forwarded-* when behind a reverse proxy
    proto = request.headers.get("X-Forwarded-Proto", request.scheme)
    host = request.headers.get("X-Forwarded-Host") or request.host
    if ":" in host and host.count(":") == 1 and "[" not in host:
        host = host.split(":")[0]
    return f"{proto}://{host}"


@app.route("/")
def home():
    return render_template("home.html", link_base=_link_base())


@app.route("/hub")
def hub():
    ports = {
        "mlb": int(os.environ.get("PORT_MLB", "8501")),
        "soccer_flask": int(os.environ.get("PORT_SOCCER_FLASK", "8504")),
        "soccer_streamlit": int(os.environ.get("PORT_SOCCER_STREAMLIT", "8506")),
        "hockey_flask": int(os.environ.get("PORT_HOCKEY_FLASK", "8503")),
        "nhl_streamlit": int(os.environ.get("PORT_NHL_STREAMLIT", "8505")),
    }
    base = _link_base()
    return render_template(
        "hub.html",
        link_base=base,
        ports=ports,
    )


if __name__ == "__main__":
    port = int(os.environ.get("HUB_DASHBOARD_PORT", "8500"))
    # Bind all interfaces so the VPS is reachable by public IP (not 127.0.0.1 only).
    host = os.environ.get("HUB_DASHBOARD_HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    print(f"Hub dashboard: http://{host}:{port}/  (open http://<server-ip>:{port}/ from your browser)", flush=True)
    app.run(debug=debug, port=port, host=host, use_reloader=debug)
