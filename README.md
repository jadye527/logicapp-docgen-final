# Logic App Documentation Generator

This project generates professional, Word-based as-built documentation for Azure Logic Apps — including flow diagrams, hybrid architecture diagrams, metadata summaries, and optional PowerShell runbook step details.

---

## 🚀 Features

- 📦 Parses Azure Logic App ARM templates + parameters
- 🔍 Automatically detects services used (Logic App, Graph, O365, Automation, etc.)
- 🧭 Generates:
  - Logic App Flow Diagram (with PowerShell runbooks)
  - Hybrid Integration Diagram (service-to-service view)
- 📄 Outputs a styled `.docx` document using a Word template
- 🐳 Fully Dockerized for repeatable local or CI use
- ✅ Dynamic naming of output files based on Logic App name

---

## 🧰 Requirements

- Docker (for containerized execution)
- A Word `.docx` template file (for styling)

---

## 📂 Input Files

Place the following in your working directory:
- `template.json` — ARM template for the Logic App
- `parameters.json` — optional ARM parameters file
- `template.docx` — Word template with styles
- `runbooks/` — optional folder containing `.ps1` PowerShell runbooks (named to match)

---

## 🐳 Running via Docker

```bash
docker run -it ^
  -v "%cd%:/app" ^
  --rm ^
  logicapp-docgen ^
  python cli_updated.py ^
    --template "template.json" ^
    --parameters "parameters.json" ^
    --docx_template "template.docx"
