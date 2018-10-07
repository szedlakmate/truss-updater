# -*- coding: utf-8 -*-
"""
Created on September 1 15:38 2018

Truss framework created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

import itertools


def read_structure_file(input_file):
    """
      Input file parser
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
          SUPPORTS - Selected dof + Prescribed displacements: 0, 0.0 | 1, 0.0 ...
    
          EOF - For compatibility reasons EOF should be placed after the commands
      """
    _read_element_names = ["Elements", "Coordinates",
                           "Cross-sections", "Materials", "Supports"]

    read_elements = {'elements': False, 'coordinates': False, 'cross-sections': False, 'materials': False,
                     'supports': False}

    try:
        with open("./structures/%s" % input_file, "r") as sourcefile:
            source_line = ""
            structure = {}
            dof = 3

            while source_line != "EOF":
                source_line = sourcefile.readline().strip()

                if source_line.upper() == "ELEMENTS":
                    source_line = sourcefile.readline().strip()
                    input_string = [x.split(',') for x in source_line.split('|')]
                    if len(input_string[0]) == 1:
                        input_string = [x.split(';') for x in source_line.split('|')]
                    if [''] in input_string:
                        input_string.remove([''])
                    input_number = [[[int(x[0]), int(x[1])], None, None]
                                    for x in input_string]

                    structure['elements'] = input_number
                    read_elements['elements'] = True

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
                        dof = 2
                        input_number = [[float(x[0]), float(x[1]), 0.0] for x in input_string]

                    structure['coordinates'] = input_number
                    read_elements['coordinates'] = True

                if source_line.upper() == "CROSS-SECTIONS":
                    source_line = sourcefile.readline().strip()
                    input_string = source_line.replace(',', '|').replace(';', '|').split('|')
                    if '' in input_string:
                        input_string.remove('')
                    input_number = [float(eval(x)) for x in input_string]

                    for index in range(len(structure['elements'])):
                        structure['elements'][index][2] = input_number[index]

                    read_elements['cross-sections'] = True

                if source_line.upper() == "MATERIALS":
                    source_line = sourcefile.readline().strip()
                    input_string = source_line.replace(',', '|').replace(';', '|').split('|')
                    if '' in input_string:
                        input_string.remove('')

                    input_number = [float(eval(x)) for x in input_string]

                    for index in range(len(structure['elements'])):
                        structure['elements'][index][1] = input_number[index]

                    read_elements['materials'] = True

                if source_line.upper() == "SUPPORTS":
                    source_line = sourcefile.readline().strip()
                    input_string = [x.split(',') for x in source_line.split('|')]
                    if len(input_string[0]) == 1:
                        input_string = [x.split(';') for x in source_line.split('|')]
                    if [''] in input_string:
                        input_string.remove([''])

                    if dof == 3:
                        input_number = [[int(x[0]), float(x[1])] for x in input_string]
                    else:
                        input_number = [[(int(x[0]) // 2) * 3 + int(x[0]) % 2, float(x[1])] for x in input_string]
                        extra_supports = [[int(x * 3 + 2), 0.0] for x in range(len(structure['coordinates']))]
                        input_number.extend(extra_supports)

                    structure['supports'] = list(k for k, _ in itertools.groupby(sorted(input_number)))
                    read_elements['supports'] = True

    except IOError:
        print("The following file could not be opened: " + "./structures/" + input_file)
        print("Please make sure that the structural data is available for the program in the run directory.")
        raise IOError

    terminate = False
    error_message_template = 'The following was not found: '
    for element in read_elements:
        if read_elements[element] is False:
            error_message_template += element + ' '
            terminate = True

    if terminate:
        raise Exception(error_message_template)

    node_list = structure['coordinates']
    element_list = structure['elements']
    boundaries = structure['supports']

    return node_list, element_list, boundaries
