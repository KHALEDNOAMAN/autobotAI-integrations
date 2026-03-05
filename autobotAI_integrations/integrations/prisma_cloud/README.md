# Prisma Cloud Integration

## Overview

**Prisma Cloud** by Palo Alto Networks is a comprehensive Cloud Native Application Protection Platform (CNAPP) that provides:

- **Cloud Security Posture Management (CSPM)** - Continuous monitoring and compliance assessment
- **Cloud Workload Protection (CWP)** - Runtime protection for containers, hosts, and serverless
- **Cloud Infrastructure Entitlement Management (CIEM)** - IAM security and least privilege enforcement
- **Cloud Network Security (CNS)** - Network visibility and micro-segmentation

This integration enables AutobotAI to connect with Prisma Cloud to retrieve security alerts, policies, compliance data, asset inventory, vulnerabilities, and IAM permissions across multi-cloud environments.

## Features

✅ **Multi-Cloud Support**: AWS, Azure, GCP, Alibaba Cloud, Oracle Cloud  
✅ **Security Alerts**: Retrieve and analyze security findings  
✅ **Policy Management**: Access configuration, network, and audit policies  
✅ **Compliance Monitoring**: Track compliance posture across frameworks  
✅ **Asset Inventory**: Comprehensive cloud asset visibility  
✅ **Vulnerability Scanning**: CVE tracking and remediation guidance  
✅ **IAM Permissions**: Entitlement analysis and least privilege recommendations  
✅ **Network Exposure**: Internet-facing resources and network path analysis  

## Configuration

### Prerequisites

1. **Prisma Cloud Account** with API access enabled
2. **Access Key ID** and **Secret Key** with appropriate permissions
3. **API URL** for your Prisma Cloud instance (varies by region)

### API URLs by Region

| Region | API URL |
|--------|---------|
| US (app.prismacloud.io) | `https://api.prismacloud.io` |
| US (app2.prismacloud.io) | `https://api2.prismacloud.io` |
| US (app3.prismacloud.io) | `https://api3.prismacloud.io` |
| US (app4.prismacloud.io) | `https://api4.prismacloud.io` |
| EU (app.eu.prismacloud.io) | `https://api.eu.prismacloud.io` |
| EU (app2.eu.prismacloud.io) | `https://api2.eu.prismacloud.io` |
| APAC (app.anz.prismacloud.io) | `https://api.anz.prismacloud.io` |
| UK (app.uk.prismacloud.io) | `https://api.uk.prismacloud.io` |
| Canada (app.ca.prismacloud.io) | `https://api.ca.prismacloud.io` |
| Singapore (app.sg.prismacloud.io) | `https://api.sg.prismacloud.io` |
| India (app.ind.prismacloud.io) | `https://api.ind.prismacloud.io` |

### Creating Access Keys

1. Log in to Prisma Cloud console
2. Navigate to **Settings** → **Access Keys**
3. Click **Add** → **Access Key**
4. Provide a name and select appropriate permissions
5. Copy the **Access Key ID** and **Secret Key** (save securely - secret key shown only once)

### Integration Setup

```python
from autobotAI_integrations.integrations.prisma_cloud import PrismaCloudService, PrismaCloudIntegrations

# Create integration configuration
integration = PrismaCloudIntegrations(
    userId="user-123",
    cspName="prisma_cloud",
    alias="Production Prisma Cloud",
    url="https://api.prismacloud.io",
    access_key_id="your-access-key-id",
    secret_key="your-secret-key"
)

# Initialize service
ctx = {"user_id": "user-123"}
service = PrismaCloudService(ctx, integration)

# Test connection
result = service._test_integration()
print(result)  # {"success": True}
```

## Available Resources

The integration provides access to 15 resource types:

### Security & Compliance
- `prisma_cloud_alert` - Security alerts and findings
- `prisma_cloud_policy` - Security policies (config, network, audit, etc.)
- `prisma_cloud_compliance_standard` - Compliance frameworks (PCI-DSS, HIPAA, etc.)
- `prisma_cloud_compliance_requirement` - Specific compliance requirements
- `prisma_cloud_vulnerability` - CVE findings and vulnerabilities

### Asset Management
- `prisma_cloud_account` - Connected cloud accounts
- `prisma_cloud_account_group` - Account groupings
- `prisma_cloud_asset_inventory` - Cloud resource inventory

### IAM & Network
- `prisma_cloud_iam_permission` - IAM entitlements and permissions
- `prisma_cloud_network_exposure` - Internet-exposed resources

### Administration
- `prisma_cloud_user` - Prisma Cloud users
- `prisma_cloud_user_role` - User roles and permissions
- `prisma_cloud_alert_rule` - Alert notification rules
- `prisma_cloud_integration` - Third-party integrations
- `prisma_cloud_audit_log` - Audit trail

## Usage Examples

### Retrieve High Severity Alerts

```python
from autobotAI_integrations.integrations.prisma_cloud.code_sample import PrismaCloudClient

client = PrismaCloudClient(
    api_url="https://api.prismacloud.io",
    access_key_id="your-access-key",
    secret_key="your-secret-key"
)

# Authenticate
client.authenticate()

# Get high severity alerts
alerts = client.get_alerts({
    "filters": [{
        "name": "policy.severity",
        "operator": "=",
        "value": "high"
    }]
})

for alert in alerts:
    print(f"Alert: {alert['policy_name']} - {alert['resource_name']}")
```

### Check Compliance Posture

```python
# Get AWS compliance posture
compliance = client.get_compliance_posture(cloud_type="aws")
print(f"Compliance Score: {compliance.get('score')}")
print(f"Failed Checks: {compliance.get('failed_resources')}")
```

### Query Asset Inventory

```python
# Get all assets in a specific account
assets = client.get_asset_inventory({
    "filters": [{
        "name": "account.id",
        "operator": "=",
        "value": "123456789012"
    }]
})

print(f"Total Assets: {len(assets)}")
```

### Find Vulnerabilities

```python
# Get critical vulnerabilities
vulns = client.get_vulnerabilities({
    "filters": [{
        "name": "severity",
        "operator": "=",
        "value": "critical"
    }]
})

for vuln in vulns:
    print(f"CVE: {vuln['cve_id']} - {vuln['package_name']} ({vuln['cvss_score']})")
```

## Supported Connection Interfaces

- ✅ **REST API** - Direct API integration
- ✅ **CLI** - Command-line interface support
- ⚠️ **Steampipe** - Placeholder (no official plugin yet)

## Permissions Required

The access key should have the following permissions:

- **Read-only access** for basic monitoring
- **System Admin** for full API access
- **Account Group Read Only** for specific account groups

Recommended: Create a dedicated service account with least privilege access.

## Rate Limits

- **Default**: 30 requests per second
- **Burst**: Up to 100 requests
- **Recommendation**: Implement exponential backoff for retries

## Troubleshooting

### Authentication Failed

**Error**: `Authentication failed. Status code: 401`

**Solutions**:
- Verify Access Key ID and Secret Key are correct
- Check if the API URL matches your Prisma Cloud instance region
- Ensure the access key is not expired or revoked
- Verify the access key has appropriate permissions

### Connection Timeout

**Error**: `Connection is unreachable`

**Solutions**:
- Verify network connectivity to Prisma Cloud API
- Check firewall rules allow outbound HTTPS (443)
- Confirm the API URL is correct for your region
- Check if Prisma Cloud is experiencing service issues

### Rate Limit Exceeded

**Error**: `429 Too Many Requests`

**Solutions**:
- Implement request throttling
- Use exponential backoff for retries
- Reduce concurrent API calls
- Contact Prisma Cloud support for rate limit increase

## Additional Resources

- [Prisma Cloud API Documentation](https://prisma.pan.dev/api/cloud/)
- [Prisma Cloud Developer Portal](https://prisma.pan.dev/)
- [Palo Alto Networks Documentation](https://docs.paloaltonetworks.com/prisma/prisma-cloud)
- [API Rate Limits](https://prisma.pan.dev/api/cloud/api-rate-limits/)

## Support

For integration issues:
- Check the [code_sample.py](./code_sample.py) for implementation examples
- Review [python_sdk_clients.yml](./python_sdk_clients.yml) for client configuration
- Refer to [inventory.json](./inventory.json) for available resource schemas

## License

This integration is part of the AutobotAI-integrations package.
