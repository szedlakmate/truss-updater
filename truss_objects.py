# -*- coding: utf-8 -*-
"""
Created on September 1 15:38 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

from copy import deepcopy
from read_input_file import read_structure_file


class Element(object):
    """
    * connection: [1. node, 2. node] where 1 -> 2
    * material: {number} E []
    * section: {number} [m^2]
    """
    def __init__(self, connection, material, section):
        if len(connection) == 2 and type(connection[0]) is int and type(connection[1]) is int:
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
    """
    Data model for structures

    * node: list of nodal coordinates [ 1.[X, Y, Z], 2.[X, Y, Z], ... ]
    * element: list of elements
        - connection [i, j]
        - material [E]
        - cross-section [m^2]
    """
    def __init__(self, node_list, element_list):
        # Reset error of the structure - according to the measurements
        self.error = 0

        # Build node list
        self.node = []
        for node in node_list:
            if type(node) is list and len(node) == 3 and type(node[0]) is float and type(node[1]) is float \
                    and type(node[2]) is float:
                self.node.append(node)
            else:
                raise TypeError('Nodal data is corrupt.\nType should be [float, float, float] but found:\n%s'
                                % str(node))
        # Build element list
        self.element = []
        for element in element_list:
            self.element.append(Element(element[0], element[1], element[2]))


class Boundaries(object):
    """
    * support [DOF ID] - Only rigid supports
    """
    def __init__(self, support_list):
        self.supports = support_list
        for support in support_list:
            if not(type(support) is list and len(support) == 2 and type(support[0]) is int and type(support[1]) is float):
                raise TypeError('support data is corrupt. Type should be [int, float] but found:\n%s' % str(support))


class Loads(object):
    """
    Load model
    """
    def __init__(self, loads):
        """
        :param loads:
            * displacements: [ID, displacement m] - DOF ID
            * forces: [ID, force KN] - DOF ID
            * stresses: [ID, stress] - element ID
        """

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


class Measurements(object):
    """
    * displacements [ID, displacement m] - DOF ID
    * forces [ID, force KN] - DOF ID
    """
    def __init__(self):
        self.displacements = [[None, None]] * 0
        self.forces = [[None, None]] * 0


class Solution(object):
    """
    * displacement [ID, displacement m] - DOF ID
    * node: list of nodal coordinates [ 1.[X, Y, Z], 2.[X, Y, Z], ... ]
    * reaction [ID, force KN] - DOF ID
    * stress [ID, stress] - element ID
    """
    def __init__(self, number_of_nodes):
        self.displacement = [None] * number_of_nodes * 3
        self.node = [[None, None, None]] * number_of_nodes
        self.reactions = [[None, None]] * 0
        self.stress = [[None, None]] * 0


class Truss(object):
    """
    """
    def __init__(self, input_file, title):
        # Labeling object
        if title == '':
            title = input_file
        self.title = title.replace('.str', '')  # Name of the structure

        # Reading structural data, boundaries and loads
        (node_list, element_list, boundaries, loads) = read_structure_file("%s.str" % input_file)

        # Setting up basic structure
        self.original = StructuralData(node_list, element_list)

        # Initiating updated structure
        self.updated = deepcopy(self.original)

        # Setting up boundaries
        self.boundaries = Boundaries(boundaries)

        # Setting up loads
        self.loads = Loads(loads)

        # Solve structure
        self.solve('original')

        # Start model updating
        self.start_model_updating()

    def calculate_stiffness_matrix(self, version):
        print('Calculate %s stiffness matrix' % version)
        pass

    def solve(self, version):
        # Calculate stiffness-matrix
        self.calculate_stiffness_matrix(version)

        print('Solve %s structure' % version)

        pass

    def start_model_updating(self):
        loop_counter = 0
        while True and loop_counter < 10:
            loop_counter += 1

            # Read sensors
            self.perceive()

            # Set new boundaries
            self.apply_new_boundaries()

            # Refine/update forces
            self.apply_new_forces()

            # Calculate refreshed and/or updated models
            self.solve('original')
            self.solve('updated')

            if self.should_reset() is False:
                self.updated = deepcopy(self.update())
            else:
                self.updated = deepcopy(self.original)
                print('Reset structure')


    def perceive(self):
        pass

    def apply_new_boundaries(self):
        pass

    def apply_new_forces(self):
        pass

    def should_reset(self):
        return False

    def update(self):
        return self.compile(self.guess())

    def guess(self):
        return None

    def compile(self, guess):
        return self.original