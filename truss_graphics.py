# -*- coding: utf-8 -*-
"""
Extended by Máté Szedlák

Used sources:
https://stackoverflow.com/questions/29188612/arrows-in-matplotlib-using-mplot3d
https://gist.github.com/jpwspicer/ea6d20e4d8c54e9daabbc1daabbdc027
"""
from copy import deepcopy
import math
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d


def scale_displacement(base, result, scale=1.0):
    scaled_structure = deepcopy(result)

    for i in range(len(base.node)):
        scaled_structure.node[i] = [base.node[i][j] + (result.node[i][j] - base.node[i][j]) * scale for j in range(3)]

    return scaled_structure.node


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


def post_process(original, deformed):
    stresses = []
    stress_ratio = []

    for i in range(len(original.element)):
        stress = -(element_length(deformed, i) - element_length(original, i)) /\
                 element_length(original, i) * original.element[i].material * original.element[i].section

        stresses.append(stress)

    for stress in stresses:
        if stress > 0:
            ratio = stress / max(stresses)
        else:
            ratio = -stress / min(stresses)
        stress_ratio.append(ratio)

    return {'stress': stresses, 'ratio': stress_ratio}


class Arrow3D(FancyArrowPatch):
    """
    Vector drawer module based on the matplotlib library using external sources, like:
        https://stackoverflow.com/questions/29188612/arrows-in-matplotlib-using-mplot3d
        https://gist.github.com/jpwspicer/ea6d20e4d8c54e9daabbc1daabbdc027
    """
    def __init__(self, xs, ys, zs, *args, **kwargs):
        FancyArrowPatch.__init__(self, (0, 0), (0, 0), *args, **kwargs)
        self._verts3d = xs, ys, zs

    def draw(self, renderer):
        _xs3d, _ys3d, _zs3d = self._verts3d
        _xs, _ys, _zs = proj3d.proj_transform(_xs3d, _ys3d, _zs3d, renderer.M)
        self.set_positions((_xs[0], _ys[0]), (_xs[1], _ys[1]))
        FancyArrowPatch.draw(self, renderer)

    def plot_structure(base, result=None, supports=True, loads=None, reactions=False, values=False,
                       save=True, show=False, node_number=False, animate=False, counter=None):

        if result is None:
            structure = base
        else:
            structure = result
            structure.node = scale_displacement(base, result, 1)

        # Check dof
        dof = 2
        for node in structure.node:
            if node[2] != 0.0:
                dof = 3
                break

        fig = plt.figure()
        _ax = fig.add_subplot(111, projection='3d')

        if dof == 2:
            _ax.view_init(elev=90., azim=-90.)
            _ax.w_zaxis.line.set_lw(0.)
            _ax.set_zticklabels([])

        if result:
            stresses = post_process(base, result)


        # Plot structure
        index = 0
        rgb_col = 'b'
        for coordinate in structure.generate_coordinate_list():
            if result:
                if stresses['ratio'][index] > 0:
                    rgb_col = [stresses['ratio'][index], 0.3, 0]
                else:
                    rgb_col = [0, 0.3, abs(stresses['ratio'][index])]

            _ax.plot([x[0] for x in coordinate],
                     [x[1] for x in coordinate],
                     zs=[x[2] for x in coordinate], color=rgb_col)

            index += 1

        # Plot node numbers
        if node_number:
            i = 0
            for node in structure.node:
                _ax.text(node[0], node[1], node[2], dict=str(i), fontsize=12,
                         horizontalalignment='right')
                i += 1

        plotname = 'test-print'

        if show:
            plt.show()

        if save:
            if counter is None:
                fig.savefig('./Results/%s.png' % plotname)
            else:
                fig.savefig('./Results/%s - %i.png' % (plotname, counter['total']))

