# The gate for this repo. CI runs the check target word for word,
# so a green local run is the whole contract.

PYTHON ?= python3

.PHONY: check test

check:
	$(PYTHON) -m unittest discover -s tests
	$(PYTHON) scripts/check_skill.py
	$(PYTHON) scripts/check_copy.py
	$(PYTHON) scripts/smoke_extract.py

test: check
