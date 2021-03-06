from profiling import profiling_data
from profiling import tools
from analysis import ray_tracing
from analysis import galaxy
from profiles import mass_profiles
from pixelization import pixelization
from autolens import exc
import numpy as np
import pytest
import numba


sub_grid_size = 4
psf_size = (41, 41)

sie = mass_profiles.EllipticalIsothermal(centre=(0.010, 0.032), einstein_radius=1.47, axis_ratio=0.849, phi=73.6)
shear = mass_profiles.ExternalShear(magnitude=0.0663, phi=160.5)
lens_galaxy = galaxy.Galaxy(mass_profile_0=sie, mass_profile_1=shear)

source_pix = galaxy.Galaxy(pixelization=pixelization.RectangularRegConst(shape=(36, 36)))

lsst = profiling_data.setup_class(name='LSST', pixel_scale=0.2, sub_grid_size=sub_grid_size, psf_shape=psf_size)
euclid = profiling_data.setup_class(name='Euclid', pixel_scale=0.1, sub_grid_size=sub_grid_size, psf_shape=psf_size)
hst = profiling_data.setup_class(name='HST', pixel_scale=0.05, sub_grid_size=sub_grid_size, psf_shape=psf_size)
hst_up = profiling_data.setup_class(name='HSTup', pixel_scale=0.03, sub_grid_size=sub_grid_size, psf_shape=psf_size)
# ao = profiling_data.setup_class(phase_name='AO', pixel_scale=0.01, sub_grid_size=sub_grid_size, psf_shape=psf_size)

lsst_tracer = ray_tracing.Tracer(lens_galaxies=[lens_galaxy], source_galaxies=[source_pix],
                                 image_plane_grids=lsst.grids)
euclid_tracer = ray_tracing.Tracer(lens_galaxies=[lens_galaxy], source_galaxies=[source_pix],
                                   image_plane_grids=euclid.grids)
hst_tracer = ray_tracing.Tracer(lens_galaxies=[lens_galaxy], source_galaxies=[source_pix], image_plane_grids=hst.grids)
hst_up_tracer = ray_tracing.Tracer(lens_galaxies=[lens_galaxy], source_galaxies=[source_pix],
                                   image_plane_grids=hst_up.grids)
# ao_tracer = ray_tracing.Tracer(lens_galaxies=[lens_galaxy], source_galaxies=[source_pix], image_plane_grids=ao.grids)

lsst_recon = lsst_tracer.reconstructors_from_source_plane(lsst.borders, cluster_mask=None)
euclid_recon = euclid_tracer.reconstructors_from_source_plane(euclid.borders, cluster_mask=None)
hst_recon = hst_tracer.reconstructors_from_source_plane(hst.borders, cluster_mask=None)
hst_up_recon = hst_up_tracer.reconstructors_from_source_plane(hst_up.borders, cluster_mask=None)
# ao_recon = ao_tracer.reconstructors_from_source_plane(ao.borders, cluster_mask=None)

lsst_reconstructed = lsst_recon.reconstruction_from_reconstructor_and_data(lsst.masked_image, lsst.masked_image.background_noise,
                                                                           lsst.masked_image.convolver_mapping_matrix)
euclid_reconstructed = euclid_recon.reconstruction_from_reconstructor_and_data(euclid.masked_image, euclid.masked_image.background_noise,
                                                                               euclid.masked_image.convolver_mapping_matrix)
hst_reconstructed = hst_recon.reconstruction_from_reconstructor_and_data(hst.masked_image, hst.masked_image.background_noise,
                                                                         hst.masked_image.convolver_mapping_matrix)
hst_up_reconstructed = hst_up_recon.reconstruction_from_reconstructor_and_data(hst_up.masked_image, hst_up.masked_image.background_noise,
                                                                               hst_up.masked_image.convolver_mapping_matrix)
# ao_reconstructed = ao_recon.reconstruct_image(ao.masked_image, ao.masked_image.noise,
#                                                   ao.masked_image.convolver_mapping_matrix)

@tools.tick_toc_x1
def lsst_solution():
    lsst_reconstructed.regularization_term()

@tools.tick_toc_x1
def euclid_solution():
    euclid_reconstructed.regularization_term()

@tools.tick_toc_x1
def hst_solution():
    hst_reconstructed.regularization_term()

@tools.tick_toc_x1
def hst_up_solution():
    hst_up_reconstructed.regularization_term()

@tools.tick_toc_x1
def ao_solution():
    ao_reconstructed.regularization_term()

if __name__ == "__main__":
    lsst_solution()
    euclid_solution()
    hst_solution()
    hst_up_solution()
    ao_solution()