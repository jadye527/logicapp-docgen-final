
import argparse
import os
import json
from logicapp_docgen.core import generate_document_from_arm, resolve_logic_app_name

def main():
    parser = argparse.ArgumentParser(description="Logic App Documentation Generator")

    parser.add_argument("--template", required=True, help="Path to ARM template file (e.g., template.json)")
    parser.add_argument("--parameters", required=False, help="Path to parameters file (optional)")
    parser.add_argument("--docx_template", required=False, help="Path to a Word .docx template (optional)")
    parser.add_argument("--output", required=False, help="Output Word document path")

    args = parser.parse_args()

    print(f"📄 Generating documentation from ARM template: {args.template}")

    # Dynamically resolve logic app name if output not explicitly provided
    if args.output:
        output_path = args.output
    else:
        with open(args.template) as f:
            arm = json.load(f)

        parameters = {}
        if args.parameters:
            with open(args.parameters) as pf:
                parameters = json.load(pf)

        logic_app_res = [r for r in arm.get("resources", []) if "/workflows" in r.get("type", "")]
        name_raw = logic_app_res[0].get("name", "LogicApp")
        logic_app_name = resolve_logic_app_name(name_raw, arm, parameters)
        logic_app_name = logic_app_name.replace(" ", "_")

        output_path = f"output/{logic_app_name}.docx"

    generate_document_from_arm(
        template_path=args.template,
        output_path=output_path,
        parameters_path=args.parameters,
        docx_template=args.docx_template
    )

    print(f"✅ Document created at: {output_path}")

if __name__ == "__main__":
    main()
