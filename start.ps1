# ========================================
# Script de lancement ECLA AI Search
# ========================================

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  ECLA AI SEARCH - Demarrage" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Verifier que Docker est installe et lance
Write-Host "[1/6] Verification de Docker..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "  OK Docker est installe" -ForegroundColor Green
} catch {
    Write-Host "  ERREUR Docker n'est pas installe ou non demarre" -ForegroundColor Red
    Write-Host "  Installez Docker Desktop depuis https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

# Verifier que docker-compose est disponible
Write-Host "[2/6] Verification de Docker Compose..." -ForegroundColor Yellow
try {
    docker compose version | Out-Null
    Write-Host "  OK Docker Compose est disponible" -ForegroundColor Green
} catch {
    Write-Host "  ERREUR Docker Compose n'est pas disponible" -ForegroundColor Red
    exit 1
}

# Verifier la presence du fichier .env pour l'API OpenAI
Write-Host "[3/6] Verification des variables d'environnement..." -ForegroundColor Yellow
if (Test-Path "backend\.env") {
    Write-Host "  OK Fichier backend\.env trouve" -ForegroundColor Green
} else {
    Write-Host "  ATTENTION Fichier backend\.env manquant" -ForegroundColor Yellow
    Write-Host "  Creation d'un fichier .env template..." -ForegroundColor Yellow
    
    $envContent = @"
# Configuration OpenAI
OPENAI_API_KEY=your-openai-api-key-here

# Configuration Qdrant (laisser par defaut pour Docker)
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Configuration Python
PYTHONUNBUFFERED=1
"@
    
    $envContent | Out-File -FilePath "backend\.env" -Encoding utf8
    Write-Host "  Fichier backend\.env cree. Configurez votre OPENAI_API_KEY !" -ForegroundColor Yellow
}

# Charger les variables d'environnement
if (Test-Path "backend\.env") {
    Get-Content "backend\.env" | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+?)\s*=\s*(.+?)\s*$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# Nettoyage prealable pour eviter les conflits de ports
Write-Host "[4/7] Nettoyage prealable (ports et processus)..." -ForegroundColor Yellow

# Arreter tous les processus Python en cours
try {
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  OK Processus Python arretes" -ForegroundColor Green
} catch {
    Write-Host "  OK Aucun processus Python a arreter" -ForegroundColor Green
}

# Arreter et supprimer l'ancien conteneur Qdrant standalone s'il existe
try {
    docker stop qdrant-chunks 2>&1 | Out-Null
    docker rm qdrant-chunks 2>&1 | Out-Null
    Write-Host "  OK Ancien conteneur Qdrant supprime" -ForegroundColor Green
} catch {
    Write-Host "  OK Aucun ancien conteneur Qdrant" -ForegroundColor Green
}

# Arreter les conteneurs Docker Compose existants
Write-Host "[5/7] Arret des conteneurs Docker Compose..." -ForegroundColor Yellow
docker compose down 2>&1 | Out-Null
Write-Host "  OK Conteneurs arretes" -ForegroundColor Green

# Lancer Docker Compose
Write-Host "[6/7] Lancement de Docker Compose..." -ForegroundColor Yellow
Write-Host "  Demarrage de Qdrant (base vectorielle)..." -ForegroundColor Cyan
Write-Host "  Demarrage du Backend (FastAPI)..." -ForegroundColor Cyan
Write-Host "  Demarrage du Frontend (React)..." -ForegroundColor Cyan
Write-Host ""

docker compose up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK Tous les services sont demarres !" -ForegroundColor Green
} else {
    Write-Host "  ERREUR lors du demarrage" -ForegroundColor Red
    exit 1
}

# Attendre que les services soient prets
Write-Host "[7/7] Verification de l'etat des services..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verifier Qdrant
$qdrantStatus = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:6333/health" -UseBasicParsing -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
        $qdrantStatus = $true
    }
} catch {}

if ($qdrantStatus) {
    Write-Host "  OK Qdrant : http://localhost:6333" -ForegroundColor Green
} else {
    Write-Host "  EN COURS Qdrant : En cours de demarrage..." -ForegroundColor Yellow
}

# Verifier Backend
$backendStatus = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
        $backendStatus = $true
    }
} catch {}

if ($backendStatus) {
    Write-Host "  OK Backend API : http://localhost:8000" -ForegroundColor Green
} else {
    Write-Host "  EN COURS Backend : En cours de demarrage..." -ForegroundColor Yellow
}

# Verifier Admin API
$adminStatus = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/" -UseBasicParsing -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
        $adminStatus = $true
    }
} catch {}

if ($adminStatus) {
    Write-Host "  OK Admin API : http://localhost:8001" -ForegroundColor Green
} else {
    Write-Host "  EN COURS Admin API : En cours de demarrage..." -ForegroundColor Yellow
}

# Verifier Frontend
Write-Host "  OK Frontend : http://localhost:5173" -ForegroundColor Green

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "  ECLA AI Search est pret !" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Application : http://localhost:5173" -ForegroundColor White -BackgroundColor Blue
Write-Host "Administration : http://localhost:5173 (bouton en haut a droite)" -ForegroundColor White -BackgroundColor Magenta
Write-Host ""
Write-Host "Tableau de bord Qdrant : http://localhost:6333/dashboard" -ForegroundColor White
Write-Host "API Backend (Swagger) : http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Commandes utiles :" -ForegroundColor Yellow
Write-Host "   - Voir les logs : docker compose logs -f" -ForegroundColor Gray
Write-Host "   - Arreter : docker compose down" -ForegroundColor Gray
Write-Host "   - Redemarrer : docker compose restart" -ForegroundColor Gray
Write-Host ""
Write-Host "Appuyez sur Ctrl+C pour arreter..." -ForegroundColor Gray

# Suivre les logs
docker compose logs -f
