# -*- coding: utf-8 -*-
import pytest

from truss_objects import Element, Truss


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
    return Element(connection(), material(), section())


@pytest.fixture(scope="module")
def element_list():
    return [[[0, 1], 4354354.1, 0.000235], [[0, 1], 4354354.1, 0.000235], [[0, 1], 4354354.1, 0.000235]]


@pytest.fixture(scope="module")
def node_list():
    return [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 1.0]]

