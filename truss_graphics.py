# -*- coding: utf-8 -*-
"""
Extended by Máté Szedlák

Used sources:
https://stackoverflow.com/questions/29188612/arrows-in-matplotlib-using-mplot3d
https://gist.github.com/jpwspicer/ea6d20e4d8c54e9daabbc1daabbdc027
"""
from copy import deepcopy
import imageio
import math


def animate(title, maximum):
    """
        GIF creator

        :param title:
        :param maximum:
        :return: None
        """
    images = []

    [images.append(imageio.imread('./results/%s - %i.png' % (title, i))) for i in range(maximum)]

    imageio.mimsave('./results/%s.gif' % title, images, duration=0.33)


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
            if max(stresses) > 0:
                ratio = stress / max(stresses)
            else:
                ratio = 0
        else:
            if max(stresses) > 0:
                ratio = -stress / min(stresses)
            else:
                ratio = 0
        stress_ratio.append(ratio)

    return {'stress': stresses, 'ratio': stress_ratio}


def plot_structure(fig, ax, base, result=None, dof=2, supports=True, loads=None, reactions=False, values=False,
                   save=True, show=False, node_number=False, counter=None, title='test'):

    if result is None:
        structure = base
    else:
        structure = result
        structure.node = scale_displacement(base, result, 1)

    if result:
        stresses = post_process(base, result)

    # Plot structure
    index = 0
    rgb_col = 'b'

    # Clean previous plot
    ax.cla()

    for coordinate in structure.generate_coordinate_list():
        if result:
            if stresses['ratio'][index] > 0:
                rgb_col = [stresses['ratio'][index], 0.3, 0]
            else:
                rgb_col = [0, 0.3, abs(stresses['ratio'][index])]
        if dof == 2:
            ax.plot([x[0] for x in coordinate], [x[1] for x in coordinate], color=rgb_col)
        else:
            ax.plot([x[0] for x in coordinate], [x[1] for x in coordinate], zs=[x[2] for x in coordinate], color=rgb_col)

        index += 1

    # Plot node numbers
    if node_number:
        i = 0
        for node in structure.node:
            ax.text(node[0], node[1], node[2], dict=str(i), fontsize=12, horizontalalignment='right')
            i += 1

    if show:
        fig.canvas.draw()

    if save:
        try:
            if counter is None:
                fig.savefig('./results/%s.png' % title)
            else:
                fig.savefig('./results/%s - %i.png' % (title, counter['total']))
        except FileNotFoundError:
            print('Known CI error - Saving files makes Travis fail')
