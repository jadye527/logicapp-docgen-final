
import os
import json
import subprocess
from docx import Document
from docx.shared import Inches
from graphviz import Digraph

from logicapp_docgen.utils import extract_services
from logicapp_docgen.diagram_builder import build_dot_with_arm_and_runbook
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
    output_dir = os.path.dirname(output_path) or "."
    os.makedirs(output_dir, exist_ok=True)

    # Load ARM template
    with open(template_path) as f:
        arm = json.load(f)

    # Load parameters (optional)
    parameters = {}
    if parameters_path:
        with open(parameters_path) as pf:
            parameters = json.load(pf)

    # Extract key details
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

    # Diagram generation
    runbook_path = os.path.join("runbooks", "DelegateMailbox.ps1")
    runbook_label = extract_runbook_label(runbook_path, "DelegateMailbox")

    print("⚙️  Generating Logic App Flow Diagram...")
    dot = build_dot_with_arm_and_runbook(actions, actions.get("Condition", {}), runbook_label)

    flow_dot_path = os.path.join(output_dir, "LogicAppFlow.dot")
    flow_png_path = os.path.join(output_dir, "LogicAppFlow.png")

    with open(flow_dot_path, "w") as f:
        f.write(dot)
    subprocess.run(["dot", "-Tpng", flow_dot_path, "-o", flow_png_path], check=True)
    print("✅ Flow diagram saved to:", flow_png_path)

    # Use existing generate_docx logic for document building
    wf = parser.extract_workflow_structure(arm)
    run_after = parser.extract_run_after_mapping(wf["action_details"])
    architecture = parser.extract_architecture_metadata(arm)
    execution = parser.extract_execution_flow_steps(wf["actions"], run_after)
    flow_text = parser.describe_flow_diagram_text(wf["action_details"], run_after)
    data_flow = parser.describe_data_flow_text(wf["action_details"])
    services = parser.extract_services(arm)
    hybrid_text = parser.describe_hybrid_integration_text(services)
    conditions = parser.extract_condition_branches(wf["action_details"])

    doc = generate_document(architecture, execution, flow_text, data_flow, hybrid_text, conditions)
    doc.save(output_path)
    print("📄 Document saved to:", output_path)

