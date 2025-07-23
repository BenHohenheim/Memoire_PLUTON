#!/bin/bash
# Helper script to test SMTP alerts.
# This version uses a Mailtrap sandbox account so that
# emails can be sent without the restrictions of the
# free ElasticEmail tier.

export SMTP_SERVER="sandbox.smtp.mailtrap.io"
export SMTP_PORT="587"
export SMTP_USERNAME="5eb439d4e17458"
export SMTP_PASSWORD="02740c73cbcd88"
export ALERT_EMAIL_FROM="test@mailtrap.io"
export ALERT_EMAIL_TO="any@recipient.com"

echo "[INFO] Running smtp_test.py with Mailtrap credentials..."
python3 feature-engine/smtp_test.py

