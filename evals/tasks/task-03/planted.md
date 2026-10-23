# Planted defects for task-03

Title. A helper is renamed and its separator changes

Grader only. Do not read this file during either review pass.

## D1 (packet)

legacy.py still defines the old slugify name with the old hyphen behaviour, so the repo now holds two slug makers that disagree and any user of the legacy one keeps the old output. A pass finds this only when it names legacy.py and its surviving definition.

## D2 (diff)

Spaces are deleted instead of turned into hyphens in the new make_slug return line, so multi word headings collapse into one word. The line sits in the diff itself.
