#!/usr/bin/env bash
set -e

CONFIG_PATH="/data/options.json"

echo "[Info] Starting MDI Battery Add-on with full features..."

HA_URL=$(jq --raw-output '.HA_URL' $CONFIG_PATH)
HA_TOKEN=$(jq --raw-output '.HA_TOKEN' $CONFIG_PATH)
ENTITIES=$(jq --raw-output '.ENTITIES | @json' $CONFIG_PATH)
BATTERY_THRESHOLD=$(jq --raw-output '.BATTERY_THRESHOLD' $CONFIG_PATH)
UNRESPONSIVE_MINUTES=$(jq --raw-output '.UNRESPONSIVE_MINUTES' $CONFIG_PATH)
NOTIFY_SERVICE=$(jq --raw-output '.NOTIFY_SERVICE' $CONFIG_PATH)

# Export so main.py can read them
export HA_URL HA_TOKEN ENTITIES BATTERY_THRESHOLD UNRESPONSIVE_MINUTES NOTIFY_SERVICE

echo "[Info] HA_URL: $HA_URL"
echo "[Info] ENTITIES: $ENTITIES"
echo "[Info] BATTERY_THRESHOLD: $BATTERY_THRESHOLD"
echo "[Info] UNRESPONSIVE_MINUTES: $UNRESPONSIVE_MINUTES"
echo "[Info] NOTIFY_SERVICE: $NOTIFY_SERVICE"

python3 /main.py
