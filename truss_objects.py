# -*- coding: utf-8 -*-
"""
Created on September 1 15:38 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

from copy import deepcopy
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy
import time

from arduino_measurements import ArduinoMeasurements
from base_objects import *
from logger import start_logging
from truss_graphics import animate, plot_structure
from read_input_file import read_structure_file


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


class Truss(object):
    def __init__(self, input_file, title, measurements, graphics=False, log=False):
        """
        Main container

        :param input_file: file with structural data
        :param title: title of the project
        :param measurements: list of measured degree of freedoms, like ['12X', '15Z']
        :param graphics: switch for GUI
        :param log: switch for saving logs
        """
        self.options = {'graphics': graphics, 'log': log}

        setup_folder('results')
        setup_folder('logs')

        # Labeling object
        if title != '':
            self.title = title
        else:
            self.title = input_file.replace('.str', '')

        # Initializing logger
        self.logger = start_logging(file=self.options['log'], label=self.title)

        self.logger.info('*******************************************************')
        self.logger.info('              STARTING TRUSS UPDATER')
        self.logger.info('Structure: %s' % self.title)
        self.logger.info('Input:     %s' % input_file)
        self.logger.info('Measured nodes: %s' % str(measurements))
        self.logger.info('*******************************************************\n')

        # Reading structural data, boundaries and loads
        (node_list, element_list, boundaries) = read_structure_file(input_file)

        # Setting up basic structure
        self.original = StructuralData(node_list, element_list)

        # Setting up boundaries
        self.boundaries = Boundaries(boundaries)

        # Setting up loads
        self.loads = Loads({'forces': [[25, -9.8]]})

        # Setup Input
        self.measurement = ArduinoMeasurements(measurements)
        self.logger.debug("Calibration is mocked: set to 0")

        # Initiating updated structure
        self.updated = deepcopy(self.original)

        if self.options['graphics']:
            self.fig = plt.figure()
            if self.dof() == 2:
                self.ax = self.fig.add_subplot(111)
            else:
                self.ax = self.fig.add_subplot(111, projection='3d')

            # plt.axis('equal')

            self.fig.canvas.draw()
            plt.show(block=False)

    def dof(self):
        dof = 3

        if sum([1 if support[0] % 3 == 2 else 0 for support in self.boundaries.supports]) == len(self.original.node):
            dof = 2

        return dof

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

        forces = [0.0] * dof_number
        for (dof, force) in loads.forces:
            forces[dof] = force

        force_new = [0.0] * (dof_number - len(constraints))
        for i, dof in enumerate(known_f_a):
            force_new[i] = forces[dof]

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
        dis_new = numpy.linalg.solve(numpy.array(stiff_new), numpy.array(force_new))

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
            self.measurement.update(self.loads, title=self.title)
            self.logger.debug('Loads are mocked: %s' % str(self.measurement.loads))

            # Calculate refreshed and/or updated models
            self.solve(self.original, self.boundaries, self.loads)
            deformed = self.solve(self.updated, self.boundaries, self.loads)

            if self.options['graphics']:
                plot_structure(self.fig, self.ax, self.original, deformed, dof=self.dof(),
                               counter=counter, title=self.title, show=True)

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
                # previous_error = structure.error
                structure.element[i].material *= (1 + delta)/(1 - delta)
                self.solve(structure, self.boundaries, self.loads)
                # self.logger.debug('Recounted error: %.6f -> %.6f' % (previous_error, structure.error))

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
