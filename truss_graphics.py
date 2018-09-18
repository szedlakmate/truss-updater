# -*- coding: utf-8 -*-
"""
Extended by Máté Szedlák

Used sources:
https://stackoverflow.com/questions/29188612/arrows-in-matplotlib-using-mplot3d
https://gist.github.com/jpwspicer/ea6d20e4d8c54e9daabbc1daabbdc027
"""
from copy import deepcopy
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d


def scale_displacement(base, result, scale=10.0):
    scaled_structure = deepcopy(result)

    for i in range(len(base.node)):
        scaled_structure.node[i] = [base.node[i][j] + (result.node[i][j] - base.node[i][j]) * scale for j in range(3)]

    return scaled_structure.node


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

    def plot_structure(base, result=None, dof=3, supports=True, loads=None, reactions=False, values=False,
                       save=True, show=False, node_number=False, animate=False):

        if result is None:
            structure = base
        else:
            structure = result
            structure.node = scale_displacement(base, result, 10)

        fig = plt.figure()
        _ax = fig.add_subplot(111, projection='3d')

        if dof == 2:
            _ax.view_init(elev=90., azim=-90.)
            _ax.w_zaxis.line.set_lw(0.)
            _ax.set_zticklabels([])

        # Plot original structure
        for coordinate in structure.generate_coordinate_list():
            _ax.plot([x[0] for x in coordinate],
                     [x[1] for x in coordinate],
                     zs=[x[2] for x in coordinate], color='b')

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
            fig.savefig('./Results/%s.png' % plotname)
