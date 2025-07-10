# Integrate Zenduty

## Overview

Zenduty is an incident management platform that helps teams respond to critical issues faster with intelligent alerting, escalations, and on-call scheduling. By integrating with Zenduty, you can automate incident response workflows and enhance your system's reliability monitoring.

## What You'll Need

### Zenduty API Token

To use Zenduty, you need an API token. This token is required for authentication and to interact with their services.

### Where to Find Your API Token

1. **Sign Up**: If you don't already have an account, sign up at [Zenduty](https://www.zenduty.com/).
2. **Login**: Once logged in, navigate to your account settings.
3. **API Tokens**: Go to the API Tokens section in your account settings.
4. **Generate Token**: Create a new API token with appropriate permissions.

## How to Integrate

### 1. Configure API Token

1. **Access the Integrations Page**: Go to integrations page in AutobotAI, Click on `Add integration` and navigate to `Zenduty`.
2. **Add API Token**: Configure integration details with your API token.
3. **Set Base URL**: Use the default `https://www.zenduty.com/api` or your custom Zenduty instance URL.
4. **Create Integration**: Click on `Create` button to add the integration.

### 2. Set Up Actions

Define the actions you want to automate using Zenduty. For example, you might want to:

- **Create Incidents**: Automatically create incidents when critical alerts are triggered.
- **Update Incidents**: Update incident status and add notes programmatically.
- **Manage On-Call**: Automate on-call schedule management and escalations.
- **Send Alerts**: Trigger alerts to specific teams or individuals.

### 3. Build Automated Workflows

Use both REST API and Python SDK interfaces to build comprehensive incident management workflows.

## Connection Interfaces

### REST API
- Direct HTTP requests to Zenduty API endpoints
- Full access to all Zenduty API functionality
- Suitable for simple integrations and webhook responses

### Python SDK
- Use the Zenduty Python SDK for more complex integrations
- Object-oriented interface for easier development
- Better error handling and type safety

## Best Practices

- **Secure Token Storage**: Keep your API token secure and rotate it regularly.
- **Rate Limiting**: Be aware of Zenduty's API rate limits to avoid throttling.
- **Error Handling**: Implement proper error handling for API failures.
- **Monitoring**: Monitor your integration's performance and alert delivery.

## Troubleshooting

- **Invalid API Token**: Verify that the API token is correct and has necessary permissions.
- **Connection Issues**: Check network connectivity and base URL configuration.
- **Rate Limiting**: Implement exponential backoff for rate-limited requests.
- **Contact Support**: Reach out to Zenduty support for platform-specific issues.

## Additional Resources

- [Zenduty API Documentation](https://docs.zenduty.com/docs/api)
- [Zenduty Python SDK](https://github.com/Zenduty/zenduty-python-sdk)
- [Incident Management Best Practices](https://docs.zenduty.com/docs/incident-management)

## Code Examples

### Python SDK Usage

```python
# Create incident using Zenduty Python SDK
api_obj = zenduty.IncidentsApi(api_client)
body = {
    "service": "c7fff4c5-2def-41e8-9120-c63f649a825c",
    "escalation_policy": "a70244c8-e343-4dd0-8d87-2f767115568a",
    "user": None,
    "title": "Name of trial",
    "summary": "summary of trial"
}
response = api_obj.create_incident(body)
print(response.data)
print(response.status_code)
```