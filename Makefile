# Variables
VENV         := .venv
PYTHON       := $(VENV)/bin/python
PIP          := $(VENV)/bin/pip
REQUIREMENTS := requirements.txt

# Default target: sets up the environment and installs packages
all: venv install

# 1. Create the virtual environment
venv:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)

# 2. Install pip packages
install: venv
	@if [ -f $(REQUIREMENTS) ]; then \
		echo "Installing dependencies from $(REQUIREMENTS)..."; \
		$(PIP) install --upgrade pip; \
		$(PIP) install -r $(REQUIREMENTS); \
	else \
		echo "Warning: $(REQUIREMENTS) not found. Skipping installation."; \
	fi

# 3. Clean the virtual environment
clean:
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	@echo "Cleanup complete."

# Prevent conflicts with files named 'venv', 'install', or 'clean'
.PHONY: all venv install clean
