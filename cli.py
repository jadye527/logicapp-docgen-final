# cli.py
import argparse
import time
import os
import json
import re
from logicapp_docgen.core import generate_document, resolve_logic_app_name

def extract_logic_app_name(template_path, parameters_path):
    try:
        with open(template_path, "r") as tf:
            arm = json.load(tf)
        with open(parameters_path, "r") as pf:
            parameters = json.load(pf)

        logic_apps = [r for r in arm["resources"] if "/workflows" in r["type"]]
        if not logic_apps:
            print("⚠️ No Logic Apps found in template.")
            return "LogicApp_Documentation"

        name_raw = logic_apps[0].get("name", "LogicApp")
        print(f"🔎 Raw name field: {name_raw}")
        resolved_name = resolve_logic_app_name(name_raw, arm, parameters)
        print(f"✅ Resolved Logic App name: {resolved_name}")
        return resolved_name.replace(" ", "_")

    except Exception as e:
        print(f"⚠️ Failed to extract Logic App name, using default. Reason: {e}")
        return "LogicApp_Documentation"

        name_raw = logic_apps[0].get("name", "LogicApp")
        return resolve_logic_app_name(name_raw, arm, parameters).replace(" ", "_")
    except Exception as e:
        print(f"⚠️ Failed to extract Logic App name, using default. Reason: {e}")
        return "LogicApp_Documentation"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Logic App Documentation")
    parser.add_argument("--template", required=True, help="Path to template.json (ARM file)")
    parser.add_argument("--output", help="Output DOCX path")
    parser.add_argument("--docx_template", default="template.docx", help="Template DOCX file")

    default_params = "parameters.json" if os.path.exists("parameters.json") else None
    parser.add_argument("--parameters", default=default_params, help="Parameters JSON file (optional)")

    args = parser.parse_args()

    if args.output:
        output_filename = args.output
    elif args.parameters:
        output_filename = f"{extract_logic_app_name(args.template, args.parameters)}.docx"
    else:
        output_filename = "LogicApp_Documentation.docx"

    print("📄 Starting Logic App documentation generation...")
    print(f"🗂 Template: {args.template}")
    print(f"📤 Output: {output_filename}")
    print(f"📑 DOCX Template: {args.docx_template}")
    print(f"🛠 Parameters: {args.parameters}\n")

    generate_document(
        template_path=args.template,
        output_path=output_filename,
        docx_template=args.docx_template,
        parameters_path=args.parameters
    )

    print("✅ Generation complete. Container will stay alive for inspection.")
    while True:
        time.sleep(60)
