#!/bin/bash
# Petit scénario pour tester les alertes email et Slack

echo "[INFO] Lancement du test : flux sains + attaques..."

# 1. Lancer 5 appels SIPP normaux (sains)
for i in {1..5}; do
  echo "[INFO] Flux sain #$i"
  docker run --rm \
    --network sipp-net \
    --entrypoint sipp \
    my-sipp-client \
      sip-server \
      -sn uac \
      -m 1 \
      -r 1 \
      -d 1000
  sleep 3
done

# 2. Lancer une petite attaque REGISTER flood (ça doit déclencher une alerte)
echo "[ALERTE] Simulation d'une attaque REGISTER flood..."
docker run --rm \
  --network sipp-net \
  -v "$(pwd)/scenario":/opt/sipp/scenarios \
  --entrypoint sipp \
  my-sipp-client \
    -sf /opt/sipp/scenarios/register_flood.xml \
    -m 2 \
    -r 2 \
    -d 2000 \
    sip-server

sleep 5

# 3. Encore 3 appels sains
for i in {6..8}; do
  echo "[INFO] Flux sain #$i"
  docker run --rm \
    --network sipp-net \
    --entrypoint sipp \
    my-sipp-client \
      sip-server \
      -sn uac \
      -m 1 \
      -r 1 \
      -d 1000
  sleep 3
done

# 4. Encore une petite attaque INVITE flood
echo "[ALERTE] Simulation d'une attaque INVITE flood..."
docker run --rm \
  --network sipp-net \
  -v "$(pwd)/scenario":/opt/sipp/scenarios \
  --entrypoint sipp \
  my-sipp-client \
    -sf /opt/sipp/scenarios/invite_flood.xml \
    -m 2 \
    -r 2 \
    -d 2000 \
    sip-server

echo "[INFO] Test terminé ✅"
