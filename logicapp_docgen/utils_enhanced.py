
import re

def extract_workflow_structure(arm):
    workflow = next((r for r in arm.get("resources", []) if "workflows" in r.get("type", "")), {})
    definition = workflow.get("properties", {}).get("definition", {})
    return {
        "triggers": definition.get("triggers", {}),
        "actions": definition.get("actions", {}),
        "action_details": definition.get("actions", {}),
    }

def extract_run_after_mapping(actions):
    run_after = {}
    for name, details in actions.items():
        run_after[name] = list(details.get("runAfter", {}).keys())
    return run_after

def extract_architecture_metadata(arm):
    workflow = next((r for r in arm.get("resources", []) if "workflows" in r.get("type", "")), {})
    return {
        "name": workflow.get("name", "Unknown"),
        "location": workflow.get("location", "Unknown"),
        "resource_group": "rk-eus-prod-rg-citinf",
        "subscription_id": "a9360cdd-bae2-448e-ae6e-0d0a1300c218",
        "tags": workflow.get("tags", {}),
        "automation_account": "wd-eus-prod-lifecycle-workflow"
    }

def extract_execution_flow_steps(actions, run_after):
    steps = []
    visited = set()

    def describe_action(name):
        if name in visited:
            return
        visited.add(name)
        step = f"Step: {name}"
        lname = name.lower()
        if "http" in lname:
            step += " → Call external HTTP endpoint"
        elif "create" in lname:
            step += " → Call Azure Automation to start job"
        elif "status" in lname:
            step += " → Poll job status"
        elif "parse" in lname:
            step += " → Parse job output"
        elif "compose" in lname:
            step += " → Compose message"
        elif "email" in lname:
            step += " → Send failure email"
        elif "callback" in lname or "post" in lname:
            step += " → Post callback to lifecycle system"
        steps.append(step)

        for next_action, deps in run_after.items():
            if name in deps:
                describe_action(next_action)

    for action in actions:
        if not run_after[action]:  # starting points
            describe_action(action)

    return steps

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

def extract_services(arm):
    services = set()
    for resource in arm.get("resources", []):
        r_type = resource.get("type", "").lower()
        if "connections" in r_type:
            conn_name = resource.get("name", "")
            services.add(conn_name)
    return sorted(services)
