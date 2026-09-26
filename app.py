"""FastAPI Webex Bot for a six-week Hundred Pushups program.

Run with: uvicorn app:app --reload
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from models import (
    Participant,
    advance_participant,
    deactivate_participant,
    init_db,
    list_active_participants,
    upsert_participant,
)
from pushup_data import get_workout


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

WEBEX_API_BASE = "https://webexapis.com/v1"
WEBEX_BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN", "")
WEBEX_WEBHOOK_SECRET = os.getenv("WEBEX_WEBHOOK_SECRET", "")
APP_TIMEZONE = ZoneInfo(os.getenv("APP_TIMEZONE", "UTC"))

# Webex and Adaptive Cards use Sunday=0. Python's weekday() uses Monday=0.
SCHEDULE_OPTIONS: dict[str, list[int]] = {
    "mon_wed_fri": [1, 3, 5],
    "tue_thu_sat": [2, 4, 6],
}

app = FastAPI(title="Hundred Pushups Webex Bot", version="1.0.0")
scheduler = BackgroundScheduler(timezone=APP_TIMEZONE)


class WebexClient:
    def __init__(self, token: str) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )

    def get(self, path: str) -> dict[str, Any]:
        response = self.session.get(f"{WEBEX_API_BASE}{path}", timeout=20)
        response.raise_for_status()
        return response.json()

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.session.post(
            f"{WEBEX_API_BASE}{path}", json=payload, timeout=20
        )
        response.raise_for_status()
        return response.json()


webex = WebexClient(WEBEX_BOT_TOKEN)


def verify_signature(raw_body: bytes, signature: str | None) -> None:
    if not WEBEX_WEBHOOK_SECRET:
        return
    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")
    expected = hmac.new(
        WEBEX_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha1
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


def adaptive_attachment(content: dict[str, Any]) -> dict[str, Any]:
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": content,
    }


def registration_card() -> dict[str, Any]:
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
            {"type": "TextBlock", "text": "Hundred Pushups", "weight": "Bolder", "size": "Large"},
            {"type": "TextBlock", "text": "Register for 3 workouts per week over 6 weeks.", "wrap": True},
            {"type": "TextBlock", "text": "Initial level", "weight": "Bolder", "spacing": "Medium"},
            {
                "type": "Input.ChoiceSet", "id": "level", "style": "expanded", "isRequired": True,
                "choices": [
                    {"title": "Level 1 — baseline under 5 pushups", "value": "1"},
                    {"title": "Level 2 — baseline 6–10 pushups", "value": "2"},
                    {"title": "Level 3 — baseline 11–20 pushups", "value": "3"},
                ],
            },
            {"type": "TextBlock", "text": "Program starting point", "weight": "Bolder", "spacing": "Medium"},
            {
                "type": "Input.ChoiceSet", "id": "starting_week", "title": "Starting week",
                "style": "compact", "value": "1", "isRequired": True,
                "choices": [
                    {"title": "Week 1 — Day 1 (start at the beginning)", "value": "1"},
                    {"title": "Week 2 — Day 1", "value": "2"},
                    {"title": "Week 3 — Day 1", "value": "3"},
                    {"title": "Week 4 — Day 1", "value": "4"},
                    {"title": "Week 5 — Day 1", "value": "5"},
                    {"title": "Week 6 — Day 1", "value": "6"},
                ],
            },
            {"type": "Input.Date", "id": "start_date", "title": "Date for your selected week's Day 1", "isRequired": True},
            {
                "type": "Input.ChoiceSet", "id": "schedule", "title": "Workout schedule",
                "style": "compact", "value": "mon_wed_fri", "isRequired": True,
                "choices": [
                    {"title": "Monday / Wednesday / Friday", "value": "mon_wed_fri"},
                    {"title": "Tuesday / Thursday / Saturday", "value": "tue_thu_sat"},
                ],
            },
            {"type": "Input.Time", "id": "reminder_time", "title": "Reminder time", "value": "08:00", "isRequired": True},
        ],
        "actions": [
            {"type": "Action.Submit", "title": "Start training", "data": {"action": "register"}}
        ],
    }


def workout_card(participant: Participant, workout: dict[str, Any]) -> dict[str, Any]:
    body: list[dict[str, Any]] = [
        {"type": "TextBlock", "text": f"Week {participant.current_week} · Day {participant.current_day}", "weight": "Bolder", "size": "Large"},
        {"type": "TextBlock", "text": "Complete each set with clean form. Rest between sets as prescribed.", "wrap": True},
    ]
    for index, reps in enumerate(workout["reps"], start=1):
        body.append({"type": "TextBlock", "text": f"Set {index}: {reps}", "wrap": True})
    body.append({"type": "TextBlock", "text": f"Rest: {workout['rest_seconds']} seconds between sets", "isSubtle": True, "wrap": True})
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": body,
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Workout Complete",
                "data": {"action": "workout_complete", "person_id": participant.person_id},
            }
        ],
    }


def send_message(*, room_id: str | None = None, email: str | None = None, markdown: str | None = None, attachments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if room_id:
        payload["roomId"] = room_id
    elif email:
        payload["toPersonEmail"] = email
    else:
        raise ValueError("room_id or email is required")
    if markdown:
        payload["markdown"] = markdown
    if attachments:
        payload["attachments"] = attachments
    return webex.post("/messages", payload)


def next_scheduled_date(start_date: date, schedule_days: list[int]) -> date:
    """Find the first selected weekday on or after the configured start date."""

    candidate = start_date
    for _ in range(7):
        if candidate.isoweekday() in schedule_days:
            return candidate
        candidate += timedelta(days=1)
    raise ValueError("schedule_days must contain at least one weekday")


def session_date(participant: Participant) -> date:
    """Calculate the calendar date for the participant's current session."""

    first = next_scheduled_date(participant.start_date, participant.schedule_day_numbers)
    # start_date is the kickoff date for starting_week, not necessarily Week 1.
    # This lets a participant begin at Week 2 (or later) without shifting their
    # first workout by the weeks they intentionally skipped.
    target_index = (participant.current_week - participant.starting_week) * 3 + (participant.current_day - 1)
    found = 0
    candidate = first
    while True:
        if candidate.isoweekday() in participant.schedule_day_numbers:
            if found == target_index:
                return candidate
            found += 1
        candidate += timedelta(days=1)


def parse_time(value: str) -> time:
    return datetime.strptime(value, "%H:%M").time()


def format_kickoff(participant: Participant) -> str:
    kickoff = next_scheduled_date(participant.start_date, participant.schedule_day_numbers)
    return kickoff.strftime("%A, %B %-d, %Y")


def parse_action_inputs(action: dict[str, Any]) -> dict[str, Any]:
    inputs: dict[str, Any] = dict(action.get("data") or {})
    submitted_inputs = action.get("inputs") or {}
    # Some Webex payloads have represented inputs as a list of {name, value}.
    if isinstance(submitted_inputs, list):
        submitted_inputs = {
            item.get("name"): item.get("value") for item in submitted_inputs
        }
    inputs.update(submitted_inputs)
    return inputs


def handle_registration(action: dict[str, Any]) -> None:
    inputs = parse_action_inputs(action)
    person_id = action.get("personId") or action.get("person_id")
    email = action.get("personEmail") or action.get("person_email")
    room_id = action.get("roomId") or action.get("room_id")
    if not all([person_id, email, room_id]):
        logger.warning("Registration action missing identity fields: %s", action)
        return

    level = int(inputs.get("level", 0))
    starting_week = int(inputs.get("starting_week", 1))
    schedule_key = inputs.get("schedule", "mon_wed_fri")
    start_date = date.fromisoformat(inputs["start_date"])
    reminder_time = inputs.get("reminder_time", "08:00")
    if level not in (1, 2, 3) or starting_week not in range(1, 7) or schedule_key not in SCHEDULE_OPTIONS:
        raise ValueError("Invalid registration form values")
    parse_time(reminder_time)

    participant = upsert_participant(
        person_id=person_id,
        email=email,
        room_id=room_id,
        level=level,
        starting_week=starting_week,
        start_date=start_date,
        schedule_days=SCHEDULE_OPTIONS[schedule_key],
        reminder_time=reminder_time,
    )
    send_message(
        room_id=room_id,
        markdown=(
            f"**You're registered for Hundred Pushups — Level {level}, Week {starting_week}!**\n\n"
            f"Your first workout is **Week {starting_week}, Day 1** on **{format_kickoff(participant)}** at {reminder_time}. "
            "I'll send your workout here on each scheduled training day."
        ),
    )


def handle_workout_complete(action: dict[str, Any]) -> None:
    person_id = action.get("personId") or action.get("person_id")
    room_id = action.get("roomId") or action.get("room_id")
    if not person_id:
        return
    if room_id:
        send_message(room_id=room_id, markdown="Nice work — workout marked complete. Keep the momentum going!")


def process_attachment_action(action_id: str) -> None:
    action = webex.get(f"/attachmentActions/{action_id}")
    action_name = parse_action_inputs(action).get("action")
    if action_name == "register":
        handle_registration(action)
    elif action_name == "workout_complete":
        handle_workout_complete(action)
    else:
        logger.info("Ignoring unsupported attachment action: %s", action_name)


def process_message(message_id: str) -> None:
    message = webex.get(f"/messages/{message_id}")
    if message.get("personId") == os.getenv("WEBEX_BOT_PERSON_ID"):
        return
    text = (message.get("text") or "").strip().lower()
    if text == "start" or text.startswith("start ") or message.get("mentionedPeople"):
        send_message(
            room_id=message.get("roomId"),
            attachments=[adaptive_attachment(registration_card())],
        )


def deliver_due_workouts() -> None:
    now = datetime.now(APP_TIMEZONE)
    today = now.date()
    for participant in list_active_participants():
        try:
            if parse_time(participant.reminder_time) > now.time().replace(second=0, microsecond=0):
                continue
            if session_date(participant) != today:
                continue
            workout = get_workout(participant.current_week, participant.current_day, participant.level)
            send_message(
                room_id=participant.room_id,
                attachments=[adaptive_attachment(workout_card(participant, workout))],
            )
            final_session = participant.current_week == 6 and participant.current_day == 3
            advance_participant(participant.person_id)
            if final_session:
                send_message(room_id=participant.room_id, markdown="Congratulations — you completed the six-week Hundred Pushups program!")
        except Exception:
            logger.exception("Unable to deliver workout to %s", participant.email)


@app.on_event("startup")
def startup() -> None:
    if not WEBEX_BOT_TOKEN:
        logger.warning("WEBEX_BOT_TOKEN is not set; API calls will fail until configured")
    init_db()
    if not scheduler.running:
        scheduler.add_job(deliver_due_workouts, "interval", minutes=1, id="deliver_workouts", replace_existing=True)
        scheduler.start()


@app.on_event("shutdown")
def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request, x_spark_signature: str | None = Header(default=None)) -> JSONResponse:
    raw_body = await request.body()
    verify_signature(raw_body, x_spark_signature)
    payload = await request.json()
    resource = payload.get("resource")
    event = payload.get("event")
    data = payload.get("data", {})
    try:
        if resource == "messages" and event == "created" and data.get("id"):
            process_message(data["id"])
        elif resource == "attachmentActions" and event == "created" and data.get("id"):
            process_attachment_action(data["id"])
    except (requests.RequestException, TypeError, ValueError, KeyError):
        logger.exception("Unable to process Webex webhook")
        # Return 200 so Webex does not retry a malformed user submission forever.
    return JSONResponse({"ok": True})
