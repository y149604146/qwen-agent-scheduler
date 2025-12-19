"""Test to verify pytest and Hypothesis setup"""

import pytest
from hypothesis import given, strategies as st


def test_basic_pytest():
    """Basic pytest test to verify setup"""
    assert True


@pytest.mark.property
@given(x=st.integers())
def test_hypothesis_setup(x):
    """Basic Hypothesis test to verify property-based testing setup"""
    # Property: any integer plus zero equals itself
    assert x + 0 == x
