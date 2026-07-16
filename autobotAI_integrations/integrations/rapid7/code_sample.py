def executor(context):
    # Cloud API (v4) client — available if API Key is configured
    rapid7 = context["clients"].get("rapid7")

    # Console API (v3) client — available if Security Console credentials are configured
    rapid7_console = context["clients"].get("rapid7_console")

    params = context["params"]

    # Example 1: Query inventory assets using Cloud API (v4)
    if rapid7:
        page = params.get("page", 0)
        size = params.get("size", 25)
        response = rapid7.get_assets(page=page, size=size)
        return response.json()

    # Example 2: Trigger live vulnerability scan using Console API (v3)
    if rapid7_console:
        site_id = params.get("site_id", 1)
        response = rapid7_console.trigger_site_scan(site_id=site_id)
        return response.json()

    return {"error": "Neither rapid7 nor rapid7_console client configured"}

