
from docx import Document

def generate_document(architecture, execution_steps, flow_diagram_text, data_flow_text, hybrid_text, condition_branches):
    doc = Document()
    doc.add_heading('AZURE LOGIC APP WORKFLOW – MAILBOX DELEGATION', 0)

    doc.add_heading('1.1 Overview', level=1)
    doc.add_paragraph(
        "This document provides an end-to-end overview of the Azure Logic App used for automated mailbox delegation. "
        "It explains the integration with lifecycle workflows, supporting systems, and failure handling mechanisms for "
        "email and callback processes. This solution is designed to streamline mailbox access provisioning and reduce manual intervention."
    )

    doc.add_heading('1.2 Purpose and Function', level=1)
    doc.add_heading('1.2.1 KEY RESPONSIBILITIES:', level=2)
    for step in execution_steps:
        doc.add_paragraph(step.replace("Step: ", "• "), style='List Bullet')

    doc.add_heading('1.3 Architecture Overview', level=1)
    doc.add_heading('1.3.1 DEPLOYMENT METADATA:', level=2)
    arch_keys = [
        ("Logic App Name", architecture["name"]),
        ("Resource Group", architecture["resource_group"]),
        ("Subscription ID", architecture["subscription_id"]),
        ("Location", architecture["location"]),
        ("Automation Account", architecture["automation_account"]),
        ("Tag - Purpose", architecture["tags"].get("Purpose", "N/A"))
    ]
    for label, value in arch_keys:
        doc.add_paragraph(f"• {label}: {value}", style='List Bullet')

    doc.add_heading('1.3.2 ARCHITECTURE SUMMARY:', level=2)
    summary_points = [
        "Triggered by a Lifecycle Workflow via HTTP.",
        "Parses metadata like subject and task details.",
        "Calls Azure Automation to run a mailbox delegation script.",
        "Parses job output to determine if the operation succeeded.",
        "Sends callback to lifecycle workflow based on job result.",
        "Failure path includes composing and sending an email notification."
    ]
    for point in summary_points:
        doc.add_paragraph(f"• {point}", style='List Bullet')

    doc.add_heading('1.4 Execution Logic Summary', level=1)
    for line in execution_steps:
        doc.add_paragraph(f"• {line}", style='List Bullet')

    doc.add_heading('1.5 Logic App Flow Diagram', level=1)
    for line in flow_diagram_text:
        doc.add_paragraph(line)

    doc.add_heading('1.6 Data Flow Diagram', level=1)
    for line in data_flow_text:
        doc.add_paragraph(line)

    doc.add_heading('1.7 Hybrid Integration Diagram', level=1)
    for line in hybrid_text:
        doc.add_paragraph(line)

    doc.add_heading('1.8 Security and Authentication', level=1)
    security_points = [
        "Uses a System Assigned Managed Identity for secure access.",
        "Authenticates with Azure Automation via OAuth 2.0 token.",
        "Calls Microsoft Graph API using secure token-based HTTP requests.",
        "Sends email from a shared Office 365 mailbox: svc_lifecycleworkflow@rehlko.com.",
        "API connections use HTTPS and are secured with managed identities."
    ]
    for point in security_points:
        doc.add_paragraph(f"• {point}", style='List Bullet')

    doc.add_heading('1.9 Error Handling', level=1)
    if condition_branches:
        for name, branch in condition_branches.items():
            doc.add_paragraph(f"If condition: {branch['expression']}")
            doc.add_paragraph("If TRUE (Failure Path):", style='List Bullet')
            for act in branch["if_true"]:
                doc.add_paragraph(f"• {act}", style='List Bullet 2')
            doc.add_paragraph("If FALSE (Success Path):", style='List Bullet')
            for act in branch["if_false"]:
                doc.add_paragraph(f"• {act}", style='List Bullet 2')

    doc.add_heading('1.10 Appendix: Integration Endpoints', level=1)
    endpoints = [
        "Azure Automation API: https://learn.microsoft.com/en-us/rest/api/automation/jobs",
        "Office 365 Connector: https://learn.microsoft.com/en-us/connectors/office365/",
        "Microsoft Graph API: https://learn.microsoft.com/en-us/graph/overview",
        "Logic Apps Security: https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-securing-a-logic-app"
    ]
    for ep in endpoints:
        doc.add_paragraph(f"• {ep}", style='List Bullet')

    return doc
