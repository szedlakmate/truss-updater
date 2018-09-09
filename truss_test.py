# -*- coding: utf-8 -*-
"""
Created on September 9 18:28 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

import pytest

from truss_objects import *


class TestClassInitialization(object):
    def test_element(self):
        new_element = Element([0, 1], 0.0, 0.0)

        assert new_element.connection == [0, 1]
        assert new_element.material == 0.0
        assert new_element.section == 0.0

    def test_element_type_error(self):
        with pytest.raises(TypeError):
            Element([0, 1], 0.0, 0)

        with pytest.raises(TypeError):
            Element([0, 1], 0, 0.0)

        with pytest.raises(TypeError):
            Element([0.0, 1], 0, 0.0)

        with pytest.raises(TypeError):
            Element([0, 1.0], 0, 0.0)

    def test_element_invalid_coordinate(self):
        with pytest.raises(ValueError):
            Element([0, 0], 0.0, 0.0)

