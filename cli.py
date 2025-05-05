# cli.py
import argparse
import time
from logicapp_docgen import generate_document

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Logic App Documentation")
    parser.add_argument("--template", required=True, help="Path to template.json (ARM file)")
    parser.add_argument("--output", default="LogicApp_Documentation.docx", help="Output DOCX path")
    parser.add_argument("--docx_template", default="template.docx", help="Template DOCX file")
    parser.add_argument("--parameters", default="parameters.json", help="Parameters JSON file")

    args = parser.parse_args()

    print("📄 Starting Logic App documentation generation...")
    print(f"🗂 Template: {args.template}")
    print(f"📤 Output: {args.output}")
    print(f"📑 DOCX Template: {args.docx_template}")
    print(f"🛠 Parameters: {args.parameters}\n")

    generate_document(
        template_path=args.template,
        output_path=args.output,
        docx_template=args.docx_template,
        parameters_path=args.parameters
    )

    print("✅ Generation complete. Container will stay alive for inspection.")
    while True:
        time.sleep(60)
