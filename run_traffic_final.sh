#!/usr/bin/env bash
# run_traffic_final.sh
# Génère un trafic SIP continu « healthy » à 10 appels/s,
# puis injecte 3 attaques (invite, register, options),
# espacées de 30 s chacune.

set -euo pipefail

# --- Configuration ---------------------------------------------------------
NET="sipp-net"                     # réseau Docker partagé
UAC_IMAGE="my-sipp-client"         # image avec SIPP et vos scénarios
UAS_HOST="sip-server"              # nom du conteneur UAS dans Docker
SCEN_DIR="$(pwd)/scenario"         # chemin local du dossier scenario/

# --- 1) Trafic « healthy » continu -----------------------------------------
echo "[$(date +%T)] ▶ Démarrage du trafic healthy à 10 appels/s"
docker run -d --name healthy-traffic \
  --network "$NET" \
  --entrypoint sipp "$UAC_IMAGE" \
    "$UAS_HOST" -sn uac -r 10

# --- 2) Attaques espacées -------------------------------------------------
for attack in invite_flood register_flood options_flood; do
  echo "[$(date +%T)] ▶ Attente de 30 s avant l'attaque $attack"
  sleep 30

  echo "[$(date +%T)] ▶ Lancement de l'attaque $attack"
  docker run --rm --network "$NET" \
    -v "$SCEN_DIR":/opt/sipp/scenarios:ro \
    --entrypoint sipp "$UAC_IMAGE" \
      "$UAS_HOST" \
      -sf "/opt/sipp/scenarios/${attack}.xml" \
      -m 1 -r 1 -trace_err -trace_msg

done

# --- 3) Arrêt du trafic healthy -------------------------------------------
echo "[$(date +%T)] ▶ Arrêt du trafic healthy"
docker rm -f healthy-traffic

echo "[FIN] Script terminé."
