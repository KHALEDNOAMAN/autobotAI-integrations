# Integrate Slack

## Overview

Slack is a popular messaging platform used by teams for communication and collaboration. Our product leverages Slack's API to enable seamless integration with your workspace. This allows you to send notifications, automate workflows, and interact with Slack channels directly from within our platform. Whether you need to alert your team about important events or trigger actions based on messages, our Slack integration ensures smooth and efficient communication.

There are two ways you can integrate Slack with AutobotAI:

1. Webhook Integration
2. Token-Based Integration

## 1. Webhook Integration

### What You’ll Need

#### Webhook URL
A **Webhook URL** is a unique URL provided by Slack that allows external applications to send messages to a Slack channel. By integrating this Webhook URL into our platform, you can automate notifications, alerts, or updates to your Slack workspace. Simply set up the webhook, and our platform will handle the communication by sending the relevant data directly to your chosen Slack channel.

**Note:**
*Messages can only be sent to the selected Slack channel. Other actions will not be available.*

#### Where to Find Webhook URL
1. **Sign Up**: If you don’t already have an account, sign up at [Slack](https://slack.com/).
2. **Login**: Once logged in, navigate to the [Slack API page](https://api.slack.com/apps) and create a new app.
3. **Create App**: Go to the [Slack API page](https://api.slack.com/apps) and create a new app.
4. **Activate Incoming Webhooks**: In the app settings, activate the "Incoming Webhooks" feature.
5. **Generate Webhook URL**: After enabling Incoming Webhooks, generate a new Webhook URL by selecting a channel where the messages will be posted.

## 2. Token-Based Integration

### What You’ll Need

#### OAuth Token
An **OAuth Token** is a token provided by Slack that allows your application to interact with Slack's API. This token can be a user or bot token, depending on the use case, but a **user token is recommended for enabling no-code actions**. The minimum required permissions include:
- `channels:read`
- `groups:read`
- `im:read`
- `mpim:read`

Additional permissions may be required depending on the specific actions you want to perform.

You can find the OAuth token by:
1. Navigating to the [Slack API page](https://api.slack.com/apps) and selecting your app.
2. Configuring the OAuth & Permissions section to request the necessary scopes and generate a token after user authorization.

#### Scopes Required
The minimum required scopes for basic functionality are mentioned above. For no-code actions, visit the [Steampipe Hub Slack Plugin](https://hub.steampipe.io/plugins/turbot/slack) to see the list of required scopes based on the actions you wish to perform. For Python actions, the scopes will depend on the specific API calls being made.


## How to Integrate

### 1. Configure Integration

#### Webhook Integration

1. **Access the Integrations Page**: Go to the integrations page in AutobotAI, click on `Add integration`, and navigate to `Slack`.
2. **Add Webhook URL**: Enter the Webhook URL generated from Slack in the integration details.
3. **Create Integration**: Click on the `Create` button to add the integration.

#### Bot Token Integration

1. **Access the Integrations Page**: Go to the integrations page in AutobotAI, click on `Add integration`, and navigate to `Slack`.
2. **Add Bot Token**: Enter the OAuth token (bot token) obtained from Slack in the integration details. Ensure the token has the necessary permissions for your use case.
3. **Create Integration**: Click on the `Create` button to add the integration.

### 2. Set Up Actions

Define the actions you want to automate using Slack. For example, you might want to:

- **Webhook Integration**:
  - **Send Notifications**: Automatically send alerts to a Slack channel when specific events occur in AutobotAI.
  - **Post Updates**: Post automated updates or status reports directly to a Slack channel.

- **Bot Token Integration**:
  - **Send Messages**: Use the bot to send direct messages or post messages in channels.
  - **Interact with Slack API**: Perform actions such as creating channels, managing users, or responding to messages based on bot capabilities.

### 3. Build Automated Workflows

Create workflows that trigger Slack actions based on predefined conditions within AutobotAI. This allows you to automate communication and streamline operations.

## Best Practices

- **Channel Management**: Regularly review the Slack channels or direct messages your integrations are posting to and ensure they are still relevant.
- **Notification Control**: Ensure that the frequency of notifications is manageable for your team and avoid overwhelming channels with too many messages.
- **Security**: Keep your Webhook URL and OAuth token secure. Avoid sharing them publicly and update them as needed to maintain security.

## Troubleshooting

- **Invalid Webhook URL or Bot Token**: Double-check that the Webhook URL or OAuth token is entered correctly and is active.
- **Integration Not Working**: Verify that your settings are correctly configured in both Slack and AutobotAI, and that the selected Slack channels or direct messages are accessible.
- **Contact Support**: If you encounter issues that you can’t resolve, contact Slack support or consult their [API Documentation](https://api.slack.com/).

## Additional Resources

- [Slack API Documentation](https://api.slack.com/)
- [Webhook Best Practices](https://api.slack.com/messaging/webhooks)
- [OAuth Token Scopes](https://api.slack.com/scopes)

