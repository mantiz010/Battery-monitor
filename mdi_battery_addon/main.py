#!/usr/bin/env python3

import os
import json
import time
import threading
import asyncio
import logging
import requests
import websockets
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
from flask import Flask

# -----------------------------------------------------------------------------
# Global Settings
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MDI Battery Add-on")

SENSOR_DF = pd.DataFrame(columns=["entity_id", "value", "timestamp"])
SENSOR_DF_LOCK = threading.Lock()
LAST_READINGS = {}

app = Flask(__name__)

# -----------------------------------------------------------------------------
# Load Environment Variables
# -----------------------------------------------------------------------------
HA_WS_URL = os.getenv("HA_URL", "ws://homeassistant.local:8123/api/websocket")
HA_TOKEN = os.getenv("HA_TOKEN", "")
ENTITIES = json.loads(os.getenv("ENTITIES", '[]'))
BATTERY_THRESHOLD = float(os.getenv("BATTERY_THRESHOLD", "20.0"))
UNRESPONSIVE_MINUTES = int(os.getenv("UNRESPONSIVE_MINUTES", "30"))
NOTIFY_SERVICE = os.getenv("NOTIFY_SERVICE", "notify.notify")

# -----------------------------------------------------------------------------
# WebSocket Handling
# -----------------------------------------------------------------------------
async def ha_websocket_loop():
    while True:
        try:
            logger.info("Connecting to Home Assistant WebSocket...")
            async with websockets.connect(HA_WS_URL, ping_interval=None) as ws:
                # Authenticate with HA
                await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
                auth_response = await ws.recv()
                logger.info(f"Auth Response: {auth_response}")

                # Subscribe to state_changed events
                await ws.send(json.dumps({
                    "id": 1,
                    "type": "subscribe_events",
                    "event_type": "state_changed"
                }))
                sub_response = await ws.recv()
                logger.info(f"Subscribed to state_changed: {sub_response}")

                # Process messages
                while True:
                    message = await ws.recv()
                    process_state_changed(json.loads(message))

        except websockets.ConnectionClosedError as e:
            logger.warning(f"WebSocket disconnected: {e}, retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket loop: {e}")
            await asyncio.sleep(5)

def process_state_changed(event):
    """Handle state_changed events."""
    entity_id = event.get("entity_id")
    if entity_id not in ENTITIES:
        return

    new_state = event.get("new_state", {})
    state_value = new_state.get("state")
    try:
        value = float(state_value)
        now = datetime.now()
        LAST_READINGS[entity_id] = {"value": value, "last_update": now}
        with SENSOR_DF_LOCK:
            SENSOR_DF.loc[len(SENSOR_DF)] = [entity_id, value, time.time()]
        if value < BATTERY_THRESHOLD:
            send_notification(f"Low battery alert for {entity_id}: {value}%")
    except ValueError:
        logger.warning(f"Non-numeric state for {entity_id}: {state_value}")

# -----------------------------------------------------------------------------
# Notifications
# -----------------------------------------------------------------------------
def send_notification(message):
    """Send a notification to Home Assistant."""
    if not HA_TOKEN:
        logger.warning("No HA_TOKEN set, skipping notification.")
        return
    notify_url = HA_WS_URL.replace("ws", "http").replace("/api/websocket", "/api/services/" + NOTIFY_SERVICE)
    headers = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}
    payload = {"message": message}
    try:
        response = requests.post(notify_url, headers=headers, json=payload)
        logger.info(f"Notification sent: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

# -----------------------------------------------------------------------------
# Flask Routes
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    return "<h1>MDI Battery Add-on</h1><ul><li><a href='/status'>/status</a></li><li><a href='/graph'>/graph</a></li></ul>"

@app.route("/health")
def health():
    return "OK", 200

@app.route("/status")
def status():
    html = ["<h2>Battery Status</h2>", "<table><tr><th>Entity</th><th>Battery</th><th>Last Update</th></tr>"]
    cutoff = datetime.now() - timedelta(minutes=UNRESPONSIVE_MINUTES)
    for entity_id, data in LAST_READINGS.items():
        status = f"{data['value']}%" if data["last_update"] > cutoff else "Stale"
        html.append(f"<tr><td>{entity_id}</td><td>{status}</td><td>{data['last_update']}</td></tr>")
    html.append("</table>")
    return "".join(html)

@app.route("/graph")
def graph():
    with SENSOR_DF_LOCK:
        if SENSOR_DF.empty:
            return "No data to display."
        plt.figure()
        for entity in SENSOR_DF["entity_id"].unique():
            sub = SENSOR_DF[SENSOR_DF["entity_id"] == entity]
            plt.plot(sub["timestamp"], sub["value"], label=entity)
        plt.legend()
        plt.savefig("graph.png")
    return "<h2>Graph</h2><img src='graph.png' />"

# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------
def start_flask():
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)

def main():
    threading.Thread(target=start_flask, daemon=True).start()
    asyncio.run(ha_websocket_loop())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
