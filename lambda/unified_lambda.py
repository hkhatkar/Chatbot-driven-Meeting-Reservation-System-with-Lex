import json
import boto3
import uuid
import random
import difflib
from datetime import datetime, timedelta
import os
import re

# Initialize DynamoDB tables from environment

dynamodb = boto3.resource("dynamodb")
bookings_table = dynamodb.Table(os.environ["BOOKINGS_TABLE"])
rooms_table    = dynamodb.Table(os.environ["ROOMS_TABLE"])
staff_table    = dynamodb.Table(os.environ["STAFF_TABLE"])


def to_alphanumeric(s: str) -> str:
    """Normalize a string by removing non-alphanumeric characters and lowercasing."""
    return re.sub(r'[^0-9a-zA-Z]', '', s).lower()


def resolve_room(raw_room_name):
    # 1) Scan all rooms
    rooms = rooms_table.scan()["Items"]
    # 2) Create normalized name -> id map
    name_to_id = {
        to_alphanumeric(r["room_name"]): r["room_id"]
        for r in rooms
    }
    # 3) Normalize user input and fuzzy-match
    norm_input = to_alphanumeric(raw_room_name)
    matches = difflib.get_close_matches(norm_input, name_to_id.keys(), n=1, cutoff=0.6)
    if not matches:
        raise ValueError(f"Room '{raw_room_name}' not found.")
    return name_to_id[matches[0]]


def check_availability(room_id, date, start_time, duration=30):
    end_time = (datetime.strptime(start_time, "%H:%M") + timedelta(minutes=duration)).strftime("%H:%M")
    items = bookings_table.scan(
        FilterExpression="room_id = :room AND #d = :date AND ((start_time BETWEEN :start AND :end) OR (end_time BETWEEN :start AND :end))",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={":room": room_id, ":date": date, ":start": start_time, ":end": end_time}
    )["Items"]
    return len(items) == 0


def book_meeting(raw_room, date, start_time, duration, attendees):
    # Resolve and check room
    room_id = resolve_room(raw_room)
    if not check_availability(room_id, date, start_time, duration):
        return "Room already booked. Suggest another slot."

    end_time = (datetime.strptime(start_time, "%H:%M") + timedelta(minutes=duration)).strftime("%H:%M")

    # Check each attendee for conflicts
    for staff_id in attendees:
        conflict = bookings_table.scan(
            FilterExpression="contains(attendees, :staff) AND #d = :date AND ((start_time BETWEEN :start AND :end) OR (end_time BETWEEN :start AND :end))",
            ExpressionAttributeNames={"#d": "date"},
            ExpressionAttributeValues={
                ":staff": staff_id,
                ":date": date,
                ":start": start_time,
                ":end": end_time
            }
        )["Items"]
        if conflict:
            return f"Staff member {staff_id} is already booked."

    # Resolve staff names to IDs
    staff_db = staff_table.scan()["Items"]
    staff_name_map = {s["full_name"].lower(): s["staff_id"] for s in staff_db}
    corrected = []
    for name in attendees:
        match = difflib.get_close_matches(name.lower(), staff_name_map.keys(), n=1, cutoff=0.5)
        if not match:
            return f"Staff {name} not found."
        corrected.append(staff_name_map[match[0]])

    # Write booking record
    booking_id = str(uuid.uuid4())
    bookings_table.put_item(Item={
        "id": booking_id,
        "room_id": room_id,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "attendees": corrected
    })

    return f"Booking confirmed for room {raw_room} ({room_id}) at {start_time} on {date} with attendees: {', '.join(corrected)}."


def fallback_response():
    return random.choice([
        "I'm not sure what you're asking.",
        "Could you please rephrase that?",
        "I didn't quite catch that. Can you say it again?"
    ])


def lambda_handler(event, context):
    # ─── Detect REST‐API HTTP events ─────────────────────────
    method = event.get("httpMethod", "")
    path   = event.get("path", "")

    # ─── CORS preflight for /bookings ────────────────────────
    if method == "OPTIONS" and path.endswith("/bookings"):
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin":  "*",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": ""
        }

    # ─── GET /bookings ───────────────────────────────────────
    if method == "GET" and path.endswith("/bookings"):
        items = bookings_table.scan()["Items"]
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(items)
        }
    # ─── Lex chatbot logic ─────────────────────
    intent = event["sessionState"]["intent"]["name"]
    slots  = event["sessionState"]["intent"]["slots"]
    try:
        if intent == "CheckAvailability":
            raw_room   = slots["Room"]["value"]["interpretedValue"]
            date       = slots["CheckDate"]["value"]["interpretedValue"]
            start_time = slots["CheckTime"]["value"]["interpretedValue"]

            room_id   = resolve_room(raw_room)
            available = check_availability(room_id, date, start_time)
            if available:
                message = f"✅ Room {raw_room} is available on {date} at {start_time}."
                state   = "Fulfilled"
            else:
                message = f"❌ Room {raw_room} is already booked on {date} at {start_time}."
                state   = "Failed"

        elif intent == "BookMeeting":
            raw_room    = slots["Room"]["value"]["interpretedValue"]
            date        = slots["MeetingDate"]["value"]["interpretedValue"]
            start_time  = slots["MeetingTime"]["value"]["interpretedValue"]
            duration    = int(slots["Duration"]["value"]["interpretedValue"])
            attendees_r = slots["Attendees"]["value"]["interpretedValue"]
            attendees   = [a.strip() for a in attendees_r.split(",")]

            message = book_meeting(raw_room, date, start_time, duration, attendees)
            state   = "Fulfilled" if "confirmed" in message else "Failed"

        else:
            message = fallback_response()
            state   = "Failed"

    except ValueError as ve:
        message = str(ve)
        state   = "Failed"
    except Exception:
        message = "Sorry, something went wrong."
        state   = "Failed"

    return {
        "sessionState": {
            "dialogAction": {"type": "Close"},
            "intent": {
                "name": intent,
                "state": state,
                "confirmationState": "Confirmed" if state == "Fulfilled" else "None"
            }
        },
        "messages": [{"contentType": "PlainText", "content": message}]
    }
