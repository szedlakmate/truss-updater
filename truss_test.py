# -*- coding: utf-8 -*-
"""
Created on September 9 18:28 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

import pytest

from truss_objects import *


class TestClassInitialization(object):

    def test_element(self, connection, material, section):
        new_element = Element(connection, material, section)

        assert new_element.connection == connection
        assert new_element.material == material
        assert new_element.section == section

    def test_element_type_error(self, connection, material, section):
        with pytest.raises(TypeError):
            Element(connection, material, 0)

        with pytest.raises(TypeError):
            Element(connection, 0, section)

        with pytest.raises(TypeError):
            Element([0.0, 1], material, section)

        with pytest.raises(TypeError):
            Element([0, 1.0], material, section)

    def test_element_invalid_coordinate(self, material, section):
        with pytest.raises(ValueError):
            Element([0, 0], material, section)
