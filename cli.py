import argparse
from logicapp_docgen import generate_document

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Logic App Documentation")
    parser.add_argument("--template", required=True, help="Path to template.json (ARM file)")
    parser.add_argument("--output", default="LogicApp_Documentation.docx", help="Output DOCX path")
    parser.add_argument("--docx_template", default="template.docx", help="Template DOCX file")
    args = parser.parse_args()

    generate_document(args.template, args.output, args.docx_template)
