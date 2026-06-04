.PHONY: help install install-dev test test-cov clean lint format version release dev-env

# Get version from pyproject.toml
VERSION := $(shell python3 -c "import re; f=open('pyproject.toml'); content=f.read(); match=re.search(r'version\s*=\s*\"([^\"]+)\"', content); print(match.group(1) if match else '0.1.0')")

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	pip install .

install-dev: ## Install the package with dev dependencies
	pip install -e ".[dev]"

dev-env: ## Create development environment and install dependencies
	@echo "Creating development environment..."
	python3 -m venv venv
	@echo "Installing dependencies..."
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -e ".[dev]"
	@echo "Virtual environment created and dependencies installed!"
	@echo "Activate it with: source venv/bin/activate"

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=ohdsi_vocabulary --cov-report=html --cov-report=term

test-fast: ## Run tests without coverage (faster)
	pytest tests/ -v --no-cov

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

lint: ## Run linter
	ruff check ohdsi_vocabulary/ tests/

format: ## Format code
	black ohdsi_vocabulary/ tests/
	ruff check --fix ohdsi_vocabulary/ tests/

format-check: ## Check code formatting
	black --check ohdsi_vocabulary/ tests/
	ruff check ohdsi_vocabulary/ tests/

version: ## Show current version
	@echo "Current version: $(VERSION)"

release: ## Create a release (update version in pyproject.toml first)
	@echo "Current version: $(VERSION)"
	@read -p "Enter new version (current: $(VERSION)): " new_version; \
	if [ -z "$$new_version" ]; then \
		echo "Version not provided. Exiting."; \
		exit 1; \
	fi; \
	sed -i '' "s/version = \"$(VERSION)\"/version = \"$$new_version\"/" pyproject.toml; \
	sed -i '' "s/version=\"$(VERSION)\"/version=\"$$new_version\"/" setup.py; \
	echo "Version updated to $$new_version"; \
	echo "Creating git tag..."; \
	git add pyproject.toml setup.py; \
	git commit -m "Bump version to $$new_version" || true; \
	git tag -a "v$$new_version" -m "Release v$$new_version"; \
	echo "Pushing changes and tags to GitHub..."; \
	git push && git push --tags; \
	echo "Release v$$new_version created and pushed to GitHub!"

release-check: ## Check if ready for release
	@echo "Checking release readiness..."
	@echo "Version: $(VERSION)"
	@echo "Running tests..."
	@make test > /dev/null 2>&1 && echo "✓ Tests pass" || (echo "✗ Tests fail" && exit 1)
	@echo "Running lint..."
	@make lint > /dev/null 2>&1 && echo "✓ Lint passes" || (echo "✗ Lint fails" && exit 1)
	@echo "All checks passed! Ready for release."

check: ## Run all checks (lint, format-check, test)
	@echo "Running all checks..."
	@make lint
	@make format-check
	@make test

ci: ## Run CI checks (same as check)
	@make check
