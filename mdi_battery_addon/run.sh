#!/usr/bin/env bash
set -e

CONFIG_PATH="/data/options.json"

echo "[Info] Starting MDI Battery Entities Add-on..."

HA_URL=$(jq --raw-output '.HA_URL' $CONFIG_PATH)
HA_TOKEN=$(jq --raw-output '.HA_TOKEN' $CONFIG_PATH)
ENTITIES=$(jq --raw-output '.ENTITIES | @json' $CONFIG_PATH)
BATTERY_THRESHOLD=$(jq --raw-output '.BATTERY_THRESHOLD' $CONFIG_PATH)
UNRESPONSIVE_MINUTES=$(jq --raw-output '.UNRESPONSIVE_MINUTES' $CONFIG_PATH)
NOTIFY_SERVICE=$(jq --raw-output '.NOTIFY_SERVICE' $CONFIG_PATH)

export HA_URL HA_TOKEN ENTITIES BATTERY_THRESHOLD UNRESPONSIVE_MINUTES NOTIFY_SERVICE

echo "[Info] HA_URL: $HA_URL"
echo "[Info] ENTITIES: $ENTITIES"
echo "[Info] Battery threshold: $BATTERY_THRESHOLD"
echo "[Info] Unresponsive after: $UNRESPONSIVE_MINUTES mins"
echo "[Info] Notify service: $NOTIFY_SERVICE"

python3 /main.py
