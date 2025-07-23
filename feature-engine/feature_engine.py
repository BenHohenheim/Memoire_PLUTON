#!/usr/bin/env python3
import sys
import json
import time
import os
import requests
import logging
from slack_sdk import WebClient

# === CONFIGURATION ===
TIMEOUT = 4.0  # secondes pour considérer une session terminée
default_url = "http://pluton-api:8000/predict"
API_URL = os.getenv("PREDICT_URL", default_url)
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")

# Initialisation Slack
slack = WebClient(token=SLACK_TOKEN)

# Ordre attendu des 11 features par le modèle
FEATURE_NAMES = [
    "session_duration",  # durée de la session
    "nb_frames",         # nombre total de paquets
    "nb_invite",         # nombre de méthodes INVITE
    "nb_register",       # nombre de méthodes REGISTER
    "nb_options",        # nombre de méthodes OPTIONS
    "nb_bye",            # nombre de méthodes BYE
    "total_bytes",       # octets totaux transmis
    "unique_ips",        # nombre d'adresses IP distinctes
    "src_to_dst_ratio",  # ratio src/dst
    "avg_frame_size",    # taille moyenne des paquets
    "max_interframe_gap" # plus grand intervalle entre paquets
]

sessions = {}  # Call-ID -> liste de paquets

# Configuration du logger
logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format='[%(levelname)s] %(message)s')

def notify_alert(call_id, label, proba, payload):
    """
    Envoie une alerte Slack si une session est malveillante.
    """
    text = (
        f"*ALERTE SIP* call_id={call_id} label={label} "
        f"proba={proba:.2f}\n```{payload}```"
    )
    try:
        slack.chat_postMessage(channel=SLACK_CHANNEL, text=text)
        logging.info(f"Alert sent for {call_id}")
    except Exception as e:
        logging.error(f"Slack notification failed for {call_id}: {e}")


def process_session(call_id):
    """Calcule les features d'une session et interroge l'API PLUTON."""
    pkts = sessions.pop(call_id, [])
    if not pkts:
        return

    # Extraction des timestamps pour la durée
    times = [p["ts"] for p in pkts]
    duration = times[-1] - times[0]

    nb_frames   = len(pkts)
    nb_invite   = sum(p["method"] == "INVITE" for p in pkts)
    nb_register = sum(p["method"] == "REGISTER" for p in pkts)
    nb_options  = sum(p["method"] == "OPTIONS" for p in pkts)
    nb_bye      = sum(p["method"] == "BYE" for p in pkts)
    total_bytes = sum(p["length"] for p in pkts)
    unique_ips  = len({p["src_ip"] for p in pkts})
    src_to_dst_ratio = nb_frames / unique_ips if unique_ips else 0
    avg_frame_size   = total_bytes / nb_frames if nb_frames else 0
    inter_gaps = [t2 - t1 for t1, t2 in zip(times, times[1:])]
    max_interframe_gap = max(inter_gaps) if inter_gaps else 0

    feat_vals = [
        duration,
        nb_frames,
        nb_invite,
        nb_register,
        nb_options,
        nb_bye,
        total_bytes,
        unique_ips,
        src_to_dst_ratio,
        avg_frame_size,
        max_interframe_gap,
    ]

    payload = {"features": feat_vals}
    logging.info(f"Sending payload for {call_id}")

    # Envoi à l’API PLUTON
    try:
        resp = requests.post(API_URL, json=payload, timeout=1.0)
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        logging.error(f"Predict error for {call_id}: {e}")
        return

    # Vérification du résultat pour alerte
    label = result.get("label")
    proba = result.get("proba", 0)
    if label != "normal" or proba >= 0.9:
        notify_alert(call_id, label, proba, payload)


def flush_timeout_sessions(now_ts):
    """Envoie les sessions dont le dernier paquet a dépassé le timeout."""
    for cid, pkts in list(sessions.items()):
        if now_ts - pkts[-1]["ts"] >= TIMEOUT:
            process_session(cid)


def main():
    """Lecture du flux JSON EK sur stdin et traitement session par session."""
    for line in sys.stdin:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        layers = obj.get("layers") or obj.get("_source", {}).get("layers")
        if not layers:
            continue

        sip   = layers.get("sip", {})
        frame = layers.get("frame", {})
        ipsec = layers.get("ip", {})

        call_id = sip.get("sip_sip_Call-ID") or sip.get("sip_sip_call_id_generated")
        if not call_id:
            continue

        method = sip.get("sip_sip_CSeq_method") or sip.get("sip_sip_Method", "")
        ts     = float(
            frame.get("frame_frame_time_relative", frame.get("frame_frame_time_delta", 0))
        )
        length = int(frame.get("frame_frame_len", 0))
        src_ip = ipsec.get("ip_ip_src", "")

        pkt = {"ts": ts, "method": method, "length": length, "src_ip": src_ip}
        sessions.setdefault(call_id, []).append(pkt)

        if method == "BYE":
            process_session(call_id)
        else:
            flush_timeout_sessions(ts)


if __name__ == "__main__":
    main()
import os
import json
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# ==========================
# CONFIG SLACK
# ==========================
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN", "xoxb-9235756128886-9236906689765-lzePQh23MYMKxGINpwRbzWMb")  # Mets ton token Slack ici si besoin
SLACK_CHANNEL = os.getenv("SLACK_ALERT_CHANNEL", "#sip-alerts")

slack_client = WebClient(token=SLACK_TOKEN)

# ==========================
# CONFIG SMTP (ElasticEmail)
# ==========================
SMTP_SERVER = "smtp.elasticemail.com"
SMTP_PORT = 2525
SMTP_USERNAME = "autreuser5@gmail.com"
SMTP_PASSWORD = "1C1587C036DDF3B6AEA54CA1E31994DB012F"

ALERT_EMAIL_FROM = "autreuser5@gmail.com"
ALERT_EMAIL_TO = "autreuser5@gmail.com"  # ✅ CHANGE ICI : mets l'email où recevoir les alertes

# ==========================
# FONCTION : Envoi Slack
# ==========================
def send_slack_alert(message):
    try:
        slack_client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
        print(f"[SLACK] Alerte envoyée sur {SLACK_CHANNEL}")
    except SlackApiError as e:
        print(f"[SLACK ERROR] {e.response['error']}")

# ==========================
# FONCTION : Envoi Email
# ==========================
def send_email_alert(subject, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = ALERT_EMAIL_FROM
        msg['To'] = ALERT_EMAIL_TO
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(ALERT_EMAIL_FROM, ALERT_EMAIL_TO, msg.as_string())

        print(f"[EMAIL] Alerte envoyée à {ALERT_EMAIL_TO}")

    except Exception as e:
        print(f"[EMAIL ERROR] Impossible d'envoyer l'alerte : {e}")

# ==========================
# FONCTION : Analyse du flux
# ==========================
def analyze_packet(packet_data):
    """
    Simule une détection d'anomalie.
    Ici, packet_data est un JSON avec des features.
    """
    # Exemple de détection simple : si "flood" dans le message => alerte
    if "flood" in packet_data.get("label", ""):
        return True
    return False

# ==========================
# MAIN LOOP : écoute des paquets
# ==========================
def main():
    print("✅ Feature Engine en écoute des flux...")
    while True:
        # Ici normalement on écoute des messages JSON en temps réel
        # On simule un paquet reçu pour test
        fake_packet = {
            "call_id": f"call_{int(time.time())}",
            "label": "register_flood",  # Simule une attaque détectée
            "features": [0.1, 0.5, 0.2]
        }

        if analyze_packet(fake_packet):
            alert_msg = (
                f"🚨 **ALERTE SIP** 🚨\n"
                f"Call ID: {fake_packet['call_id']}\n"
                f"Type: {fake_packet['label']}\n"
                f"Features: {fake_packet['features']}"
            )

            # 🔔 Envoi Slack
            send_slack_alert(alert_msg)

            # 🔔 Envoi Email
            send_email_alert("🚨 ALERTE SIP détectée !", alert_msg)

        # Attendre un peu avant de lire le prochain paquet
        time.sleep(1)

if __name__ == "__main__":
    main()
