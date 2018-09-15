# -*- coding: utf-8 -*-
"""
Created on September 1 15:38 2018

3D truss model updater program created by Máté Szedlák.
Copyright MIT, Máté Szedlák 2016-2018.
"""

from truss_objects import Truss
import argparse


# Setup console run
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--title", metavar='str', type=str,
                        help="Manually label project. By default it comes from the input file's name.", default='')

    parser.add_argument("-i", "--input", metavar='str', type=str, default="",
                        help="Input file, stored in the ./Structure folder [*.str]", required=True)

    parser.add_argument('-m', '--measurements', nargs='+', help='Enlist the measured nodes as: 12X 14Z', required=True)

    #parser.add_argument("-s", "--simulation", metavar='int', type=int, choices=range(2), default=0, help="0: No|1: Yes")

    args = parser.parse_args()

    # Define new structure
    Truss = Truss(input_file='%s.str' % args.input.replace('.str', ''), title=args.title,
                  measurements=args.measurements)

    Truss.start_model_updating()
