# Hundred Pushups Webex Bot

This FastAPI application registers Webex users for a six-week, three-days-per-week pushup progression, stores each participant's state in SQLite, and delivers workout cards on schedule.

## 1. Create the Webex bot

1. Sign in at [developer.webex.com](https://developer.webex.com/), open **My Webex Apps**, choose **Create a New App**, then choose **Create a Bot**.
2. Give the bot a name, username, and icon. Copy the generated bot access token; it is only shown once.
3. Decide where the bot should run. The sample uses the server's configured `APP_TIMEZONE` for reminder times. Set it in `.env` if the server is not in the desired timezone.

## 2. Install and run

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `WEBEX_BOT_TOKEN` in `.env`, then load the variables in your shell and start the server:

```bash
set -a; source .env; set +a
uvicorn app:app --host 0.0.0.0 --port 8000
```

The SQLite database is created automatically as `pushups.db` on startup. Use `GET /health` to confirm the process is running.

## 3. Expose the local server with ngrok

In another terminal:

```bash
ngrok http 8000
```

Copy the HTTPS forwarding URL, for example `https://example.ngrok.app`, and use `https://example.ngrok.app/webhook` as the webhook target URL.

## 4. Register the Webex webhooks

Create one webhook for messages and one for Adaptive Card submissions. Replace the token, URL, and the two IDs below:

```bash
curl -X POST https://webexapis.com/v1/webhooks \
  -H "Authorization: Bearer $WEBEX_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hundred-pushups-messages",
    "targetUrl": "https://example.ngrok.app/webhook",
    "resource": "messages",
    "event": "created",
    "secret": "'$WEBEX_WEBHOOK_SECRET'"
  }'

curl -X POST https://webexapis.com/v1/webhooks \
  -H "Authorization: Bearer $WEBEX_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hundred-pushups-actions",
    "targetUrl": "https://example.ngrok.app/webhook",
    "resource": "attachmentActions",
    "event": "created",
    "secret": "'$WEBEX_WEBHOOK_SECRET'"
  }'
```

If you do not configure a secret, omit the `secret` property and leave `WEBEX_WEBHOOK_SECRET` empty. For production, use a secret and keep it outside source control.

The message webhook fetches the full message from `GET /v1/messages/{id}`. The attachment-action webhook fetches submitted values from `GET /v1/attachmentActions/{id}`. The bot ignores its own messages when `WEBEX_BOT_PERSON_ID` is set.

## 5. Test the flow

1. Add the bot to a 1-on-1 space and send `start`.
2. Submit the registration card. Choose **Week 1 — Day 1** to begin at the beginning, or select a later starting week and use the date as that week's Day 1 kickoff.
3. Confirm the bot replies with the first scheduled workout date.
4. On a scheduled date at or after the selected time, the scheduler sends the workout card and advances the participant's state.
5. Clicking **Workout Complete** sends an acknowledgement. The scheduled delivery is idempotent for a given participant state because the state advances only after the workout message is accepted by Webex.

## Notes

- `pushup_data.py` contains the complete editable six-week sample progression. Each record has five targets and a rest interval in seconds.
- Registration stores the selected `starting_week`; the chosen `start_date` is the first scheduled Day 1 for that week. Starting at Week 2 therefore skips Weeks 1's sessions intentionally.
- The database stores weekdays as ISO weekday numbers: Monday=1 through Sunday=7.
- The scheduler runs every minute so each user's selected reminder time is honored. For a multi-instance production deployment, use a single scheduler instance or add a distributed job lock.
- Webex webhook requests are acknowledged with HTTP 200 after the application records a processing error, which prevents endless retries for invalid form data. Errors are logged for diagnosis.
