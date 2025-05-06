
from docx import Document
from docx.shared import Inches
import graphviz
import os
import json
from logicapp_docgen import parser


def generate_document(architecture, execution, flow_text, data_flow, hybrid_text, conditions):
    arm = architecture.get("arm", {})
    logic_app_name = architecture.get("name", "LogicApp")
    region = architecture.get("location", "unknown")
    resource_group = architecture.get("resource_group", "n/a")
    subscription_id = architecture.get("subscription_id", "n/a")
    automation_account = architecture.get("automation_account", "n/a")
    tags = architecture.get("tags", {})

    doc = Document("template.docx")

    doc.add_heading("1 Azure Logic App Workflow – Mailbox Delegation", level=1)

    doc.add_heading("1.1 Overview", level=2)
    doc.add_paragraph(
        "This document provides an end-to-end overview of the Azure Logic App used for automated mailbox delegation. "
        "It explains the integration with lifecycle workflows, supporting systems, and failure handling mechanisms. "
        "This solution is designed to streamline mailbox access provisioning and reduce manual intervention."
    )

    doc.add_heading("1.2 Purpose and Function", level=2)
    doc.add_heading("1.2.1 Key Responsibilities:", level=3)
    for item in execution:
        doc.add_paragraph(item, style='Bullets')

    doc.add_heading("1.3 Architecture Overview", level=2)
    doc.add_heading("1.3.1 Deployment Metadata:", level=3)
    doc.add_paragraph(f"Logic App Name: {logic_app_name}", style='Bullets')
    doc.add_paragraph(f"Resource Group: {resource_group}", style='Bullets')
    doc.add_paragraph(f"Subscription ID: {subscription_id}", style='Bullets')
    doc.add_paragraph(f"Location: {region}", style='Bullets')
    doc.add_paragraph(f"Automation Account: {automation_account}", style='Bullets')
    for k, v in tags.items():
        doc.add_paragraph(f"Tag - {k}: {v}", style='Bullets')

    doc.add_heading("1.3.2 Architecture Summary:", level=3)
    doc.add_paragraph(
        "This Logic App is built on a modular and event-driven integration pattern. It connects several Azure and Microsoft services "
        "to handle a mailbox delegation scenario with minimal manual oversight."
    )
    for item in execution:
        doc.add_paragraph(item, style='Bullets')

    doc.add_heading("1.4 Execution Logic Summary", level=2)
    for item in execution:
        doc.add_paragraph(item, style='Bullets')

    doc.add_heading("1.5 Logic App Flow Diagram", level=2)
    try:
        flow_png = os.path.join("output", "LogicAppFlow.png")
        if os.path.exists(flow_png):
            doc.add_picture(flow_png, width=Inches(6.0))
            doc.paragraphs[-1].alignment = 1
            doc.add_paragraph("Figure 1: Azure Logic App Flow Diagram", style="Caption")
        else:
            doc.add_paragraph("❌ Could not render Logic App Flow Diagram.")
    except Exception as e:
        doc.add_paragraph("❌ Could not render Logic App Flow Diagram.")

    doc.add_heading("1.6 Data Flow Diagram", level=2)
    for item in data_flow:
        doc.add_paragraph(item, style='Bullets')

    doc.add_heading("1.7 Hybrid Integration Diagram", level=2)
    for item in hybrid_text:
        doc.add_paragraph(item, style='Bullets')

    doc.add_heading("1.8 Security and Authentication", level=2)
    doc.add_paragraph("The Logic App uses token-based identity and secure channels to connect with Microsoft services.")
    doc.add_paragraph("Includes system-assigned managed identity, secure OAuth tokens, and HTTPS for all APIs.")

    doc.add_heading("1.9 Error Handling", level=2)
    for item in conditions:
        doc.add_paragraph(item, style='Bullets')

    doc.add_heading("1.10 Appendix: Integration Endpoints", level=2)
    doc.add_paragraph("Azure Automation API: https://learn.microsoft.com/en-us/rest/api/automation/jobs", style='Bullets')
    doc.add_paragraph("Office 365 Connector: https://learn.microsoft.com/en-us/connectors/office365/", style='Bullets')
    doc.add_paragraph("Microsoft Graph API: https://learn.microsoft.com/en-us/graph/overview", style='Bullets')
    doc.add_paragraph("Logic Apps Security: https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-securing-a-logic-app", style='Bullets')

    return doc
