import json
import boto3
import uuid
import difflib
from datetime import datetime, timedelta
from fuzzywuzzy import process

dynamodb = boto3.resource("dynamodb")
bookings_table = dynamodb.Table("Bookings")
staff_table = dynamodb.Table("Staff")

def lambda_handler(event, context):
    request = event["currentIntent"]["slots"]
    
    date = request["Date"]
    start_time = request["StartTime"]
    duration = int(request["Duration"])
    room_id = request["Room"]
    attendees = request["Attendees"]

    end_time = (datetime.strptime(start_time, "%H:%M") + timedelta(minutes=duration)).strftime("%H:%M")

    # Validate room availability
    overlapping = bookings_table.scan(
        FilterExpression="room_id = :room AND date = :date AND ((start_time BETWEEN :start AND :end) OR (end_time BETWEEN :start AND :end))",
        ExpressionAttributeValues={":room": room_id, ":date": date, ":start": start_time, ":end": end_time},
    )["Items"]

    if overlapping:
        return {
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Failed",
                "message": {
                    "contentType": "PlainText",
                    "content": "Room already booked. Suggest another slot."
                }
            }
        }

    # Validate staff availability
    for staff in attendees:
        booked_meetings = bookings_table.scan(
            FilterExpression="contains(attendees, :staff) AND date = :date AND ((start_time BETWEEN :start AND :end) OR (end_time BETWEEN :start AND :end))",
            ExpressionAttributeValues={":staff": staff, ":date": date, ":start": start_time, ":end": end_time},
        )["Items"]
        if booked_meetings:
            return {
                "dialogAction": {
                    "type": "Close",
                    "fulfillmentState": "Failed",
                    "message": {
                        "contentType": "PlainText",
                        "content": f"Staff member {staff} is already booked."
                    }
                }
            }

    # Fuzzy name matching
    staff_db = staff_table.scan()["Items"]
    staff_names = {s["full_name"]: s["staff_id"] for s in staff_db}

    corrected_attendees = []
    for name in attendees:
        matches = difflib.get_close_matches(name, staff_names.keys(), n=1, cutoff=0.8)
        if matches:
            best_match = matches[0]
            corrected_attendees.append(staff_names[best_match])
        else:
            return {
                "dialogAction": {
                    "type": "Close",
                    "fulfillmentState": "Failed",
                    "message": {
                        "contentType": "PlainText",
                        "content": f"Staff {name} not found."
                    }
                }
            }

    # Save booking
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

    return {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "PlainText",
                "content": f"Booking confirmed for room {room_id} at {start_time} with attendees: {', '.join(corrected_attendees)}."
            }
        }
    }
