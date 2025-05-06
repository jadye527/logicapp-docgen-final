param(
    [string]$projectPath = ".",
    [string]$containerName = "logicapp-docgen-local"
)

Write-Host "📦 Building Docker image..."
docker build -t logicapp-docgen $projectPath

Write-Host "`n🧹 Stopping previous container (if running)..."
docker rm -f $containerName 2>$null

Write-Host "`n🚀 Running Docker container with interactive shell and logs..."

<# docker run -it `
    -v ${projectPath}:/app `
    --name $containerName `
    logicapp-docgen

Write-Host "`n✅ Container exited. Use logs above to debug if needed." #>

    docker run -it `
    -v ${projectPath}:/app `
    --name $containerName `
    logicapp-docgen `
    python cli_updated.py `
        --template template.json `
        --parameters parameters.json `
        --docx_template template.docx `
        --output output/logicapp_test.docx

Write-Host "`n✅ Container exited. Use logs above to debug if needed."
<# docker run -it `
  -v "${projectPath}:/app" `
  --name $containerName `
  logicapp-docgen `
  python cli_updated.py `
    --template "450-SendOnboardingEmailtoNewEmployee-template.json" `
    --parameters "450-SendOnboardingEmailtoNewEmployee-parameters.json" `
    --docx_template "template.docx" `
    --output "output/logicapp_test.docx"
Write-Host "`n✅ Container exited. Use logs above to debug if needed." #>