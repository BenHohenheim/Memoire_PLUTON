# Memoire PLUTON

This repository contains experimentation scripts for SIP attack detection.

## SMTP configuration

Email alerts require a working SMTP account. Set the following environment variables before running `feature_engine.py` or `smtp_test.py`:

- `SMTP_SERVER` and `SMTP_PORT`
- `SMTP_USERNAME` and `SMTP_PASSWORD`
- `ALERT_EMAIL_FROM` and `ALERT_EMAIL_TO`

For local testing you can use services like [ElasticEmail](https://elasticemail.com) or [Mailtrap](https://mailtrap.io). Ensure these variables are exported or present in your `.env` file.

You can verify the SMTP configuration independently by running:

```bash
python3 feature-engine/smtp_test.py
```

A ✅ message indicates that the email was accepted by the SMTP server.
