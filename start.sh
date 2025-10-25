#!/bin/bash

# ========================================
# 🚀 Script de lancement ECLA AI Search
# ========================================

echo "================================"
echo "  ECLA AI SEARCH - Démarrage"
echo "================================"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Vérifier que Docker est installé
echo -e "${YELLOW}[1/6] Vérification de Docker...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}  ✅ Docker est installé${NC}"
else
    echo -e "${RED}  ❌ Docker n'est pas installé${NC}"
    echo -e "${RED}  Installez Docker depuis https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

# Vérifier que docker compose est disponible
echo -e "${YELLOW}[2/6] Vérification de Docker Compose...${NC}"
if docker compose version &> /dev/null; then
    echo -e "${GREEN}  ✅ Docker Compose est disponible${NC}"
else
    echo -e "${RED}  ❌ Docker Compose n'est pas disponible${NC}"
    exit 1
fi

# Vérifier la présence du fichier .env
echo -e "${YELLOW}[3/6] Vérification des variables d'environnement...${NC}"
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}  ✅ Fichier backend/.env trouvé${NC}"
else
    echo -e "${YELLOW}  ⚠️  Fichier backend/.env manquant${NC}"
    echo -e "${YELLOW}  Création d'un fichier .env template...${NC}"
    
    cat > backend/.env << 'EOF'
# Configuration OpenAI
OPENAI_API_KEY=your-openai-api-key-here

# Configuration Qdrant (laisser par défaut pour Docker)
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Configuration Python
PYTHONUNBUFFERED=1
EOF
    
    echo -e "${YELLOW}  📝 Fichier backend/.env créé. Configurez votre OPENAI_API_KEY !${NC}"
fi

# Charger les variables d'environnement
if [ -f "backend/.env" ]; then
    export $(cat backend/.env | grep -v '^#' | xargs)
fi

# Arrêter les conteneurs existants
echo -e "${YELLOW}[4/6] Nettoyage des conteneurs existants...${NC}"
docker compose down &> /dev/null
echo -e "${GREEN}  ✅ Conteneurs arrêtés${NC}"

# Lancer Docker Compose
echo -e "${YELLOW}[5/6] Lancement de Docker Compose...${NC}"
echo -e "${CYAN}  🐳 Démarrage de Qdrant (base vectorielle)...${NC}"
echo -e "${CYAN}  🐍 Démarrage du Backend (FastAPI)...${NC}"
echo -e "${CYAN}  ⚛️  Démarrage du Frontend (React)...${NC}"
echo ""

docker compose up -d --build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✅ Tous les services sont démarrés !${NC}"
else
    echo -e "${RED}  ❌ Erreur lors du démarrage${NC}"
    exit 1
fi

# Attendre que les services soient prêts
echo -e "${YELLOW}[6/6] Vérification de l'état des services...${NC}"
sleep 5

# Vérifier Qdrant
if curl -sf http://localhost:6333/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Qdrant : http://localhost:6333${NC}"
else
    echo -e "${YELLOW}  ⏳ Qdrant : En cours de démarrage...${NC}"
fi

# Vérifier Backend
if curl -sf http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Backend API : http://localhost:8000${NC}"
else
    echo -e "${YELLOW}  ⏳ Backend : En cours de démarrage...${NC}"
fi

# Frontend
echo -e "${GREEN}  ✅ Frontend : http://localhost:5173${NC}"

echo ""
echo "================================"
echo "  ✨ ECLA AI Search est prêt !"
echo "================================"
echo ""
echo -e "${CYAN}📱 Accédez à l'application : http://localhost:5173${NC}"
echo ""
echo "📊 Tableau de bord Qdrant : http://localhost:6333/dashboard"
echo "🔧 API Backend (Swagger) : http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}💡 Commandes utiles :${NC}"
echo "   - Voir les logs : docker compose logs -f"
echo "   - Arrêter : docker compose down"
echo "   - Redémarrer : docker compose restart"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter..."

# Suivre les logs
docker compose logs -f

