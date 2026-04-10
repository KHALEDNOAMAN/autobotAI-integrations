# Zscaler Integration — Implementation Guide

## Overview

This integration connects autobotAI to the **Zscaler OneAPI** platform, providing programmatic access to Zscaler Internet Access (ZIA) and other Zscaler products through a unified authentication model.

It supports two connection interfaces:
- **REST API** — 162 ZIA endpoints auto-generated from the official OneAPI Postman collection
- **Python SDK** — Uses the official `zscaler-sdk-python` package with the `ZscalerClient`

## Authentication

### OneAPI Client Credentials (OAuth2)

This integration uses the **Zscaler OneAPI** framework with an OAuth2 `client_credentials` grant. This is a simple server-to-server token exchange — no UI flow, no redirects, no browser interaction.

**Credentials required:**

| Field | Description |
|---|---|
| `client_id` | API Client ID created in ZIdentity (Administration > API Clients) |
| `client_secret` | The corresponding client secret |
| `vanity_domain` | Your organization's vanity domain (the part before `.zslogin.net`) |

**Token exchange flow:**

```
POST https://<vanity_domain>.zslogin.net/oauth2/v1/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=<client_id>
&client_secret=<client_secret>
&audience=https://api.zscaler.com
```

Returns a Bearer token used as `Authorization: Bearer <token>` for all subsequent API calls.

**Base URL:** `https://api.zsapi.net`

All Zscaler products are accessed through product-specific path prefixes under this single base URL:

| Product | Path Prefix |
|---|---|
| ZIA (Internet Access) | `/zia/api/v1` |
| ZPA (Private Access) | `/zpa` |
| ZCC (Client Connector) | `/zcc/papi/public` |
| ZDX (Digital Experience) | `/zdx/v1` |
| ZTW (Cloud & Branch Connector) | `/ztw/api/v1` |
| ZIdentity | `/ziam/admin/api/v1` |

### Why OneAPI over Legacy ZIA Auth

The legacy ZIA API used `username + password + api_key + cloud` with a complex API key obfuscation algorithm and JSESSIONID session cookies. OneAPI replaces all of that with a single `client_id + client_secret` token exchange that:

- Is **simpler** (no obfuscation algorithm, no cookie management)
- Covers **all products** under one auth (ZIA, ZPA, ZCC, ZDX, ZTW, ZIdentity)
- Uses **standard OAuth2** (client_credentials grant)
- Is **Zscaler's recommended** going-forward approach

> **Note:** OneAPI requires the tenant to be migrated to ZIdentity. Tenants not yet migrated must use the legacy per-product APIs.

## File Structure

```
zscaler/
├── __init__.py              # Integration schema + service (auth, forms, creds)
├── code_sample.py           # Python SDK code sample template
├── python_sdk_clients.yml   # SDK client definition (zscaler-sdk-python)
├── inventory.json           # 18 ZIA resource tables for inventory
├── open_api.json            # 162 ZIA REST API endpoints (from Postman collection)
├── IMPLEMENTATION.md        # This file
└── logo-img/
    ├── dark.svg             # Zscaler logo for dark theme
    └── light.svg            # Zscaler logo for light theme
```

## Module Details

### `__init__.py`

**Schema (`ZscalerIntegration`):**
- `client_id` — API Client ID (excluded from serialization, stored securely)
- `client_secret` — API Client Secret (excluded from serialization, stored securely)
- `vanity_domain` — Organization's vanity domain (visible, not sensitive)

**Service (`ZscalerService`):**

| Method | Description |
|---|---|
| `_test_integration()` | Gets a token via `_get_token()`, then verifies by hitting `GET /zia/api/v1/status` |
| `get_forms()` | Returns form config with `client_id`, `client_secret`, `vanity_domain` fields |
| `supported_connection_interfaces()` | Returns `[REST_API, PYTHON_SDK]` |
| `generate_rest_api_creds()` | Gets Bearer token, returns `RestAPICreds` with `base_url=https://api.zsapi.net/zia` |
| `generate_python_sdk_creds()` | Returns `SDKCreds` with `ZSCALER_CLIENT_ID`, `ZSCALER_CLIENT_SECRET`, `ZSCALER_VANITY_DOMAIN` env vars |
| `build_python_exec_combinations_hook()` | Creates a `ZscalerClient` from the SDK and enters its context manager |

**Helper function:**

| Function | Description |
|---|---|
| `_get_token(client_id, client_secret, vanity_domain)` | POSTs to ZIdentity token endpoint, returns Bearer access token |

### `code_sample.py`

Template for Python SDK actions. The client is a `ZscalerClient` instance that provides access to all Zscaler products:

```python
client = clients["zscaler"]

# ZIA
users, _, err = client.zia.user_management.list_users()

# ZPA
groups, _, err = client.zpa.segment_groups.list_groups()

# ZDX
apps, _, err = client.zdx.apps.list_apps()
```

### `open_api.json`

OpenAPI 3.0 specification with **162 unique ZIA endpoint paths** converted from the official Zscaler OneAPI Postman collection (`OneAPI_postman_collection_03_05_2026.json`). Covers:

- Activation (2 endpoints)
- Admin Audit Logs (12 endpoints)
- Admin & Role Management (5 endpoints)
- Browser Isolation (1 endpoint)
- Data Loss Prevention (35 endpoints)
- Device Groups (2 endpoints)
- Event Logs (4 endpoints)
- Firewall Policies (40 endpoints)
- Forwarding Control Policy (10 endpoints)
- Intermediate CA Certificates (19 endpoints)
- IoT Report (4 endpoints)
- Location Management (19 endpoints)
- Rule Labels (5 endpoints)
- Sandbox Report & Settings (6 endpoints)
- Security Policy Settings (6 endpoints)
- Shadow IT Report (6 endpoints)
- Traffic Forwarding (29 endpoints)
- URL Categories (11 endpoints)
- URL Filtering Policies (5 endpoints)
- User Authentication Settings (6 endpoints)
- User Management (15 endpoints)
- Workload Groups (1 endpoint)

Methods breakdown: **120 GET**, **44 POST**, **30 PUT**, **24 DELETE**

The `{base_url}` server variable is resolved at runtime to `https://api.zsapi.net/zia` by `generate_rest_api_creds()`.

### `python_sdk_clients.yml`

```yaml
- name: zscaler
  import_library_names:
    - zscaler
  pip_package_names:
    - zscaler-sdk-python
```

### `inventory.json`

18 ZIA resource tables for steampipe/inventory operations:

| Table | Key Columns |
|---|---|
| `zscaler_admin_user` | id, login_name, username, email, role |
| `zscaler_user` | id, name, email, groups, department |
| `zscaler_group` | id, name, comments |
| `zscaler_department` | id, name, idp_id |
| `zscaler_location` | id, name, country, ip_addresses, ports |
| `zscaler_url_category` | id, configured_name, super_category, type, urls |
| `zscaler_url_filtering_rule` | id, name, order, state, action, url_categories |
| `zscaler_firewall_rule` | id, name, order, state, action, src_ips, dest_addresses |
| `zscaler_dlp_dictionary` | id, name, confidence_threshold, dictionary_type |
| `zscaler_dlp_engine` | id, name, engine_expression |
| `zscaler_ip_source_group` | id, name, ip_addresses |
| `zscaler_ip_destination_group` | id, name, type, addresses |
| `zscaler_network_service` | id, name, src_tcp_ports, dest_tcp_ports |
| `zscaler_vpn_credential` | id, type, fqdn, ip_address |
| `zscaler_sandbox_report` | md5, sha256, file_type, status, zscaler_score |
| `zscaler_security_policy` | allowlist_urls, blocklist_urls |
| `zscaler_admin_role` | id, name, rank, policy_access, permissions |
| `zscaler_activation_status` | status |

## Setup Instructions

### Prerequisites

1. Your Zscaler tenant must be migrated to **ZIdentity**
2. An **API Client** must be created in ZIdentity Admin UI:
   - Navigate to **Administration > API Clients**
   - Create a new API client with the required scopes/roles
   - Note the `Client ID` and `Client Secret`
3. Know your **vanity domain** (e.g., if your login URL is `https://mycompany.zslogin.net`, the vanity domain is `mycompany`)

### Configuration

Provide these three values when creating the integration in autobotAI:

| Field | Example |
|---|---|
| Client ID | `abc123def456...` |
| Client Secret | `secret789xyz...` |
| Vanity Domain | `mycompany` |

### Verifying

The integration test hits `GET /zia/api/v1/status` after obtaining a token. A successful test confirms:
1. The token endpoint is reachable (`https://<vanity_domain>.zslogin.net`)
2. The client credentials are valid
3. The Bearer token works against the ZIA API

## References

- [Zscaler OneAPI Documentation](https://automate.zscaler.com/docs/getting-started/getting-started)
- [Zscaler Python SDK (zscaler-sdk-python)](https://github.com/zscaler/zscaler-sdk-python)
- [ZIdentity API Clients Guide](https://help.zscaler.com/zidentity/about-api-clients)
- [OneAPI Postman Collection](https://automate.zscaler.com) — Source for `open_api.json` (243 ZIA requests → 148 unique paths)

## Updating the OpenAPI Spec

To regenerate `open_api.json` from a newer Postman collection:

1. Download the latest collection from:
   `https://automate.zscaler.com/downloads/OneAPI_postman_collection_03_05_2026.json`
2. Run the converter script:
   ```
   python convert_postman_to_openapi.py <downloaded_collection.json> open_api.json
   ```