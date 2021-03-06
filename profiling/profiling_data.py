import os
import pickle

from autolens.imaging import scaled_array
from autolens.imaging import image
from autolens.imaging import mask
from autolens.imaging import masked_image

path =  "{}/".format(os.path.dirname(os.path.realpath(__file__)))

def load_data(name, pixel_scale, psf_shape):
    im = scaled_array.ScaledArray.from_fits_with_scale(file_path=path + 'data/' + name + '/masked_image', hdu=0, pixel_scale=pixel_scale)
    noise = scaled_array.ScaledArray.from_fits_with_scale(file_path=path + 'data/' + name + '/noise', hdu=0, pixel_scale=pixel_scale)
    exposure_time = scaled_array.ScaledArray.from_fits_with_scale(file_path=path + 'data/' + name + '/exposure_time', hdu=0,
                                                                  pixel_scale=pixel_scale)
    psf = image.PSF.from_fits(file_path=path + 'data/LSST/psf', hdu=0, pixel_scale=pixel_scale).trim(psf_shape)

    return im, noise, exposure_time, psf

def setup_class(name, pixel_scale, radius_mask=4.0, psf_shape=(21,21), sub_grid_size=4):

    def pickle_path():
        return path + 'data/' + name + '/pickle/r' + str(radius_mask) + '_psf' + str(psf_shape[0]) + '_sub' + \
               str(sub_grid_size)

    if not os.path.isdir(path + 'data/' + name + '/pickle'):
        os.mkdir(path + 'data/' + name + '/pickle')

    if not os.path.isfile(pickle_path()):
        return Data(name, pixel_scale, radius_mask, psf_shape, sub_grid_size)
    elif os.path.isfile(pickle_path()):
        with open(pickle_path(), 'rb') as pickle_file:
             thing=pickle.load(file=pickle_file)
        return thing


class Data(object):

    def __init__(self, name, pixel_scale, radius_mask=4.0, psf_shape=(21, 21), sub_grid_size=4):

        def pickle_path():
            return path + 'data/' + name + '/pickle/r' + str(radius_mask) + '_psf' + str(psf_shape[0]) + '_sub' + \
                   str(sub_grid_size)

        im, noise, exposure_time, psf = load_data(name=name, pixel_scale=pixel_scale, psf_shape=psf_shape)

        im = image.Image(array=im, effective_exposure_time=exposure_time, pixel_scale=pixel_scale, psf=psf,
                         background_noise=noise, poisson_noise=noise)

        ma = mask.Mask.circular(shape_arc_seconds=im.shape_arc_seconds, pixel_scale=im.pixel_scale,
                                radius_mask=radius_mask)

        self.masked_image = masked_image.MaskedImage(image=im, mask=ma)

        self.grids = mask.GridCollection.from_mask_sub_grid_size_and_blurring_shape(mask=ma,
                                                                                   sub_grid_size=sub_grid_size,
                                                                                   blurring_shape=psf.shape)

        self.borders = mask.BorderCollection.from_mask_and_sub_grid_size(mask=ma, sub_grid_size=sub_grid_size)

        with open(pickle_path(), 'wb') as pickle_file:
            pickle.dump(self, file=pickle_file)
