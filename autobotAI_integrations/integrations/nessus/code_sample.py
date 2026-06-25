from autobotAI_integrations.integrations.nessus import NessusClient

# Initialize the Nessus client
client = NessusClient(
    url="https://localhost:8834",
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY"
)

# Fetch all scans
response = client.list_scans()
if response.status_code == 200:
    scans = response.json().get("scans", [])
    for scan in scans:
        print(f"Scan Name: {scan['name']}, Status: {scan['status']}")
else:
    print(f"Error: {response.status_code}")
