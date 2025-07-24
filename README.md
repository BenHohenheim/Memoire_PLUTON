# Memoire PLUTON

This repository contains experimentation scripts for SIP attack detection.
When an attack is detected, the feature engine now sends both a Slack message
and an email notification.

## SMTP configuration

Email alerts require a working SMTP account. Set the following environment variables before running `feature_engine.py` or `smtp_test.py`:

- `SMTP_SERVER` and `SMTP_PORT`
- `SMTP_USERNAME` and `SMTP_PASSWORD`
- `ALERT_EMAIL_FROM` and `ALERT_EMAIL_TO`
- `ENABLE_EMAIL_ALERT` (set to `false` to disable email alerts)

`ENABLE_EMAIL_ALERT` defaults to `true` so emails are sent unless explicitly
disabled.

For local testing you can use services like [ElasticEmail](https://elasticemail.com) or [Mailtrap](https://mailtrap.io). Ensure these variables are exported or present in your `.env` file.

You can verify the SMTP configuration independently by running:

```bash
python3 feature-engine/smtp_test.py
```

A ✅ message indicates that the email was accepted by the SMTP server.

## Tester l'envoi d'email avec ElasticEmail

Pour tester rapidement l'envoi des alertes par email avec le service
ElasticEmail, utilisez le script `smtp_run_test.sh` à la racine du dépôt :

```bash
./smtp_run_test.sh
```

Le script exporte automatiquement les variables d'environnement nécessaires puis
exécute `smtp_test.py`. Si tout est correct, le message `✅ Email envoyé avec succès` doit
s'afficher.

## Tester avec Mailtrap

Les tests utilisent la sandbox [Mailtrap](https://mailtrap.io) pour recevoir les
emails sans les envoyer vers de vraies adresses. Il suffit d'exécuter :

```bash
./smtp_run_test.sh
```

Les emails générés apparaîtront directement dans la sandbox Mailtrap.

## Slack configuration

The feature engine can also send alerts to Slack. Define `SLACK_TOKEN` and
`SLACK_CHANNEL` in your environment. You can verify the Slack integration
independently with:

```bash
docker compose run --rm feature-engine python3 -c 'from feature_engine import send_slack_alert; send_slack_alert("Slack test OK")'
```

If you obtain an `invalid_auth` error, check that the bot token has the
`chat:write` scope and reinstall the Slack application if necessary.

After modifying `.env`, recreate the `feature-engine` container so it picks up
the new values:

```bash
docker compose up -d --force-recreate feature-engine
```
