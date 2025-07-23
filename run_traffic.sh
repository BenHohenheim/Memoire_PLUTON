#!/bin/bash
# run_traffic.sh – lance tous les flux SIP pour 30 min (arrêt manuel de la capture)

# 1. Trafic sain – 92 500 appels (≈51 call/s)
docker run -d --name normal-traffic \
  --network sipp-net \
  --entrypoint sipp \
  my-sipp-client \
    sip-server \
    -sn uac \
    -l 92500 \
    -r 51 \
    -d 1800

# 2. INVITE Flood – 37 000 INVITE (≈21 INVITE/s)
docker run -d --name attack-invite \
  --network sipp-net \
  -v "$(pwd)/scenario":/opt/sipp/scenarios \
  --entrypoint sipp \
  my-sipp-client \
    -sf /opt/sipp/scenarios/invite_flood.xml \
    -l 37000 \
    -r 21 \
    -d 1800 \
    sip-server

# 3. REGISTER Flood – 27 750 REGISTER (≈15 REGISTER/s)
docker run -d --name attack-register \
  --network sipp-net \
  -v /home/benhohenheim/SIPp-Docker/scenario:/opt/sipp/scenarios \
  --entrypoint sipp \
  my-sipp-client \
    -sf /opt/sipp/scenarios/register_flood.xml \
    -l 27750 \
    -r 15 \
    -d 1800 \
    sip-server

# 4. OPTIONS Flood – 18 500 OPTIONS (≈10 OPTIONS/s)
docker run -d --name attack-options \
  --network sipp-net \
  -v "$(pwd)/scenario":/opt/sipp/scenarios \
  --entrypoint sipp \
  my-sipp-client \
    -sf /opt/sipp/scenarios/options_flood.xml \
    -l 18500 \
    -r 10 \
    -d 1800 \
    sip-server

echo "Tous les flux SIP ont démarré (durée 30 min)."
echo "Arrêtez manuellement la capture tcpdump quand vous le souhaitez."
