#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================================="
echo "🧹 Nettoyage et arrêt des ressources Kubernetes / Minikube"
echo "=========================================================="

cd "${PROJECT_ROOT}"

if kubectl cluster-info &>/dev/null; then
    echo "Suppression des applications et namespaces..."
    kubectl delete -k "${PROJECT_ROOT}/k8s/" --ignore-not-found=true || true
    kubectl delete namespace ecommerce airflow argocd --ignore-not-found=true || true
fi

echo "Arrêt de Minikube (optionnel)..."
read -p "Voulez-vous arrêter Minikube ? (o/N) : " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]]; then
    minikube stop || true
fi

echo "✅ Environnement nettoyé."

