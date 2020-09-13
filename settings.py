from dotenv import load_dotenv
import os

load_dotenv()

account_sid   = os.getenv("TWILIO_ACCOUNT_SID")
auth_token    = os.getenv("TWILIO_AUTH_TOKEN")
service_sid   = os.getenv("TWILIO_SERVICE_ID")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
ENDPOINT      = os.getenv("DB_ENDPOINT")
PORT          = os.getenv("DB_PORT")
DBNAME        = os.getenv("DB_NAME")
REGION        = os.getenv("AWS_REGION")
USER          = os.getenv("DB_USER")
PW            = os.getenv("DB_PW")
TIMEOUT_VALUE = 15
