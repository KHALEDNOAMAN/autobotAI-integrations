def executor(context):
    client = context["clients"]["mxtoolbox"]
    params = context["params"]
    
    command = params.get("command", "dns")
    argument = params.get("argument", "example.com")
    
    response = client.lookup(command, argument)
    return response.json()
