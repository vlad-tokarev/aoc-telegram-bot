
SECRETS_DIR=
DOCKER_REGISTRY=

-include .env
-include .env.local

.EXPORT_ALL_VARIABLES:

install-dev:
	pipenv install --dev

install:
	pipenv install

lint:
	flake8 aoc_bot

test:
	cd aoc_bot && pytest test.py

# Docker

docker-build:
	docker build . -t aoc-telegram-bot

docker-bash:
	 docker run -ti --env-file=.env -v ${SECRETS_DIR}:/run/secrets aoc-telegram-bot:latest bash

docker-run:
	 docker run -ti --env-file=.env -v ${SECRETS_DIR}:/run/secrets aoc-telegram-bot:latest

docker-push:
	docker tag aoc-telegram-bot:latest ${DOCKER_REGISTRY}/aoc-telegram-bot:latest
	docker push ${DOCKER_REGISTRY}/aoc-telegram-bot:latest

docker-all: docker-build docker-push

# Kubernetes

deploy-config-map:
	kubectl delete cm/aoc-bot --ignore-not-found -n default
	kubectl create cm aoc-bot --from-env-file=.env

deploy-secret:
	kubectl delete secret/aoc-bot --ignore-not-found -n default
	kubectl create secret generic aoc-bot --from-file=${SECRETS_DIR}/aoc_bot__aoc_session_id --from-file=${SECRETS_DIR}/aoc_bot__telegram_token -n default

deploy-app:
	kubectl apply -f deploy/deployment.yaml -n default

restart-app:
	kubectl rollout restart deploy/aoc-bot

deploy-all: deploy-config-map deploy-secret deploy-app

# Sync

all: docker-all deploy-all