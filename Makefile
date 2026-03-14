	# Variables
	VENV := venv
	PYTHON := $(VENV)/bin/python
	PIP := $(VENV)/bin/pip
	PYLINT := $(VENV)/bin/pylint
	MODULES_DIR := modules
	MAIN_SCRIPT := main.py


	# Create Virtual Environment
	venv:
		@echo "Creating virtual environment..."
		python3 -m venv $(VENV)

	# Install Dependencies
	install: venv
		@echo "Installing packages from requirements.txt..."
		$(PIP) install --upgrade pip
		$(PIP) install -r requirements.txt

	# Code Quality Analysis
	lint: install
		@echo "Running Pylint on modules and main script..."
		$(PYLINT) $(MAIN_SCRIPT) $(MODULES_DIR)/*.py --disable=C0114,C0115,C0116

	# Run Unit Tests
	test:
		@echo "Running unit tests..."
		$(PYTHON) -m unittest discover -s modules/tests


	# Clean Environment
	clean:
		@echo "Removing virtual environment and temporary files..."
		rm -rf $(VENV)
		rm -rf __pycache__
		rm -rf $(MODULES_DIR)/__pycache__
		rm -f *.png
		rm -f *.json
		rm -f *.pdf
