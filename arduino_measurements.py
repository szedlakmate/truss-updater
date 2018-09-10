# -*- coding: utf-8 -*-
"""
Created on September 1 15:38 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

import random


class ArduinoMeasurements(object):
    def __init__(self, id_list):
        self.id_list = id_list

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
            print("Randomized raw input function is mocked: %.2f" % random_input)
            return [random_input]
        else:
            print("Raw input function is mocked: %.2f" % fake)
            return [fake]

    def calibrate(self):
        print("Calibration is mocked: set to 0")
        return [0]

    def update(self):
        """
        One measurement means a displacement along one axis (X/Y/Z)
        A measurement value is negative if the displacement's ordinate is lower than at the initial moment,
        e.g. when it goes "down".

        Other radial displacement shall be divided into X/Y/Z directional components.
        """
        # TODO: write function for:
        print('Loads are mocked: [25, -9.80]')
        self.loads = [[25, -9.80]]

        measurements = self.read_raw_input(25, 10)

        self.displacements = [[self.id_list[i], self.initial_measurements[i] - measurements[i]]
                              for i in range(len(self.id_list))]
