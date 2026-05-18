SHELL := /bin/bash
.PHONY: run run-top5 test sync lint typecheck clean sync-local

run:
	cd ~/bounty_swarm_pipeline/secbrain && source ../venv/bin/activate && python -m bridge run --top-n 3

run-top5:
	cd ~/bounty_swarm_pipeline/secbrain && source ../venv/bin/activate && python -m bridge run --top-n 5

test:
	cd ~/bounty_swarm_pipeline/secbrain && source ../venv/bin/activate && pytest secbrain/tests/ -v

lint:
	cd ~/bounty_swarm_pipeline/secbrain && source ../venv/bin/activate && ruff check secbrain/

typecheck:
	cd ~/bounty_swarm_pipeline/secbrain && source ../venv/bin/activate && mypy secbrain/secbrain/

sync:
	cd ~/bounty_swarm_pipeline/secbrain && git pull && source ../venv/bin/activate && pip install -e secbrain/

sync-local:
	@echo "WARNING: This will overwrite files in WSL (~/bounty_swarm_pipeline/secbrain/) with files from Windows host."
	@echo "Checking for uncommitted changes in WSL..."
	@cd ~/bounty_swarm_pipeline/secbrain && if [ -d .git ] && ! git diff --quiet; then echo 'ERROR: Uncommitted changes found in WSL. Commit or stash them first.'; exit 1; fi
	rsync -av --exclude 'venv' --exclude '.git' /mnt/c/Users/Michael/.gemini/antigravity/scratch/bounty_swarm_pipeline/secbrain/ ~/bounty_swarm_pipeline/secbrain/

clean:
	find ~/bounty_swarm_pipeline/secbrain -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; find ~/bounty_swarm_pipeline/secbrain -name '*.pyc' -delete 2>/dev/null; echo 'Clean done.'
