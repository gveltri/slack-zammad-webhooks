# slack-zammad-webhooks
Webhooks that allow ticket creation in Zammad from Slack/Mattermost for better knowledge management and communication between platforms.

### Quickstart

In the Slack/Mattermost Integrations tab, create a slash command for with the endpoint being the designated IP/hostname from which you intend to run the webhook application. For ticket creation, the url should look something like:

[POST] http://[webhooks domain]/zammad/ticket

After SSH'ing onto the server hosting your organization's webhook, run

```git clone git@github.com:gveltri/slack-zammad-webhooks.git```

to copy the application into your environment. Fill in the values in docker-compose.yml.j2 and rename to docker-compose.yml:
```
version: '2'
services:
  web:
    image: # image name for docker
    ports:
    - 80:80
    environment:
      ZAMMAD_TOKEN: # zammad api token
      MATTERMOST_TOKENS: # mattermost token(s) if multiple slash commands, comma delimited
      COMPANY_DOMAIN: # email domain to infer from --assignee option
      ZAMMAD_DOMAIN: # zammad domain
      ZAMMAD_DEFAULT_GROUP: # default group for ticket ownership
```
Build the image with the command

```docker build . -t [image name from docker-compose]```

and launch the service with 

```docker-compose up -d```.
