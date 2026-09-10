#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================================================="
echo "🐙 Configuration & Liaison avec votre Dépôt GitHub (GitOps)"
echo "=========================================================================="

if [ -z "${1:-}" ]; then
    echo "Usage : $0 <URL_DE_VOTRE_REPO_GITHUB>"
    echo "Exemple : $0 https://github.com/naval0506/devsecops-ecommerce.git"
    exit 1
fi

GITHUB_REPO_URL="$1"

echo "1. Mise à jour de l'URL du dépôt dans les fichiers ArgoCD..."
for f in "${PROJECT_ROOT}"/k8s/argocd/app-*.yaml; do
    sed -i "s|repoURL: '.*'|repoURL: '${GITHUB_REPO_URL}'|g" "$f"
    echo "  -> Modifié : $(basename "$f")"
done

echo ""
echo "2. Configuration de l'origine Git et commit des changements..."
cd "${PROJECT_ROOT}"
git add k8s/argocd/
git commit -m "feat(gitops): configure GitHub repository URL for ArgoCD" || true
git remote remove origin 2>/dev/null || true
git remote add origin "${GITHUB_REPO_URL}"
git branch -M main

echo ""
echo "3. Envoi du code vers GitHub..."
echo "Exécution de : git push -u origin main"
git push -u origin main || {
    echo "⚠️ Le push a échoué. Vérifiez vos droits d'accès ou créez d'abord le dépôt vide sur GitHub."
}

echo ""
echo "4. Application des applications dans ArgoCD Kubernetes..."
if kubectl cluster-info &>/dev/null; then
    kubectl apply -f "${PROJECT_ROOT}/k8s/argocd/app-ecommerce.yaml" || true
    kubectl apply -f "${PROJECT_ROOT}/k8s/argocd/app-airflow.yaml" || true
    kubectl apply -f "${PROJECT_ROOT}/k8s/argocd/app-ingress.yaml" || true
    echo "✅ Applications ArgoCD synchronisées avec votre GitHub !"
fi

echo ""
echo "=========================================================================="
echo "🎉 Votre projet est maintenant connecté à GitHub et géré par ArgoCD !"
echo "=========================================================================="

