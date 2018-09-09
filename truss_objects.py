# -*- coding: utf-8 -*-
"""
Created on September 1 15:38 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

from copy import deepcopy
import math

import numpy

from read_input_file import read_structure_file
from arduino_measurements import ArduinoMeasurements


def element_length(structure, index):
    return math.sqrt(sum([(j - k) ** 2 for j, k
                          in zip(structure.node[structure.element[index].connection[1]],
                                 structure.node[structure.element[index].connection[0]])]))


def error(measurements, calculated_displacements):
    """
    Error function using least-square method

    :param measurements: [[DOF ID, displacement], ...]
    :param calculated_displacements: [1. DOF's displacement, 2. DOF's displacement, ...]
    :return: summarized error (float)
    """
    sum_of_errors = 0
    for index in range(len(measurements)):
        sum_of_errors += (measurements[index][1] - calculated_displacements[measurements[index][0]])**2

    return math.sqrt(sum_of_errors)


def calculate_stiffness_matrix(structure):
    """
    Stiffness matrix compilation

    :param structure: pointer to a structure (original or updated)
    :return: (stiffness_matrix, known_f_a)
    """

    stiffness_matrix = [[0] * (len(structure.node) * 3)] * (len(structure.node) * 3)

    for i in range(len(structure.element)):
        _cx = (structure.node[structure.element[i].connection[1]][0] -
               structure.node[structure.element[i].connection[0]][0]) / element_length(structure, i)

        _cy = (structure.node[structure.element[i].connection[1]][1] -
               structure.node[structure.element[i].connection[0]][1]) / element_length(structure, i)

        _cz = (structure.node[structure.element[i].connection[1]][2] -
               structure.node[structure.element[i].connection[0]][2]) / element_length(structure, i)

        _norm_stiff = structure.element[i].material / element_length(structure, i)

        # local stiffness matrix calculation
        _s_loc = [[_cx ** 2, _cx * _cy, _cx * _cz, -_cx ** 2, -_cx * _cy, -_cx * _cz],
                  [_cx * _cy, _cy ** 2, _cy * _cz, -_cx * _cy, -_cy ** 2, -_cy * _cz],
                  [_cx * _cz, _cy * _cz, _cz ** 2, -_cx * _cz, -_cy * _cz, -_cz ** 2],
                  [-_cx ** 2, -_cx * _cy, -_cx * _cz, _cx ** 2, _cx * _cy, _cx * _cz],
                  [-_cx * _cy, -_cy ** 2, -_cy * _cz, _cx * _cy, _cy ** 2, _cy * _cz],
                  [-_cx * _cz, -_cy * _cz, -_cz ** 2, _cx * _cz, _cy * _cz, _cz ** 2]]

        local_stiffness_matrix = [[y * structure.element[i].section * _norm_stiff for y in x] for x in _s_loc]

        # Creating mapping tool for elements
        element_dof = []
        for element in structure.element:
            node = element.connection
            element_dof.append(
                [node[0] * 3, node[0] * 3 + 1, node[0] * 3 + 2, node[1] * 3, node[1] * 3 + 1, node[1] * 3 + 2])

        ele_dof_vec = element_dof[i]

        stiffness_increment = [0] * (len(structure.node) * 3)

        for j in range(3 * 2):
            for k in range(3 * 2):
                stiffness_increment[ele_dof_vec[k]] = local_stiffness_matrix[j][k]

            stiffness_matrix[ele_dof_vec[j]] = \
                [x + y for x, y in zip(stiffness_matrix[ele_dof_vec[j]], stiffness_increment)]

    return stiffness_matrix


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
        # Reset error of the structure - according to the measurements
        self.error = 0

        self.label = label

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


class Solution(object):
    """
    Solution container model

    * displacement [DOF ID, displacement m]
    * node: list of nodal coordinates [ 1.[X, Y, Z], 2.[X, Y, Z], ... ]
    * reaction [ID, force KN] - DOF ID
    * stress [ID, stress] - element ID
    """
    def __init__(self, number_of_nodes):
        """
        :param number_of_nodes: used for vector length calculation
        """
        self.displacement = [None] * number_of_nodes * 3
        self.node = [[None, None, None]] * number_of_nodes
        self.reactions = [[None, None]] * 0
        self.stress = [[None, None]] * 0
        self.measurement = None


class Truss(object):
    def __init__(self, input_file, title=''):
        """
        Main container

        :param input_file: file with structural data
        :param title: title of the project
        """
        # Labeling object
        if title == '':
            title = input_file
        self.title = title.replace('.str', '')  # Name of the structure

        # Reading structural data, boundaries and loads
        (node_list, element_list, boundaries, loads) = read_structure_file("%s.str" % input_file)

        # Setting up basic structure
        self.original = StructuralData(node_list, element_list)

        # Setting up boundaries
        self.boundaries = Boundaries(boundaries)

        # Setting up loads
        self.loads = Loads(loads)

        # Solve structure
        self.solve(self.original, self.boundaries, self.loads)

        # Initiating updated structure
        self.updated = deepcopy(self.original)

    def solver_helper(self, structure):
        # Setting known forces
        known_f_a = []
        known_f_not_zero = []
        known_displacement_a = []

        for location in range(len(structure.node) * 3):
            known_f_a.append(location)
            if location in [x[0] for x in self.loads.forces]:
                known_f_not_zero.append(location)

        for constraint in self.boundaries.supports:
            known_displacement_a.append(constraint[0])
            if constraint[0] in known_f_a:
                known_f_a.remove(constraint[0])

            if constraint[0] in known_f_not_zero:
                known_f_not_zero.remove(constraint[0])

        return {'known_f_a': known_f_a,
                'known_f_not_zero': known_f_not_zero,
                'known_displacement_a': known_displacement_a}

    def solve(self, structure, boundaries, loads):

        # Calculate stiffness-matrix
        stiffness_matrix = calculate_stiffness_matrix(structure)

        helper = self.solver_helper(structure)
        known_f_a = helper['known_f_a']

        constraints = deepcopy(boundaries.supports)

        forces = [0] * (len(structure.node) * 3 - len(constraints))
        for (dof, force) in deepcopy(loads.forces):
            forces[dof] = force

        # deepcopy(loads.forces)
        displacements = [0.0] * (len(structure.node) * 3)
        for (dof, displacement) in deepcopy(loads.displacements):
            displacements[dof] = displacement

        stiff_new = [[0.0] * (len(structure.node) * 3 - len(constraints))] * \
                    (len(structure.node) * 3 - len(constraints))

        stiffness_increment = [0.0] * (len(structure.node) * 3 - len(constraints))

        for i, kfai in enumerate(known_f_a):
            for j, kfaj in enumerate(known_f_a):
                stiffness_increment[j] = stiffness_matrix[kfai][kfaj]

            stiff_new[i] = [x + y for x, y in zip(stiff_new[i], stiffness_increment)]

        # SOLVING THE STRUCTURE
        dis_new = numpy.linalg.solve(numpy.array(stiff_new), numpy.array(forces))

        for i, known_f_a in enumerate(known_f_a):
            displacements[known_f_a] = dis_new[i]

        deformed = {'node': [], 'displacement': displacements}

        # Deformed shape
        for i in range(len(structure.node)):
            deformed['node'].extend([structure.node[i][0] + displacements[i * 3 + 0],
                                     structure.node[i][1] + displacements[i * 3 + 1],
                                     structure.node[i][2] + displacements[i * 3 + 2]])

        # solution = {'deformed': deformed, 'known_displacement_a': known_displacement_a, 'displacements': displacements}

        return deformed

    def post_process(self, truss, loads, boundaries, solution):

        stiffness_matrix = calculate_stiffness_matrix(truss)

        helper = self.solver_helper(truss)
        known_displacement_a = helper['known_displacement_a']

        # Calculates reaction forces and stresses
        for i in known_displacement_a:
            loads.forces[i] = 0
            for j, displacement in enumerate(solution.displacements):
                loads.forces[i] += stiffness_matrix[i][j]*displacement

        stress = []

        #s_max = max([abs(min(self.stress)), max(self.stress), 0.000000001])

        # TODO: Should be written out using a function
        #stress_color = [float(x)/float(s_max) for x in self.stress]

        #return stress_color

    def start_model_updating(self):
        loop_counter = 0

        self.measurement = ArduinoMeasurements([37])

        while True and loop_counter < 10:
            loop_counter += 1

            # Read sensors
            self.measurement.update()

            # Refine/update forces
            self.loads.forces = self.measurement.loads

            # Calculate refreshed and/or updated models
            solution_original = self.solve(self.original, self.boundaries, self.loads)
            solution_updated = self.solve(self.updated, self.boundaries, self.loads)

            # Calculate errors
            self.original.error = error(self.measurement.displacements, solution_original['displacement'])
            self.updated.error = error(self.measurement.displacements, solution_updated['displacement'])

            print('Error: %.2f' % self.updated.error)

            if self.should_reset() is False:
                self.updated = deepcopy(self.update())
            else:
                self.updated = deepcopy(self.original)
                print('Reset structure')

    def should_reset(self):
        should_reset = False

        if self.updated.error > self.original.error:
            should_reset = True

        return should_reset

    def update(self):
        return self.compile(self.guess())

    def guess(self):
        return None

    def compile(self, guess):
        return self.original
