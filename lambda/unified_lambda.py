import json
import boto3
import uuid
import random
from datetime import datetime, timedelta
from fuzzywuzzy import process

dynamodb = boto3.resource("dynamodb")
bookings_table = dynamodb.Table("Bookings")
staff_table = dynamodb.Table("Staff")

def check_availability(date, start_time, room_id):
    end_time = (datetime.strptime(start_time, "%H:%M") + timedelta(minutes=30)).strftime("%H:%M")
    overlapping = bookings_table.scan(
        FilterExpression="room_id = :room AND date = :date AND ((start_time BETWEEN :start AND :end) OR (end_time BETWEEN :start AND :end))",
        ExpressionAttributeValues={":room": room_id, ":date": date, ":start": start_time, ":end": end_time},
    )["Items"]
    return not overlapping

def book_meeting(date, start_time, duration, room_id, attendees):
    end_time = (datetime.strptime(start_time, "%H:%M") + timedelta(minutes=duration)).strftime("%H:%M")
    overlapping = bookings_table.scan(
        FilterExpression="room_id = :room AND date = :date AND ((start_time BETWEEN :start AND :end) OR (end_time BETWEEN :start AND :end))",
        ExpressionAttributeValues={":room": room_id, ":date": date, ":start": start_time, ":end": end_time},
    )["Items"]
    if overlapping:
        return "Room already booked. Suggest another slot."
    
    for staff in attendees:
        booked_meetings = bookings_table.scan(
            FilterExpression="contains(attendees, :staff) AND date = :date AND ((start_time BETWEEN :start AND :end) OR (end_time BETWEEN :start AND :end))",
            ExpressionAttributeValues={":staff": staff, ":date": date, ":start": start_time, ":end": end_time},
        )["Items"]
        if booked_meetings:
            return f"Staff member {staff} is already booked."
    
    staff_db = staff_table.scan()["Items"]
    staff_names = {s["full_name"]: s["staff_id"] for s in staff_db}
    corrected_attendees = []
    for name in attendees:
        best_match, score = process.extractOne(name, staff_names.keys())
        if score > 80:
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
    intent_name = event["currentIntent"]["name"]
    request = event["currentIntent"]["slots"]
    
    if intent_name == "CheckAvailability":
        date, start_time, room_id = request["Date"], request["StartTime"], request["Room"]
        available = check_availability(date, start_time, room_id)
        message = f"Room {room_id} is available at {start_time}." if available else "Room not available at the requested time."
    elif intent_name == "BookMeeting":
        date, start_time, duration, room_id, attendees = request["Date"], request["StartTime"], int(request["Duration"]), request["Room"], request["Attendees"]
        message = book_meeting(date, start_time, duration, room_id, attendees)
    else:
        message = fallback_response()
    
    return {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled" if "confirmed" in message else "Failed",
            "message": {"contentType": "PlainText", "content": message}
        }
    }
