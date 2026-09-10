# 📂 GUIDE DÉTAILLÉ DE CHAQUE FICHIER - DEVSECOPS

## 🎯 Structure du Projet & Rôle de Chaque Fichier

---

## 📦 NIVEAU 1: RACINE DU PROJET

### 📄 `README.md`
**Rôle:** Documentation générale du projet  
**Contenu:**
- Architecture overview
- Instructions de setup
- Table des matières complète
- Lien vers tous les services

**Importance DevSecOps:** ✅ Point de départ pour les développeurs

---

### 📄 `Makefile`
**Rôle:** Raccourcis pour commandes fréquentes  

**Commandes essentielles:**
```makefile
make setup    # Déploie TOUT automatiquement
make scan     # Lance suite de scans sécurité
make test     # Exécute tests unitaires
make build    # Build image Docker
make deploy   # Apply manifests Kubernetes
make clean    # Nettoie le cluster
```

**Importance DevSecOps:** ✅ Automatisation = moins d'erreurs humaines

---

### 📄 `.gitignore`
**Rôle:** Empêche commit de fichiers sensibles  

**Fichiers ignorés (sécurité):**
```
*.key          # Clés privées
*.pem          # Certificats
.env           # Variables d'env (secrets)
__pycache__    # Fichiers compilés
.DS_Store      # Fichiers système
```

**Importance DevSecOps:** 🔴 CRITIQUE - Prévient leaks de secrets

---

## 🐍 NIVEAU 2: CODE SOURCE (src/)

### 📁 `src/app/`
Structure Flask de l'application

#### 🔴 `src/app/app.py`
**Rôle:** Factory Flask + Initialization  

**Code clé:**
```python
def create_app(test_config=None):
    app = Flask(__name__)
    # ✅ Configuration sécurisée
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    
    # ✅ Healthchecks pour Kubernetes
    @app.route('/healthz')
    def healthz():
        return jsonify({'status': 'healthy'}), 200
    
    @app.route('/ready')
    def ready():
        # Vérifie si DB est accessible
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'ready'}), 200
```

**Sécurité:**
- ✅ Secrets from environment (jamais hardcoded)
- ✅ Healthchecks pour Kubernetes probes
- ✅ Database connectivity check

---

#### 🔴 `src/app/models.py`
**Rôle:** ORM SQLAlchemy (Database models)  

**Modèles:**
- `Product` - Produits e-commerce
- `Customer` - Clients
- `Order` - Commandes
- `OrderItem` - Items dans les commandes
- `SalesAnalyticsSummary` - KPIs ETL

**Sécurité SQLAlchemy:**
```python
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  # ✅ Limit length
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

# ✅ SQLAlchemy utilise prepared statements
# Protection contre SQL injection AUTOMATIQUE
```

**Importance DevSecOps:** 🟢 ORM = protection SQL injection

---

#### 🔴 `src/app/routes.py`
**Rôle:** CRUD endpoints REST API  

**Endpoints:**
```python
@main_bp.route('/', methods=['GET'])
def home():  # ✅ Affiche page d'accueil

@api_bp.route('/api/products', methods=['GET'])
def get_products():  # ✅ Liste tous les produits (JSON)

@api_bp.route('/api/orders', methods=['POST'])
def create_order(product_id, quantity):  # ✅ Crée une commande

@api_bp.route('/api/analytics/summary', methods=['POST'])
def update_analytics(payload):  # ✅ Receives Airflow ETL results
```

**Sécurité Input Validation:**
```python
# ✅ Valide les inputs avant traitement
if not product_id or not isinstance(product_id, int):
    return jsonify({'error': 'Invalid product_id'}), 400

if quantity <= 0 or quantity > 1000:
    return jsonify({'error': 'Invalid quantity'}), 400
```

**Importance DevSecOps:** 🟢 Input validation = XSS/Injection prevention

---

#### 📁 `src/app/templates/`
**Rôle:** HTML templates Bootstrap 5  

**Fichiers:**
- `index.html` - Page d'accueil
- `products.html` - Liste produits (CRUD)
- `orders.html` - Gestion commandes
- `analytics.html` - Dashboard Airflow ETL
- `layout.html` - Layout de base

**Sécurité Jinja2:**
```html
<!-- ✅ Jinja2 échappe automatiquement le HTML -->
<h1>{{ product.name }}</h1>  <!-- Sûr contre XSS -->

<!-- ✅ CSRF token dans tous les forms -->
<form method="POST">
    {{ csrf_token() }}
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <input type="text" name="product_name" required>
</form>
```

**Importance DevSecOps:** 🟢 CSRF protection + XSS prevention

---

#### 📁 `src/app/static/`
**Rôle:** Fichiers CSS/JS client-side  

- `style.css` - Styling Bootstrap
- `chart.js` - Graphiques interactifs (Analytics)
- `app.js` - Interactions JavaScript

**Sécurité:** ✅ Fichiers statiques (pas de logique sensible)

---

### 🔴 `src/requirements.txt`
**Rôle:** Dépendances Python (pinned versions)  

```
Flask==3.0.3                    # ✅ Version spécifique (pas "latest")
SQLAlchemy==2.0.30              # ORM
psycopg2-binary==2.9.9          # PostgreSQL driver
gunicorn==22.0.0                # WSGI server
pytest==8.2.0                   # Testing
python-dotenv==1.0.1            # Environment variables
```

**Importance DevSecOps:**
- ✅ Versions pinnées = reproducible builds
- ❌ Jamais "Flask" sans version = risque sécurité
- ✅ Auditable avec `pip audit`

---

### 🔴 `src/Dockerfile`
**Rôle:** Construire image Docker sécurisée  

**Architecture multi-stage:**

```dockerfile
# ===== STAGE 1: BUILDER =====
FROM python:3.11-slim AS builder

# ✅ Installer SEULEMENT les outils nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc postgresql-client && \
    rm -rf /var/lib/apt/lists/*  # ✅ Nettoyer cache apt

# ✅ Créer utilisateur non-root
RUN useradd -m -u 1001 appuser

# ✅ Copier code source avec ownership correct
COPY --chown=appuser:appuser src/ /app/

# ✅ Installer dépendances sans cache (réduit taille)
RUN pip install --no-cache-dir -r /app/requirements.txt

# ===== STAGE 2: FINAL (minimale) =====
FROM python:3.11-slim

# ✅ Copier SEULEMENT le nécessaire du builder
COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.11/site-packages/ \
                    /usr/local/lib/python3.11/site-packages/

# ✅ Créer utilisateur appuser
RUN useradd -m -u 1001 appuser
USER appuser  # ✅ RUN AS NON-ROOT!

WORKDIR /app

# ✅ Healthcheck intégré
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/healthz')"

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app.app:app"]
```

**Sécurité Dockerfile:**

| Ligne | Protection |
|------|-----------|
| `FROM python:3.11-slim` | ✅ Image minimale (pas d'outils non-nécessaires) |
| `--no-install-recommends` | ✅ Réduit dépendances |
| `rm -rf /var/lib/apt/lists/*` | ✅ Réduit taille image |
| `useradd -u 1001 appuser` | ✅ Utilisateur non-root (uid ≠ 0) |
| `USER appuser` | ✅ Run as non-root |
| `--no-cache-dir` | ✅ Pas de pip cache |
| Multi-stage | ✅ Final image sans gcc/build tools |

**Importance DevSecOps:** 🔴 CRITIQUE - Image durcie = moins de vulnérabilités

---

### 🔴 `src/.dockerignore`
**Rôle:** Exclure fichiers du build Docker  

```
.git                # ✅ Pas de Git history dans image
.gitignore
__pycache__         # ✅ Pas de .pyc compilés
*.egg-info
.pytest_cache
.venv
*.log               # ✅ Pas de logs sensibles
.env                # ✅ Pas de secrets!
```

**Importance DevSecOps:** 🟢 Réduit surface d'attaque

---

## ⚙️ NIVEAU 3: APACHE AIRFLOW (airflow/)

### 🔴 `airflow/dags/ecommerce_sales_etl.py`
**Rôle:** Pipeline ETL (Directed Acyclic Graph)  

**Étapes:**
1. **Extract** → Récupère données depuis API e-commerce
2. **Transform** → Calcule KPIs (revenue, avg order value, top category)
3. **Validate** → Data quality checks (non-négatif, cohérence)
4. **Load** → Insère résultats dans la base + appelle API

```python
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'data-team',
    'retries': 3,  # ✅ Retry policy
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'ecommerce_sales_etl',
    default_args=default_args,
    schedule_interval='0 * * * *',  # ✅ Toutes les heures
)

extract_task = PythonOperator(
    task_id='extract_ecommerce_data',
    python_callable=extract_ecommerce_data,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_sales_metrics',
    python_callable=transform_sales_metrics,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_data_quality',
    python_callable=validate_data_quality,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_to_datamart',
    python_callable=load_to_datamart_and_export,
    dag=dag,
)

# ✅ Dependency chain
extract_task >> transform_task >> validate_task >> load_task
```

**Sécurité ETL:**
- ✅ Service-to-service auth via DNS interne (pas d'API keys)
- ✅ Data validation (fail fast)
- ✅ Retry logic (resilience)
- ✅ Audit logging (tous les runs sauvegardés)

**Importance DevSecOps:** 🟢 Automated data pipeline

---

### 🔴 `airflow/requirements.txt`
```
apache-airflow==2.9.2           # ✅ Version spécifique
apache-airflow-providers-postgres==5.11.0
requests==2.31.0                # HTTP client
```

**Importance DevSecOps:** 🟢 Dependencies pinned

---

## ☸️ NIVEAU 4: KUBERNETES (k8s/)

### 📁 `k8s/base/`
**Rôle:** Ressources de base Kubernetes  

#### 🔴 `k8s/base/namespaces.yaml`
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ecommerce
---
apiVersion: v1
kind: Namespace
metadata:
  name: airflow
---
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
```

**Importance DevSecOps:** 🟢 Isolation workloads (RBAC, policies)

---

### 📁 `k8s/apps/ecommerce/`

#### 🔴 `deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce-deployment
  namespace: ecommerce
spec:
  replicas: 2  # ✅ High Availability
  
  template:
    spec:
      containers:
      - name: ecommerce
        image: ecommerce-app:v1.0.0
        
        # ✅ Resource limits (prevent DoS)
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        
        # ✅ Security context
        securityContext:
          runAsNonRoot: true  # ✅ Pas de root
          runAsUser: 1001     # ✅ Même user que Dockerfile
        
        # ✅ Kubernetes probes
        livenessProbe:
          httpGet:
            path: /healthz
            port: 5000
          periodSeconds: 10
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          periodSeconds: 5
        
        # ✅ Environment variables depuis Secrets/ConfigMaps
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ecommerce-secret
              key: database-url
```

**Importance DevSecOps:**
- ✅ Replicas 2 = High Availability
- ✅ Resource limits = prevent resource exhaustion
- ✅ Security context = run as non-root
- ✅ Probes = auto-healing
- ✅ Secrets management = no hardcoded credentials

---

#### 🔴 `postgres-deployment.yaml`
Database PostgreSQL pour l'app  

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-deployment
  namespace: ecommerce
spec:
  template:
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine  # ✅ Minimal image
        
        # ✅ Credentials depuis Secret
        env:
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: ecommerce-secret
              key: postgres-user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ecommerce-secret
              key: postgres-password
        
        # ✅ Persistent volume (données ne sont pas perdues)
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
```

**Importance DevSecOps:**
- ✅ Secrets (pas de passwords en clair)
- ✅ Persistent volume (data durability)
- ✅ Alpine image (minimal)

---

#### 🔴 `service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: ecommerce-service
  namespace: ecommerce
spec:
  type: ClusterIP  # ✅ Pas d'exposition externe directe
  
  ports:
  - port: 5000
    targetPort: 5000
  
  selector:
    app: ecommerce-app
```

**Rôle:** Service discovery interne  
**Importance DevSecOps:** 🟢 Isolé au cluster (pas accessible depuis internet)

---

#### 🔴 `configmap-secret.yaml`
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ecommerce-secret
  namespace: ecommerce
type: Opaque
data:
  postgres-user: ZWNvbW1lcmNlX3VzZXI=  # ✅ base64 encoded (not plaintext!)
  postgres-password: ZWNvbW1lcmNlX3Bhc3MxMjM=
  database-url: cG9zdGdyZXM6Ly9...

---

apiVersion: v1
kind: ConfigMap
metadata:
  name: ecommerce-config
data:
  LOG_LEVEL: "INFO"
  DEBUG: "false"
```

**Importance DevSecOps:**
- ✅ Secrets = chiffrés dans etcd (Kubernetes secret encryption)
- ✅ ConfigMaps = données publiques (logs level, etc.)
- ⚠️ base64 = encode, pas encrypt (kubernetes encrypt si activé)

---

### 📁 `k8s/apps/airflow/`

#### 🔴 `airflow-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: airflow-deployment
  namespace: airflow
spec:
  replicas: 1
  
  template:
    spec:
      containers:
      - name: airflow-standalone
        image: apache/airflow:2.9.2-python3.11
        
        command: ["/bin/bash"]
        args:
          - "-c"
          - |
            airflow db migrate &&  # ✅ Init database
            airflow users create --username admin ... &&
            airflow standalone
        
        # ✅ FIX APPLIQUÉ: Memory limits
        resources:
          limits:
            memory: "2048Mi"  # ← AUGMENTÉ DE 1536Mi
          requests:
            memory: "512Mi"
        
        # ✅ Volume pour DAGs
        volumeMounts:
        - name: dags-volume
          mountPath: /opt/airflow/dags
```

**Importance DevSecOps:**
- ✅ Memory limits correctement configurés
- ✅ DAGs injectés via ConfigMap (immutable)
- ✅ Database migrations automatiques

---

### 📁 `k8s/apps/ingress/`

#### 🔴 `ingress.yaml`
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ecommerce-ingress
  namespace: ecommerce
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"  # ✅ Force HTTPS
spec:
  ingressClassName: nginx
  
  # ✅ TLS configuration
  tls:
  - hosts:
    - www.ecommerce.lcl
    - argocd.ecommerce.lcl
    - airflow.ecommerce.lcl
    secretName: ecommerce-tls-secret  # ✅ Kubernetes Secret
  
  rules:
  - host: www.ecommerce.lcl
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ecommerce-service
            port:
              number: 5000
```

**Importance DevSecOps:**
- ✅ TLS/SSL enforced
- ✅ Certificates managed by Kubernetes
- ✅ HTTPS redirect (no plaintext)

---

### 📁 `k8s/argocd/`

#### 🔴 `app-ecommerce.yaml`
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ecommerce
  namespace: argocd
spec:
  project: default
  
  # ✅ Source: Git repository
  source:
    repoURL: 'https://github.com/YOUR_USER/devsecops-ecommerce.git'
    targetRevision: HEAD
    path: k8s/apps/ecommerce
  
  # ✅ Destination: Kubernetes cluster
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: ecommerce
  
  # ✅ Sync policy: auto-sync + self-heal
  syncPolicy:
    automated:
      prune: true        # ✅ Supprimer ressources supprimées de Git
      selfHeal: true     # ✅ Resync si manual change
    syncOptions:
    - CreateNamespace=true
```

**Importance DevSecOps:**
- ✅ Git = source of truth
- ✅ Auto-sync = deployments toujours à jour
- ✅ Self-heal = protection contre drift
- ✅ Audit trail: chaque changement dans Git

---

## 🔄 NIVEAU 5: CI/CD (.github/)

### 🔴 `.github/workflows/devsecops-ci.yml`
**Rôle:** GitHub Actions - Automated pipeline sécurité

**5 Jobs principaux:**

#### Job 1: Code Security & Tests
```yaml
- name: 🔍 Flake8 - Code Quality
  run: flake8 src/ --max-complexity=10

- name: 🔒 Bandit - SAST (Security Analysis)
  run: bandit -r src/ -ll -ii

- name: 📦 Safety - Dependency Audit
  run: safety check -r src/requirements.txt

- name: 🧪 Pytest - Unit Tests
  run: pytest tests/ -v
```

#### Job 2: Secrets Scanning
```yaml
- name: 🔑 Gitleaks - Detect Secrets
  run: gitleaks detect -v --source github
```

#### Job 3: Docker Scanning
```yaml
- name: 🐳 Hadolint - Dockerfile Check
  run: hadolint src/Dockerfile

- name: 📦 Trivy - Image Vulnerability Scan
  run: |
    docker build -t ecommerce-app:latest .
    trivy image ecommerce-app:latest
```

#### Job 4: Build Docker Image
```yaml
- name: 🏗️ Build Docker Image
  run: docker build -t ecommerce-app:${{ github.sha }} .
```

#### Job 5: Deploy to Kubernetes
```yaml
- name: 🚀 Trigger ArgoCD Sync
  run: |
    # ArgoCD détecte le nouveau commit et synce automatiquement
    git push origin main  # Déclenche ArgoCD
```

**Importance DevSecOps:** 🔴 CRITIQUE - Automated security checks avant deployment

---

## 🛠️ NIVEAU 6: SCRIPTS D'AUTOMATISATION (scripts/)

### 🔴 `setup-all.sh`
**Rôle:** Déploiement complet (one-liner)  

```bash
#!/bin/bash

# 1. Start Minikube
minikube start --cpus=4 --memory=6144

# 2. Enable addons
minikube addons enable ingress
minikube addons enable metrics-server

# 3. Generate SSL certificates
./scripts/generate-ssl.sh

# 4. Create namespaces & deploy
kubectl apply -k k8s/

# 5. Create TLS secret
kubectl create secret tls ecommerce-tls-secret \
  --cert=certs/file.crt \
  --key=certs/file.key \
  -n ecommerce

# 6. Wait for pods ready
kubectl wait --for=condition=ready pod -l app=ecommerce-app -n ecommerce --timeout=300s

echo "✅ Setup complete!"
```

**Importance DevSecOps:** 🟢 Reproductible, idempotent, auditable

---

### 🔴 `generate-ssl.sh`
**Rôle:** Générer certificats TLS/SSL  

```bash
#!/bin/bash

openssl req -x509 \
  -newkey rsa:2048 \
  -keyout certs/file.key \
  -out certs/file.crt \
  -days 365 \
  -subj "/CN=www.ecommerce.lcl" \
  -addext "subjectAltName=DNS:www.ecommerce.lcl,\
DNS:argocd.ecommerce.lcl,\
DNS:airflow.ecommerce.lcl"

chmod 600 certs/file.key  # ✅ Permissions restrictives
```

**Importance DevSecOps:** 🟢 SAN certificates (multi-domain)

---

### 🔴 `devsecops-scan.sh`
**Rôle:** Scans de sécurité locaux  

```bash
#!/bin/bash

echo "🛡️ DEVSECOPS SECURITY SCANS"

# 1. GITLEAKS
gitleaks detect -v

# 2. BANDIT
bandit -r src/ -ll -ii

# 3. HADOLINT
hadolint src/Dockerfile

# 4. TRIVY
trivy image ecommerce-app:v1.0.0

# 5. SAFETY
safety check -r src/requirements.txt

echo "✅ All security checks completed"
```

**Importance DevSecOps:** 🟢 Shift-left (scans AVANT commit)

---

## 📊 RÉSUMÉ: RÔLE DE CHAQUE FICHIER

### 🔐 SÉCURITÉ
- `src/Dockerfile` - Image durcie
- `src/requirements.txt` - Dépendances pinées
- `src/.dockerignore` - Réduit surface
- `k8s/apps/*/configmap-secret.yaml` - Secrets management
- `.github/workflows/devsecops-ci.yml` - Automated checks
- `scripts/devsecops-scan.sh` - Local security audits

### 🏗️ INFRASTRUCTURE
- `k8s/base/namespaces.yaml` - Isolation
- `k8s/apps/*/deployment.yaml` - Pod configuration
- `k8s/apps/*/service.yaml` - Service discovery
- `k8s/apps/ingress/ingress.yaml` - Entry point + TLS
- `k8s/argocd/app-*.yaml` - GitOps sync

### 🔄 AUTOMATION
- `Makefile` - Command shortcuts
- `setup-all.sh` - Full deployment
- `generate-ssl.sh` - Certificate generation
- `.github/workflows/` - CI/CD pipeline

### ⚙️ APPLICATION
- `src/app/app.py` - Flask factory
- `src/app/models.py` - Database ORM
- `src/app/routes.py` - API endpoints
- `src/app/templates/` - Web UI
- `airflow/dags/ecommerce_sales_etl.py` - ETL pipeline

---

**Tous les fichiers sont critiques pour une architecture DevSecOps robuste!** ✅
