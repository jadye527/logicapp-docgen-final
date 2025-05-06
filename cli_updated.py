
import argparse
import os
from logicapp_docgen.core import generate_document_from_arm

def main():
    parser = argparse.ArgumentParser(description="Logic App Documentation Generator")

    parser.add_argument("--template", required=True, help="Path to ARM template file (e.g., template.json)")
    parser.add_argument("--parameters", required=False, help="Path to parameters file (optional)")
    parser.add_argument("--docx_template", required=False, help="Path to a Word .docx template (optional, not used yet)")
    parser.add_argument("--output", default="output/logicapp_document.docx", help="Output Word document path")

    args = parser.parse_args()

    print(f"📄 Generating documentation from ARM template: {args.template}")
    output_path = generate_document_from_arm(args.template, args.output)
    print(f"✅ Document created at: {output_path}")

if __name__ == "__main__":
    main()
