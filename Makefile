
SECRETS_DIR=
DOCKER_REGISTRY=
ENV_D=shmatov
TAG=latest

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
	docker build . -t aoc-telegram-bot:${TAG}

docker-bash:
	 docker run -ti --env-file=.env -v ${SECRETS_DIR}:/run/secrets aoc-telegram-bot:${TAG} bash

docker-run:
	 docker run -ti --env-file=.env -v ${SECRETS_DIR}:/run/secrets aoc-telegram-bot:${TAG}

docker-push:
	docker tag aoc-telegram-bot:${TAG} ${DOCKER_REGISTRY}/aoc-telegram-bot:${TAG}
	docker push ${DOCKER_REGISTRY}/aoc-telegram-bot:${TAG}

docker-all: docker-build docker-push

# Kubernetes

deploy-config-map:
	kubectl delete cm/aoc-bot-${ENV_D} --ignore-not-found -n default
	kubectl create cm aoc-bot-${ENV_D} --from-env-file=envs/${ENV_D}/.env

deploy-secret:
	kubectl delete secret/aoc-bot-${ENV_D} --ignore-not-found -n default
	kubectl create secret generic aoc-bot-${ENV_D} --from-file=${SECRETS_DIR}/aoc_bot__aoc_session_id --from-file=${SECRETS_DIR}/aoc_bot__telegram_token -n default

deploy-app:
	kubectl apply -f envs/${ENV_D}/deployment.yaml -n default

restart-app:
	kubectl rollout restart deploy/aoc-bot-${ENV_D}

deploy-all: deploy-config-map deploy-secret deploy-app

# Sync

all: docker-all deploy-all