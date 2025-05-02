import json
import boto3
import uuid
import random
import difflib
from datetime import datetime, timedelta
import os

dynamodb = boto3.resource("dynamodb")
bookings_table = dynamodb.Table(os.environ["BOOKINGS_TABLE"])
rooms_table    = dynamodb.Table(os.environ["ROOMS_TABLE"])
staff_table = dynamodb.Table(os.environ["STAFF_TABLE"])

def resolve_room(raw_room_name):
    # 1) Scan all rooms
    rooms = rooms_table.scan()["Items"]
    # 2) Build name -> id map
    name_to_id = { r["room_name"].lower(): r["room_id"] for r in rooms }
    # 3) Fuzzy-match user input
    matches = difflib.get_close_matches(raw_room_name.lower(), name_to_id.keys(), n=1, cutoff=0.6)
    if not matches:
        raise ValueError(f"Room '{raw_room_name}' not found.")
    return name_to_id[matches[0]]



def check_availability(room_id, date, start_time, duration=30):
    end_time = (datetime.strptime(start_time, "%H:%M") + timedelta(minutes=duration)).strftime("%H:%M")
    return not bookings_table.scan(
        FilterExpression="room_id = :room AND #d = :date AND ((start_time BETWEEN :start AND :end) OR (end_time BETWEEN :start AND :end))",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={
            ":room": room_id,
            ":date": date,
            ":start": start_time,
            ":end": end_time
        }
    )["Items"]

def book_meeting(raw_room, date, start_time, duration, attendees):
    # Resolve to actual room_id
    room_id = resolve_room(raw_room)

    # Check room availability
    if not check_availability(room_id, date, start_time, duration):
        return "Room already booked. Suggest another slot."

    end_time = (datetime.strptime(start_time, "%H:%M") + timedelta(minutes=duration)).strftime("%H:%M")

    # Check each attendee’s availability
    for staff_id in attendees:
        if bookings_table.scan(
            FilterExpression="contains(attendees, :staff) AND #d = :date AND ((start_time BETWEEN :start AND :end) OR (end_time BETWEEN :start AND :end))",
            ExpressionAttributeNames={"#d": "date"},
            ExpressionAttributeValues={
                ":staff": staff_id,
                ":date": date,
                ":start": start_time,
                ":end": end_time
            }
        )["Items"]:
            return f"Staff member {staff_id} is already booked."

    # Convert staff names -> IDs
    staff_db = staff_table.scan()["Items"]
    name_to_id = { s["full_name"].lower(): s["staff_id"] for s in staff_db }
    corrected = []
    for name in attendees:
        match = difflib.get_close_matches(name.lower(), name_to_id.keys(), n=1, cutoff=0.5)
        if not match:
            return f"Staff {name} not found."
        corrected.append(name_to_id[match[0]])

    # write the booking
    booking_id = str(uuid.uuid4())
    bookings_table.put_item(Item={
        "id": booking_id,
        "room_id": room_id,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "attendees": corrected
    })

    return f"Booking confirmed for room {room_id} at {start_time} with attendees: {', '.join(corrected)}."


def fallback_response():
    responses = [
        "I'm not sure what you're asking.",
        "Could you please rephrase that?",
        "I didn't quite catch that. Can you say it again?"
    ]
    return random.choice(responses)

def lambda_handler(event, context):
    intent = event["sessionState"]["intent"]["name"]
    slots = event["sessionState"]["intent"]["slots"]
    
    #if intent_name == "CheckAvailability":
    #    date = slots.get("MeetingDate", {}).get("value", {}).get("interpretedValue")
    #    start_time = slots.get("MeetingTime", {}).get("value", {}).get("interpretedValue")
    #    room_id = slots.get("Room", {}).get("value", {}).get("interpretedValue")
    #    available = check_availability(date, start_time, room_id)
    #    message = f"Room {room_id} is available at {start_time}." if available else "Room not available at the requested time."
    #    fulfillment_state = "Fulfilled"
        
    if intent == "BookMeeting":
        raw_room    = slots["Room"]["value"]["interpretedValue"]
        date        = slots["MeetingDate"]["value"]["interpretedValue"]
        start_time  = slots["MeetingTime"]["value"]["interpretedValue"]
        duration    = int(slots["Duration"]["value"]["interpretedValue"])
        attendees_r = slots["Attendees"]["value"]["interpretedValue"]
        attendees   = [a.strip() for a in attendees_r.split(",")]

        message = book_meeting(raw_room, date, start_time, duration, attendees)
        state   = "Fulfilled" if "confirmed" in message else "Failed"


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