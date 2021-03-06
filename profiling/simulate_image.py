import sys
sys.path.append("../")
import os
import numpy as np
import matplotlib.pyplot as plt

from autolens.imaging import image
from autolens.imaging import mask
from autolens.profiles import light_profiles as lp
from autolens.profiles import mass_profiles as mp
from autolens.analysis import ray_tracing
from autolens.analysis import galaxy
from imaging import array_util

path =  "{}/".format(os.path.dirname(os.path.realpath(__file__)))
output_path = "{}/../profiling/data/".format(os.path.dirname(os.path.realpath(__file__)))

psf_size = (51, 51)

lens_name = 'LSST/'
pixel_scale = 0.2

lens_name = 'Euclid/'
pixel_scale = 0.1

lens_name = 'HST/'
pixel_scale = 0.05

lens_name = 'HSTup/'
pixel_scale = 0.03

lens_name = 'AO/'
pixel_scale = 0.01

psf = image.PSF.from_fits(file_path=path+'../profiling/data/psf', hdu=3, pixel_scale=pixel_scale)
psf = psf.trim(psf_size)
ma = mask.Mask.for_simulate(shape_arc_seconds=(15.0, 15.0), pixel_scale=pixel_scale, psf_size=psf_size)

image_plane_grids = mask.GridCollection.from_mask_sub_grid_size_and_blurring_shape(mask=ma, sub_grid_size=4,
                                                                                   blurring_shape=psf_size)

### Setup the ray tracing model, and use to generate the 2D galaxy image_coords ###

sersic = lp.EllipticalSersicLightProfile(centre=(0.0, 0.0), axis_ratio=0.8, phi=90.0, intensity=0.5, effective_radius=1.3,
                                         sersic_index=3.0)
isothermal = mp.EllipticalIsothermal(centre=(0.0, 0.0), axis_ratio=0.8, phi=90.0, einstein_radius=1.4)

lens_galaxy = galaxy.Galaxy(light_profile=sersic, mass_profile=isothermal)
source_galaxy = galaxy.Galaxy(light_profile=sersic)

ray_trace = ray_tracing.Tracer(lens_galaxies=[lens_galaxy], source_galaxies=[source_galaxy],
                               image_plane_grids=image_plane_grids)

galaxy_image_1d = ray_trace.galaxy_light_profiles_image_from_planes()
galaxy_image_2d = ma.map_to_2d(galaxy_image_1d)

plt.imshow(galaxy_image_2d)
plt.show()

### Setup as a simulated image_coords and output as a fits for an analysis ###

shape = galaxy_image_2d.shape
sim_image = image.Image.simulate(array=galaxy_image_2d, effective_exposure_time=np.ones(shape), pixel_scale=pixel_scale,
                                 background_sky_map=np.ones(shape), psf=psf, include_poisson_noise=True, seed=1)

if os.path.exists(output_path + lens_name) == False:
    os.makedirs(output_path + lens_name)

array_util.numpy_array_to_fits(sim_image, file_path=output_path + lens_name + 'masked_image')
array_util.numpy_array_to_fits(np.ones(sim_image.shape), file_path=output_path + lens_name + 'noise')
array_util.numpy_array_to_fits(np.ones(sim_image.shape), file_path=output_path + lens_name + 'exposure_time')
array_util.numpy_array_to_fits(psf, file_path=output_path + lens_name + '/psf')