# -*- coding: utf-8 -*-
"""
Created on September 1 15:38 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

import random


def convert_node_id_to_dof_id(node_list):
    dof_list = []

    for node in node_list:
        remainder = None
        if node[-1].upper() == 'X':
            remainder = 0
        elif node[-1].upper() == 'Y':
            remainder = 1
        elif node[-1].upper() == 'Z':
            remainder = 2

        dof = int(node[0:len(node)-1]) * 3 + remainder
        dof_list.append(dof)

    return dof_list


class ArduinoMeasurements(object):
    def __init__(self, node_list):
        self.id_list = convert_node_id_to_dof_id(node_list)

        self.displacements = []
        self.loads = []

        # Measure initial distances
        self.initial_measurements = self.calibrate()

    def read_raw_input(self, fake, random_limit = 0):
        """
        Arduino input

        :param fake: it will be returned wrapped in an array
        :return: fake
        """

        if random_limit > 0:
            random_input = fake + random.randint(-random_limit*10, +random_limit*10)/10
            return [random_input]
        else:
            return [fake]

    def calibrate(self):
        return [0]

    def update(self):
        """
        One measurement means a displacement along one axis (X/Y/Z)
        A measurement value is negative if the displacement's ordinate is lower than at the initial moment,
        e.g. when it goes "down".

        Other radial displacement shall be divided into X/Y/Z directional components.
        """
        # TODO: write function for:
        self.loads = [[18, -9.80]]

        measurements = self.read_raw_input(25, 0)

        self.displacements = [[self.id_list[i], self.initial_measurements[i] - measurements[i]]
                              for i in range(len(self.id_list))]
