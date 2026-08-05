import requests

def executor(context):
    # Retrieve the initialized Nessus client from the context
    nessus_client = context["clients"].get("nessus")
    
    if not nessus_client:
        return {"error": "Nessus client not found in context. Ensure integration is configured."}
        
    # Example: Fetch all scans
    try:
        response = nessus_client.list_scans()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to list scans due to network error: {e!s}"}
    
    if response.status_code == 200:
        try:
            data = response.json()
            if not isinstance(data, dict) or not isinstance(data.get("scans"), list):
                return {"error": "Unexpected response schema from API: invalid 'scans' list"}
            return {"scans": data.get("scans", [])}
        except ValueError:
            return {"error": "Invalid JSON payload in response"}
            
    return {
        "error": f"Failed to list scans. Status code: {response.status_code}", 
        "details": response.text
    }
