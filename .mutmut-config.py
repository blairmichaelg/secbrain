# Mutmut Configuration for SecBrain
# Mutation testing verifies the quality of test suites by introducing bugs
# Documentation: https://mutmut.readthedocs.io/

[mutmut]
# Test command to run after each mutation
runner = pytest -x -q

# Test discovery pattern
tests_dir = secbrain/tests/
