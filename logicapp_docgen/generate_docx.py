from docx import Document
from docx.shared import Inches
import os

def generate_document(
    architecture, execution, flow_text, data_flow, hybrid_text, conditions,
    overview_summary=None,
    architecture_summary=None,
    execution_summary=None,
    purpose_summary=None,
    security_summary=None,
    error_handling_summary=None,
    integration_endpoints=None,
    docx_template=None
):
    doc = Document(docx_template)

    logic_app_name = architecture.get("name", "LogicApp")
    region = architecture.get("location", "unknown")
    resource_group = architecture.get("resource_group", "n/a")
    subscription_id = architecture.get("subscription_id", "n/a")
    automation_account = architecture.get("automation_account", "n/a")
    tags = architecture.get("tags", {})

    doc.add_heading(f"1 Azure Logic App Workflow – {logic_app_name}", level=1)

    doc.add_heading("1.1 Overview", level=2)
    if overview_summary:
        doc.add_paragraph(overview_summary)

    doc.add_heading("1.2 Purpose and Function", level=2)
    if purpose_summary:
        doc.add_paragraph(purpose_summary)
    doc.add_heading("1.2.1 Key Responsibilities:", level=3)
    for item in execution:
        doc.add_paragraph(item, style='Bullets')

    doc.add_heading("1.3 Architecture", level=2)
    doc.add_heading("1.3.1 Overview:", level=3)
    if architecture_summary:
        doc.add_paragraph(architecture_summary)

    doc.add_heading("1.3.2 Deployment Metadata:", level=3)
    doc.add_paragraph(f"Logic App Name: {logic_app_name}", style='Bullets')
    doc.add_paragraph(f"Resource Group: {resource_group}", style='Bullets')
    doc.add_paragraph(f"Subscription ID: {subscription_id}", style='Bullets')
    doc.add_paragraph(f"Location: {region}", style='Bullets')
    doc.add_paragraph(f"Automation Account: {automation_account}", style='Bullets')
    for k, v in tags.items():
        doc.add_paragraph(f"Tag - {k}: {v}", style='Bullets')

    doc.add_heading("1.4 Execution Logic Summary", level=2)
    if execution_summary:
        doc.add_paragraph(execution_summary)

    doc.add_heading("1.5 Logic App Flow Diagram", level=2)
    flow_png = os.path.join("output", "LogicAppFlow.png")
    if os.path.exists(flow_png):
        doc.add_picture(flow_png, width=Inches(6.0))
        doc.paragraphs[-1].alignment = 1
        doc.add_paragraph("Figure 1: Azure Logic App Flow Diagram", style="Caption")
    else:
        doc.add_paragraph("❌ Could not render Logic App Flow Diagram.")

    doc.add_heading("1.6 Data Flow Diagram", level=2)
    for item in data_flow:
        doc.add_paragraph(item, style='Bullets')

    doc.add_heading("1.7 Hybrid Integration Diagram", level=2)
    hybrid_png = os.path.join("output", "HybridIntegration.png")
    if os.path.exists(hybrid_png):
        doc.add_picture(hybrid_png, width=Inches(6.0))
        doc.paragraphs[-1].alignment = 1
        doc.add_paragraph("Figure: Hybrid Integration Diagram", style="Caption")
    else:
        doc.add_paragraph("❌ Could not render Hybrid Integration Diagram.")
    for item in hybrid_text:
        doc.add_paragraph(item, style='Bullets')

    doc.add_heading("1.8 Security and Authentication", level=2)
    if security_summary:
        doc.add_paragraph(security_summary)

    doc.add_heading("1.9 Error Handling", level=2)
    if error_handling_summary:
        doc.add_paragraph(error_handling_summary)

    doc.add_heading("1.10 Appendix: Integration Endpoints", level=2)
    if integration_endpoints:
        for item in integration_endpoints:
            doc.add_paragraph(item, style='Bullets')

    return doc