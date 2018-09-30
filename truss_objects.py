# -*- coding: utf-8 -*-
"""
Created on September 1 15:38 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

from copy import deepcopy
import math
import matplotlib.pyplot as plt
import numpy
import time

from arduino_measurements import ArduinoMeasurements
from logger import start_logging
from truss_graphics import animate, plot_structure
from read_input_file import read_structure_file


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


def error(measurements, calculated_displacements):
    """
    Sum of errors using least-square method

    This function returns a scalar as the error of the truss. The error is the difference between the calculated
    and the measured displacements. The errors are measured on the measurement points. The number and the location
    of measurement points are essential. Wrongly chosen measurements might cause bad behavior during convergence.

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


class Truss(object):
    def __init__(self, input_file, title, measurements, graphics=False):
        """
        Main container

        :param input_file: file with structural data
        :param title: title of the project
        :param measurements: list of measured degree of freedoms, like ['12X', '15Z']
        """
        # Labeling object
        if title != '':
            self.title = title
        else:
            self.title = input_file.replace('.str', '')

        # Initializing logger
        self.logger = start_logging(True, self.title)

        self.logger.info('*******************************************************')
        self.logger.info('              STARTING TRUSS UPDATER')
        self.logger.info('Structure: %s' % self.title)
        self.logger.info('Input:     %s' % input_file)
        self.logger.info('Measured nodes: %s' % str(measurements))
        self.logger.info('*******************************************************\n')

        self.options = {'graphics': graphics}

        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        # plt.axis('equal')

        # Reading structural data, boundaries and loads
        (node_list, element_list, boundaries) = read_structure_file(input_file)

        # Setting up basic structure
        self.original = StructuralData(node_list, element_list)

        # Setting up boundaries
        self.boundaries = Boundaries(boundaries)

        # Setting up loads
        self.loads = Loads({'forces': [[20, -9.80]]})

        # Setup Input
        self.measurement = ArduinoMeasurements(measurements)
        self.logger.debug("Calibration is mocked: set to 0")

        # Initiating updated structure
        self.updated = deepcopy(self.original)

        self.fig.canvas.draw()
        plt.show(block=False)

    def solver_helper(self, structure):
        """
        Solver helper. Should be refactored/deprecated.

        :param structure: Structure object
        :return: { known_f_a, known_f_not_zero, known_displacement_a }
        """
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

    def solve(self, structure, boundaries, loads, label=''):
        """
        Main solver. Calculates displacements for a given structure + loads + boundaries combination.

        :param structure: Structure object pointer. Sets the error of the structure according to self.measurements
        :param boundaries: Boundaries object
        :param loads: Loads object
        :param label: label for solution return value
        :return: returns an non-standardized array of deformations
        """
        if label == '':
            label = 'result'

        # Calculate stiffness-matrix
        stiffness_matrix = calculate_stiffness_matrix(structure)

        dof_number = len(structure.node) * 3

        helper = self.solver_helper(structure)
        known_f_a = helper['known_f_a']

        constraints = deepcopy(boundaries.supports)

        forces = [0] * (dof_number - len(constraints))
        for (dof, force) in deepcopy(loads.forces):
            forces[dof] = force

        displacements = [0.0] * dof_number
        for (dof, displacement) in deepcopy(loads.displacements):
            displacements[dof] = displacement

        stiff_new = [[0.0] * (dof_number - len(constraints))] * (dof_number - len(constraints))

        stiffness_increment = [0.0] * (dof_number - len(constraints))

        for i, kfai in enumerate(known_f_a):
            for j, kfaj in enumerate(known_f_a):
                stiffness_increment[j] = stiffness_matrix[kfai][kfaj]

            stiff_new[i] = [x + y for x, y in zip(stiff_new[i], stiffness_increment)]

        # SOLVING THE STRUCTURE
        dis_new = numpy.linalg.solve(numpy.array(stiff_new), numpy.array(forces))

        for i, known_f_a in enumerate(known_f_a):
            displacements[known_f_a] = dis_new[i]

        node = []

        # Deformed shape
        for i in range(len(structure.node)):
            node.append([structure.node[i][0] + displacements[i * 3 + 0],
                         structure.node[i][1] + displacements[i * 3 + 1],
                         structure.node[i][2] + displacements[i * 3 + 2]])

        # Calculating the error
        structure.error = error(self.measurement.displacements, displacements)

        deformed = StructuralData(node, [[x.connection, x.material, x.section] for x in structure.element], label)

        return deformed

    def start_model_updating(self, max_iteration=0):
        """
        Starting main model updating process:
            - Read displacements and loads from sensors
            - Calculate refreshed and/or updated model including the error based on self.measurements.
            - Check reset condition

        :param: max_iteration: Sets the maximum number of updates. If 0, the iteration number is unlimited.

        :return: None
        """
        self.logger.info('Start model updating\n')
        counter = {'total': 0, 'loop': 0}

        while True and (counter['total'] < max_iteration or max_iteration == 0):
            self.logger.info('*** %i. loop ***' % counter['loop'])

            # Read sensors
            self.measurement.update()
            self.logger.debug('Loads are mocked: %s' % str(self.measurement.loads))

            # Refine/update forces
            self.loads.forces = self.measurement.loads

            # Calculate refreshed and/or updated models
            self.solve(self.original, self.boundaries, self.loads)
            deformed = self.solve(self.updated, self.boundaries, self.loads)

            plot_structure(self.fig, self.ax, self.original, deformed, counter=counter, title=self.title, show=True)

            counter['loop'] += 1
            counter['total'] += 1

            if self.should_reset() is False:
                self.updated = deepcopy(self.update())
            else:
                self.updated = deepcopy(self.original)
                self.logger.warn('RESET STRUCTURE')
                counter['loop'] = 0

        if self.options['graphics']:
            animate(self.title, counter['total'])

        self.logger.info('Exiting...')
        time.sleep(2)

    def should_reset(self):
        """
        Checks reset condition

        :return: Boolean
        """
        should_reset = False

        if self.updated.error > self.original.error:
            self.logger.debug('The updated structure\'s error is higher than the original\'s one:')
            self.logger.debug('updated: %.3f original: %.3f' % (self.updated.error, self.original.error))

            should_reset = True

        return should_reset

    def update(self):
        """
        Returns updated Structure

        :return: Structure object
        """
        self.logger.debug('Update')
        return self.compile(self.guess())

    def guess(self):
        """
        Returns an array of possible modifications

        :return:
        """
        self.logger.debug('Guess')
        structures = []
        delta = 0.1

        for i in range(len(self.updated.element)):
            structure = deepcopy(self.updated)
            structure.element[i].material *= 1 - delta
            self.solve(structure, self.boundaries, self.loads)

            if structure.error > self.original.error:
                # Modification resulted worse result: turn effect backward
                previous_error = structure.error
                structure.element[i].material *= (1 + delta)/(1 - delta)
                self.solve(structure, self.boundaries, self.loads)
                self.logger.debug('Recounted error: %.6f -> %.6f' % (previous_error, structure.error))

            structures.append(structure)

        return structures

    def compile(self, guesses):
        """
        Compiles the best updated Structure based on the guesses.

        :param guesses:
        :return: Structure object
        """
        self.logger.debug('Compile')
        guess_errors = [x.error for x in guesses]

        update = None

        for index, structure in enumerate(guesses):
            if structure.error == min(guess_errors):
                update = deepcopy(structure)
                self.logger.info('Delta:\t%7.3f \t(original:\t%7.3f)' %
                                 (update.error, self.original.error))
        return update
