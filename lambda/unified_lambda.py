import json
import boto3
import uuid
import random
import difflib
from datetime import datetime, timedelta

dynamodb = boto3.resource("dynamodb")
bookings_table = dynamodb.Table("BOOKINGS_TABLE")
staff_table = dynamodb.Table("Staff")

def check_availability(date, start_time, room_id):
    end_time = (datetime.strptime(start_time, "%H:%M") + timedelta(minutes=30)).strftime("%H:%M")
    overlapping = bookings_table.scan(
        FilterExpression="room_id = :room AND #d = :date AND ((start_time BETWEEN :start AND :end) OR (end_time BETWEEN :start AND :end))",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={
            ":room": room_id,
            ":date": date,
            ":start": start_time,
            ":end": end_time
        }
    )["Items"]
    return not overlapping

def book_meeting(date, start_time, duration, room_id, attendees):
    end_time = (datetime.strptime(start_time, "%H:%M") + timedelta(minutes=duration)).strftime("%H:%M")
    overlapping = bookings_table.scan(
        FilterExpression="room_id = :room AND #d = :date AND ((start_time BETWEEN :start AND :end) OR (end_time BETWEEN :start AND :end))",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={
            ":room": room_id,
            ":date": date,
            ":start": start_time,
            ":end": end_time
        }
    )["Items"]

    if overlapping:
        return "Room already booked. Suggest another slot."
    
    for staff in attendees:
        booked_meetings = bookings_table.scan(
            FilterExpression="contains(attendees, :staff) AND #d = :date AND ((start_time BETWEEN :start AND :end) OR (end_time BETWEEN :start AND :end))",
            ExpressionAttributeNames={"#d": "date"},
            ExpressionAttributeValues={
                ":staff": staff,
                ":date": date,
                ":start": start_time,
                ":end": end_time
            },
        )["Items"]

        if booked_meetings:
            return f"Staff member {staff} is already booked."
    
    staff_db = staff_table.scan()["Items"]
    staff_names = {s["full_name"]: s["staff_id"] for s in staff_db}
    corrected_attendees = []
    for name in attendees:
        matches = difflib.get_close_matches(name, staff_names.keys(), n=1, cutoff=0.5)
        if matches:
            best_match = matches[0]
            corrected_attendees.append(staff_names[best_match])
        else:
            return f"Staff {name} not found."
    
    booking_id = str(uuid.uuid4())
    
    bookings_table.put_item(
        Item={
            "id": booking_id,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "room_id": room_id,
            "attendees": corrected_attendees,
        }
    )

    return f"Booking confirmed for room {room_id} at {start_time} with attendees: {', '.join(corrected_attendees)}."

def fallback_response():
    responses = [
        "I'm not sure what you're asking.",
        "Could you please rephrase that?",
        "I didn't quite catch that. Can you say it again?"
    ]
    return random.choice(responses)

def lambda_handler(event, context):
    intent_name = event["sessionState"]["intent"]["name"]
    slots = event["sessionState"]["intent"]["slots"]
    
    if intent_name == "CheckAvailability":
        date = slots.get("MeetingDate", {}).get("value", {}).get("interpretedValue")
        start_time = slots.get("MeetingTime", {}).get("value", {}).get("interpretedValue")
        room_id = slots.get("Room", {}).get("value", {}).get("interpretedValue")
        available = check_availability(date, start_time, room_id)
        message = f"Room {room_id} is available at {start_time}." if available else "Room not available at the requested time."
        fulfillment_state = "Fulfilled"
        
    elif intent_name == "BookMeeting":
        date = slots.get("MeetingDate", {}).get("value", {}).get("interpretedValue")
        start_time = slots.get("MeetingTime", {}).get("value", {}).get("interpretedValue")
        duration = slots.get("Duration", {}).get("value", {}).get("interpretedValue")
        room_id = slots.get("Room", {}).get("value", {}).get("interpretedValue")
        attendees_raw = slots.get("Attendees", {}).get("value", {}).get("interpretedValue")

        attendees = [att.strip() for att in attendees_raw.split(",")] if attendees_raw else []

        if date and start_time and duration and room_id and attendees:
            message = book_meeting(date, start_time, int(duration), room_id, attendees)
            fulfillment_state = "Fulfilled" if "confirmed" in message else "Failed"
        else:
            message = "Missing information for booking."
            fulfillment_state = "Failed"

    else:
        message = fallback_response()
        fulfillment_state = "Failed"
    
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": intent_name,
                "state": fulfillment_state,
                "confirmationState": "Confirmed" if fulfillment_state == "Fulfilled" else "None"
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": message
            }
        ],
        "sessionId": event.get("sessionId"),
        "requestAttributes": event.get("requestAttributes", {})
    }
