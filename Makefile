.PHONY: setup dev test e2e eval eval-fast train gen-types fixtures scan-mcp-output demo demo-docker _demo-api lint accept conformance security

ROOT := $(abspath .)
API_DIR := $(ROOT)/apps/api
WEB_DIR := $(ROOT)/apps/web
export PYTHONPATH := $(API_DIR)/src:$(ROOT)

UV ?= uv
PNPM ?= pnpm

setup:
	@command -v $(UV) >/dev/null || (echo "Install uv: https://github.com/astral-sh/uv" && exit 1)
	@command -v $(PNPM) >/dev/null || (echo "Install pnpm: https://pnpm.io/installation" && exit 1)
	$(UV) python install 3.11
	cd $(API_DIR) && $(UV) sync --python 3.11
	cd $(ROOT) && $(PNPM) install
	cd $(ROOT) && $(UV) --directory $(API_DIR) run python $(ROOT)/scripts/seed_eval_data.py
	@if [ ! -f $(ROOT)/.env ]; then cp $(ROOT)/.env.example $(ROOT)/.env; fi
	$(MAKE) train
	@echo "Setup complete. For e2e: cd apps/web && pnpm exec playwright install chromium"
	@echo "For make demo / make dev Redis: Docker required (docker compose)."

dev:
	docker compose up -d redis
	cd $(API_DIR) && $(UV) run uvicorn promptshield.api.app:app --reload --host 127.0.0.1 --port 8000 & \
	cd $(WEB_DIR) && $(PNPM) dev

test:
	cd $(API_DIR) && $(UV) run pytest -q
	@if [ -f $(WEB_DIR)/package.json ]; then cd $(WEB_DIR) && $(PNPM) test --if-present; fi

e2e:
	cd $(WEB_DIR) && $(PNPM) exec playwright test

eval:
	cd $(ROOT) && $(UV) --directory $(API_DIR) run python $(ROOT)/eval/run_eval.py --full

eval-fast:
	cd $(ROOT) && $(UV) --directory $(API_DIR) run python $(ROOT)/eval/run_eval.py --fast

train:
	cd $(ROOT) && $(UV) --directory $(API_DIR) run python $(ROOT)/eval/train_classifier.py

gen-types:
	cd $(API_DIR) && $(UV) run python -c "from promptshield.api.app import app; import json; print(json.dumps(app.openapi()))" > $(ROOT)/packages/shared-types/openapi.json
	cd $(ROOT)/packages/shared-types && $(PNPM) run gen

fixtures:
	cd $(ROOT) && $(UV) --directory $(API_DIR) run python $(ROOT)/scripts/generate_fixtures.py
	cd $(ROOT) && $(UV) --directory $(API_DIR) run python $(ROOT)/scripts/generate_binary_fixtures.py

scan-mcp-output:
	@test -n "$(FILE)" || (echo "Usage: make scan-mcp-output FILE=path.txt" && exit 1)
	cd $(API_DIR) && $(UV) run python -c "from promptshield.pipeline import scan_text; import pathlib; print(scan_text(pathlib.Path('$(FILE)').read_text()).model_dump_json(indent=2))"

# Non-Docker demo (default): API + web on the host. Docker path: `make demo-docker`.
# PYTHONPATH is exported above so `uv run uvicorn promptshield…` resolves the package.
demo: setup
	@echo "Non-Docker demo path (no Compose required):"
	@echo "  Terminal A: make -C $(ROOT) _demo-api   # or: cd apps/api && uv run uvicorn promptshield.api.app:app --reload --host 127.0.0.1 --port 8000"
	@echo "  Terminal B: cd apps/web && $(PNPM) dev"
	@echo "  Open http://localhost:3000/arena"
	@echo "Verified: POST /v1/scan against host API (see docs/FRESH_CLONE.md)."
	@echo "Docker (when daemon unpaused): make demo-docker"

_demo-api:
	cd $(API_DIR) && $(UV) run uvicorn promptshield.api.app:app --reload --host 127.0.0.1 --port 8000

demo-docker: setup
	docker compose up -d
	@echo "Open http://localhost:3000/arena"

lint:
	cd $(API_DIR) && $(UV) run ruff check src tests || true

# Measured README conformance (writes docs/CONFORMANCE.md; non-zero on FAIL).
conformance:
	cd $(ROOT) && $(UV) --directory $(API_DIR) run python $(ROOT)/eval/conformance_audit_v20.py

# End-to-end acceptance from host (no Docker). Non-zero on any failure. Writes docs/ACCEPT_RUN.md.
accept:
	cd $(ROOT) && $(UV) --directory $(API_DIR) run python $(ROOT)/scripts/accept_v20.py

purge:
	cd $(API_DIR) && PYTHONPATH=src $(UV) run python -c "from promptshield.api.persist import purge; print(purge())"

security:
	cd $(API_DIR) && $(UV) run pytest -q tests/test_product_security.py tests/test_whitetext_pack.py tests/test_image_agent_taint.py
	cd $(ROOT) && $(UV) --directory $(API_DIR) run python $(ROOT)/scripts/security_scan.py
