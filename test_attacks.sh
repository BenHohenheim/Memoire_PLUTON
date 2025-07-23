#!/bin/bash
set -e

# CONFIG SLACK
SLACK_TOKEN="xoxb-9235756128886-9236906689765-lzePQh23MYMKxGINpwRbzWMb"
SLACK_CHANNEL="#sip-alerts"

echo "✅ [1/4] Test Slack avant les attaques..."
docker exec -i feature-engine python3 - <<EOF
from slack_sdk import WebClient
slack = WebClient(token="$SLACK_TOKEN")
slack.chat_postMessage(channel="$SLACK_CHANNEL", text="✅ Test Slack OK depuis feature-engine (avant attaques)")
EOF

echo "⏳ Attente 3s avant d'envoyer les attaques..."
sleep 3

# ✅ [2/4] Attaque INVITE flood
echo "🚀 [2/4] Lancement attaque INVITE flood..."
docker run --rm --network sipp-net \
  -v "$(pwd)/scenario":/opt/sipp/scenarios \
  --entrypoint sipp my-sipp-client \
  -sf /opt/sipp/scenarios/invite_flood.xml \
  -r 5 -m 20 sip-server
echo "✅ Attaque INVITE terminée, Slack devrait recevoir une alerte !"
sleep 10

# ✅ [3/4] Attaque REGISTER flood
echo "🚀 [3/4] Lancement attaque REGISTER flood..."
docker run --rm --network sipp-net \
  -v "$(pwd)/scenario":/opt/sipp/scenarios \
  --entrypoint sipp my-sipp-client \
  -sf /opt/sipp/scenarios/register_flood.xml \
  -r 5 -m 20 sip-server
echo "✅ Attaque REGISTER terminée, Slack devrait recevoir une alerte !"
sleep 10

# ✅ [4/4] Attaque OPTIONS flood
echo "🚀 [4/4] Lancement attaque OPTIONS flood..."
docker run --rm --network sipp-net \
  -v "$(pwd)/scenario":/opt/sipp/scenarios \
  --entrypoint sipp my-sipp-client \
  -sf /opt/sipp/scenarios/options_flood.xml \
  -r 5 -m 20 sip-server
echo "✅ Attaque OPTIONS terminée, Slack devrait recevoir une alerte !"

echo "🎯 Toutes les attaques ont été envoyées. Vérifie ton Slack !"
