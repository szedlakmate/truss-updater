# -*- coding: utf-8 -*-
"""
Created on September 1 15:38 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""


def read_deflections(measurement_config):
    """
    One measurement means a displacement along one axis (X/Y/Z)
    A measurement value is negative if the displacement's ordinate is lower than at the initial moment,
    e.g. when it goes "down".

    Other radial displacement shall be divided into X/Y/Z directional components.
    :return:
    """
    measurements = measurement_config.read_raw_input()

    return [[measurement_config.id_list[i], measurements[i] - measurement_config.initial_distances[i][1]] for i
            in range(len(measurement_config.id_list))]


class ArduinoMeasurements(object):
    def __init__(self, id_list):
        self.id_list = id_list

        self.displacements = []
        self.loads = []


        # Measure initial distances
        calibration = self.calibrate()

        # Store initial measurements by DOF ID
        self.initial_distances = [[self.id_list[i], calibration[i]] for i in range(len(self.id_list))]

    def read_raw_input(self):
        return [0]

    def calibrate(self):
        return [0]

    def update(self):
        # TODO: write function: (read load from file should be eliminated)
        # self.distances = [[ID, load]]
        # self.loads = [[ID, measurement]]
        pass
