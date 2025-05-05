# logicapp_docgen/core.py
import os
import json
import re
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

def resolve_logic_app_name(name_value, arm, parameters):
    if not isinstance(name_value, str) or not name_value.startswith("[parameters("):
        return name_value
    match = re.match(r"\[parameters\('([^']+)'\)\]", name_value)
    if match:
        param_key = match.group(1)
        resolved = parameters.get("parameters", {}).get(param_key, {}).get("value")
        if resolved:
            return resolved
        param_def = arm.get("parameters", {}).get(param_key, {})
        default_val = param_def.get("defaultValue")
        if default_val:
            return default_val
        fallback_name = param_key.replace("workflows_", "").replace("_name", "")
        return fallback_name
    return name_value

def generate_document(template_path, output_path, docx_template="template.docx", parameters_path="parameters.json"):
    try:
        with open(template_path, "r") as f:
            arm = json.load(f)
        parameters = {}
        if os.path.exists(parameters_path):
            with open(parameters_path, "r") as pf:
                parameters = json.load(pf)

        logic_apps = [r for r in arm["resources"] if "/workflows" in r["type"]]
        logic_app = logic_apps[0] if logic_apps else {}
        name_raw = logic_app.get("name", "Unknown Logic App")
        name = resolve_logic_app_name(name_raw, arm, parameters)
        location = logic_app.get("location", "Unknown Location")
        tags = logic_app.get("tags", {})

        doc = Document(docx_template)

        def add_heading(doc, title, level=1):
            doc.add_heading(title, level=level)

        def add_paragraph(doc, text):
            p = doc.add_paragraph(text)
            p.style.font.size = Pt(11)

        def add_bullet(doc, text):
            p = doc.add_paragraph(style='Bullets')
            run = p.add_run(text)
            run.font.size = Pt(11)

        def add_diagram(doc, title, image_path, caption):
            add_heading(doc, title, level=2)
            if os.path.exists(image_path):
                doc.add_picture(image_path, width=Inches(6))
                doc.add_paragraph(caption).alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            else:
                add_paragraph(doc, f"[Missing Diagram: {image_path}]")

        add_heading(doc, "Overview")
        add_paragraph(doc, "This document summarizes the Logic App design, flow, and external integrations based on the provided ARM template.")

        add_heading(doc, "Purpose")
        add_paragraph(doc, "The purpose of this Logic App is to support automated workflows for mailbox delegation and lifecycle events. Key functional steps include:")
        for item in [
            "Trigger workflow via HTTP from Lifecycle.",
            "Execute Azure Automation runbook.",
            "Evaluate job status and parse results.",
            "Notify via Office 365 email on failure.",
            "Post callback to lifecycle endpoint."
        ]: add_bullet(doc, item)

        add_heading(doc, "Architecture")
        add_paragraph(doc, "The Logic App architecture includes connections to multiple Azure services and Microsoft 365 components. Relevant configuration and metadata include:")
        for item in [
            f"Logic App: {name}",
            f"Region: {location}"
        ] + [f"Tag - {k}: {v}" for k, v in tags.items()]:
            add_bullet(doc, item)

        add_heading(doc, "Execution")
        add_paragraph(doc, "The following outlines the step-by-step execution path from the initiation to conclusion of the workflow:")
        for item in [
            "Start: Trigger from external HTTP request.",
            "Call: Azure Automation to delegate mailbox.",
            "Parse: Check JSON results for success/failure.",
            "Notify: On failure, send email.",
            "Callback: Send status to lifecycle API."
        ]: add_bullet(doc, item)

        add_heading(doc, "Security")
        add_paragraph(doc, "Security practices applied within the Logic App include identity management, encrypted connections, and restricted API access:")
        for item in [
            "Secure connections via HTTPS.",
            "Managed Identity for Automation access.",
            "OAuth tokens for Microsoft Graph API."
        ]: add_bullet(doc, item)

        add_heading(doc, "Error Handling")
        add_paragraph(doc, "In the event of failed automation runs or parsing errors, the Logic App takes the following steps to gracefully manage failures:")
        for item in [
            "Branching logic to detect runbook failures.",
            "Compose HTML email with failure summary.",
            "Send failure alert via Office 365 connector.",
            "Trigger failure callback endpoint."
        ]: add_bullet(doc, item)

        add_heading(doc, "Logic App Flow Diagram")
        add_diagram(doc, "", "flow_diagram_preview.png", "Figure 1: Workflow Execution Flow")

        add_heading(doc, "Data Flow Diagram")
        add_diagram(doc, "", "data_flow_diagram_preview.png", "Figure 2: Data Flow Integration")

        add_heading(doc, "Hybrid Integration Diagram")
        add_diagram(doc, "", "hybrid_integration_diagram_preview.png", "Figure 3: Cloud & M365 Integration Map")

        add_heading(doc, "Appendix")
        add_paragraph(doc, "Helpful documentation and reference links related to Azure Logic Apps and integrated services:")
        for item in [
            "https://learn.microsoft.com/en-us/azure/logic-apps/",
            "https://learn.microsoft.com/en-us/graph/",
            "https://learn.microsoft.com/en-us/connectors/office365/"
        ]: add_bullet(doc, item)

        doc.save(output_path)
        print(f"✅ Document saved to {output_path}")

    except Exception as e:
        print(f"❌ Error generating document: {e}")
