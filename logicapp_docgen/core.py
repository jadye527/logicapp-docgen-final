
import json
from docx import Document
from docx.shared import Inches
from graphviz import Digraph

def resolve_logic_app_name(name_expr, arm, parameters):
    if name_expr.startswith("[parameters("):
        param_key = name_expr.split("'")[1]
        param_obj = parameters.get(param_key) or arm.get("parameters", {}).get(param_key)
        return param_obj.get("value") or param_obj.get("defaultValue") or param_key
    return name_expr

def extract_services(arm):
    services = set()
    for res in arm.get("resources", []):
        if res.get("type", "").startswith("Microsoft.Web/connections"):
            conn_type = res.get("properties", {}).get("parameterValues", {}).get("connectionName", "")
            if conn_type:
                services.add(conn_type.split("-")[0].capitalize())
    return sorted(services)

def generate_bullets_from_actions(actions):
    bullets = []
    for name, action in actions.items():
        kind = action.get("type", "")
        bullets.append(f"{name}: {kind}")
    return bullets

def generate_flow_diagram(actions, output_file="flow_diagram_preview"):
    dot = Digraph("LogicAppFlow", format="png")
    dot.attr(compound="true", fontname="Segoe UI", fontsize="11", rankdir="TB")
    dot.attr("node", fontname="Segoe UI", fontsize="10", shape="box", style="filled")

    with dot.subgraph(name="cluster_lifecycle") as c:
        c.attr(label="Lifecycle Workflow", color="#3399ff", fontcolor="black", style="dashed")
        c.node("Start", "Lifecycle Workflow\nInitiates Logic App", fillcolor="#e6f2ff")
        c.node("FailureCallback", "HTTP POST\nFailure Callback", fillcolor="#ffcccc")
        c.node("SuccessCallback", "HTTP POST\nSuccess Callback", fillcolor="#ccffcc")

    with dot.subgraph(name="cluster_logicapp") as c:
        c.attr(label="Azure Logic App", color="#666666", fontcolor="black", style="dashed")
        c.node("HTTPTrigger", "Manual Trigger\nHTTP Request", fillcolor="#d0e0f0")
        c.node("ParseJSON", "Parse JSON Result", fillcolor="#ffedcc")
        c.node("Condition", "Delegation Successful?", shape="diamond", fillcolor="#ffeeee")

    with dot.subgraph(name="cluster_automation") as c:
        c.attr(label="Azure Automation (via Logic App)", color="#00cc44", fontcolor="black", style="dashed")
        c.node("CreateJob", "Create Job\nAzure Automation", fillcolor="#b3e6b3")
        c.node("Runbook", "DelegateMailbox Runbook\nCheck mailbox\nDelegate to manager\nConvert to shared", fillcolor="#e6ccff")
        c.node("GetStatus", "Get Job Status\nHTTP GET", fillcolor="#b3e6b3")

    with dot.subgraph(name="cluster_o365") as c:
        c.attr(label="Error Handling & O365 Email", color="#cc0000", fontcolor="black", style="dashed")
        c.node("ComposeEmail", "Compose_1\nHTML Email Body", fillcolor="#fff2cc")
        c.node("SendEmail", "Send Email\nOffice 365 Shared Mailbox", fillcolor="#ffd699")

    dot.edge("Start", "HTTPTrigger")
    dot.edge("HTTPTrigger", "CreateJob")
    dot.edge("CreateJob", "Runbook")
    dot.edge("Runbook", "GetStatus")
    dot.edge("GetStatus", "ParseJSON")
    dot.edge("ParseJSON", "Condition")
    dot.edge("Condition", "ComposeEmail", label="Failure")
    dot.edge("ComposeEmail", "SendEmail")
    dot.edge("SendEmail", "FailureCallback")
    dot.edge("Condition", "SuccessCallback", label="Success")

    dot.render(filename=output_file, cleanup=True)

def generate_document(template_path, output_path, docx_template, parameters_path=None):
    with open(template_path) as f:
        arm = json.load(f)
    if parameters_path:
        with open(parameters_path) as pf:
            parameters = json.load(pf)
    else:
        parameters = {}

    doc = Document(docx_template)

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

    generate_flow_diagram(actions)

    # OVERVIEW
    doc.add_heading("1. Overview", level=1)
    doc.add_paragraph("This document provides an overview of the Azure Logic App including purpose, architecture, and execution flow.")
    doc.add_paragraph(f"Logic App: {logic_app_name}")
    doc.add_paragraph(f"Region: {region}")
    doc.add_paragraph(f"Tag - Purpose: {tag_purpose}")

    # PURPOSE
    doc.add_heading("2. Purpose", level=1)
    doc.add_paragraph("This Logic App automates the following key tasks:")
    for bullet in generate_bullets_from_actions(actions):
        doc.add_paragraph(bullet, style="Bullets")

    # ARCHITECTURE
    doc.add_heading("3. Architecture", level=1)
    doc.add_paragraph("This Logic App integrates with the following external services and components:")
    for svc in extract_services(arm):
        doc.add_paragraph(svc, style="Bullets")

    # EXECUTION
    doc.add_heading("4. Execution", level=1)
    doc.add_paragraph("The Logic App follows this sequence of actions:")
    for bullet in generate_bullets_from_actions(actions):
        doc.add_paragraph(bullet, style="Bullets")

    # SECURITY
    doc.add_heading("5. Security", level=1)
    doc.add_paragraph("This Logic App may include HTTP actions or identity-based connectors:")
    for key in ["authentication", "authorization"]:
        if key in definition:
            doc.add_paragraph(f"Includes: {key}", style="Bullets")

    # ERROR HANDLING
    doc.add_heading("6. Error Handling", level=1)
    doc.add_paragraph("Failure branches and conditions are defined as follows:")
    for name, action in actions.items():
        if "runAfter" in action and any("Failure" in v for v in action["runAfter"].values()):
            doc.add_paragraph(f"{name} handles failure from another action", style="Bullets")

    # APPENDIX
    doc.add_heading("7. Appendix", level=1)
    doc.add_paragraph("See Logic App designer for full visual configuration.")
    doc.add_paragraph("Generated automatically by Logic App Documentation Generator.")

    try:
        doc.add_heading("Flow Diagram", level=2)
        doc.add_picture("flow_diagram_preview.png", width=Inches(6.0))
    except Exception:
        doc.add_paragraph("Flow diagram not available.")

    doc.save(output_path)
