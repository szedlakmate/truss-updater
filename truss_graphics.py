# -*- coding: utf-8 -*-
"""
Extended by Máté Szedlák

Used sources:
https://stackoverflow.com/questions/29188612/arrows-in-matplotlib-using-mplot3d
https://gist.github.com/jpwspicer/ea6d20e4d8c54e9daabbc1daabbdc027
"""
from copy import deepcopy
from matplotlib import pyplot as plt
try:
    from matplotlib import pyplot
    from matplotlib.patches import FancyArrowPatch
    from mpl_toolkits.mplot3d import proj3d
except ImportError:
    print("Graphical libraries could not be loaded. GUI can not be used.")


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

    def plot_structure(original, result, dof=3, supports=1,
                      forces=1, reactions=1, show_values=1, save_plot=1):

        fig = pyplot.figure()
        _ax = fig.add_subplot(111, projection='3d')

        if dof == 2:
            _ax.view_init(elev=90., azim=-90.)
            _ax.w_zaxis.line.set_lw(0.)
            _ax.set_zticklabels([])

        fig.set_size_inches(100, 10)


        # Plot original structure
        coordinates = original.generate_coordinate_list()
        if dof == 3:
            _ax.plot([x[0][0] for x in coordinates],
                     [x[0][1] for x in coordinates],
                     zs=[x[0][2] for x in coordinates],  color='b')

        else:
            _ax.plot([x[0][0] for x in coordinates],
                     [x[0][1] for x in coordinates], color='b')

        i = 0
        for node in original.node:
            _ax.text(node[0], node[1], node[2], str(i), fontsize=12,
                     horizontalalignment='right')
            i += 1

        path = None
        plotname = 'test-print'

        plt.show()

        # pyplot.show()
        if save_plot:
            path = './Results/%s.png' % plotname
            fig.savefig(path)
            print("'%s.png' is saved." % plotname)
            print('------------------------------------')

        return path

