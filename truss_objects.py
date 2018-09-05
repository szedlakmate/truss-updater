# -*- coding: utf-8 -*-
"""
Created on September 1 15:38 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

from copy import deepcopy
import itertools
import math
import numpy

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
        self.solve('original', self.boundaries, self.loads)

        # Start model updating
        self.start_model_updating()

    def calculate_stiffness_matrix(self, version):
        """
        Stiffness matrix compilation
        """
        # Set pointer to target structure
        if version == 'original':
            structure = self.original
        elif version == 'updated':
            structure = self.updated
        else:
            raise TypeError("Pointer is unknown. Should be 'original' or 'updated' but got:\n%s" % version)
        
        self.boundaries.supports = list(k for k, _ in itertools.groupby(sorted(self.boundaries.supports)))

        # Setting known forces
        known_f_a = []
        known_f_not_zero = []
        
        for location in range(len(structure.node * 3)):
            known_f_a.append(location)
            if location in [x[0] for x in self.loads.forces]:
                known_f_not_zero.append(location)
                
        for constraint in self.boundaries.supports:
            if constraint[0] in known_f_a:
                known_f_a.remove(constraint[0])
                
            if constraint[0] in known_f_not_zero:
                known_f_not_zero.remove(constraint[0])

        elements_lengths = [0] * len(structure.element)
        _norm_stiff = [0] * len(structure.element)
        _cx = [0] * len(structure.element)
        _cy = [0] * len(structure.element)
        _cz = [0] * len(structure.element)
        _s_loc = [0] * len(structure.element)
        local_stiffness_matrix = [0] * len(structure.element)
        stiffness_matrix = [[0] * (len(structure.node) * 3)] * (len(structure.node) * 3)

        for i in range(len(structure.element)):

            elements_lengths[i] = \
                math.sqrt(sum([(j - k) ** 2 for j, k
                               in zip(structure.node[structure.element[i].connection[1]],
                                      structure.node[structure.element[i].connection[0]])]))

            _cx[i] = (structure.node[structure.element[i].connection[1]][0]
                      - structure.node[structure.element[i].connection[0]][0]) / elements_lengths[i]

            _cy[i] = (structure.node[structure.element[i].connection[1]][1]
                      - structure.node[structure.element[i].connection[0]][1]) / elements_lengths[i]

            _cz[i] = (structure.node[structure.element[i].connection[1]][2]
                      - structure.node[structure.element[i].connection[0]][2]) / elements_lengths[i]

            _norm_stiff[i] = structure.element[i].material / elements_lengths[i]

            # local stiffness matrix calculation
            _s_loc[i] = [
                [_cx[i] ** 2, _cx[i] * _cy[i], _cx[i] * _cz[i], -_cx[i] ** 2,
                 -_cx[i] * _cy[i], -_cx[i] * _cz[i]],
                [_cx[i] * _cy[i], _cy[i] ** 2, _cy[i] * _cz[i], -_cx[i] * _cy[i],
                 -_cy[i] ** 2, -_cy[i] * _cz[i]],
                [_cx[i] * _cz[i], _cy[i] * _cz[i], _cz[i] ** 2, -_cx[i] * _cz[i],
                 -_cy[i] * _cz[i], -_cz[i] ** 2],
                [-_cx[i] ** 2, -_cx[i] * _cy[i], -_cx[i] * _cz[i], _cx[i] ** 2,
                 _cx[i] * _cy[i], _cx[i] * _cz[i]],
                [-_cx[i] * _cy[i], -_cy[i] ** 2, -_cy[i] * _cz[i], _cx[i] * _cy[i],
                 _cy[i] ** 2, _cy[i] * _cz[i]],
                [-_cx[i] * _cz[i], -_cy[i] * _cz[i], -_cz[i] ** 2, _cx[i] * _cz[i],
                 _cy[i] * _cz[i], _cz[i] ** 2]]

            local_stiffness_matrix[i] = [[y * structure.element[i].section * _norm_stiff[i]
                                          for y in x] for x in _s_loc[i]]

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
                    stiffness_increment[ele_dof_vec[k]] = local_stiffness_matrix[i][j][k]
                stiffness_matrix[ele_dof_vec[j]] = \
                    [x + y for x, y in zip(stiffness_matrix[ele_dof_vec[j]], stiffness_increment)]

        return stiffness_matrix, known_f_a

    def solve(self, version, boundaries, loads):
        print('Solve %s structure' % version)

        # Set pointer to target structure
        if version == 'original':
            structure = self.original
        elif version == 'updated':
            structure = self.updated
        else:
            raise TypeError("Pointer is unknown. Should be 'original' or 'updated' but got:\n%s" % version)

        # Calculate stiffness-matrix
        (stiffness_matrix, known_f_a) = self.calculate_stiffness_matrix(version)

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

        deformed = {'node': []}
        
        # Deformed shape
        for i in range(len(structure.node)):
            deformed['node'].append(
                [structure.node[i][0] + displacements[i * 3 + 0],
                 structure.node[i][1] + displacements[i * 3 + 1],
                 structure.node[i][2] + displacements[i * 3 + 2]])

        return deformed

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
            self.solve('original', self.boundaries, self.loads)
            self.solve('updated', self.boundaries, self.loads)

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