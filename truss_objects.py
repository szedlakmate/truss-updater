# -*- coding: utf-8 -*-
"""
Created on September 1 15:38 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""


class Element(object):
    """
    * connection: [1. node, 2. node] where 1 -> 2
    * material: {number} E []
    * section: {number} [m^2]
    """
    def __init__(self):
        self.connection = [None, None]
        self.material = None
        self.section = None


class StructuralData(object):
    """
    Data model for structures

    * node: list of nodal coordinates [ 1.[X, Y, Z], 2.[X, Y, Z], ... ]
    * element: list of elements
        - connection [i, j]
        - material [E]
        - cross-section [m^2]
    """
    def __init__(self):
        self.node = [[None, None]] * 0
        self.element = [Element()] * 0


class Boundaries(object):
    """
    * support [DOF ID] - Only rigid supports
    """
    def __init__(self):
        self.support = [None] * 0


class Loads(object):
    """
    Load model

    * displacement [ID, displacement m] - DOF ID
    * force [ID, force KN] - DOF ID
    * stress [ID, ] - element ID
    """
    def __init__(self):
        self.displacement = [[None, None]] * 0
        self.force = [[None, None]] * 0
        self.stress = [[None, None]] * 0


class Measurements(object):
    """
    * displacement [ID, displacement m] - DOF ID
    * force [ID, force KN] - DOF ID
    """
    def __init__(self):
        self.displacement = [[None, None]] * 0
        self.force = [[None, None]] * 0


class Solution(object):
    """
    * displacement [ID, displacement m] - DOF ID
    * node: list of nodal coordinates [ 1.[X, Y, Z], 2.[X, Y, Z], ... ]
    * reaction [ID, force KN] - DOF ID
    * stress [ID, stress] - element ID
    """
    def __init__(self):
        self.displacement = [[None, None]] * 0
        self.node = [[None, None, None]] * 0
        self.reaction = [[None, None]] * 0
        self.stress = [[None, None]] * 0
