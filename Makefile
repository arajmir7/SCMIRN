COMPOSE_FILE=infrastructure/docker-compose.yml
SCMIRN_ENV_FILE ?= .env.production

.PHONY: up down build logs restart ps test-backend test-ai verify-local release-gate production-config

up:
	docker compose -f $(COMPOSE_FILE) up -d --build

down:
	docker compose -f $(COMPOSE_FILE) down

build:
	docker compose -f $(COMPOSE_FILE) build

logs:
	docker compose -f $(COMPOSE_FILE) logs -f --tail=200

restart:
	docker compose -f $(COMPOSE_FILE) down
	docker compose -f $(COMPOSE_FILE) up -d --build

ps:
	docker compose -f $(COMPOSE_FILE) ps

test-backend:
	python -m pytest -q -p no:cacheprovider src/backend/tests

test-ai:
	python -m pytest -q -p no:cacheprovider src/ai-service/tests

production-config:
	python3 scripts/validate_production_config.py --env-file "$(SCMIRN_ENV_FILE)"

verify-local:
	python -m pytest -q -p no:cacheprovider src/backend/tests
	cd src/frontend && npm run typecheck && npm run build && npm run test:e2e
	python scripts/check_feature_parity.py
	python scripts/validate_openapi_contract.py

release-gate:
	bash scripts/release_gate.sh
