from profiling import profiling_data
from profiling import tools
from profiles import geometry_profiles

import numpy as np

class EllipticalProfile(geometry_profiles.Profile):

    def __init__(self, centre=(0.0, 0.0), axis_ratio=1.0, phi=0.0):
        """ Generic elliptical profiles class to contain functions shared by light and mass profiles.

        Parameters
        ----------
        centre: (float, float)
            The coordinates of the centre of the profiles
        axis_ratio : float
            Ratio of profiles ellipse's minor and major axes (b/a)
        phi : float
            Rotational angle of profiles ellipse counter-clockwise from positive x-axis
        """
        super(EllipticalProfile, self).__init__(centre)
        self.axis_ratio = axis_ratio
        self.phi = phi

    @property
    def phi_radians(self):
        return np.radians(self.phi)

    def grid_angle_to_profile(self, theta_grid):
        theta_coordinate_to_profile = np.add(theta_grid, - self.phi_radians)
        return np.cos(theta_coordinate_to_profile), np.sin(theta_coordinate_to_profile)

    def grid_radius_to_cartesian(self, grid, radius):
        theta_grid = np.arctan2(grid[:, 1], grid[:, 0])
        cos_theta, sin_theta = self.grid_angle_to_profile(theta_grid)
        return np.multiply(radius[:, None], np.vstack((cos_theta, sin_theta)).T)

    def transform_grid_to_reference_frame_jitted(self, grid):
        shifted_coordinates = np.subtract(grid, self.centre)
        radius = np.sqrt(np.sum(shifted_coordinates ** 2.0, 1))
        theta_coordinate_to_profile = np.arctan2(shifted_coordinates[:, 1], shifted_coordinates[:, 0]) - self.phi_radians
        transformed = np.vstack(
            (radius * np.cos(theta_coordinate_to_profile), radius * np.sin(theta_coordinate_to_profile))).T
        return transformed.view(geometry_profiles.TransformedGrid)

sub_grid_size=2

lsst = profiling_data.setup_class(name='LSST', pixel_scale=0.2, sub_grid_size=sub_grid_size)
euclid = profiling_data.setup_class(name='Euclid', pixel_scale=0.1, sub_grid_size=sub_grid_size)
hst = profiling_data.setup_class(name='HST', pixel_scale=0.05, sub_grid_size=sub_grid_size)
hst_up = profiling_data.setup_class(name='HSTup', pixel_scale=0.03, sub_grid_size=sub_grid_size)
ao = profiling_data.setup_class(name='AO', pixel_scale=0.01, sub_grid_size=sub_grid_size)

geometry = EllipticalProfile(centre=(0.0, 0.0), axis_ratio=0.8, phi=90.0)

@tools.tick_toc_x20
def lsst_solution():
    geometry.transform_grid_to_reference_frame_jitted(grid=lsst.coords.sub_grid_coords)

@tools.tick_toc_x20
def euclid_solution():
    geometry.transform_grid_to_reference_frame_jitted(grid=euclid.coords.sub_grid_coords)

@tools.tick_toc_x20
def hst_solution():
    geometry.transform_grid_to_reference_frame_jitted(grid=hst.coords.sub_grid_coords)

@tools.tick_toc_x20
def hst_up_solution():
    geometry.transform_grid_to_reference_frame_jitted(grid=hst_up.coords.sub_grid_coords)

@tools.tick_toc_x20
def ao_solution():
    geometry.transform_grid_to_reference_frame_jitted(grid=ao.coords.sub_grid_coords)


if __name__ == "__main__":
    lsst_solution()
    euclid_solution()
    hst_solution()
    hst_up_solution()
    ao_solution()