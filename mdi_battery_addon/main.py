#!/usr/bin/env python3

import os
import json
import time
import threading
import asyncio
import requests
import websockets

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from io import BytesIO
import base64
from datetime import datetime, timedelta
from flask import Flask

##############################################################################
# GLOBALS
##############################################################################
SENSOR_DF = pd.DataFrame(columns=["entity_id", "value", "timestamp"])
SENSOR_DF_LOCK = threading.Lock()

# Latest reading per entity
LAST_READINGS = {}

# Flask app
app = Flask(__name__)

##############################################################################
# ENVIRONMENT VARIABLES
##############################################################################
def env(key, default=None):
    return os.environ.get(key, default)

HA_WS_URL = env("HA_URL", "ws://homeassistant.local:8123/api/websocket")
HA_TOKEN = env("HA_TOKEN", "")
ENTITIES = json.loads(env("ENTITIES", '["sensor.my_phone_battery"]'))
BATTERY_THRESHOLD = float(env("BATTERY_THRESHOLD", "20.0"))
UNRESPONSIVE_MINUTES = int(env("UNRESPONSIVE_MINUTES", "30"))
NOTIFY_SERVICE = env("NOTIFY_SERVICE", "notify.notify")

##############################################################################
# MDI BATTERY SVG PATHS
##############################################################################
MDI_PATHS = {
    # battery-unknown
    "unknown": "M17,4H7V2H17V4M17,4H19V22H5V4H7V6H17V4M15,11C15,9.34 13.66,8 12,8C10.34,8 9,9.34 9,11H11C11,10.45 11.45,10 12,10C12.55,10 13,10.45 13,11C13,11.55 12.55,12 12,12H11C9.9,12 9,12.9 9,14V15H11V14C11,13.45 11.45,13 12,13C12.55,13 13,13.45 13,14C13,14.55 12.55,15 12,15H11C9.9,15 9,15.9 9,17V18H15V17C15,15.66 14,14.66 13,14.16C13.65,13.78 14,13.16 14,12.5C14,11.79 13.7,11.21 13.23,10.76C14.37,10.36 15,9.27 15,8.11V8M17,8V6H7V8H17Z",

    # battery (100%)
    "battery": "M16,4H8V2H16V4M16,4H18V22H6V4H8V6H16V4Z",
    # battery-90
    "battery90": "M16,4H8V2H16V4M16,4H18V9H6V4H8V6H16V4Z",
    # battery-80
    "battery80": "M16,4H8V2H16V4M16,4H18V11H6V4H8V6H16V4Z",
    # battery-60
    "battery60": "M16,4H8V2H16V4M16,4H18V15H6V4H8V6H16V4Z",
    # battery-50
    "battery50": "M16,4H8V2H16V4M16,4H18V17H6V4H8V6H16V4Z",
    # battery-30
    "battery30": "M16,4H8V2H16V4M16,4H18V19H6V4H8V6H16V4Z",
    # battery-20
    "battery20": "M16,4H8V2H16V4M16,4H18V20H6V4H8V6H16V4Z",
    # battery-10
    "battery10": "M16,4H8V2H16V4M16,4H18V21H6V4H8V6H16V4Z"
}

def get_battery_svg(value: float) -> str:
    """
    Pick an MDI battery icon + color based on numeric battery value.
    """
    # Color
    if value >= 80:
        color = "green"
    elif value >= 50:
        color = "orange"
    else:
        color = "red"

    # Path
    if value >= 90:
        path = MDI_PATHS["battery"]
    elif value >= 80:
        path = MDI_PATHS["battery90"]
    elif value >= 60:
        path = MDI_PATHS["battery80"]
    elif value >= 50:
        path = MDI_PATHS["battery60"]
    elif value >= 40:
        path = MDI_PATHS["battery50"]
    elif value >= 30:
        path = MDI_PATHS["battery30"]
    elif value >= 20:
        path = MDI_PATHS["battery20"]
    else:
        path = MDI_PATHS["battery10"]

    svg = f"""
    <svg width="20" height="20" viewBox="0 0 24 24">
      <path fill="{color}" d="{path}" />
    </svg>
    """
    return svg

def get_battery_svg_unknown() -> str:
    """Return a red battery-unknown icon."""
    path = MDI_PATHS["unknown"]
    return f"""
    <svg width="20" height="20" viewBox="0 0 24 24">
      <path fill="red" d="{path}" />
    </svg>
    """

##############################################################################
# NOTIFICATION
##############################################################################
def notify_ha(message: str):
    """Send a notification to Home Assistant if HA_TOKEN is set."""
    if not HA_TOKEN:
        print("[Warn] HA_TOKEN not provided. Skipping notification.")
        return

    rest_url = HA_WS_URL.replace("ws", "http").replace("/api/websocket", "") + "/api/services/" + NOTIFY_SERVICE
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "message": message,
        "title": "Battery Alert"
    }

    try:
        resp = requests.post(rest_url, headers=headers, json=payload, timeout=10)
        print(f"[Info] Notification response: {resp.text}")
    except Exception as e:
        print(f"[Error] Notify request failed: {e}")

##############################################################################
# HANDLE STATE CHANGES
##############################################################################
def handle_state_changed(event_data):
    """
    event_data structure:
      {
        "entity_id": "...",
        "old_state": {...},
        "new_state": {...}
      }
    """
    entity_id = event_data.get("entity_id")
    if entity_id not in ENTITIES:
        return

    new_state = event_data.get("new_state", {})
    state_str = new_state.get("state")
    if not state_str or state_str in ["unknown", "unavailable"]:
        return

    try:
        val = float(state_str)
    except ValueError:
        print(f"[Warn] Non-numeric battery for {entity_id}: {state_str}")
        return

    now = datetime.now()

    LAST_READINGS[entity_id] = {
        "value": val,
        "last_update": now
    }

    # Store for historical graph
    with SENSOR_DF_LOCK:
        global SENSOR_DF
        SENSOR_DF = SENSOR_DF.append({
            "entity_id": entity_id,
            "value": val,
            "timestamp": time.time()
        }, ignore_index=True)

    # Check threshold => notify
    if val < BATTERY_THRESHOLD:
        notify_ha(f"Battery low on '{entity_id}' -> {val:.1f}%")

##############################################################################
# WEBSOCKET LOOP
##############################################################################
async def ha_websocket_loop():
    """Connect to HA WebSocket, subscribe to state_changed, handle relevant events."""
    while True:
        try:
            print(f"[Info] Connecting to {HA_WS_URL}...")
            async with websockets.connect(HA_WS_URL, ping_interval=None) as ws:
                # Wait for auth_required
                msg_auth_req = await ws.recv()
                print("[Debug] auth_required:", msg_auth_req)

                # Send auth
                await ws.send(json.dumps({
                    "type": "auth",
                    "access_token": HA_TOKEN
                }))

                # Wait for auth_ok
                msg_auth_ok = await ws.recv()
                print("[Info] Auth response:", msg_auth_ok)

                # Subscribe to state_changed
                await ws.send(json.dumps({
                    "id": 1,
                    "type": "subscribe_events",
                    "event_type": "state_changed"
                }))
                ack = await ws.recv()
                print("[Info] Subscribed:", ack)

                # Process incoming events
                while True:
                    msg_str = await ws.recv()
                    msg = json.loads(msg_str)
                    if (msg.get("event") and 
                        msg["event"].get("event_type") == "state_changed"):
                        handle_state_changed(msg["event"]["data"])

        except websockets.ConnectionClosedError as e:
            print("[Error] WebSocket closed, retrying in 5s:", e)
            await asyncio.sleep(5)
        except Exception as e:
            print("[Error] Unexpected error in ha_websocket_loop:", e)
            await asyncio.sleep(5)

##############################################################################
# FLASK ROUTES
##############################################################################
@app.route("/")
def index():
    return """
    <h1>MDI Battery Entities Add-on</h1>
    <ul>
      <li><a href="/status">View Battery Status</a></li>
      <li><a href="/graph">View Graph</a></li>
    </ul>
    """

@app.route("/status")
def status_page():
    """Shows a table of each entity with MDI icons + last update time."""
    cutoff = datetime.now() - timedelta(minutes=UNRESPONSIVE_MINUTES)

    html = [
        "<h2>Battery Status</h2>",
        "<table border='1' cellpadding='5'>",
        "<tr><th>Entity</th><th>Battery</th><th>Last Update</th></tr>"
    ]

    if not ENTITIES:
        html.append("<tr><td colspan='3'>No entities configured.</td></tr>")
    else:
        for entity_id in ENTITIES:
            data = LAST_READINGS.get(entity_id)
            if not data:
                # No data received yet
                html.append(f"<tr><td>{entity_id}</td><td>?</td><td>No data</td></tr>")
                continue

            val = data["value"]
            last_update = data["last_update"]

            if last_update < cutoff:
                # Stale => red unknown icon
                battery_svg = get_battery_svg_unknown()
                battery_display = f"{battery_svg} Stale"
            else:
                # Normal => color-coded icon
                battery_svg = get_battery_svg(val)
                battery_display = f"{battery_svg} {val:.1f}%"

            html.append(
                f"<tr><td>{entity_id}</td>"
                f"<td>{battery_display}</td>"
                f"<td>{last_update}</td></tr>"
            )

    html.append("</table>")
    return "".join(html)

@app.route("/graph")
def graph_page():
    """Plots historical battery data using matplotlib."""
    with SENSOR_DF_LOCK:
        if SENSOR_DF.empty:
            return "No data yet."

        plt.figure(figsize=(8, 4))

        for ent in SENSOR_DF["entity_id"].unique():
            sub_df = SENSOR_DF[SENSOR_DF["entity_id"] == ent].copy()
            sub_df.sort_values("timestamp", inplace=True)
            plt.plot(sub_df["timestamp"], sub_df["value"], label=ent)

        plt.legend()
        plt.xlabel("Timestamp")
        plt.ylabel("Battery Level")
        plt.title("Battery Levels Over Time")

        buf = BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return f'<img src="data:image/png;base64,{img_b64}" />'

##############################################################################
# STARTUP
##############################################################################
def start_flask():
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)

def main():
    # Run Flask in background
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Run websocket loop in main thread
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ha_websocket_loop())

if __name__ == "__main__":
    main()
