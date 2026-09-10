.PHONY: help setup build test scan ssl hosts deploy clean logs

SHELL := /bin/bash

help: ## Affiche l'aide sur les commandes disponibles
	@echo "=========================================================================="
	@echo "🛠️ Commandes Disponibles - Plateforme E-Commerce GitOps & DevSecOps"
	@echo "=========================================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Déploie tout l'environnement de A à Z (Minikube, Ingress, SSL, ArgoCD, Airflow)
	@chmod +x scripts/*.sh
	@./scripts/setup-all.sh

ssl: ## Génère les certificats SSL auto-signés pour www.ecommerce.lcl
	@chmod +x scripts/generate-ssl.sh
	@./scripts/generate-ssl.sh

hosts: ## Configure l'entrée DNS locale dans /etc/hosts
	@chmod +x scripts/add-hosts.sh
	@./scripts/add-hosts.sh

build: ## Construit l'image Docker durcie de l'application E-commerce
	@docker build -t ecommerce-app:v1.0.0 -f src/Dockerfile src/

test: ## Exécute les tests unitaires et d'intégration avec pytest
	@pytest tests/ -v

scan: ## Lance la suite de scans DevSecOps (Hadolint, Bandit, Trivy, Gitleaks)
	@chmod +x scripts/devsecops-scan.sh
	@./scripts/devsecops-scan.sh

deploy: ## Applique les manifestes Kubernetes kustomize
	@kubectl apply -k k8s/

tunnel: ## Lance le tunnel Minikube pour le routage Ingress sur Linux
	@minikube tunnel

logs: ## Affiche les logs de l'application E-commerce
	@kubectl -n ecommerce logs -l app=ecommerce-app --tail=100 -f

logs-airflow: ## Affiche les logs d'Apache Airflow
	@kubectl -n airflow logs -l app=airflow --tail=100 -f

clean: ## Supprime les ressources déployées dans Kubernetes
	@chmod +x scripts/teardown.sh
	@./scripts/teardown.sh

