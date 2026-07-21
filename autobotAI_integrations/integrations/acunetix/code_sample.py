from autobotAI_integrations.integrations.acunetix import AcunetixClient

# Initialize the Acunetix client
client = AcunetixClient(
    url="https://online.acunetix.com/api/v1",
    api_key="YOUR_API_KEY",
    verify_ssl=False
)

# Fetch targets list
response = client.list_targets(limit=10)
if response.status_code == 200:
    targets = response.json().get("targets", [])
    for target in targets:
        print(f"Target ID: {target['target_id']}, Address: {target['address']}")
else:
    print(f"Failed to query targets: {response.status_code} - {response.text}")
