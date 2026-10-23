# Planted defects for task-01

Title. A required parameter is added to a priced function

Grader only. Do not read this file during either review pass.

## D1 (packet)

shop.py still calls price with two arguments at its total function, so the new required tax parameter makes that call raise TypeError. A pass finds this only when it names shop.py and its two argument call.

## D2 (diff)

The tax is added twice in the new return line of calc.py, so every price is overcharged by one tax amount. The line sits in the diff itself.
