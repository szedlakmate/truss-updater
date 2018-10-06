# -*- coding: utf-8 -*-
"""
Created on September 1 15:38 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

import math
import os


def setup_folder(directory):
    """
    :param directory: folder name to be checked
    :return: None
    """
    path = str(os.path.dirname('./')) + '/' + directory.replace('/', '').replace('.', '') + '/'

    if not os.path.exists(path):
        os.makedirs(path)


def element_length(structure, index):
    """
    Returns the length of the index-th element in a Structure

    :param structure: Structure object
    :param index: the index of the target element
    :return: the length of the index-th element
    """
    return math.sqrt(sum([(j - k) ** 2 for j, k
                          in zip(structure.node[structure.element[index].connection[1]],
                                 structure.node[structure.element[index].connection[0]])]))


class Element(object):
    def __init__(self, connection, material, section):
        """
        Element model

        :param connection: [1. node, 2. node] where 1 -> 2
        :param material: E []
        :param section: cross-sectional area [m^2]
        """
        if len(connection) == 2 and type(connection[0]) is int and type(connection[1]) is int:
            if connection[0] == connection[1]:
                raise ValueError('Connection start-end should not match: %s' % str(connection))
            self.connection = connection
        else:
            raise TypeError('connection data is corrupt. Type should be [int, int] but found:\n%s' % str(connection))

        if type(material) is float:
            self.material = material
        else:
            raise TypeError('material data should be float but got:\n%s %s' % (material, type(material)))

        if type(section) is float:
            self.section = section
        else:
            raise TypeError('section data should be float but got:\n%s %s' % (section, type(section)))


class StructuralData(object):
    def __init__(self, node_list, element_list, label=''):
        """
        Data model for structures

        :param node_list: list of nodal coordinates [ 1.[X, Y, Z], 2.[X, Y, Z], ... ]
        :param element_list: list of elements
        - connection [i, j]
        - material [E]
        - cross-section [m^2]
        :param label: title of the structure
        """
        self.error = 0
        self.label = label

        # Build node list
        self.node = []
        for node in node_list:
            if type(node) is list and len(node) == 3:
                self.node.append(node)
            else:
                raise TypeError('Nodal data is corrupt.\nType should be [float, float, float] but found:\n%s as %s'
                                % (str([type(x) for x in node]), str(node)))
        # Build element list
        self.element = []
        for element in element_list:
            self.element.append(Element(element[0], element[1], element[2]))

    def generate_coordinate_list(self):
        """
        Extracts coordinate list from Structure element

        :return: [1. connection [1. node [X, Y, Z], 2. node [X, Y, Z]], 2. connection [[], []], ...]
        """
        return [[self.node[x.connection[0]], self.node[x.connection[1]]] for x in self.element]


class Boundaries(object):
    def __init__(self, support_list):
        """
        Support model

        :param support_list: [DOF ID, displacement] - Only rigid supports (displacement = 0 by default)
        """
        self.supports = support_list
        for support in support_list:
            if not(type(support) is list and len(support) == 2 and
                   type(support[0]) is int and type(support[1]) is float):
                raise TypeError('support data is corrupt. Type should be [int, float] but found:\n%s' % str(support))


class Loads(object):
    def __init__(self, loads):
        """
        Load model

        :param loads:
            * displacements: [ID, displacement m] - DOF ID - NOT IMPLEMENTED
            * forces: [ID, force KN] - DOF ID
            * stresses: [ID, stress] - element ID - NOT IMPLEMENTED
        """
        # TODO: implement displacements and stresses as loads

        self.displacements = []
        if 'displacements' in loads:
            for displacement in loads['displacements']:
                if type(displacement) is list and len(displacement) == 2 and type(displacement[0]) is int \
                        and type(displacement[1]) is float:
                    self.displacements.append(displacement)
                else:
                    raise TypeError(
                        'displacement data is corrupt. Type should be [int, float] but found:\n%s' % str(displacement))

        self.forces = []
        if 'forces' in loads:
            for force in loads['forces']:
                if type(force) is list and len(force) == 2 and type(force[0]) is int and type(force[1]) is float:
                    self.forces.append(force)
                else:
                    raise TypeError(
                        'force data is corrupt. Type should be [int, float] but found:\n%s' % str(force))

        self.stresses = []
        if 'stresses' in loads:
            for stress in loads['stresses']:
                if type(stress) is list and len(stress) == 2 and type(stress[0]) is int and type(stress[1]) is float:
                    self.stresses.append(stress)
                else:
                    raise TypeError(
                        'stress data is corrupt. Type should be [int, float] but found:\n%s' % str(stress))


class Solution(object):
    """
    Solution container model

    * displacement [DOF ID, displacement m]
    * node: list of nodal coordinates [ 1.[X, Y, Z], 2.[X, Y, Z], ... ]
    * reaction [ID, force KN] - DOF ID
    * stress [ID, stress] - element ID
    """
    # TODO: refactor to result a Structure instead of non-standard arrays
    def __init__(self, number_of_nodes):
        """
        :param number_of_nodes: used for vector length calculation
        """
        self.displacement = [None] * number_of_nodes * 3
        self.node = [[None, None, None]] * number_of_nodes
        self.reactions = [[None, None]] * 0
        self.stress = [[None, None]] * 0
