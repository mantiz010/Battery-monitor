# MDI Battery Entities Add-on

This add-on connects to Home Assistant via WebSocket to monitor battery entity IDs, displaying:

- **MDI battery icons** (inline SVG) in **green/orange/red** based on the numeric level.
- A **red unknown** battery icon if no updates for X minutes (stale).
- An optional notification to Home Assistant if battery < threshold.
- A **graph** of historical battery levels (using pandas + matplotlib).

## Installation

1. In Home Assistant, go to **Settings > Add-ons > Add-on Store**.
2. Click the **...** menu (top-right) > **Repositories**.
3. Add the GitHub URL of your repo, e.g. `https://github.com/YourUser/mdi-battery-addons`.
4. You should see **"MDI Battery Entities Add-on"**. Click **Install**.
5. Configure:
   - `HA_URL`: e.g., `ws://homeassistant.local:8123/api/websocket`
   - `HA_TOKEN`: A long-lived token
   - `ENTITIES`: List of sensor entity IDs
   - `BATTERY_THRESHOLD`: e.g. 20.0
   - `UNRESPONSIVE_MINUTES`: e.g. 30
   - `NOTIFY_SERVICE`: e.g. `notify.notify`
6. **Start** the add-on.
7. **Open Web UI**. Check out:
   - **`/status`**: A table with color-coded battery icons or red unknown if stale.
   - **`/graph`**: A matplotlib chart of battery levels over time.

## Updating the Icons

- The SVG paths are stored in `MDI_PATHS`. Feel free to add more battery icons (battery70, battery40, etc.) or custom colors.

Enjoy your color-coded MDI battery monitor!
