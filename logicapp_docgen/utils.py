
def extract_services(arm):
    services = set()

    # Extract from resources
    for res in arm.get("resources", []):
        if res.get("type", "").lower() == "microsoft.web/connections":
            name = res.get("name", "").lower()
            if "office365" in name:
                services.add("Office365")
            elif "automation" in name:
                services.add("AzureAutomation")
            elif "graph" in name:
                services.add("Graph")

    # Extract from actions
    logic_app = next((r for r in arm.get("resources", []) if "workflows" in r.get("type", "")), {})
    actions = logic_app.get("properties", {}).get("definition", {}).get("actions", {})

    for action in actions.values():
        if isinstance(action, dict):
            blob = str(action).lower()
            if "office365" in blob or "outlook.office365" in blob:
                services.add("Office365")
            if "automation" in blob or "azureautomation" in blob:
                services.add("AzureAutomation")
            if "graph.microsoft.com" in blob or "graph" in blob:
                services.add("Graph")
            if "sharepoint" in blob:
                services.add("SharePoint")
            if "teams" in blob:
                services.add("Teams")

    return sorted(services)
