def executor(context):
    client = context["clients"]["rapid7"]
    params = context["params"]

    # Example: list assets with optional pagination
    page = params.get("page", 0)
    size = params.get("size", 25)

    response = client.get_assets(page=page, size=size)
    return response.json()
