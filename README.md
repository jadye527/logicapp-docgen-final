# Logic App DocGen

This tool parses an Azure Logic App ARM template and generates a Word document (.docx) with embedded diagrams.

## Requirements (Locally)
- Python 3.10+
- `pip install -r requirements.txt`
- Graphviz (`apt install graphviz`)

## Usage

```bash
python cli.py --template template.json --output LogicApp_Documentation.docx --docx_template template.docx
```

## Usage with Docker

```bash
./run-docker.ps1
```

## Output
- Word doc: `LogicApp_Documentation.docx`
- Includes Flow, Data Flow, and Hybrid Integration diagrams