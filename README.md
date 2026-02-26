A Django based shop system 
# as_shoppy_frm_v2

# 📊 Analyse du Framework AS-SHOPY-ECOMMERCE

> Created le 26 Fev  2026
>
> autheur : AS + Kimi_v2.5

## 🎯 Vue d'ensemble

Votre framework AS-SHOPY-ECOMMERCE est une architecture Django/Python ambitieuse qui vise à standardiser le processus de vente e-commerce/ERP. Voici mon analyse détaillée :

---

## ✅ Forces du Framework

### 1. **Architecture Modulaire**

- Utilisation efficace de l'**héritage polymorphique** avec  **django-polymorphic**
- **Séparation claire entre `core` (logique métier) et applications spécifiques**
- Pattern de "**deferred foreign keys**" pour découpler les modèles

### 2. **Gestion des Produits**

```python
# BaseProduct bien structurée avec hooks extensibles
class BaseProduct(PolymorphicModel):
    # Champs essentiels: price, stock, UOM, taxes
    # Méthodes abstraites: get_price(), get_absolute_url()
```

### 3. **Workflow Complet**

- Panier → Devis → Commande → Facture
- Gestion des statuts via Enum (StatutDevis, StatutFacture)
- Conversion automatique devis→facture

### 4. **Multi-Business Ready**

- `ImmoProduct` pour l'immobilier
- `Product` standard pour e-commerce
- Extensible pour automobile, B2B, etc.

---

## ⚠️ Problèmes Critiques Identifiés

### 1. **BUGS MAJEURS**

#### A. Double sauvegarde dans [`invoice/models.py`](invoice/models.py:107)

```python
# LIGNES 107-120: Code dupliqué !
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)  # Premier save
    if not self.numero:
        self.numero = self.generate_invoice_number()
        super().save(update_fields=['numero'])
    # ... RÉPÉTITION DU MÊME CODE (lignes 117-120)
    if not self.numero:  # Jamais exécuté car déjà défini
        self.numero = self.generate_invoice_number()
        super().save(update_fields=['numero'])
```

#### B. Référence circulaire dans [`devis/models.py`](devis/models.py:84)

```python
def convertir_en_facture(self):
    facture = Invoice.objects.create(...)  # Invoice importé ?
    # ERREUR: Invoice n'est pas importé dans ce fichier!
```

#### C. Mauvaise gestion du stock dans [`core/base_product/models.py`](core/base_product/models.py:121)

```python
def augment_quantity(self, quantity):
    self.quantity = self.quantity + int(quantity)  # 'quantity' n'existe pas!
    self.save()
```

### 2. **Problèmes d'Architecture**

#### A. Incohérence des modèles Order

- [`core/orders/models.py`](core/orders/models.py:4): `Order` basique sans lien customer
- [`devis/models.py`](devis/models.py:31): `Quote` avec workflow complet
- **Manque**: Une classe `Order` unifiée qui étend le devis validé

#### B. Gestion du panier fragile

```python
# core/cart/cart.py - Problèmes:
- Ligne 18: Écrasement systématique du panier session
- Ligne 31: Exception silencieuse (try/except trop large)
- Ligne 35: Comparaison incorrecte (AnonymousUser() vs is_authenticated)
```

### 3. **Problèmes de Sécurité**

```python
# config/settings.py:33
SECRET_KEY = 'jf$ac236s)uv)6xa&o0#@wmt+37zvlwf=atbi)%et^7=%3#$bb'
# Clé en dur - DOIT être dans variables d'environnement
```

### 4. **Problèmes de Performance**

```python
# product/models.py:19
from config.settings import product  # Mauvaise pratique!
# Import circulaire potentiel et couplage fort
```

---

## 🔧 Corrections Recommandées

### 1. **Corriger le double save dans Invoice**

```python
def save(self, *args, **kwargs):
    is_new = self.pk is None
    super().save(*args, **kwargs)
    
    if not self.numero:
        self.numero = self.generate_invoice_number()
        super().save(update_fields=['numero'])
```

### 2. **Unifier la gestion des statuts**

```python
# Créer un module core/common/enums.py
from django.db import models

class BaseStatusEnum(models.TextChoices):
    """Enum de base pour tous les workflows"""
    DRAFT = 'draft', _('Brouillon')
    PENDING = 'pending', _('En attente')
    VALIDATED = 'validated', _('Validé')
    CANCELLED = 'cancelled', _('Annulé')
```

### 3. **Implémenter le pattern State Machine pour les workflows**

```python
# core/workflows/state_machine.py
class WorkflowStateMachine:
    """
    Gestionnaire de transitions d'état
    Quote(DRAFT) → Quote(SENT) → Quote(ACCEPTED) → Order → Invoice
    """
    TRANSITIONS = {
        'Quote': {
            'draft': ['sent', 'cancelled'],
            'sent': ['accepted', 'refused', 'expired'],
            'accepted': ['converted'],  # → Order
        }
    }
```

### 4. **Corriger la gestion du stock**

```python
# core/inventory/managers.py
class InventoryManager(models.Manager):
    @transaction.atomic
    def deduct_stock(self, product, quantity, order_reference):
        """Déduction atomique avec vérification de disponibilité"""
        stock = self.select_for_update().get(product=product)
        if stock.quantity < quantity:
            raise InsufficientStockError(f"Stock insuffisant: {stock.quantity} < {quantity}")
        stock.quantity -= quantity
        stock.save()
        StockMovement.objects.create(
            product=product,
            quantity=-quantity,
            type='SALE',
            reference=order_reference
        )
```

---

## 🚀 Améliorations Architecturales

### 1. **Système d'Événements (Milestones/Streams)**

```python
# core/events/models.py
class Milestone(models.Model):
    """Points clés du parcours client"""
    name = models.CharField(max_length=100)  # 'quote_created', 'payment_received'
    timestamp = models.DateTimeField(auto_now_add=True)
    entity_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    entity_id = models.PositiveIntegerField()
    entity = GenericForeignKey('entity_type', 'entity_id')
    metadata = models.JSONField(default=dict)

class Stream(models.Model):
    """Flux de milestones pour un parcours client"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    milestones = models.ManyToManyField(Milestone, related_name='streams')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
```

### 2. **Service Layer Pattern**

```python
# services/quote_service.py
class QuoteService:
    """Encapsule la logique métier des devis"""
    
    def create_from_cart(self, cart: ShopCart, customer: Customer) -> Quote:
        with transaction.atomic():
            quote = Quote.objects.create(
                client=customer,
                total_amount=cart.summary(),
                status=QuoteStatus.DRAFT
            )
            for item in cart.items.all():
                QuoteItem.objects.create(
                    quote=quote,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
            return quote
    
    def convert_to_order(self, quote: Quote) -> Order:
        if quote.status != QuoteStatus.ACCEPTED:
            raise InvalidStateTransition("Le devis doit être accepté")
        # Conversion logique...
```

### 3. **API REST Unifiée**

```python
# api/views.py
class QuoteViewSet(viewsets.ModelViewSet):
    """Endpoints pour la gestion des devis"""
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        quote = self.get_object()
        quote.send_to_customer()
        return Response({'status': 'sent'})
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        quote = self.get_object()
        order = quote.convert_to_order()
        return Response({'order_id': order.id})
```

---

## 📋 Plan de Migration Recommandé

### Phase 1: Corrections Critiques (Immédiat)

1. ✅ Corriger le double save dans Invoice
2. ✅ Ajouter l'import manquant dans devis/models.py
3. ✅ Sécuriser SECRET_KEY
4. ✅ Corriger augment_quantity()

### Phase 2: Refactoring (1-2 semaines)

1. 🔄 Extraire les enums dans un module commun
2. 🔄 Implémenter State Machine pour les workflows
3. 🔄 Créer le service layer
4. 🔄 Unifier les modèles Order

### Phase 3: Évolutions (2-4 semaines)

1. 🚀 Système de milestones/streams
2. 🚀 API REST complète
3. 🚀 Tests automatisés (pytest)
4. 🚀 Documentation API (Swagger/OpenAPI)

---

## 🎯 Pertinence Globale

| Critère            | Score | Commentaire                                        |
| ------------------ | ----- | -------------------------------------------------- |
| **Architecture**   | ⭐⭐⭐⭐  | Bonne base polymorphique, mais besoin de nettoyage |
| **Maintenabilité** | ⭐⭐⭐   | Code dupliqué, imports circulaires à corriger      |
| **Extensibilité**  | ⭐⭐⭐⭐⭐ | Excellent pour multi-business                      |
| **Sécurité**       | ⭐⭐    | SECRET_KEY exposé, manque de validations           |
| **Performance**    | ⭐⭐⭐   | Besoin d'optimisation des requêtes N+1             |
| **Documentation**  | ⭐⭐    | Manque de docstrings et de README                  |

**Verdict**: Framework solide avec un excellent potentiel, mais nécessite un nettoyage technique avant production.

---

## 📚 Ressources Complémentaires

- [Django Polymorphic Best Practices](https://django-polymorphic.readthedocs.io/)
- [State Machine Pattern in Django](https://github.com/viewflow/django-fsm)
- [Django Service Layer Pattern](https://github.com/AltSchool/dynamic-rest)

Souhaitez-vous que j'implémente certaines de ces corrections ou que je développe un module spécifique ?

### Git ini 

**OUI, gh CLI = SOLUTION PARFAITE** pour ton problème SSH persistant ! **Plus simple, plus sûr, sans clés** → **token automatique**. Idéal dev Django/Vue.js.[[cli.github](https://cli.github.com/manual/gh_auth_login)]

## gh vs SSH : Pourquoi gh mieux maintenant

| Aspect             | SSH                         | gh CLI                    |
| ------------------ | --------------------------- | ------------------------- |
| **Setup**          | Clés/config/agent complexe  | `gh auth login` 30s       |
| **Sécurité**       | Clé compromise = tout perdu | Token auto (PAT scoped)   |
| **Multi-comptes**  | Config compliquée           | `gh auth switch`          |
| **Git push/clone** | `git` normal                | `git + gh auth setup-git` |
| **Bonus**          | PR/issues/repo en CLI       | ✅ gh pr create/list       |

## Migration gh (5min)

## 1. Login gh (si pas fait)

```
bashgh auth login --git-protocol https  # Token HTTPS
# Browser code → Authorize → Fini !
gh auth status  # Logged in ✓
```

## 2. Config git utiliser gh

```
bash
gh auth setup-git  # Git utilise gh creds auto
```

## 3. Push/clone instantané

```shell
bash# Clone
gh repo clone Siab/ad_erp

# Push (ton cas)
git remote set-url origin https://github.com/Siabdel/pr_ashopy.git  # Ton repo
git push -u origin main  # SANS SSH erreur !

# Créer repo + push
gh repo create pr_ashopy --public --push --source=.
```

## Avantages concrets

```shell
text# SSH ko → gh OK
gh pr create --title "Fix SVG" --body "..."
gh issue list --assignee @me
git push  # gh gère auth
```

**gh = SSH + GitHub CLI** (PR/issues/repo). **Installe si pas fait** (`sudo apt install gh`) → `gh auth login` → **fini galères clés** ![[cli.github](https://cli.github.com/manual/gh_auth_login)]

**SSH fixe** ? Recollé ta clé ED25519. **gh = solution immédiate** ! Quel choix ? 🚀

---



### Phase 2 : Refactoring 

## Refactoring Complete

I have successfully completed all four refactoring tasks:

### 1. ✅ Extracted Enums into a Common Module ([`core/enums.py`](core/enums.py))

Created a centralized enum module with:

- **ChoiceEnum** base class with metaclass for Django-compatible choices
- **CustomerState** - Customer recognition states
- **OrderStatus** - Order lifecycle states (PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, etc.)
- **PaymentStatus** - Payment processing states
- **QuoteStatus** - Quote lifecycle states (DRAFT, SENT, ACCEPTED, CONVERTED, etc.)
- **InvoiceStatus** - Invoice lifecycle states (DRAFT, SENT, PAID, OVERDUE, etc.)
- **ProjectStatus** - Project lifecycle states (PLANNING, UNDER_CONSTRUCTION, COMPLETED, etc.)
- **TicketStatus, TaskStatus** - Project management states
- **ChoiceEnumField** and **IntegerChoiceEnumField** - Django model fields for enums
- Legacy compatibility aliases (StatutDevis, StatutFacture)

### 2. ✅ Implemented State Machine for Workflows ([`core/state_machine.py`](core/state_machine.py))

Created a comprehensive state machine framework:

- **StateMachine** base class with transition management
- **Transition** dataclass for defining valid state changes
- **WorkflowMixin** for adding workflow capabilities to models
- **Decorators**: `@transition`, `@on_enter`, `@on_exit`
- Predefined workflows:
  - **QuoteWorkflow** - Quote lifecycle management
  - **InvoiceWorkflow** - Invoice lifecycle management
  - **OrderWorkflow** - Order lifecycle management
  - **ProjectWorkflow** - Project lifecycle management

### 3. ✅ Created the Service Layer ([`core/services/`](core/services/))

Implemented a complete service layer with:

- **BaseService** - Abstract base class with CRUD operations, validation, and workflow integration
- **ServiceResult** - Result wrapper for consistent success/failure handling
- **OrderService** - Order management with cart conversion and workflow triggers
- **QuoteService** - Quote management with invoice conversion
- **InvoiceService** - Invoice management with payment recording
- **ProjectService** - Project management with task/ticket support
- **CartService** - Shopping cart operations
- **BulkServiceMixin** - Bulk operations support
- **AuditedServiceMixin** - User action tracking

### 4. ✅ Unified Order Models ([`core/orders/models.py`](core/orders/models.py))

Consolidated order models with:

- **Order** model with:
  - Workflow support via WorkflowMixin
  - Status management using OrderStatus enum
  - Payment tracking with PaymentStatus
  - Complete address fields (shipping & billing)
  - Financial fields (subtotal, tax, discount, total)
  - Shipping information (tracking, carrier, dates)
  - Customer relations and notes
  - Database indexes for performance
- **OrderItem** model with:
  - Product snapshot fields
  - Pricing and discount tracking
  - Tax calculation support
- **OrderPayment** model for payment tracking
- **OrderStatusHistory** for audit trail

### Files Created/Modified:

- [`core/enums.py`](core/enums.py) - New centralized enum module
- [`core/state_machine.py`](core/state_machine.py) - New state machine framework
- [`core/services/__init__.py`](core/services/__init__.py) - Service package init
- [`core/services/base.py`](core/services/base.py) - Base service classes
- [`core/services/order_service.py`](core/services/order_service.py) - Order service
- [`core/services/quote_service.py`](core/services/quote_service.py) - Quote service
- [`core/services/invoice_service.py`](core/services/invoice_service.py) - Invoice service
- [`core/services/project_service.py`](core/services/project_service.py) - Project service
- [`core/orders/models.py`](core/orders/models.py) - Unified order models

I have successfully implemented a comprehensive **Milestones/Streams System** for the Django marketplace application. Here's a summary of what was created:

## 📁 New Module: `core/streams/`

### Models Created:

1. **[`Stream`](core/streams/models.py:15)** - Activity streams for projects, orders, and user activities
2. **[`StreamEvent`](core/streams/models.py:130)** - Individual events in streams with importance levels
3. **[`Milestone`](core/streams/models.py:217)** - Project milestones with progress tracking and dependencies
4. **[`StreamSubscription`](core/streams/models.py:428)** - User subscriptions for following streams
5. **[`MilestoneComment`](core/streams/models.py:491)** - Threaded comments on milestones

### Enums Created ([`core/streams/enums.py`](core/streams/enums.py:1)):

- `StreamType`: PROJECT, ORDER, USER, SYSTEM, MILESTONE, PRODUCT
- `EventType`: 25+ event types for different actions
- `MilestoneStatus`: PENDING, PLANNED, IN_PROGRESS, COMPLETED, DELAYED, CANCELLED, ON_HOLD
- `MilestonePriority`: LOW, MEDIUM, HIGH, CRITICAL
- `SubscriptionType`: FOLLOW, WATCH, NOTIFY, MUTE
- `EventImportance`: LOW, NORMAL, HIGH, CRITICAL

### Services Created:

1. **[`StreamService`](core/streams/services.py:20)** - Business logic for stream operations
2. **[`MilestoneService`](core/streams/services.py:151)** - Milestone lifecycle management
3. **[`SubscriptionService`](core/streams/services.py:363)** - Subscription and dashboard management

### API Endpoints (REST Framework):

- **Streams**: `/api/streams/` - List, create, subscribe, events, feed
- **Milestones**: `/api/milestones/` - CRUD, start/complete, progress, comments
- **Subscriptions**: `/api/subscriptions/` - User subscriptions and dashboard

### Admin Interface:

All models registered with custom admin classes featuring:

- Colored status badges
- Progress bars for milestones
- Importance indicators
- Search and filtering

### Integration:

- Added `core.streams` to [`INSTALLED_APPS`](config/settings/base.py:49)
- Added API routes at `/api/streams/`
- Created initial migration [`0001_initial.py`](core/streams/migrations/0001_initial.py:1)

### Documentation:

Comprehensive [`README.md`](core/streams/README.md:1) with usage examples, API reference, and integration guide.

## Key Features:

- **Activity Tracking**: Generic streams attachable to any model
- **Milestone Dependencies**: Milestones can depend on others with auto-unblocking
- **Progress Tracking**: Percentage-based progress with timeline visualization
- **User Notifications**: Subscription-based with importance filtering
- **Financial Tracking**: Budget and actual cost per milestone
- **Threaded Comments**: Discussion threads on milestones
- **Overdue Detection**: Automatic overdue status calculation



I have successfully updated all APIs, endpoints, and admin configurations to match the refactored models. Here's a summary of the changes:

## Project App Updates

### [`project/api_views.py`](project/api_views.py:1)

- Fixed `created_by` → `author` to match the [`BaseProject`](core/base_product/models.py:319) model
- Added [`TaskViewSet`](project/api_views.py:175) and [`TicketViewSet`](project/api_views.py:210) for project management
- Added new actions: `tasks`, `tickets`, `images`, `activate`
- Fixed status filtering to use [`ProjectStatus`](project/models.py:34) enum
- Added proper `select_related` for performance

### [`project/serializers.py`](project/serializers.py:1)

- Added [`TaskSerializer`](project/serializers.py:108), [`TicketSerializer`](project/serializers.py:135) with proper fields
- Fixed [`ProjectSerializer`](project/serializers.py:20) to match actual model fields
- Added counts for tasks, tickets, products, and images

### [`project/admin.py`](project/admin.py:1)

- Added [`TaskInline`](project/admin.py:42) and [`TicketInline`](project/admin.py:48)
- Fixed fieldsets to use correct fields from [`BaseProject`](core/base_product/models.py:319)
- Added [`TaskAdmin`](project/admin.py:100) and [`TicketAdmin`](project/admin.py:138) for standalone management

### [`project/urls.py`](project/urls.py:1)

- Registered [`TaskViewSet`](project/api_views.py:175) and [`TicketViewSet`](project/api_views.py:210) in router

## Product App Updates

### [`product/api_views.py`](product/api_views.py:1)

- Added filtering by project, category, status, availability
- Added new actions: `update_price`, `stats`
- Added [`ProductImageViewSet`](product/api_views.py:139), [`ProductTypeViewSet`](product/api_views.py:147), [`ProductSpecificationViewSet`](product/api_views.py:154)

### [`product/serializers.py`](product/serializers.py:1)

- Fixed image URL handling with `SerializerMethodField`
- Added [`ProductTypeSerializer`](product/serializers.py:71), [`ProductSpecificationSerializer`](product/serializers.py:49), [`ProductSpecificationValueSerializer`](product/serializers.py:59)
- Added [`ProductListSerializer`](product/serializers.py:79) with proper default_image_url

### [`product/admin.py`](product/admin.py:1)

- Fixed `exlude` typo → proper `readonly_fields`
- Added [`ProductSpecificationValueInline`](product/admin.py:14), [`ProductImageInline`](product/admin.py:49)
- Added standalone admins: [`ProductTypeAdmin`](product/admin.py:27), [`ProductSpecificationAdmin`](product/admin.py:33), [`ProductSpecificationValueAdmin`](product/admin.py:38), [`ProductImageAdmin`](product/admin.py:44)

### [`product/routers.py`](product/routers.py:1)

- Registered new viewsets: `product-images`, `product-types`, `product-specifications`

## Devis (Quote) App Updates

### [`devis/api_views.py`](devis/api_views.py:1)

- Fixed field names: `statut` → `status`, `montant_total` → `total_amount`, `date_creation` → `created_at`
- Added [`QuoteItemViewSet`](devis/api_views.py:145)
- Added actions: `mark_as_sent`, `mark_as_accepted`, `mark_as_rejected`, `items`, `stats`
- Added proper filtering and permissions

### [`devis/serializers.py`](devis/serializers.py:1)

- Fixed field names to match [`Quote`](devis/models.py:31) model
- Added [`QuoteItemSerializer`](devis/serializers.py:9), [`QuoteCreateUpdateSerializer`](devis/serializers.py:71)
- Added `item_count` and `subtotal` computed fields

### [`devis/urls.py`](devis/urls.py:1)

- Registered [`QuoteItemViewSet`](devis/api_views.py:145) in router

## Unified API Configuration

### [`config/api_urls.py`](config/api_urls.py:1)

- Added all new viewsets to the unified `/api/v1/` endpoint:
  - `tasks`, `tickets` (project management)
  - `product-images`, `product-types`, `product-specifications` (product catalog)
  - `quotes`, `quote-items` (quote management)

## Key API Endpoints Available

| Endpoint                  | Description                                           |
| ------------------------- | ----------------------------------------------------- |
| `/api/v1/projects/`       | Projects CRUD + tasks/tickets/products/images actions |
| `/api/v1/tasks/`          | Task management with filtering                        |
| `/api/v1/tickets/`        | Ticket/issue management                               |
| `/api/v1/products/`       | Products with filtering and actions                   |
| `/api/v1/product-images/` | Product image management                              |
| `/api/v1/quotes/`         | Quote (devis) management                              |
| `/api/v1/quote-items/`    | Quote line items                                      |
| `/api/v1/customers/`      | Customer management                                   |
| `/api/v1/streams/`        | Activity streams                                      |
| `/api/v1/milestones/`     | Project milestones                                    |