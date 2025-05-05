param(
    [string]$projectPath = "."
)

Write-Host "📦 Building Docker image..."
docker build -t logicapp-docgen $projectPath

Write-Host "🧹 Stopping previous container if running..."
docker rm -f logicapp-docgen-local 2>$null

Write-Host "🚀 Running Docker container..."
docker run -it -v ${projectPath}:/app --name logicapp-docgen-local logicapp-docgen