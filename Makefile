# The gate for this repo. A green local run covers the checks on the
# local Python version only. CI runs the check target word for word
# on both configured Python versions and adds one job with no local
# step, the DCO trailer check.

PYTHON ?= python3

.PHONY: check test

check:
	$(PYTHON) -m unittest discover -s tests
	$(PYTHON) scripts/check_skill.py
	$(PYTHON) scripts/check_copy.py
	$(PYTHON) scripts/smoke_extract.py

test: check
