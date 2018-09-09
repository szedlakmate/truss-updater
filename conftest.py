# -*- coding: utf-8 -*-
import pytest

from truss_objects import Element


@pytest.fixture(scope="module")
def connection():
    return [0, 1]


@pytest.fixture(scope="module")
def material():
    return 1321432.12


@pytest.fixture(scope="module")
def section():
    return 0.000034


@pytest.fixture(scope="module")
def element():
    return Element([0, 1], 13145346465.000, 0.0000043)
