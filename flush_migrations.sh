#!/bin/bash

# =============================================================================
# Script de suppression des migrations et flush de la base de données
# Pour recréer les migrations proprement
# =============================================================================

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Django Migration Flush Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Liste des applications Django avec migrations
APPS=(
    "autocar"
    "business.auto"
    "business.immo"
    "business.retail"
    "core.addressing"
    "core.orders"
    "core.products"
    "core.profile"
    "core.streams"
    "core.taxonomy"
    "customer"
    "devis"
    "immoshop"
    "invoice"
    "product"
    "project"
    "shop"
)

# -----------------------------------------------------------------------------
# Fonction pour supprimer les fichiers de migration
# -----------------------------------------------------------------------------
delete_migrations() {
    local app=$1
    local app_path=""
    
    # Déterminer le chemin de l'app
    if [[ $app == core.* ]]; then
        app_path="core/${app#core.}"
    elif [[ $app == business.* ]]; then
        app_path="business/${app#business.}"
    else
        app_path="$app"
    fi
    
    local migrations_dir="$app_path/migrations"
    
    if [ -d "$migrations_dir" ]; then
        echo -e "${YELLOW}Suppression des migrations dans $app...${NC}"
        
        # Supprimer tous les fichiers sauf __init__.py
        find "$migrations_dir" -type f ! -name "__init__.py" -delete
        
        # Compter les fichiers restants
        local count=$(find "$migrations_dir" -type f ! -name "__init__.py" | wc -l)
        
        if [ $count -eq 0 ]; then
            echo -e "${GREEN}  ✓ Migration$GREENs supprimées pour $app${NC}"
        else
            echo -e "${RED}  ✗ Erreur lors de la suppression pour $app${NC}"
        fi
    else
        echo -e "${YELLOW}  - Pas de répertoire migrations pour $app${NC}"
    fi
}

# -----------------------------------------------------------------------------
# Étape 1: Supprimer les fichiers de migration
# -----------------------------------------------------------------------------
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Étape 1: Suppression des migrations${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

for app in "${APPS[@]}"; do
    delete_migrations "$app"
done

echo ""
echo -e "${GREEN}✓ Suppression des migrations terminée${NC}"
echo ""

# -----------------------------------------------------------------------------
# Étape 2: Flush de la base de données
# -----------------------------------------------------------------------------
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Étape 2: Flush de la base de données${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}Exécution de: python manage.py flush --noinput${NC}"
python manage.py flush --noinput

echo ""
echo -e "${GREEN}✓ Flush de la base de données terminé${NC}"
echo ""

# -----------------------------------------------------------------------------
# Résumé
# -----------------------------------------------------------------------------
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Résumé${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}✓ Toutes les migrations ont été supprimées${NC}"
echo -e "${GREEN}✓ La base de données a été vidée${NC}"
echo ""
echo -e "${YELLOW}Pour recréer les migrations proprement, exécutez:${NC}"
echo -e "${YELLOW}  python manage.py makemigrations${NC}"
echo -e "${YELLOW}puis:${NC}"
echo -e "${YELLOW}  python manage.py migrate${NC}"
echo ""
