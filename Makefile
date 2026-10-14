# CarbonKheti Platform Makefile
.PHONY: all dev seed-sandbox test verify build clean

all: verify

dev:
	npm run dev

seed-sandbox:
	python -m services.api.db.seed_sandbox

test:
	python packages/facts/verify_facts.py
	python -m pytest tests/ -v

build:
	npm run build

verify:
	python services/verify_all.py

clean:
	python -c "import shutil, os; [shutil.rmtree(p, ignore_errors=True) for p in ['dist', '.pytest_cache', '__pycache__']]"
