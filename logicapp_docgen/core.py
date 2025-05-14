import os
import json
import subprocess
from docx import Document
from docx.shared import Inches
from graphviz import Digraph

from logicapp_docgen.utils import extract_services
from logicapp_docgen.diagram_builder import (
    build_dot_with_arm_and_runbook,
    build_simple_dot_from_arm_final,
    render_flow_diagram_from_arm,
    build_hybridintegration_from_flow,
    build_hybrid_with_o365_graph
)
from logicapp_docgen.runbook_utils import extract_runbook_label
from logicapp_docgen.generate_docx import generate_document
from logicapp_docgen import parser

def resolve_logic_app_name(name_expr, arm, parameters):
    if name_expr.startswith("[parameters("):
        param_key = name_expr.split("'")[1]
        param_obj = parameters.get(param_key) or arm.get("parameters", {}).get(param_key)
        return param_obj.get("value") or param_obj.get("defaultValue") or param_key
    return name_expr

def generate_document_from_arm(template_path, parameters_path, docx_template, output_path):
    output_dir = os.path.join(".", "output")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    with open(template_path) as f:
        arm = json.load(f)

    parameters = {}
    if parameters_path:
        with open(parameters_path) as pf:
            parameters = json.load(pf)

    logic_app_res = [r for r in arm.get("resources", []) if "/workflows" in r.get("type", "")]
    logic_app = logic_app_res[0] if logic_app_res else {}
    name_raw = logic_app.get("name", "LogicApp")
    logic_app_name = resolve_logic_app_name(name_raw, arm, parameters)
    region = logic_app.get("location", "unknown")
    tags = logic_app.get("tags", {})
    tag_purpose = tags.get("Purpose", "Not defined")
    definition = logic_app.get("properties", {}).get("definition", {})
    actions = definition.get("actions", {})
    triggers = definition.get("triggers", {})

       # 🔁 NEW DYNAMIC RUNBOOK LOGIC
    runbook_name = ""
    create_job = actions.get("Create_job", {})
    inputs = create_job.get("inputs", {})
    if "properties" in inputs:
        runbook_name = inputs["properties"].get("runbook", {}).get("name", "")
    elif "queries" in inputs:
        runbook_name = inputs["queries"].get("runbookName", "")

    runbook_path = os.path.join("runbooks", f"{runbook_name}.ps1")

    if os.path.exists(runbook_path):
        runbook_steps = extract_runbook_label(runbook_path, runbook_name).splitlines()
        if runbook_steps and runbook_steps[0].strip().lower() == f"{runbook_name.lower()} runbook":
            runbook_steps = runbook_steps[1:]
        runbook_label = "\\n".join([f"{runbook_name} Runbook"] + runbook_steps)
    else:
        runbook_label = f"{runbook_name} Runbook\\n{runbook_name}.ps1 not found"

    print("⚙️  Generating Logic App Flow Diagram...")
    condition_raw = actions.get("Condition", {})
    condition = condition_raw if isinstance(condition_raw, dict) else {}

    dot = render_dot = (
        build_dot_with_arm_and_runbook(actions, condition, runbook_label)
        if "AzureAutomation" in extract_services(arm)
        else build_simple_dot_from_arm_final(actions, triggers, condition)
    )

    flow_dot_path = os.path.join(output_dir, f"{logic_app_name}_Flow.dot")
    flow_png_path = os.path.join(output_dir, f"{logic_app_name}_Flow.png")

    with open(flow_dot_path, "w") as f:
        f.write(dot)
    subprocess.run(["dot", "-Tpng", flow_dot_path, "-o", flow_png_path], check=True)
    print("✅ Flow diagram saved to:", flow_png_path)

    hybrid_dot = build_hybrid_with_o365_graph(logic_app_name)
    hybrid_dot_path = os.path.join(output_dir, f"{logic_app_name}_Hybrid.dot")
    hybrid_png_path = os.path.join(output_dir, f"{logic_app_name}_Hybrid.png")

    with open(hybrid_dot_path, "w") as f:
        f.write(hybrid_dot)
    subprocess.run(["dot", "-Tpng", hybrid_dot_path, "-o", hybrid_png_path], check=True)

    wf = parser.extract_workflow_structure(arm)
    run_after = parser.extract_run_after_mapping(wf["action_details"])
    architecture = parser.extract_architecture_metadata(arm)
    architecture["name"] = logic_app_name  # override with resolved name
    execution = parser.extract_execution_flow_steps(wf["actions"], run_after)
    flow_text = parser.describe_flow_diagram_text(wf["action_details"], run_after)
    data_flow = parser.describe_data_flow_text(wf["action_details"])
    services = parser.extract_services(arm)
    hybrid_text = parser.describe_hybrid_integration_text(services)
    conditions = parser.extract_condition_branches(wf["action_details"])

    overview_summary = (
        f"This document provides an overview of the Azure Logic App named '{logic_app_name}', "
        f"which supports {tag_purpose.lower()} scenarios. It integrates services like {', '.join(services)} "
        "to streamline automated workflows and reduce manual effort."
    )

    architecture_summary = (
        f"The Logic App uses an event-driven architecture orchestrated through Azure connectors. "
        f"Primary services integrated include {', '.join(services)}. The workflow is built to support resilience, reusability, and monitoring."
    )

    execution_summary = (
        "The workflow includes multiple stages including job creation, status polling, external HTTP interaction, "
        "JSON parsing, conditional logic branching, email notifications, and Graph API callbacks."
    )

        # Dynamic purpose summary based on Logic App name and tags
    name_lower = logic_app_name.lower()

    if "delegate" in name_lower and "mailbox" in name_lower:
        purpose_summary = (
            "This Logic App automates mailbox delegation by converting mailboxes and assigning access "
            "via Azure Automation and Microsoft Graph."
        )
    elif "remotemailbox" in name_lower:
        purpose_summary = (
            "This Logic App manages remote mailbox provisioning, synchronizing attributes between hybrid environments."
        )
    elif "onboarding" in name_lower:
        purpose_summary = (
            "This Logic App handles employee onboarding workflows, including notification emails and provisioning tasks."
        )
    elif "manageremail" in name_lower or "sendtap" in name_lower:
        purpose_summary = (
            "This Logic App notifies managers of key user lifecycle events such as onboarding, terminations, or approvals."
        )
    elif "removegroups" in name_lower:
        purpose_summary = (
            "This Logic App automates group removal from Azure AD for lifecycle or security cleanup processes."
        )
    elif "createsharelink" in name_lower:
        purpose_summary = (
            "This Logic App provisions OneDrive shareable links for collaboration or external sharing requests."
        )
    elif "revokesession" in name_lower:
        purpose_summary = (
            "This Logic App revokes user sessions or tokens using Microsoft Graph API for security compliance."
        )
    elif tag_purpose and tag_purpose.lower() != "not defined":
        purpose_summary = (
            f"This Logic App supports automated workflows related to {tag_purpose.lower()}, "
            "integrating connectors such as Graph, Automation, and Office365."
        )
    else:
        purpose_summary = (
            f"This Logic App named '{logic_app_name}' integrates Azure services like {', '.join(services)} "
            "to support automated IT workflows."
        )


    security_summary = generate_security_summary_with_intro(logic_app, actions)
    error_handling_summary = generate_error_handling_summary_enhanced(actions)

    integration_endpoints = [
        "Azure Automation API: https://learn.microsoft.com/en-us/rest/api/automation/jobs",
        "Office 365 Connector: https://learn.microsoft.com/en-us/connectors/office365/",
        "Microsoft Graph API: https://learn.microsoft.com/en-us/graph/overview",
        "Logic Apps Security: https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-securing-a-logic-app"
    ]

    doc = generate_document(
        architecture, execution, flow_text, data_flow, hybrid_text, conditions,
        overview_summary=overview_summary,
        architecture_summary=architecture_summary,
        execution_summary=execution_summary,
        purpose_summary=purpose_summary,
        security_summary=security_summary,
        error_handling_summary=error_handling_summary,
        integration_endpoints=integration_endpoints,
        docx_template=docx_template
    )
    doc.save(output_path)
    print("📄 Document saved to:", output_path)


def collect_all_nested_actions(actions_dict):
    all_actions = {}
    def recurse(actions):
        for k, v in actions.items():
            all_actions[k] = v
            if isinstance(v, dict):
                for subkey in ["actions", "else", "case", "cases"]:
                    sub = v.get(subkey)
                    if isinstance(sub, dict):
                        inner = sub.get("actions", sub) if "actions" in sub else sub
                        if isinstance(inner, dict):
                            recurse(inner)
    recurse(actions_dict)
    return all_actions

def generate_security_summary_with_intro(arm_data, actions_dict):
    identity_block = arm_data.get("identity", {})
    identity_type_raw = identity_block.get("type", "").lower()
    user_assigned_names_arm = list(identity_block.get("userAssignedIdentities", {}).keys()) if isinstance(identity_block.get("userAssignedIdentities"), dict) else []

    nested_actions = collect_all_nested_actions(actions_dict)
    uses_graph = False
    uses_https = False
    found_mailbox = None
    user_assigned_from_actions = set()
    system_assigned_detected_from_action = False

    def scan(obj):
        nonlocal uses_graph, uses_https, found_mailbox, system_assigned_detected_from_action
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "authentication" and isinstance(v, dict):
                    id_val = v.get("identity", "")
                    if "userAssignedIdentities" in id_val:
                        user_assigned_from_actions.add(id_val.split("/")[-1])
                    elif v.get("type", "").lower() == "managedserviceidentity" and "identity" not in v:
                        system_assigned_detected_from_action = True
                if k == "uri" and isinstance(v, str):
                    if v.lower().startswith("https"):
                        uses_https = True
                    if "graph.microsoft.com" in v.lower():
                        uses_graph = True
                if k.lower() == "mailboxaddress" and isinstance(v, str):
                    found_mailbox = v
                if isinstance(v, (dict, list)):
                    scan(v)
        elif isinstance(obj, list):
            for item in obj:
                scan(item)

    scan(nested_actions)

    if user_assigned_names_arm or user_assigned_from_actions:
        intro = "This Logic App uses a user-assigned managed identity for authentication."
    elif identity_type_raw == "systemassigned" or system_assigned_detected_from_action:
        intro = "This Logic App uses a system-assigned managed identity to securely authenticate with Azure services and connectors."
    else:
        intro = "This Logic App secures its connectors using standard Azure mechanisms and encrypted API transport."

    lines = [intro, "", "The Logic App uses the following mechanisms to secure integration:"]
    if user_assigned_names_arm or user_assigned_from_actions:
        all_names = set(user_assigned_names_arm) | user_assigned_from_actions
        lines.append(f"• Uses User Assigned Managed Identity: {', '.join(all_names)}")
    elif identity_type_raw == "systemassigned" or system_assigned_detected_from_action:
        lines.append("• Uses a System Assigned Managed Identity for secure access.")
    if uses_graph:
        lines.append("• Calls Microsoft Graph API using managed identity.")
    if found_mailbox:
        lines.append(f"• Sends email from shared mailbox: {found_mailbox}.")
    if uses_https:
        lines.append("• All API connectors use HTTPS transport.")
    return "\n".join(lines)

def generate_error_handling_summary_enhanced(actions_dict):
    nested_actions = collect_all_nested_actions(actions_dict)
    has_condition = any("condition" in k.lower() for k in nested_actions)
    has_parse_json = any("parse_json" in k.lower() for k in nested_actions)
    has_compose = any("compose" in k.lower() for k in nested_actions)
    has_failure_email = any("send" in k.lower() and "email" in k.lower() for k in nested_actions)

    structured_automation_handling = False
    for action in nested_actions.values():
        if isinstance(action, dict):
            inputs = action.get("inputs", {})
            if isinstance(inputs, dict):
                body = inputs.get("body", {})
                if isinstance(body, dict):
                    body_json = json.dumps(body).lower()
                    if "status" in body_json or "errors" in body_json or "workflowrunid" in body_json:
                        structured_automation_handling = True

    if structured_automation_handling:
        intro = "This Logic App implements structured error-handling logic using job output parsing, condition-based evaluation, and automated notification."
    else:
        intro = "Error handling in this Logic App is managed by lifecycle alerts within Microsoft Entra ID."

    lines = [intro]
    if has_condition:
        lines.append("• Uses a Condition block to evaluate branching logic.")
    if has_parse_json:
        lines.append("• Parses output using Parse_JSON.")
    if has_compose:
        lines.append("• Composes error messages using Compose.")
    if has_failure_email:
        lines.append("• Sends failure notification email using Office 365.")
    return "\n".join(lines)
