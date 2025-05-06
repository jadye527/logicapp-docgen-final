
import json

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

def extract_workflow_structure(arm):
    workflow = next((r for r in arm.get("resources", []) if "workflows" in r.get("type", "")), {})
    definition = workflow.get("properties", {}).get("definition", {})
    return {
        "name": workflow.get("name"),
        "triggers": list(definition.get("triggers", {}).keys()),
        "actions": list(definition.get("actions", {}).keys()),
        "action_details": definition.get("actions", {}),
    }

def extract_run_after_mapping(actions):
    run_after_map = {}
    for name, action in actions.items():
        run_after = action.get("runAfter", {})
        run_after_map[name] = run_after
    return run_after_map

def extract_conditions_and_branches(actions):
    branches = {
        "conditions": [],
        "foreach": [],
        "switch": []
    }
    for name, action in actions.items():
        if action.get("type", "").lower() == "if":
            branches["conditions"].append(name)
        if action.get("type", "").lower() == "foreach":
            branches["foreach"].append(name)
        if action.get("type", "").lower() == "switch":
            branches["switch"].append(name)
    return branches

def extract_error_handling(actions):
    error_actions = []
    for name, action in actions.items():
        if "error" in name.lower() or "failed" in name.lower():
            error_actions.append(name)
        elif "runAfter" in action:
            for dep, results in action["runAfter"].items():
                if any(status.lower() == "failed" for status in results):
                    error_actions.append(name)
    return list(set(error_actions))

def extract_architecture_metadata(arm):
    workflow = next((r for r in arm.get("resources", []) if "workflows" in r.get("type", "")), {})
    return {
        "name": workflow.get("name", "Unknown"),
        "location": workflow.get("location", "Unknown"),
        "resource_group": "rk-eus-prod-rg-citinf",  # optional: parse from parameters if needed
        "subscription_id": "a9360cdd-bae2-448e-ae6e-0d0a1300c218",  # optional: parse from connections
        "tags": workflow.get("tags", {}),
        "automation_account": "wd-eus-prod-lifecycle-workflow"  # hardcoded for now, extract from connection?
    }

def extract_execution_flow_steps(actions, run_after):
    steps = []
    visited = set()

    def describe_action(name):
        if name in visited:
            return
        visited.add(name)
        step = f"Step: {name}"
        if name.lower().startswith("http") or "http" in name.lower():
            step += " → Call external HTTP endpoint"
        elif "create" in name.lower():
            step += " → Call Azure Automation to start job"
        elif "status" in name.lower():
            step += " → Poll job status"
        elif "parse" in name.lower():
            step += " → Parse job output"
        elif "compose" in name.lower():
            step += " → Compose message"
        elif "email" in name.lower():
            step += " → Send failure email"
        elif "callback" in name.lower() or "post" in name.lower():
            step += " → Post callback to lifecycle system"
        steps.append(step)

        for next_action, deps in run_after.items():
            if name in deps:
                describe_action(next_action)

    for action in actions:
        if not run_after[action]:  # start points
            describe_action(action)

    return steps

def describe_flow_diagram_text(actions, run_after):
    lines = ["Logic App Flow:"]
    for action, deps in run_after.items():
        if not deps:
            lines.append(f"{action} →")
        for dep in deps:
            lines.append(f"{dep} → {action}")
    return lines

def describe_data_flow_text(actions):
    flow = set()
    for name, action in actions.items():
        if action.get("type") == "Http" or "uri" in str(action).lower():
            flow.add(f"{name}: interacts with external API or service")
        if "connection" in str(action).lower():
            flow.add(f"{name}: uses a connector (e.g., Office365, Automation)")
    return sorted(flow)

def describe_hybrid_integration_text(services):
    return [f"Service Integrated: {s}" for s in services]

def extract_condition_branches(actions):
    condition_details = {}
    for name, action in actions.items():
        if action.get("type", "").lower() == "if":
            condition_details[name] = {
                "expression": action.get("expression"),
                "if_true": list(action.get("actions", {}).keys()),
                "if_false": list(action.get("else", {}).get("actions", {}).keys())
            }
    return condition_details

def describe_flow_diagram_text(actions, run_after):
    lines = ["Logic App Flow:"]
    printed_arrows = set()
    for action, deps in run_after.items():
        if not deps and all((action, other) not in printed_arrows for other in run_after):
            lines.append(f"{action} →")
        for dep in deps:
            arrow = (dep, action)
            if arrow not in printed_arrows:
                lines.append(f"{dep} → {action}")
                printed_arrows.add(arrow)
    return lines
