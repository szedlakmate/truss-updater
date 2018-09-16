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

        for line in original.generate_coordinate_list():
            # Plot original structure
            if original:
                _ax.plot(line[0], line[1],  color='b')

        path = None
        plotname = 'test-print'

        # pyplot.show()
        if save_plot:
            path = './Results/%s.png' % plotname
            fig.savefig(path)
            print("'%s.png' is saved." % plotname)
            print('------------------------------------')

        return path

