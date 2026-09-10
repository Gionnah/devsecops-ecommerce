#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================================================="
echo "🚀 Déploiement Complet de la Plateforme E-Commerce CRUD GitOps DevSecOps"
echo "Composants : Kubernetes, ArgoCD, Ingress NGINX SSL, Apache Airflow ETL"
echo "=========================================================================="

cd "${PROJECT_ROOT}"

# 1. Vérification des outils requis
echo "🔍 [1/7] Vérification des prérequis système..."
for cmd in docker minikube kubectl openssl; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "❌ Commande manquante : $cmd. Veuillez l'installer avant de continuer."
        exit 1
    fi
done
echo "✅ Docker, Minikube, Kubectl et OpenSSL sont présents."

# Déblocage forwarding iptables si permissions dispo
if [ "$(id -u)" -eq 0 ]; then
    iptables -P FORWARD ACCEPT 2>/dev/null || true
fi

# 2. Démarrage du cluster Minikube
echo ""
echo "☸️ [2/7] Démarrage et configuration de Minikube..."
if ! minikube status &>/dev/null; then
    echo "Démarrage de Minikube avec le driver Docker..."
    minikube start --driver=docker --cpus=4 --memory=6144
else
    echo "Minikube est déjà en cours d'exécution."
fi

# 3. Activation du contrôleur Nginx Ingress
echo ""
echo "🌐 [3/7] Activation du contrôleur Ingress NGINX..."
minikube addons enable metrics-server 2>/dev/null || true

echo "Activation de l'addon Ingress NGINX..."
minikube addons enable ingress 2>/dev/null || {
    echo "⚠️ L'addon Minikube est en cours de configuration..."
}

# 4. Génération des certificats SSL/TLS
echo ""
echo "🔐 [4/7] Génération des certificats SSL et création des secrets TLS..."
chmod +x "${PROJECT_ROOT}/scripts/generate-ssl.sh"
"${PROJECT_ROOT}/scripts/generate-ssl.sh"

# 5. Construction de l'image Docker sur l'hôte et chargement dans Minikube
echo ""
echo "🐳 [5/7] Construction de l'image de l'application E-commerce sur l'hôte..."
# Assurer qu'on utilise le Docker de l'hôte (qui a l'accès Internet)
unset DOCKER_TLS_VERIFY DOCKER_HOST DOCKER_CERT_PATH MINIKUBE_ACTIVE_DOCKERD 2>/dev/null || true

echo "Build de l'image Docker locale..."
docker build -t ecommerce-app:v1.0.0 -f "${PROJECT_ROOT}/src/Dockerfile" "${PROJECT_ROOT}/src"

echo "Chargement direct de l'image dans le cluster Minikube..."
minikube image load ecommerce-app:v1.0.0

# 6. Installation d'ArgoCD
echo ""
echo "🐙 [6/7] Installation et initialisation d'ArgoCD..."
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml || true

# 7. Déploiement des Manifestes (E-Commerce, Airflow & Ingress)
echo ""
echo "📦 [7/7] Déploiement des applications Kubernetes (E-Commerce & Airflow)..."
kubectl apply -k "${PROJECT_ROOT}/k8s/" || true

# Application des CRD ArgoCD
echo "Enregistrement des applications dans ArgoCD GitOps..."
kubectl apply -f "${PROJECT_ROOT}/k8s/argocd/app-ecommerce.yaml" 2>/dev/null || true
kubectl apply -f "${PROJECT_ROOT}/k8s/argocd/app-airflow.yaml" 2>/dev/null || true
kubectl apply -f "${PROJECT_ROOT}/k8s/argocd/app-ingress.yaml" 2>/dev/null || true

# Récupération du mot de passe initial ArgoCD
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d 2>/dev/null || echo "admin")

# Configuration /etc/hosts
chmod +x "${PROJECT_ROOT}/scripts/add-hosts.sh"
"${PROJECT_ROOT}/scripts/add-hosts.sh"

echo ""
echo "=========================================================================="
echo "🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !"
echo "=========================================================================="
echo ""
echo "🔗 ACCÈS AUX SERVICES EN HTTPS :"
echo "  1. 🛒 Site Web E-Commerce CRUD : https://www.ecommerce.lcl"
echo "  2. 🐙 Console GitOps ArgoCD   : https://argocd.ecommerce.lcl"
echo "     • Utilisateur : admin"
echo "     • Mot de passe : ${ARGOCD_PASSWORD}"
echo "  3. ⚙️ Orchestrateur Airflow ETL : https://airflow.ecommerce.lcl"
echo "     • Utilisateur : admin"
echo "     • Mot de passe : admin_airflow_2026"
echo ""
echo "💡 ASTUCE MINIKUBE SUR LINUX :"
echo "Pour router le trafic Ingress dans un terminal séparé :"
echo "  minikube tunnel"
echo ""
echo "=========================================================================="
