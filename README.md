# Withings-Slack integration

Pushes messages to a pre-selected slack channel, when users log new weight data in Withings.

[![GitHub Workflow Status (with branch)](https://img.shields.io/github/actions/workflow/status/caarmen/withings-slack/check.yml)](https://github.com/caarmen/withings-slack/actions/workflows/check.yml?query=branch%3Amain)
[![GitHub](https://img.shields.io/github/license/caarmen/withings-slack)](https://github.com/caarmen/withings-slack/blob/main/LICENSE)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/caarmen/withings-slack)](https://github.com/caarmen/withings-slack/releases)

[![GitHub repo size](https://img.shields.io/github/repo-size/caarmen/withings-slack)](https://github.com/caarmen/withings-slack/archive/refs/heads/main.zip)
![GitHub language count](https://img.shields.io/github/languages/count/caarmen/withings-slack)
[![GitHub Release Date](https://img.shields.io/github/release-date/caarmen/withings-slack)](https://github.com/caarmen/withings-slack/releases)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/caarmen/withings-slack)](https://github.com/caarmen/withings-slack/commits/main)
[![GitHub last commit](https://img.shields.io/github/last-commit/caarmen/withings-slack)](https://github.com/caarmen/withings-slack/commits/main)

[![GitHub Repo stars](https://img.shields.io/github/stars/caarmen/withings-slack?style=social)](https://github.com/caarmen/withings-slack/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/caarmen/withings-slack?style=social)](https://github.com/caarmen/withings-slack/forks)

## Configuration

* Create an application in the [Withings developer dashboard](https://developer.withings.com/dashboard/).
* Create an application [on Slack](https://api.slack.com/apps), with a webhook to post messages to a specific channel.
* Copy the `.env.template` file to `.env`, and modify the values.

## Retrieve the docker image

Log into the [github container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

Retrieve the image:
```
docker pull ghcr.io/caarmen/withings-slack:latest
```

## Run the docker image

Create a folder on the host where the database will be saved: `/path/to/data/`.

Run the docker image.

```
docker run --detach --publish 8000:8000 -v `pwd`/.env:/app/.env -v /path/to/data/:/tmp/data ghcr.io/caarmen/withings-slack
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
sqlite3 -header -column /path/to/slackhealthbot.db \
  "select
     slack_alias,
     withings_users.oauth_userid as withings_userid,
     fitbit_users.oauth_userid as fitbit_userid
  from users
    left outer join withings_users on users.id = withings_users.user_id
    left outer join fitbit_users on users.id = fitbit_users.user_id;"
```
