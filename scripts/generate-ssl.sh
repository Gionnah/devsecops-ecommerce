#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CERTS_DIR="${PROJECT_ROOT}/certs"

mkdir -p "${CERTS_DIR}"

echo "=========================================================="
echo "🔐 Génération des Certificats SSL/TLS pour Ingress NGINX"
echo "Domaines : www.ecommerce.lcl, ecommerce.lcl, argocd.ecommerce.lcl, airflow.ecommerce.lcl"
echo "=========================================================="

cd "${CERTS_DIR}"

# 1. Génération de la Clé Privée CA et du Certificat Racine
if [ ! -f "ca.key" ] || [ ! -f "ca.crt" ]; then
    echo "📜 1. Création de l'Autorité de Certification (CA) locale..."
    openssl genrsa -out ca.key 4096
    openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 \
        -subj "/C=FR/ST=IDF/L=Paris/O=CloudShop DevSecOps/OU=Security/CN=CloudShop Local Root CA" \
        -out ca.crt
fi

# 2. Génération de la Clé Privée du Serveur Web (file.key)
echo "🔑 2. Création de la clé privée serveur (file.key)..."
openssl genrsa -out file.key 2048

# 3. Création du fichier de configuration SAN (Subject Alternative Names)
cat <<EOF > cert.ext
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = www.ecommerce.lcl
DNS.2 = ecommerce.lcl
DNS.3 = argocd.ecommerce.lcl
DNS.4 = airflow.ecommerce.lcl
DNS.5 = localhost
IP.1 = 127.0.0.1
EOF

# 4. Génération de la demande de signature (CSR)
echo "📝 3. Création du CSR..."
openssl req -new -key file.key -out server.csr \
    -subj "/C=FR/ST=IDF/L=Paris/O=CloudShop DevSecOps/OU=E-Commerce/CN=www.ecommerce.lcl"

# 5. Signature du certificat avec la CA locale (file.crt)
echo "✍️ 4. Signature du certificat SSL (file.crt)..."
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out file.crt -days 825 -sha256 -extfile cert.ext

rm -f server.csr cert.ext ca.srl

echo "✅ Certificats générés avec succès dans : ${CERTS_DIR}"
ls -lh "${CERTS_DIR}"

# 6. Injection dans Kubernetes Secret si kubectl est connecté
if kubectl cluster-info &>/dev/null; then
    echo "☸️ 5. Mise à jour du Secret TLS dans Kubernetes..."
    kubectl create namespace ecommerce --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace airflow --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

    kubectl create secret tls ecommerce-tls-secret \
        --cert=file.crt \
        --key=file.key \
        --namespace=ecommerce \
        --dry-run=client -o yaml | kubectl apply -f -

    kubectl create secret tls ecommerce-tls-secret \
        --cert=file.crt \
        --key=file.key \
        --namespace=airflow \
        --dry-run=client -o yaml | kubectl apply -f -

    kubectl create secret tls ecommerce-tls-secret \
        --cert=file.crt \
        --key=file.key \
        --namespace=argocd \
        --dry-run=client -o yaml | kubectl apply -f -

    echo "✅ Secret 'ecommerce-tls-secret' synchronisé dans les namespaces ecommerce, airflow, argocd !"
fi

