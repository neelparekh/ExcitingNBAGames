from twilio.rest import Client
from typing import Dict, Tuple, List
import settings

 # load variables from .env into environment variables

def send_SMS(data: Dict, phone_number: str):
    '''
    Send data to phone number

    Parameters
    ----------
    data: Dict
    phone_number: str
        must be E.164 format

    '''

    try:
        # Your Account sid and Auth Token from twilio.com/console
        account_sid   = settings.account_sid
        auth_token    = settings.auth_token
        service_sid   = settings.service_sid
        twilio_number = settings.twilio_number

        # Make a client and POST a message
        client = Client(account_sid, auth_token)
        message = client.messages \
                        .create(
                             body=data['message_body'],
                             # messaging_service_sid=service_sid,
                             from_=twilio_number,
                             to=phone_number
                         )

        print(message.sid)
        return f"Success! SMS sent to {phone_number}"
    except Exception as e:
        print(e)
        return f"The SMS to {phone_number} did not send."
