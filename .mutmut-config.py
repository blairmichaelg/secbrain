# Mutmut Configuration for SecBrain
# Mutation testing verifies the quality of test suites by introducing bugs
# Documentation: https://mutmut.readthedocs.io/

# This file is read by mutmut but follows TOML syntax
# Note: mutmut uses a custom config format, not standard Python

[mutmut]
# Test command to run after each mutation
runner = "pytest -x -q"

# Test discovery pattern
tests_dir = "secbrain/tests/"
