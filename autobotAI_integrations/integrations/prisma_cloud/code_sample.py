"""
Prisma Cloud API Integration Code Sample

This sample demonstrates how to authenticate and interact with Prisma Cloud API
to retrieve security alerts, policies, and compliance data.
"""

import requests
import json
from typing import Dict, List, Optional


class PrismaCloudClient:
    """
    Prisma Cloud API Client
    
    This client provides methods to interact with Prisma Cloud CSPM APIs
    for retrieving alerts, policies, compliance data, and asset inventory.
    """
    
    def __init__(self, api_url: str, access_key_id: str, secret_key: str):
        """
        Initialize Prisma Cloud client
        
        Args:
            api_url: Prisma Cloud API URL (e.g., https://api.prismacloud.io)
            access_key_id: Access Key ID for authentication
            secret_key: Secret Key for authentication
        """
        self.api_url = api_url.rstrip('/')
        self.access_key_id = access_key_id
        self.secret_key = secret_key
        self.token = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with Prisma Cloud and obtain JWT token
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        auth_url = f"{self.api_url}/login"
        payload = {
            "username": self.access_key_id,
            "password": self.secret_key
        }
        
        try:
            response = requests.post(auth_url, json=payload, timeout=30)
            response.raise_for_status()
            self.token = response.json().get('token')
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        return {
            'Content-Type': 'application/json',
            'x-redlock-auth': self.token
        }
    
    def get_alerts(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Retrieve security alerts from Prisma Cloud
        
        Args:
            filters: Optional filters for alerts (time range, severity, etc.)
            
        Returns:
            List of alert objects
        """
        url = f"{self.api_url}/v2/alert"
        
        if not self.token:
            self.authenticate()
        
        try:
            response = requests.post(
                url, 
                headers=self._get_headers(),
                json=filters or {},
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('items', [])
        except Exception as e:
            print(f"Failed to retrieve alerts: {e}")
            return []
    
    def get_policies(self, policy_type: Optional[str] = None) -> List[Dict]:
        """
        Retrieve security policies from Prisma Cloud
        
        Args:
            policy_type: Optional policy type filter (config, network, audit_event, etc.)
            
        Returns:
            List of policy objects
        """
        url = f"{self.api_url}/v2/policy"
        
        if not self.token:
            self.authenticate()
        
        params = {}
        if policy_type:
            params['policy.policyType'] = policy_type
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to retrieve policies: {e}")
            return []
    
    def get_compliance_posture(self, cloud_type: Optional[str] = None) -> Dict:
        """
        Retrieve compliance posture summary
        
        Args:
            cloud_type: Optional cloud type filter (aws, azure, gcp, etc.)
            
        Returns:
            Compliance posture data
        """
        url = f"{self.api_url}/compliance/posture"
        
        if not self.token:
            self.authenticate()
        
        params = {}
        if cloud_type:
            params['cloudType'] = cloud_type
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to retrieve compliance posture: {e}")
            return {}
    
    def get_asset_inventory(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Retrieve asset inventory from Prisma Cloud
        
        Args:
            filters: Optional filters for assets (cloud type, account, region, etc.)
            
        Returns:
            List of asset objects
        """
        url = f"{self.api_url}/v2/inventory"
        
        if not self.token:
            self.authenticate()
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=filters or {},
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('items', [])
        except Exception as e:
            print(f"Failed to retrieve asset inventory: {e}")
            return []
    
    def get_vulnerabilities(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Retrieve vulnerability findings
        
        Args:
            filters: Optional filters for vulnerabilities (severity, CVE, etc.)
            
        Returns:
            List of vulnerability objects
        """
        url = f"{self.api_url}/v2/vulnerability"
        
        if not self.token:
            self.authenticate()
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=filters or {},
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('items', [])
        except Exception as e:
            print(f"Failed to retrieve vulnerabilities: {e}")
            return []


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = PrismaCloudClient(
        api_url="https://api.prismacloud.io",
        access_key_id="your-access-key-id",
        secret_key="your-secret-key"
    )
    
    # Authenticate
    if client.authenticate():
        print("Authentication successful!")
        
        # Get high severity alerts
        alerts = client.get_alerts({
            "filters": [
                {
                    "name": "policy.severity",
                    "operator": "=",
                    "value": "high"
                }
            ]
        })
        print(f"Found {len(alerts)} high severity alerts")
        
        # Get all policies
        policies = client.get_policies()
        print(f"Found {len(policies)} policies")
        
        # Get compliance posture for AWS
        compliance = client.get_compliance_posture(cloud_type="aws")
        print(f"AWS Compliance Score: {compliance.get('score', 'N/A')}")
    else:
        print("Authentication failed!")
