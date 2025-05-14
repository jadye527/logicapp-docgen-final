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
```

📝 Output file will be named based on Logic App name (e.g., `output/SendOnboardingEmail.docx`)

---

## 🔧 Optional CLI Flags

| Flag             | Description                          | Required |
|------------------|--------------------------------------|----------|
| `--template`      | ARM template file                    | ✅        |
| `--parameters`    | Parameters file                      | ❌        |
| `--docx_template` | Word `.docx` file                    | ✅        |
| `--output`        | Override output `.docx` file name    | ❌        |

---

## 📸 Output Files

- **Diagrams:** saved as `.png` in the `output/` directory
- **Word Document:** default output to `output/{LogicAppName}.docx`

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Submit a pull request with a description of changes
4. Let’s improve Azure Logic App documentation together!

---

## 📄 License

MIT License
