#!/bin/bash
set -euo pipefail

# Load Slack configuration from .env so it matches the running container
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
fi

# Check that the container uses the same token as .env
container_token=$(docker compose exec -T feature-engine printenv SLACK_TOKEN | tr -d '\r')
if [ "$container_token" != "$SLACK_TOKEN" ]; then
  echo "❌ Slack token mismatch between .env and running container." >&2
  echo "   Run 'docker compose up -d --force-recreate feature-engine' to reload it." >&2
  exit 1
fi

echo "✅ [1/4] Test Slack avant les attaques..."
docker compose exec -T feature-engine python3 feature_engine.py --test-slack

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
