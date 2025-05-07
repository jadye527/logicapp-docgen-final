
import sys
import os
import subprocess
import json
from logicapp_docgen.utils import extract_services
from logicapp_docgen.diagram_builder import build_dot_with_arm_and_runbook
from logicapp_docgen.runbook_utils import extract_runbook_label

# Ensure working directory
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Load ARM template
with open("template.json", "r") as f:
    arm = json.load(f)

definition = arm["resources"][0]["properties"]["definition"]
actions = definition["actions"]
condition = actions.get("Condition", None)
if condition is None:
    raise KeyError("The key 'Condition' is not defined in the actions dictionary.")

# Build DOT + render
runbook_path = os.path.join("runbooks", "DelegateMailbox.ps1")
runbook_label = extract_runbook_label(runbook_path, "DelegateMailbox")

print("⚙️  Starting build_dot_with_arm_and_runbook...")
dot = build_dot_with_arm_and_runbook(actions, condition, runbook_label)
print("✅ DOT built. Writing to file...")

flow_dot_path = os.path.join(output_dir, "LogicAppFlow.dot")
flow_png_path = os.path.join(output_dir, "LogicAppFlow.png")

with open(flow_dot_path, "w") as f:
    f.write(dot)
print("📄 Saved DOT to:", flow_dot_path)

subprocess.run(["dot", "-Tpng", flow_dot_path, "-o", flow_png_path], check=True)
print("🖼️  Rendered PNG to:", flow_png_path)
