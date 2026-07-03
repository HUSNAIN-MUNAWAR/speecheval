SHELL := /bin/bash
.PHONY: bootstrap api web worker test lint format demo seed db-migrate db-reset docker-up docker-down logs
bootstrap:
	python -m venv .venv
	. .venv/bin/activate && pip install -e "backend[dev]"
	cd apps/web && npm install
api:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
web:
	cd apps/web && npm run dev
worker:
	cd backend && if [ "$${SPEECHEVAL_QUEUE_MODE:-inline}" = "dramatiq" ]; then dramatiq app.workers.tasks --processes 1 --threads 1; else python -m app.workers.worker; fi
test:
	cd backend && pytest -q
	cd apps/web && npm run test
lint:
	cd backend && ruff check . && mypy app
	cd apps/web && npm run typecheck
format:
	cd backend && ruff format .
	cd apps/web && npm run format
seed:
	cd backend && python -m app.db.seed
demo: seed
	@echo "Demo seed completed. Start make api and make web."
db-migrate:
	cd backend && alembic upgrade head
db-reset:
	rm -f backend/.data/speecheval.db
	$(MAKE) seed
docker-up:
	docker compose up --build
docker-down:
	docker compose down
logs:
	docker compose logs -f --tail=150
