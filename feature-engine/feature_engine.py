#!/usr/bin/env python3
import sys
import json
import time
import os
import requests
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from slack_sdk import WebClient

# === CONFIGURATION ===
TIMEOUT = 4.0  # secondes pour considérer une session terminée
default_url = "http://pluton-api:8000/predict"
API_URL = os.getenv("PREDICT_URL", default_url)
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")

# Initialisation Slack
slack = WebClient(token=SLACK_TOKEN)

# Configuration SMTP
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.elasticemail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "2525"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")

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


def send_email_alert(subject: str, message: str):
    """Send alert via SMTP."""
    if not (ALERT_EMAIL_FROM and ALERT_EMAIL_TO and SMTP_SERVER):
        raise RuntimeError("SMTP configuration incomplete")

    msg = MIMEMultipart()
    msg["From"] = ALERT_EMAIL_FROM
    msg["To"] = ALERT_EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(ALERT_EMAIL_FROM, [ALERT_EMAIL_TO], msg.as_string())


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

    try:
        send_email_alert(f"SIP alert for {call_id}", text)
    except Exception as e:
        logging.error(f"Email notification failed for {call_id}: {e}")


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
