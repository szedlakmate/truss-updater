# -*- coding: utf-8 -*-
"""
Created on September 1 15:38 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

import os


def setup_folder(directory):
    """
    :param directory: folder name to be checked
    :return: None
    """
    path = str(os.path.dirname('.')) + '/' + directory.replace('/', '').replace('.', '') + '/'

    if not os.path.exists(path):
        os.makedirs(path)


def read_structure_file(input_file):
    """
      Input file for TRUSS.py program
      All commands must be written with uppercase characters
      *** The values MUST be written in the exact following line of a command
      Only lines with the command and nothing more counts.
      Everything else will be neglected. Even hashtags are useless :)
      The order of the commands are indifferent.
    
      Commands and their format (example):
          ELEMENTS - Elements given by end-nodes: 0, 1 | 0, 2 ...
          COORDINATES - Nodal coordinates: 0, 0, 0, | 0, 3., 0. ...
          CROSS-SECTIONS - This data will be evaluated in Python: 3.0*(10**(-4)), 5.0*(10**(-4)) ...
          MATERIALS - This data will be evaluated in Python: 70.0*(10**9), 100.0*(10**9) ...
          FORCES - Selected dof + Force: 11, +1000000.0 | 12, +1000000.0 ...
          SUPPORTS - Selected dof + Prescribed displacements: 0, 0.0 | 1, 0.0 ...
          SPECIAL_DOF - Selected node's dof will be analysed during Model Updating: 1, xyz | 3 y | 10 xz ...
    
          EOF - For compatibility reasons EOF should be placed after the commands
      """
    _read_element_names = ["DOF", "Elements", "Coordinates",
                           "Cross-sections", "Materials", "Forces", "Supports", "Measured dofs"]

    try:
        setup_folder('Structures')
        with open("./Structures/" + input_file, "r") as sourcefile:
            source_line = ""
            while source_line != "EOF":
                source_line = sourcefile.readline().strip()

                if source_line.upper() == "ELEMENTS":
                    source_line = sourcefile.readline().strip()
                    input_string = [x.split(',') for x in source_line.split('|')]
                    if len(input_string[0]) == 1:
                        input_string = [x.split(';') for x in source_line.split('|')]
                    if [''] in input_string:
                        input_string.remove([''])
                    input_number = [[int(x[0]), int(x[1])]
                                    for x in input_string]

                    truss.bulk_set_elements(input_number)
                    read_elements[2] = 1

                if source_line.upper() == "COORDINATES":
                    source_line = sourcefile.readline().strip()
                    input_number = []
                    input_string = [x.split(',') for x in source_line.split('|')]
                    if len(input_string[0]) == 1:
                        input_string = [x.split(';') for x in source_line.split('|')]
                    if [''] in input_string:
                        input_string.remove([''])
                    if len(input_string[0]) == 3:
                        input_number = [[float(x[0]), float(x[1]), float(x[2])] for x in input_string]
                    elif len(input_string[0]) == 2:
                        input_number = [[float(x[0]), float(x[1]), 0] for x in input_string]
                    truss.bulk_set_coordinates(input_number)
                    read_elements[3] = 1

                if source_line.upper() == "CROSS-SECTIONS":
                    source_line = sourcefile.readline().strip()
                    input_string = source_line.replace(',', '|').replace(';', '|').split('|')
                    if '' in input_string:
                        input_string.remove('')
                    input_number = [float(eval(x)) for x in input_string]
                    truss.bulk_set_cross_sections(input_number)
                    read_elements[4] = 1

                if source_line.upper() == "MATERIALS":
                    source_line = sourcefile.readline().strip()
                    input_string = source_line.replace(',', '|').replace(';', '|').split('|')
                    if '' in input_string:
                        input_string.remove('')

                    input_number = [float(eval(x)) for x in input_string]
                    truss.bulk_set_materials(input_number)
                    read_elements[5] = 1

                if source_line.upper() == "FORCES":
                    source_line = sourcefile.readline().strip()
                    input_string = [x.split(',') for x in source_line.split('|')]
                    if len(input_string[0]) == 1:
                        input_string = [x.split(';') for x in source_line.split('|')]
                    if [''] in input_string:
                        input_string.remove([''])
                    input_number = [[int(x[0]) - _io_origin, float(x[1])] for x in input_string]
                    truss.bulk_set_forces(sorted(input_number))
                    read_elements[6] = 1

                if source_line.upper() == "SUPPORTS":
                    source_line = sourcefile.readline().strip()
                    input_string = [x.split(',') for x in source_line.split('|')]
                    if len(input_string[0]) == 1:
                        input_string = [x.split(';') for x in source_line.split('|')]
                    if [''] in input_string:
                        input_string.remove([''])
                    input_number = [[int(x[0]) - _io_origin, float(x[1])] for x in input_string]
                    truss.bulk_set_supports(sorted(input_number))
                    read_elements[7] = 1

                if source_line.upper() == "MEASUREMENTS":
                    source_line = sourcefile.readline().strip()
                    special_dof_input_string = source_line
                    updating_container.arduino_mapping = source_line.split(',')
                    truss.bulk_set_measurement_points(updating_container.arduino_mapping, _io_origin)
                    read_elements[8] = 1
    except IOError:
        print("The following file could not be opened: " + "./Structures/" + input_file)
        print("Please make sure that the structural data is available for the program in the run directory.")
        raise IOError

    terminate = False
    for i, value in enumerate(read_elements):
        if i > 0 and (i < 8 or configuration.updating):  # if i > 0:
            if value == 0:
                print("The following was not found: " + _read_element_names[i])
                terminate = True
    if terminate:
        raise Exception

    return [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]], [[[0, 1], 0.0, 0.0]], [0, 1, 2, 3, 5], {'forces': [[4, 1.0]]}