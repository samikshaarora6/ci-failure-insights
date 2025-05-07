import random
import pytest

# This test always passes
def test_pass():
    assert True

# This test has a 50% chance of failure
@pytest.mark.parametrize("value", [random.randint(0, 1) for _ in range(10)])
def test_random_failure(value):
    assert value == 0  # will fail half the time

# This test will fail if the number is odd
def test_fail_if_odd():
    number = random.randint(1, 100)
    assert number % 2 == 0  # fails if the number is odd

# A hard-coded failure
def test_hard_coded_fail():
    assert False  # This will always fail
