# VPN Subscription Telegram Bot

A Telegram bot that sells VPN subscriptions and provisions access automatically on a [3x-ui](https://github.com/MHSanaei/3x-ui) panel.

## Features

- Main menu with tariff selection (subscription plans of different lengths).
- Payments inside Telegram via the Telegram Payments API (pre-checkout and successful-payment handlers).
- After payment, the bot logs in to the 3x-ui panel API and creates a VPN client for the user with the right expiry date.
- Free 3-day trial, limited to one per Telegram account (tracked in `trial_status.json`).
- "My account" screen showing the user's current subscription.

## Tech stack

Python, python-telegram-bot (async), requests, 3x-ui panel API.

## Setup

```bash
pip install python-telegram-bot requests
```

Open `BOT_VPN.py` and fill in your own values (they are placeholders in the repository):

- `BOT_TOKEN` — bot token from @BotFather
- `PROVIDER_TOKEN` — payment provider token from @BotFather
- `VPN_API_URL` — address of your 3x-ui panel, plus the panel login and password

Then run:

```bash
python BOT_VPN.py
```

> Never commit real tokens or panel credentials. Consider loading them from environment variables.
