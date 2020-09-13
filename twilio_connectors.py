# twilio imports
from twilio.rest import Client
from twilio.request_validator import RequestValidator

# external dependencies
from typing import Dict, Tuple, List
from flask import abort, current_app, request
from functools import wraps

# custom packages
import settings


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
        twilio_number = settings.twilio_number

        # Make a client and POST a message
        client = Client(account_sid, auth_token)
        message = client.messages \
                        .create(
                             body=data['message_body'],
                             from_=twilio_number,
                             to=phone_number
                         )

        print(message.sid)
        return f"Success! SMS sent to {phone_number}"
    except Exception as e:
        print(e)
        return f"The SMS to {phone_number} did not send."


def validate_twilio_request(f):
    """
    Validates that incoming requests genuinely originated from Twilio. Stole this from
    Twilio tutorial.

    Example Usage: 
    @app.route('/message', methods=['POST'])
    @validate_twilio_request
    def incoming_message():
        resp = MessagingResponse()
        resp.message("Message was len {len(request.values['Body'])} characters.")
        return str(resp)


    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Create an instance of the RequestValidator class
        validator = RequestValidator(settings.auth_token)

        # Validate the request using its URL, POST data,
        # and X-TWILIO-SIGNATURE header
        request_valid = validator.validate(
            request.url,
            request.form,
            request.headers.get('X-TWILIO-SIGNATURE', ''))

        # Continue processing the request if it's valid (or if DEBUG is True)
        # and return a 403 error if it's not
        if request_valid or current_app.debug:
            return f(*args, **kwargs)
        else:
            return abort(403)
    return decorated_function

