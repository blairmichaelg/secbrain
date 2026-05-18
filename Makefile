SHELL := /bin/bash
WSL_DIR := $(HOME)/bounty_swarm_pipeline/secbrain
WIN_SRC := /mnt/c/Users/Michael/.gemini/antigravity/scratch/bounty_swarm_pipeline/secbrain
.PHONY: run run-top5 test sync lint typecheck clean sync-local

run:
	cd $(WSL_DIR) && source ../venv/bin/activate && python -m bridge run --top-n 3

run-top5:
	cd $(WSL_DIR) && source ../venv/bin/activate && python -m bridge run --top-n 5

test:
	cd $(WSL_DIR) && source ../venv/bin/activate && pytest secbrain/tests/ -v

lint:
	cd $(WSL_DIR) && source ../venv/bin/activate && ruff check secbrain/

typecheck:
	cd $(WSL_DIR) && source ../venv/bin/activate && mypy secbrain/secbrain/

sync:
	cd $(WSL_DIR) && git pull && source ../venv/bin/activate && pip install -e secbrain/

sync-local:
	@echo "WARNING: This will overwrite files in WSL ($(WSL_DIR)/) with files from Windows host."
	@echo "Checking for uncommitted changes in WSL..."
	@cd $(WSL_DIR) && \
	  git diff --exit-code --quiet && \
	  git diff --cached --exit-code --quiet || \
	  (echo "ERROR: WSL has uncommitted changes. Commit or stash first."; exit 1)
	rsync -av --delete --exclude 'venv' --exclude '.git' $(WIN_SRC)/ $(WSL_DIR)/

clean:
	find $(WSL_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; find $(WSL_DIR) -name '*.pyc' -delete 2>/dev/null; echo 'Clean done.'
