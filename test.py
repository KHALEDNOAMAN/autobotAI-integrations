from opensearchpy import OpenSearch, RequestsHttpConnection, Urllib3AWSV4SignerAuth
import boto3
import os

# --- Configuration ---
# Corrected HOST - remove the 'https://' prefix
HOST = 'gm5wovxagaci1z546q2f.ap-south-1.aoss.amazonaws.com' 

# Correct region for your host
REGION = 'ap-south-1' 

SERVICE = 'aoss' # Important: 'aoss' for OpenSearch Serverless

# --- Get AWS Credentials ---
credentials = boto3.Session().get_credentials()
auth = Urllib3AWSV4SignerAuth(credentials, REGION, SERVICE)

# --- Connect to OpenSearch Serverless ---
try:
    client = OpenSearch(
        hosts=[{'host': HOST, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True        
    )

    # --- Test the connection (e.g., get cluster info) ---
    print("Attempting to connect to OpenSearch Serverless...")
    response = client.info()
    print("Connection successful!")
    print(f"OpenSearch Serverless Info: {response}")

    # ... rest of your code for indexing, searching, etc. ...

except Exception as e:
    print(f"An error occurred: {e}")