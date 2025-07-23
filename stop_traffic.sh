#!/bin/bash
# stop_traffic.sh – arrête et supprime tous les conteneurs de trafic SIP

set -e

# Liste des conteneurs à stopper/supprimer
CONTAINERS=(
  normal-traffic
  attack-invite
  attack-register
  attack-options
)

echo "Arrêt et suppression des conteneurs SIPp…"
for c in "${CONTAINERS[@]}"; do
  if docker ps -a --format '{{.Names}}' | grep -qw "$c"; then
    echo " • $c"
    docker rm -f "$c"
  else
    echo " • $c (non trouvé)"
  fi
done

echo "Terminé."
