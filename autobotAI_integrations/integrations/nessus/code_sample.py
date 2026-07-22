def executor(context):
    # Retrieve the initialized Nessus client from the context
    nessus_client = context["clients"].get("nessus")
    
    if not nessus_client:
        return {"error": "Nessus client not found in context. Ensure integration is configured."}
        
    # Example: Fetch all scans
    response = nessus_client.list_scans()
    
    if response.status_code == 200:
        scans = response.json().get("scans", [])
        return {"scans": scans}
    else:
        return {
            "error": f"Failed to list scans. Status code: {response.status_code}", 
            "details": response.text
        }
