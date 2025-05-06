
def extract_services(arm):
    services = set()

    def find_services_in_blob(blob):
        b = str(blob).lower()
        if "office365" in b or "outlook.office365" in b:
            services.add("Office365")
        if "automation" in b or "azureautomation" in b:
            services.add("AzureAutomation")
        if "graph.microsoft.com" in b or "graph" in b:
            services.add("Graph")
        if "teams" in b:
            services.add("Teams")
        if "sharepoint" in b:
            services.add("SharePoint")

    # Scan all resources
    for res in arm.get("resources", []):
        find_services_in_blob(res)

    # Find logic app actions
    logic_app = next((r for r in arm.get("resources", []) if "workflows" in r.get("type", "")), {})
    definition = logic_app.get("properties", {}).get("definition", {})
    actions = definition.get("actions", {})

    for action in actions.values():
        find_services_in_blob(action.get("inputs", {}))
        find_services_in_blob(action.get("metadata", {}))
        find_services_in_blob(action.get("runAfter", {}))
        find_services_in_blob(action)

    return sorted(services)
