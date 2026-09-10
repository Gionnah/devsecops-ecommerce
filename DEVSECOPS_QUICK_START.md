# ⚡ DEVSECOPS QUICK START - COMMANDES ESSENTIELLES

---

## 🚀 DÉMARRAGE COMPLET (ONE COMMAND)

```bash
make setup
```

**Ce que ça fait:**
1. ✅ Démarre Minikube (4 CPU, 6GB RAM)
2. ✅ Active Ingress & Metrics Server
3. ✅ Génère certificats SSL/TLS
4. ✅ Déploie tous les namespaces Kubernetes
5. ✅ Crée secrets TLS
6. ✅ Affiche passwords & URLs

---

## 📊 VÉRIFIER STATUS

```bash
# Tous les pods
kubectl get pods -A

# Tous les services
kubectl get svc -A

# Ingress (entry points)
kubectl get ingress -A

# ArgoCD applications (GitOps)
kubectl get applications -n argocd

# Voir les erreurs
kubectl get events -A --sort-by='.lastTimestamp'
```

---

## 🔐 SÉCURITÉ - SCANS LOCAUX

```bash
# Lancer TOUS les scans DevSecOps localement
make scan

# Ou individuellement:

# Code quality
flake8 src/

# SAST - Static code analysis
bandit -r src/ -ll -ii

# Secrets detection
gitleaks detect -v

# Docker best practices
hadolint src/Dockerfile

# Dependency audit
safety check -r src/requirements.txt

# Container vulnerability scan
trivy image ecommerce-app:v1.0.0
```

---

## 🧪 TESTS & VALIDATION

```bash
# Run all unit tests
make test

# Run with coverage
pytest tests/ -v --cov=src/

# Watch mode (auto-rerun on changes)
pytest-watch tests/
```

---

## 📈 LOGS & MONITORING

```bash
# E-Commerce app logs (follow)
make logs

# Airflow logs
make logs-airflow

# Specific pod logs
kubectl -n ecommerce logs -f deployment/ecommerce-deployment

# Logs with timestamps
kubectl -n ecommerce logs -f deployment/ecommerce-deployment --timestamps=true

# Last 50 lines
kubectl -n ecommerce logs deployment/ecommerce-deployment --tail=50

# All container logs (if multiple containers)
kubectl -n ecommerce logs deployment/ecommerce-deployment --all-containers=true
```

---

## 🔧 DÉPLOIEMENT & CONFIGURATION

```bash
# Build Docker image locally
make build

# Deploy Kubernetes manifests
make deploy

# Update after Git changes
kubectl apply -k k8s/

# Force ArgoCD sync
argocd app sync ecommerce -n argocd

# Check ArgoCD status
kubectl get applications -n argocd

# Describe ArgoCD app
kubectl describe app ecommerce -n argocd
```

---

## 🛠️ KUBERNETES DEBUGGING

```bash
# Describe pod (see status, events, constraints)
kubectl describe pod ecommerce-deployment-XXXXX -n ecommerce

# Execute command inside pod
kubectl exec -it deployment/ecommerce-deployment -n ecommerce -- bash

# Port forward (access service locally)
kubectl port-forward -n ecommerce svc/ecommerce-service 5000:5000

# View pod resources usage (if metrics available)
kubectl top pods -n ecommerce

# Check pod security context
kubectl get pod -n ecommerce -o jsonpath='{.items[0].spec.securityContext}'

# View all environment variables in pod
kubectl set env pod/ecommerce-deployment-XXXXX --list -n ecommerce
```

---

## 🌐 ACCÈS AUX SERVICES

### Option 1: Via Ingress (HTTPS)

Ouvrir dans navigateur:
```
https://www.ecommerce.lcl       → E-Commerce App
https://argocd.ecommerce.lcl    → ArgoCD Console (admin / <password>)
https://airflow.ecommerce.lcl   → Airflow UI (admin / admin_airflow_2026)
```

**Prérequis:**
- Tunnel Minikube actif: `minikube tunnel` (terminal séparé)
- /etc/hosts configuré: `make hosts`
- Certificat SSL accepté dans navigateur (auto-signé)

---

### Option 2: Via Port Forwarding

```bash
# E-Commerce (5000)
kubectl port-forward -n ecommerce svc/ecommerce-service 5000:5000
# Puis: http://localhost:5000

# Airflow (8080)
kubectl port-forward -n airflow svc/airflow-service 8080:8080
# Puis: http://localhost:8080

# ArgoCD (8081)
kubectl port-forward -n argocd svc/argocd-server 8081:443
# Puis: https://localhost:8081
```

---

## 📝 GIT & GITOPS

```bash
# Initialize Git (if not already)
git init
git add .
git commit -m "Initial commit: devsecops ecommerce platform"

# Push to GitHub
git remote add origin https://github.com/YOUR_USER/devsecops-ecommerce.git
git push -u origin main

# Update ArgoCD to sync from YOUR repo
# Edit: k8s/argocd/app-ecommerce.yaml
# Change: repoURL: https://github.com/YOUR_USER/devsecops-ecommerce.git

# Re-apply
kubectl apply -f k8s/argocd/app-ecommerce.yaml

# Check status
kubectl get app ecommerce -n argocd -o jsonpath='{.status.sync.status}'
# Output should be: Synced
```

---

## 🔄 CI/CD PIPELINE WORKFLOW

```bash
# 1. Make code changes
vim src/app/routes.py

# 2. Run local scans (shift-left)
make scan        # All tests + security checks
make test        # Unit tests only

# 3. Commit & push
git add src/app/routes.py
git commit -m "feat: add new API endpoint"
git push origin main

# 4. GitHub Actions runs automatically
# → Job 1: Code security (Bandit, Flake8)
# → Job 2: Secrets scanning (Gitleaks)
# → Job 3: Docker scan (Trivy, Hadolint)
# → Job 4: Unit tests
# → Job 5: Build image (if all pass)
# → Job 6: ArgoCD syncs automatically

# 5. Verify in cluster
kubectl get deployment -n ecommerce
# Should show new rollout after sync

# 6. Check ArgoCD
kubectl get app ecommerce -n argocd -o wide
```

---

## 🧹 NETTOYAGE & TEARDOWN

```bash
# Delete all Kubernetes resources (keep Minikube)
make clean

# Stop Minikube
minikube stop

# Delete Minikube completely
minikube delete

# Full cleanup
make clean && minikube delete
```

---

## 📊 SECURITY CHECKLIST

```bash
# 1. No secrets in Git history
gitleaks detect -v

# 2. No vulnerable dependencies
safety check -r src/requirements.txt
pip-audit -r src/requirements.txt

# 3. Code vulnerabilities
bandit -r src/ -ll -ii

# 4. Container vulnerabilities
trivy image ecommerce-app:v1.0.0

# 5. Dockerfile security
hadolint src/Dockerfile

# 6. Kubernetes security
kubectl get pod -n ecommerce -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.securityContext}{"\n"}{end}'

# 7. Secrets not leaked
kubectl get secrets -n ecommerce -o yaml | grep -i password
# Should show base64 encoded, not plaintext
```

---

## 🔍 TROUBLESHOOTING

### Pod stuck in pending
```bash
kubectl describe pod <pod-name> -n <namespace>
# Look for: insufficient resources, pending volumes

# Check nodes capacity
kubectl describe nodes
```

### CrashLoopBackOff
```bash
# Check logs
kubectl logs <pod-name> -n <namespace>

# Check for OOM (Out of Memory)
kubectl describe pod <pod-name> -n <namespace> | grep -i memory

# Check restart count
kubectl get pod <pod-name> -n <namespace> -o wide
```

### Service not reachable
```bash
# Check DNS resolution
kubectl exec <pod-name> -n <namespace> -- nslookup ecommerce-service

# Check network policies
kubectl get networkpolicies -n <namespace>

# Check ingress
kubectl describe ingress ecommerce-ingress -n ecommerce
```

### ArgoCD not syncing
```bash
# Check ArgoCD logs
kubectl logs -n argocd deployment/argocd-application-controller

# Check if repository is accessible
kubectl exec -n argocd pod/argocd-repo-server-XXXXX -- git ls-remote <repo-url>

# Manual sync
argocd app sync ecommerce -n argocd
```

---

## 📋 PRODUCTION CHECKLIST

- ✅ All tests passing (6/6)
- ✅ All security scans passing
  - ✅ No secrets detected
  - ✅ No vulnerable code
  - ✅ No container CVEs
- ✅ Namespaces isolated
- ✅ Resource limits configured
- ✅ Health checks active
- ✅ ArgoCD syncing correctly
- ✅ HTTPS/TLS enabled
- ✅ Secrets stored securely (Kubernetes)
- ✅ Database backups tested
- ⚠️ Network policies configured
- ⚠️ Pod security policies enabled
- ⚠️ Monitoring/alerting configured
- ⚠️ Disaster recovery plan in place

---

## 📞 COMMON ISSUES & FIXES

| Issue | Command |
|-------|---------|
| Airflow workers crashing (OOM) | Already fixed: memory: 2048Mi |
| Pods pending | `kubectl describe pod POD -n NS` |
| Ingress not working | `minikube tunnel` (separate terminal) |
| DNS not resolving | `kubectl run -it --rm debug --image=busybox --restart=Never -- sh` |
| Database connection failed | `kubectl exec POD -n NS -- psql -h postgres-service` |
| ArgoCD not syncing | `argocd app sync APP -n argocd --force` |
| Secrets not mounted | `kubectl get secret -n NS -o yaml` |
| Image pull failed | `kubectl describe pod POD -n NS` |

---

## 🎓 LEARNING RESOURCES

```bash
# Kubernetes docs
kubectl explain deployment
kubectl explain pod.spec.securityContext
kubectl explain ingress

# Logs with grep
kubectl logs deployment/ecommerce-deployment -n ecommerce | grep -i error

# Interactive troubleshooting
kubectl debug node/minikube --it --image=ubuntu

# Watch resources
watch kubectl get pods -n ecommerce
watch kubectl get events -n ecommerce --sort-by='.lastTimestamp'
```

---

## 🚀 PERFORMANCE OPTIMIZATION

```bash
# Check resource requests vs usage
kubectl describe node minikube

# Optimize Minikube resources
minikube config set cpus 8
minikube config set memory 16384

# Check if metrics server is working
kubectl get deployment metrics-server -n kube-system
```

---

**Prêt à déployer en production!** ✅

*Pour les questions: consulter `DEVSECOPS_PRESENTATION.md` ou `DEVSECOPS_FILE_GUIDE.md`*
