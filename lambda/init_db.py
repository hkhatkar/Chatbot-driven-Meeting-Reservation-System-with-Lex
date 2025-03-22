import boto3
import json
import os

# Initialize DynamoDB clients
dynamodb = boto3.resource("dynamodb")

# Get table names from environment variables
BOOKINGS_TABLE = os.getenv("BOOKINGS_TABLE")
ROOMS_TABLE = os.getenv("ROOMS_TABLE")
STAFF_TABLE = os.getenv("STAFF_TABLE")

# Load sample data from a JSON file
def load_sample_data(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

def seed_table(table_name, data):
    table = dynamodb.Table(table_name)
    for item in data:
        table.put_item(Item=item)

def lambda_handler(event, context):
    try:
        # Load data from sample JSON file (ensure this file exists in the Lambda package)
        sample_data = load_sample_data("/var/task/sample_data.json")

        # Insert data into DynamoDB tables
        seed_table(BOOKINGS_TABLE, sample_data.get("bookings", []))
        seed_table(ROOMS_TABLE, sample_data.get("rooms", []))
        seed_table(STAFF_TABLE, sample_data.get("staff", []))

        return {
            "statusCode": 200,
            "body": json.dumps("Database initialized successfully!")
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error initializing database: {str(e)}")
        }
