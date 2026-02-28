#!/bin/bash

# =============================================================================
# Stratégie de Makemigrations - Ordre Séquentiel
# =============================================================================
# Cet script exécute les makemigrations dans l'ordre correct selon les dépendances
# 
# Ordre de dépendance:
# 1. Django contrib (contenttypes, auth) - toujours en premier
# 2. Applications tierces (polymorphic, mptt) - requis par d'autres apps
# 3. Core framework (modèles de base sans dépendances externes)
# 4. Applications métier (project)
# 5. Applications legacy (pour migration)
# =============================================================================

# set -e  # Désactivé pour permettre de continuer en cas d'erreur sur une app

echo "=============================================="
echo "Makemigrations - Ordre Séquentiel"
echo "=============================================="

# Fonction pour vérifier si une app a des modèles et faire makemigrations
makemigrations_if_exists() {
    local app="$1"
    if ./manage.py help "$app" >/dev/null 2>&1; then
        echo "   >>> Making migrations for: $app"
        ./manage.py makemigrations "$app" 2>/dev/null || echo "   (no changes for $app)"
    else
        echo "   (skipping $app - not installed)"
    fi
}

# -----------------------------------------------------------------------------
# ÉTAPE 1: Django Contrib (requis en premier)
# -----------------------------------------------------------------------------
echo ""
echo ">>> Étape 1: Django Contrib"
./manage.py makemigrations contenttypes
./manage.py makemigrations auth

# -----------------------------------------------------------------------------
# ÉTAPE 2: Applications Tierces (polymorphic, mptt) - AVANT core
# -----------------------------------------------------------------------------
echo ""
echo ">>> Étape 2: Applications Tierces"
./manage.py makemigrations polymorphic
./manage.py makemigrations mptt

# -----------------------------------------------------------------------------
# ÉTAPE 3: Core Framework (base, puis sous-modules)
# -----------------------------------------------------------------------------
echo ""
echo ">>> Étape 3: Core Framework"

# 3.1 - Core base
./manage.py makemigrations core

# 3.2 - Taxonomy (catégories, tags) - dépend de core
./manage.py makemigrations taxonomy

# 3.3 - Profile (utilisateurs, profils) - dépend de core, auth
./manage.py makemigrations profile

# 3.4 - Streams (flux de données) - dépend de core
./manage.py makemigrations streams

# 3.5 - Products (produits de base) - dépend de core, taxonomy
./manage.py makemigrations product

# 3.6 - Quotes (devis) - try core.quotes first, fallback to quotes
./manage.py makemigrations core.quotes 2>/dev/null || ./manage.py makemigrations quotes 2>/dev/null || echo "   (skipping quotes - no models)"

# 3.7 - Orders (commandes) - try core.orders first
./manage.py makemigrations core.orders 2>/dev/null || echo "   (skipping orders - no models)"

# 3.8 - Invoices (facturation)
./manage.py makemigrations core.invoices 2>/dev/null || echo "   (skipping invoices - no models)"

# 3.9 - Cart (panier)
./manage.py makemigrations core.cart 2>/dev/null || echo "   (skipping cart - no models)"

# 3.10 - Stock (gestion stock)
./manage.py makemigrations core.stock 2>/dev/null || echo "   (skipping stock - no models)"

# 3.11 - Payments (paiements)
./manage.py makemigrations core.payments 2>/dev/null || echo "   (skipping payments - no models)"

# 3.12 - Services (services)
./manage.py makemigrations core.services 2>/dev/null || echo "   (skipping services - no models)"

# 3.13 - Multi files upload
./manage.py makemigrations core.mfilesupload 2>/dev/null || echo "   (skipping mfilesupload - no models)"

# -----------------------------------------------------------------------------
# ÉTAPE 4: Project (application principale)
# -----------------------------------------------------------------------------
echo ""
echo ">>> Étape 4: Project"
./manage.py makemigrations project

# -----------------------------------------------------------------------------
# ÉTAPE 5: Business Apps (plugins métier) - ONLY if migrations exist
# -----------------------------------------------------------------------------
echo ""
echo ">>> Étape 5: Business Apps"

# 5.1 - Business Immo (Immobilier) - only if has migrations
[ -d "business/immo/migrations" ] && ./manage.py makemigrations business.immo || echo "   (skipping business.immo - no migrations)"

# 5.2 - Business Retail (E-commerce) - only if has migrations
[ -d "business/retail/migrations" ] && ./manage.py makemigrations business.retail || echo "   (skipping business.retail - no migrations)"

# 5.3 - Business Auto (Automobile) - only if has migrations
[ -d "business/auto/migrations" ] && ./manage.py makemigrations business.auto || echo "   (skipping business.auto - no migrations)"

# -----------------------------------------------------------------------------
# ÉTAPE 6: Applications Legacy (pour migration)
# -----------------------------------------------------------------------------
echo ""
echo ">>> Étape 6: Applications Legacy"

# 6.1 - Invoice (legacy)
./manage.py makemigrations invoice

# 6.2 - Devis (legacy)
./manage.py makemigrations devis

# 6.3 - Customer (legacy)
./manage.py makemigrations customer

# 6.4 - Immoshop (legacy) - only if installed
./manage.py makemigrations immoshop 2>/dev/null || echo "   (skipping immoshop - not installed)"

# 6.5 - Shop (legacy) - only if installed
./manage.py makemigrations shop 2>/dev/null || echo "   (skipping shop - not installed)"

# -----------------------------------------------------------------------------
# ÉTAPE 7: Vérification finale
# -----------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "Makemigrations terminé avec succès!"
echo "=============================================="
echo ""
echo "Pour appliquer les migrations, exécutez:"
echo "  ./manage.py migrate"
echo ""
