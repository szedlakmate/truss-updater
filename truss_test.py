# -*- coding: utf-8 -*-
"""
Created on September 9 18:28 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

import pytest

from truss_objects import *


class TestClassInitializations(object):
    """Test Element class"""
    def test_element(self, connection, material, section):
        new_element = Element(connection, material, section)

        assert new_element.connection == connection
        assert new_element.material == material
        assert new_element.section == section

    def test_element_type_error(self, connection, material, section):
        """Test element constructor"""
        with pytest.raises(TypeError):
            Element(connection, material, 0)

        with pytest.raises(TypeError):
            Element(connection, 0, section)

        with pytest.raises(TypeError):
            Element([0.0, 1], material, section)

        with pytest.raises(TypeError):
            Element([0, 1.0], material, section)

    def test_element_invalid_connection(self, material, section):
        """Test element constructor - connection"""
        with pytest.raises(ValueError):
            Element([0, 0], material, section)

    def test_structure(self, node_list, element_list):
        """Test StructuralData class"""
        new_structure = StructuralData(node_list, element_list)

        assert new_structure.node == node_list
        assert new_structure.element[0].connection == element_list[0][0]
        assert new_structure.element[0].material == element_list[0][1]
        assert new_structure.element[0].section == element_list[0][2]

    def test_structure_type_error(self, node_list, element_list):
        """Test StructuralData constructor"""
        with pytest.raises(TypeError):
            StructuralData([0.1], element_list)

        with pytest.raises(TypeError):
            StructuralData([[0.1, 0.1]], element_list)

        with pytest.raises(TypeError):
            StructuralData([[0.1, 0.1, 0.1, 0.1]], element_list)

        with pytest.raises(TypeError):
            StructuralData(node_list, [1.0])


class TestStaticCalculations(object):
    def test_element_length(self, BRIDGE):
        """Test element length calculation"""
        assert element_length(BRIDGE.original, 0) == 158.11388300841898

    def test_error(self, bridge_displacement):
        """Test error calculation"""
        assert error([[0, 0.0]], bridge_displacement) == 0.0
        assert error([[3, 0.0]], bridge_displacement) == 0.7777777777784746
        assert error([[3, 0.7777777777784746]], bridge_displacement) == 0.0
        assert error([[3, 0.0], [5, 2.0]], bridge_displacement) == math.sqrt(0.7777777777784746**2 + 2**2)


class TestBridgeCalculations(object):
    """Test stiffness matrix compilation"""
    def test_stiffness_matrix_calculation(self, BRIDGE_STIFFNESS_MATRIX):
        Bridge = Truss('bridge.str', 'test', ['11Y'])
        new_stiffness_matrix = calculate_stiffness_matrix(Bridge.original)

        assert new_stiffness_matrix == BRIDGE_STIFFNESS_MATRIX

    def test_2d_structural_z_displacement(self):
        """Test whether 2D structures Z-displacement is blocked automatically"""
        bridge = Truss('bridge.str', 'test', ['11Y'])

        deformed = bridge.solve(bridge.original, bridge.boundaries, bridge.loads)

        z_total = sum([deformed['node'][x] if x % 3 == 2 else 0 for x in range(len(deformed['node']))])

        assert z_total == 0

    def test_should_reset(self, BRIDGE):
        """Test reset condition"""
        BRIDGE.original.error = 0
        BRIDGE.updated.error = 0
        assert BRIDGE.should_reset() is False

        BRIDGE.original.error = 1
        BRIDGE.updated.error = 0
        assert BRIDGE.should_reset() is False

        BRIDGE.original.error = 0
        BRIDGE.updated.error = 1
        assert BRIDGE.should_reset() is True

    def test_update_is_better(self, BRIDGE):
        """Test first update for BRIDGE"""
        BRIDGE.start_model_updating(1)
        assert BRIDGE.should_reset() is False
        assert BRIDGE.original.error > BRIDGE.updated.error
