import json
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource("dynamodb")
bookings_table = dynamodb.Table("Bookings")

def lambda_handler(event, context):
    request = event["currentIntent"]["slots"]
    
    date = request["Date"]
    start_time = request["StartTime"]
    room_id = request["Room"]
    
    end_time = (datetime.strptime(start_time, "%H:%M") + timedelta(minutes=30)).strftime("%H:%M")  # Default duration 30 mins

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
                    "content": "Room not available at the requested time."
                }
            }
        }

    return {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "PlainText",
                "content": f"Room {room_id} is available at {start_time}."
            }
        }
    }
