# Withings-Slack integration

Pushes messages to a pre-selected slack channel, when users log new weight data in Withings.

## Configuration

* Create an application in the Withings developer console
* Create an application on Slack, with a webhook to post messages to a specific channel.
* Copy the `.env.template` file to `.env`, and modify the values.

## Retrieve the docker image

### Option 1: build the docker image from this repositor:

docker build -t withings-slack .

### Option 2: pull the docker image

docker pull ghcr.io/caarmen/withings-slack:latest

## Run the docker image

Create a folder on the host where the database will be saved. This should match what you put in `.env` for `DATABASE_PATH`.

Run the docker image. In this example, we save the database to the `/tmp/withingsslack/` folder on the host, and `DATABASE_PATH` has been set to `/tmp/withingsslack/users.db`.

```
docker run --detach --publish 8000:8000 -v `pwd`/.env:/app/.env -v /tmp/withingsslack/:/tmp/withingsslack withings-slack
```

## Using the application

* Open the following url in a browser: http://your-server/v1/withings-authorization/your-slack-alias
  - Change `your-server` with the address on which the server is available.
  - Change `your-slack-alias` with your slack username.
* Authorize the app in the Withings screen.
* Log a new weight measurement in your Withings account.
  - You should see a message in the configured slack channel saying: "`your-slack-alias` weighed in at XX kg on Sat 29 Apr 2023, 17:45"

### Forcing a measurement to be pushed to slack
You can force a measurement to be posted to slack, by simulating Withings calling the webhook:
```
curl --location 'http://your-server/withings-notification-webhook/' \
--form 'userid="1234567"' \
--form 'startdate="1680377444"' \
--form 'enddate="1682969444"'
```

You can find your userid in the database file:
```
sqlite3 /path/to/database.db "select slack_alias, oauth_userid from users;"
```
where `/path/to/database.db` matches `DATABASE_PATH` in `.env`.