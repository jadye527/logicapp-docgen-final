param(
    [string]$projectPath = ".",
    [string]$containerName = "logicapp-docgen-local"
)

Write-Host "📦 Building Docker image..."
docker build -t logicapp-docgen $projectPath

Write-Host "`n🧹 Stopping previous container (if running)..."
docker rm -f $containerName 2>$null

Write-Host "`n🚀 Running Docker container with interactive shell and logs..."

docker run -it `
    -v ${projectPath}:/app `
    --name $containerName `
    logicapp-docgen

Write-Host "`n✅ Container exited. Use logs above to debug if needed."
