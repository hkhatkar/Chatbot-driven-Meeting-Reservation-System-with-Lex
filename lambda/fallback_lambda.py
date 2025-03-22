import json
import random

def lambda_handler(event, context):
    # List of fallback responses
    fallback_responses = [
        "I'm not sure what you're asking.",
        "Could you please rephrase that?",
        "I didn't quite catch that. Can you say it again?"
    ]
    
    # Randomly choose a fallback response
    response = random.choice(fallback_responses)
    
    # Return the response in the format Lex expects
    return {
        'sessionAttributes': event.get('sessionAttributes', {}),
        'dialogAction': {
            'type': 'ElicitIntent',
            'message': {
                'contentType': 'PlainText',
                'content': response
            }
        }
    }
