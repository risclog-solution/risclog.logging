# Makefile
# Fetch upstream appenv.py and (optionally) overwrite local root scripts.

SHELL := /bin/sh

APPENV_UPSTREAM_URL := https://raw.githubusercontent.com/flyingcircusio/appenv/master/src/appenv.py
APPENV_CACHE_DIR := .vendor
APPENV_CACHE_FILE := $(APPENV_CACHE_DIR)/appenv.py

# Root-level script names to overwrite *if they already exist*.
OVERWRITE_IF_PRESENT := alembic pytest appenv uvicorn main

.PHONY: help appenv-fetch appenv-overwrite appenv-sync appenv-diff

help:
	@echo "Targets:"
	@echo "  appenv-fetch      Download upstream appenv.py into $(APPENV_CACHE_FILE)"
	@echo "  appenv-overwrite  Overwrite existing root files: $(OVERWRITE_IF_PRESENT) (only if present)"
	@echo "  appenv-sync       Convenience target: appenv-fetch + appenv-overwrite"
	@echo "  appenv-diff       Show a unified diff between existing root files and cached appenv.py"

$(APPENV_CACHE_DIR):
	@mkdir -p "$(APPENV_CACHE_DIR)"

appenv-fetch: $(APPENV_CACHE_DIR)
	@echo "Fetching $(APPENV_UPSTREAM_URL) -> $(APPENV_CACHE_FILE)"
	@curl -fsSL "$(APPENV_UPSTREAM_URL)" -o "$(APPENV_CACHE_FILE)"
	@chmod +x "$(APPENV_CACHE_FILE)"

appenv-overwrite: appenv-fetch
	@set -eu; \
	for f in $(OVERWRITE_IF_PRESENT); do \
		if [ -e "$$f" ]; then \
			echo "Overwriting ./$$f"; \
			cp "$(APPENV_CACHE_FILE)" "$$f"; \
			chmod +x "$$f" || true; \
		else \
			echo "Skipping ./$$f (not present)"; \
		fi; \
	done

appenv-sync: appenv-fetch appenv-overwrite

appenv-diff: appenv-fetch
	@set -eu; \
	for f in $(OVERWRITE_IF_PRESENT); do \
		if [ -e "$$f" ]; then \
			echo "==== diff ./$$f vs $(APPENV_CACHE_FILE) ===="; \
			diff -u "$$f" "$(APPENV_CACHE_FILE)" || true; \
		else \
			echo "Skipping ./$$f (not present)"; \
		fi; \
	done
