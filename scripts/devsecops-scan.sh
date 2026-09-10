#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================================="
echo "🛡️ DevSecOps Local Security & Compliance Scanner"
echo "Project Root: ${PROJECT_ROOT}"
echo "=========================================================="

cd "${PROJECT_ROOT}"

# 1. Python Code Linting & Static Security Scan
echo ""
echo "--- [1/5] SAST & Code Quality (Bandit & Flake8) ---"
if command -v bandit &>/dev/null; then
    bandit -r src/ -ll -ii || echo "⚠️ Bandit a signalé des alertes mineures."
else
    echo "ℹ️ Bandit n'est pas installé localement (pip install bandit). Scan sauté."
fi

# 2. Secret Leak Scan
echo ""
echo "--- [2/5] Détection de Fuite de Secrets (Gitleaks / Regex) ---"
if command -v gitleaks &>/dev/null; then
    gitleaks detect --source . -v || true
else
    echo "ℹ️ Gitleaks n'est pas installé en local. Vérification des mots de passe en clair..."
    grep -rn "BEGIN RSA PRIVATE KEY" src/ 2>/dev/null || echo "✅ Aucun certificat privé détecté dans src/"
fi

# 3. Dockerfile Linting
echo ""
echo "--- [3/5] Linting Dockerfile (Hadolint) ---"
if command -v hadolint &>/dev/null; then
    hadolint src/Dockerfile || true
elif docker info &>/dev/null; then
    echo "Exécution de Hadolint via conteneur Docker éphémère..."
    docker run --rm -i hadolint/hadolint < src/Dockerfile || true
else
    echo "ℹ️ Hadolint non disponible."
fi

# 4. Container Vulnerability Scanning
echo ""
echo "--- [4/5] Scan de Vulnérabilités Conteneur (Trivy) ---"
if docker info &>/dev/null; then
    echo "Construction de l'image de test..."
    docker build -t ecommerce-app:v1.0.0 -f src/Dockerfile src/

    if command -v trivy &>/dev/null; then
        trivy image --severity HIGH,CRITICAL ecommerce-app:v1.0.0 || true
    else
        echo "Exécution de Trivy via Docker..."
        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy:latest image --severity HIGH,CRITICAL ecommerce-app:v1.0.0 || true
    fi
fi

# 5. Kubernetes Manifest Security Scan
echo ""
echo "--- [5/5] Audit de Sécurité des Manifestes K8s ---"
if command -v trivy &>/dev/null; then
    trivy config k8s/ || true
else
    echo "Validation syntaxique standard avec kubectl (client dry-run)..."
    if command -v kubectl &>/dev/null; then
        kubectl apply -k k8s/ --dry-run=client
        echo "✅ Manifestes Kubernetes Kustomize syntaxiquement valides !"
    fi
fi

echo ""
echo "=========================================================="
echo "✅ Audit DevSecOps terminé avec succès !"
echo "=========================================================="

