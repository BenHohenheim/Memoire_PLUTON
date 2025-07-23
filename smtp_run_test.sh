#!/bin/bash
# Helper script to test SMTP alerts with ElasticEmail

export SMTP_SERVER="smtp.elasticemail.com"
export SMTP_PORT="2525"
export SMTP_USERNAME="autreuser5@gmail.com"
export SMTP_PASSWORD="1C1587C036DDF3B6AEA54CA1E31994DB012F"
export ALERT_EMAIL_FROM="autreuser5@gmail.com"
export ALERT_EMAIL_TO="ruben.nyaku2@gmail.com"

echo "[INFO] Running smtp_test.py with ElasticEmail credentials..."
python3 feature-engine/smtp_test.py

