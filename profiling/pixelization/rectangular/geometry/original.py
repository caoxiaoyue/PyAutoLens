from profiling import profiling_data
from profiling import tools
from autolens import exc
import numpy as np
import pytest

class Pixelization(object):

    def __init__(self, pixels, regularization_coefficients=(1.0,), pix_signal_scale=1.0):
        """
        Abstract base class for a pixelization, which discretizes a set of masked_image and sub grid grid into \
        pixels. These pixels then fit a  data_vector-set using a linear inversion, where their regularization_matrix matrix
        enforces smoothness between pixel values.

        A number of 1D and 2D arrays are used to represent mappings betwen masked_image, sub, pix, and cluster pixels. The \
        nomenclature here follows grid_to_grid, such that it maps the index of a value on one grid to another. For \
        example:

        - pix_to_image[2] = 5 tells us that the 3rd pixelization-pixel maps to the 6th masked_image-pixel.
        - sub_to_pixelization[4,2] = 2 tells us that the 5th sub-pixel maps to the 3rd pixelization-pixel.

        Parameters
        ----------
        pixels : int
            The number of pixels in the pixelization.
        regularization_coefficients : (float,)
            The regularization_matrix coefficients used to smooth the pix reconstructed_image.
        pix_signal_scale : float
            A hyper-parameter which scales the signal attributed to each pixel, used for weighted regularization_matrix.
        """
        self.pixels = pixels
        self.regularization_coefficients = regularization_coefficients
        self.pix_signal_scale = pix_signal_scale

class Rectangular(Pixelization):

    def __init__(self, shape=(3,3), regularization_coefficients=(1.0,)):
        """A rectangular pixelization where pixels appear on a Cartesian, uniform and rectangular grid \
        of  shape (rows, columns).

        Like an masked_image grid, the indexing of the rectangular grid begins in the top-left corner and goes right and down.

        Parameters
        -----------
        shape : (int, int)
            The dimensions of the rectangular grid of pixels (x_pixels, y_pixel)
        regularization_coefficients : (float,)
            The regularization_matrix coefficients used to smooth the pix reconstructed_image.
        """

        if shape[0] <= 2 or shape[1] <= 2:
            raise exc.PixelizationException('The rectangular pixelization must be at least dimensions 3x3')

        super(Rectangular, self).__init__(shape[0] * shape[1], regularization_coefficients)

        self.shape = shape

    class Geometry(object):

        def __init__(self, x_min, x_max, x_pixel_scale, y_min, y_max, y_pixel_scale):
            """The geometry of a rectangular grid, defining where the grids top-left, top-right, bottom-left and \
            bottom-right corners are in arc seconds. The arc-second size of each rectangular pixel is also computed.

            Parameters
            -----------

            """
            self.x_min = x_min
            self.x_max = x_max
            self.x_pixel_scale = x_pixel_scale
            self.y_min = y_min
            self.y_max = y_max
            self.y_pixel_scale = y_pixel_scale

        def arc_second_to_pixel_index_x(self, coordinate):
            return np.floor((coordinate - self.x_min) / self.x_pixel_scale)

        def arc_second_to_pixel_index_y(self, coordinate):
            return np.floor((coordinate - self.y_min) / self.y_pixel_scale)

    def geometry_from_pix_sub_grid(self, pix_sub_grid, buffer=1e-8):
        """Determine the geometry of the rectangular grid, by alligning it with the outer-most pix_grid grid \
        plus a small buffer.

        Parameters
        -----------
        pix_sub_grid : [[float, float]]
            The x and y pix grid (or sub-coordinaates) which are to be matched with their pixels.
        buffer : float
            The size the grid-geometry is extended beyond the most exterior grid.
        """
        x_min = np.min(pix_sub_grid[:, 0]) - buffer
        x_max = np.max(pix_sub_grid[:, 0]) + buffer
        y_min = np.min(pix_sub_grid[:, 1]) - buffer
        y_max = np.max(pix_sub_grid[:, 1]) + buffer
        x_pixel_scale = (x_max - x_min) / self.shape[0]
        y_pixel_scale = (y_max - y_min) / self.shape[1]

        return self.Geometry(x_min, x_max, x_pixel_scale, y_min, y_max, y_pixel_scale)

sub_grid_size=4

lsst = profiling_data.setup_class(name='LSST', pixel_scale=0.2, sub_grid_size=sub_grid_size)
euclid = profiling_data.setup_class(name='Euclid', pixel_scale=0.1, sub_grid_size=sub_grid_size)
hst = profiling_data.setup_class(name='HST', pixel_scale=0.05, sub_grid_size=sub_grid_size)
hst_up = profiling_data.setup_class(name='HSTup', pixel_scale=0.03, sub_grid_size=sub_grid_size)
ao = profiling_data.setup_class(name='AO', pixel_scale=0.01, sub_grid_size=sub_grid_size)

pix = Rectangular()

@tools.tick_toc_x10
def lsst_solution():
    pix.geometry_from_pix_sub_grid(pix_sub_grid=lsst.grids.sub)

@tools.tick_toc_x10
def euclid_solution():
    pix.geometry_from_pix_sub_grid(pix_sub_grid=euclid.grids.sub)

@tools.tick_toc_x10
def hst_solution():
    pix.geometry_from_pix_sub_grid(pix_sub_grid=hst.grids.sub)

@tools.tick_toc_x10
def hst_up_solution():
    pix.geometry_from_pix_sub_grid(pix_sub_grid=hst_up.grids.sub)

@tools.tick_toc_x10
def ao_solution():
    pix.geometry_from_pix_sub_grid(pix_sub_grid=ao.grids.sub)


if __name__ == "__main__":
    lsst_solution()
    euclid_solution()
    hst_solution()
    hst_up_solution()
    ao_solution()