.PHONY: run run-top5 test sync lint typecheck clean

run:
	wsl bash -c "cd ~/bounty_swarm_pipeline/secbrain && source ../venv/bin/activate && python -m bridge run --top-n 3"

run-top5:
	wsl bash -c "cd ~/bounty_swarm_pipeline/secbrain && source ../venv/bin/activate && python -m bridge run --top-n 5"

test:
	wsl bash -c "cd ~/bounty_swarm_pipeline/secbrain && source ../venv/bin/activate && pytest secbrain/tests/ -v"

lint:
	wsl bash -c "cd ~/bounty_swarm_pipeline/secbrain && source ../venv/bin/activate && ruff check secbrain/"

typecheck:
	wsl bash -c "cd ~/bounty_swarm_pipeline/secbrain && source ../venv/bin/activate && mypy secbrain/secbrain/"

sync:
	wsl bash -c "cd ~/bounty_swarm_pipeline/secbrain && git pull && source ../venv/bin/activate && pip install -e secbrain/"

sync-local:
	wsl bash -c "rsync -av --exclude 'venv' --exclude '.git' /mnt/c/Users/Michael/.gemini/antigravity/scratch/bounty_swarm_pipeline/secbrain/ ~/bounty_swarm_pipeline/secbrain/"

clean:
	wsl bash -c "find ~/bounty_swarm_pipeline/secbrain -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; find ~/bounty_swarm_pipeline/secbrain -name '*.pyc' -delete 2>/dev/null; echo 'Clean done.'"
