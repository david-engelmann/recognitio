# The gate for this repo. A green local run covers the checks on the
# local Python version only. CI runs the check target word for word
# on both configured Python versions and adds one job with no local
# step, the DCO trailer check.

PYTHON ?= python3

.PHONY: check test

check:
	$(PYTHON) -m unittest discover -s tests
	$(PYTHON) scripts/check_skill.py
	$(PYTHON) scripts/check_version.py
	$(PYTHON) scripts/check_copy.py
	$(PYTHON) scripts/check_evals.py
	$(PYTHON) scripts/check_persona.py
	$(PYTHON) scripts/check_fanout.py
	$(PYTHON) scripts/check_mod.py
	$(PYTHON) scripts/check_package.py
	$(PYTHON) scripts/check_codex.py
	$(PYTHON) scripts/check_cursor.py
	$(PYTHON) scripts/check_coderabbit.py
	$(PYTHON) scripts/check_antigravity.py
	$(PYTHON) scripts/check_copilot.py
	$(PYTHON) scripts/check_kimi.py
	$(PYTHON) scripts/check_test_vacuity.py
	$(PYTHON) scripts/smoke_extract.py

test: check
