#!/usr/bin/env bash
set -euo pipefail

DOMAINS="www.ecommerce.lcl ecommerce.lcl argocd.ecommerce.lcl airflow.ecommerce.lcl"

# Determine target IP
TARGET_IP="127.0.0.1"

# Check if minikube is running and get its IP if not using 127.0.0.1 tunnel
if command -v minikube &>/dev/null; then
    MK_IP=$(minikube ip 2>/dev/null || true)
    if [ -n "$MK_IP" ] && [ "$MK_IP" != "127.0.0.1" ]; then
        TARGET_IP="$MK_IP"
    fi
fi

HOSTS_LINE="${TARGET_IP} ${DOMAINS}"

echo "=========================================================="
echo "🌐 Configuration du fichier /etc/hosts pour la résolution DNS locale"
echo "IP ciblée : ${TARGET_IP}"
echo "Entrée : ${HOSTS_LINE}"
echo "=========================================================="

if grep -q "www.ecommerce.lcl" /etc/hosts 2>/dev/null; then
    echo "ℹ️ Le domaine www.ecommerce.lcl est déjà présent dans /etc/hosts."
    echo "Ligne actuelle :"
    grep "www.ecommerce.lcl" /etc/hosts || true
else
    echo "⚠️ Pour activer la résolution automatique sur votre machine, exécutez :"
    echo ""
    echo "  echo \"${HOSTS_LINE}\" | sudo tee -a /etc/hosts"
    echo ""
    if [ "$(id -u)" -eq 0 ]; then
        echo "${HOSTS_LINE}" >> /etc/hosts
        echo "✅ Entrée ajoutée automatiquement à /etc/hosts !"
    fi
fi

