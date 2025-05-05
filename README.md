# Logic App Documentation Generator

This tool parses Azure Logic App ARM templates and generates a fully formatted Word document (.docx), complete with diagrams, metadata, and execution flow.

## 🧰 Features

- Parses ARM template and parameter files
- Resolves Logic App names from parameters
- Generates diagrams (flow, data flow, hybrid integration)
- Outputs styled Word document based on a DOCX template
- Supports Docker and CLI usage
- Optionally stays alive after generation for inspection/debugging

## 🚀 Usage

### Run Locally

```bash
python cli.py --template template.json --parameters parameters.json --docx_template template.docx --output LogicApp_Documentation.docx
