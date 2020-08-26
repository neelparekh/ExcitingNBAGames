# Alerts for Exciting NBA Games

Get a text message to your phone number (Twilio) when an NBA game becomes exciting. Uses Python and Flask.

## Set up

### Requirements

- [Python](https://www.python.org/) **3.6**, **3.7** or **3.8** version.

### Twilio Account Settings

This application should give you a ready-made starting point for writing your own application.
Before we begin, we need to collect all the config values we need to run the application:

| Config Value | Description |
| :----------  | :---------- |
| TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN | You could find them in your [Twilio Account Settings](https://www.twilio.com/console/account/settings)|
| TWILIO_NUMBER | You may find it [here](https://www.twilio.com/console/phone-numbers/incoming) |

### Local development

1. First clone this repository and `cd` into it.

   ```bash
   git clone <this_repo>
   cd ExcitingNBAGames
   ```

2. Create your virtual environment, load it and install the dependencies. They're outlined in the requirements.txt

3. Copy the sample configuration file and edit it to match your configuration.

   ```bash
   cp .env.example .env
   ```

   See [Twilio Account Settings](#twilio-account-settings) to locate the necessary environment variables.

4. Start the server.

   ```bash
   python exciting_nba_games_app/app.py
   ```

5. Check it out at: [http://localhost:5000/](http://localhost:5000/).

That's it!
