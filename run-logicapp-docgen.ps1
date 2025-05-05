param(
    [string]$TemplatePath = "./template.json",
    [string]$OutputDirectory = "./output",
    [string]$DocxTemplate = "./template.docx"
)

if (-not (Test-Path $OutputDirectory)) {
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
}

Write-Host "📤 Generating Logic App documentation..."

python cli.py --template $TemplatePath --output "$OutputDirectory\LogicApp_Documentation.docx" --docx_template $DocxTemplate