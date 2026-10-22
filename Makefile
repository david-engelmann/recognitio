# The gate for this repo. CI runs the check target word for word and
# adds one job with no local step, the DCO trailer check, so a green
# local run covers everything except that trailer check.

PYTHON ?= python3

.PHONY: check test

check:
	$(PYTHON) -m unittest discover -s tests
	$(PYTHON) scripts/check_skill.py
	$(PYTHON) scripts/check_copy.py
	$(PYTHON) scripts/smoke_extract.py

test: check
