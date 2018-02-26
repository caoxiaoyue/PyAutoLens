import math
import cmath
import numpy as np
from functools import wraps
import inspect
from matplotlib import pyplot
import colorsys


def plot(func, x_min=-5, y_min=-5, x_max=5, y_max=5, pixel_scale=0.1):
    """
    Draws a plot from a function that accepts coordinates . Upper normalisation limit determined by taking mean plus one
    standard deviation. Creates colour plot if the input function returns a tuple.

    func
    ----------
    function: (float, float) -> float OR (float, float)
    pixel_scale : float
        The arcsecond (") size of each pixel
    x_min : int
        The minimum x bound
    y_min : int
        The minimum y bound
    x_max : int
        The maximum x bound
    y_max : int
        The maximum y bound

    """

    def absolute(vector):
        return math.sqrt(vector[0] ** 2 + vector[1] ** 2)

    arr = array_function(function)(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max, pixel_scale=pixel_scale)

    if isinstance(arr[0][0], float):
        pyplot.imshow(arr)
        pyplot.clim(vmax=np.mean(func) + np.std(func))
    else:
        absolute_values = [absolute(t) for line in arr for t in line]
        max_value = np.mean(absolute_values) + np.std(absolute_values)

        def vector_to_color(vector):
            hue = (cmath.phase(complex(vector[0], vector[1])) + math.pi) / 2 * math.pi
            saturation = absolute(vector) / max_value
            brightness = saturation
            return map(lambda i: i if i > 0 else 0, colorsys.hsv_to_rgb(hue, saturation, brightness))

        result = []
        for row in arr:
            result.append(map(vector_to_color, row))
        pyplot.imshow(np.array(result))
    pyplot.show()


def nan_tuple(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ZeroDivisionError:
            return np.nan, np.nan
    return wrapper


def avg(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        Parameters
        ----------
        Returns
        -------
            The logical average of that collection
        """
        results = func(*args, **kwargs)
        try:
            return sum(results) / len(results)
        except TypeError:
            sum_tuple = (0, 0)
            for t in results:
                sum_tuple = (sum_tuple[0] + t[0], sum_tuple[1] + t[1])
            return sum_tuple[0] / len(results), sum_tuple[1] / len(results)

    return wrapper


def subgrid(func):
    """
    Decorator to permit generic subgridding
    Parameters
    ----------
    func : function(coordinates) -> value OR (value, value)
        Function that takes coordinates and calculates some value
    Returns
    -------
    func: function(coordinates, pixel_scale, grid_size)
        Function that takes coordinates and pixel scale/grid_size required for subgridding
    """

    @wraps(func)
    def wrapper(coordinates, pixel_scale=0.1, grid_size=1):
        """

        Parameters
        ----------
        coordinates : (float, float)
            A coordinate pair
        pixel_scale : float
            The scale of a pixel
        grid_size : int
            The side length of the subgrid (i.e. there will be grid_size^2 pixels)
        Returns
        -------
        result : [value] or [(value, value)]
            A list of results
        """

        half = pixel_scale / 2
        step = pixel_scale / (grid_size + 1)
        results = []
        for x in range(grid_size):
            for y in range(grid_size):
                x1 = coordinates[0] - half + (x + 1) * step
                y1 = coordinates[1] - half + (y + 1) * step
                results.append(func((x1, y1)))
        return results

    return wrapper


def iterative_subgrid(subgrid_func):
    """
    Decorator to iteratively increase the grid size until the difference between results reaches a defined threshold
    Parameters
    ----------
    subgrid_func : function(coordinates, pixel_scale, grid_size) -> value
        A function decorated with subgrid and average
    Returns
    -------
        A function that will iteratively increase grid size until a desired accuracy is reached
    """

    @wraps(subgrid_func)
    def wrapper(coordinates, pixel_scale=0.1, threshold=0.0001):
        """

        Parameters
        ----------
        coordinates : (float, float)
            x, y coordinates in image space
        pixel_scale : float
            The size of a pixel
        threshold : float
            The minimum difference between the result at two different grid sizes
        Returns
        -------
            The last result calculated once the difference between two results becomes lower than the threshold
        """
        last_result = None
        grid_size = 1
        while True:
            next_result = subgrid_func(coordinates, pixel_scale=pixel_scale, grid_size=grid_size)
            if last_result is not None and abs(next_result - last_result) / last_result < threshold:
                return next_result
            last_result = next_result
            grid_size += 1

    return wrapper


def array_function(func):
    """

    Parameters
    ----------
    func : function(coordinates)
            A function that takes coordinates and returns a value

    Returns
    -------
        A function that takes bounds, a pixel scale and mask and returns an array
    """

    @wraps(func)
    def wrapper(x_min=-5, y_min=-5, x_max=5, y_max=5, pixel_scale=0.1, mask=None):
        """

        Parameters
        ----------
        mask : Mask
            An object that has an is_masked method which returns True if (x, y) coordinates should be masked (i.e. not
            return a value)
        x_min : float
            The minimum x bound
        y_min : float
            The minimum y bound
        x_max : float
            The maximum x bound
        y_max : float
            The maximum y bound
        pixel_scale : float
            The arcsecond (") size of each pixel

        Returns
        -------
        array: []
            A 2D numpy array of values returned by the function at each coordinate
        """
        x_size = side_length(x_min, x_max, pixel_scale)
        y_size = side_length(y_min, y_max, pixel_scale)

        array = []

        for i in range(x_size):
            row = []
            for j in range(y_size):
                x = pixel_to_coordinate(x_min, pixel_scale, i)
                y = pixel_to_coordinate(y_min, pixel_scale, j)

                if mask is not None and not mask[i][j]:
                    row.append(None)
                else:
                    row.append(func((x, y)))
            array.append(row)
        # This conversion was to resolve a bug with putting tuples in the array. It might increase execution time.
        return np.array(array)

    return wrapper


def side_length(dim_min, dim_max, pixel_scale):
    return int((dim_max - dim_min) / pixel_scale)


def pixel_to_coordinate(dim_min, pixel_scale, pixel_coordinate):
    return dim_min + pixel_coordinate * pixel_scale


class TransformedCoordinates(tuple):
    """Coordinates that have been transformed to the coordinate system of the profiles"""

    def __init__(self, coordinates):
        super(TransformedCoordinates, self).__init__()


def transform_coordinates(func):
    """
    Wrap the function in a function that checks whether the coordinates have been transformed. If they have not been
    transformed then they are transformed. If coordinates are returned they are returned in the coordinate system in
    which they were passed in.
    Parameters
    ----------
    func : (profiles, *args, **kwargs) -> Object
        A function that requires transformed coordinates

    Returns
    -------
        A function that can except cartesian or transformed coordinates

    """

    @wraps(func)
    def wrapper(profile, coordinates, *args, **kwargs):
        """

        Parameters
        ----------
        profile : Profile
            The profiles that owns the function
        coordinates : TransformedCoordinates or (float, float)
            Coordinates in either cartesian or profiles coordinate system
        args
        kwargs

        Returns
        -------
            A value or coordinates in the same coordinate system as those passed ins
        """
        if not isinstance(coordinates, TransformedCoordinates):
            result = func(profile, profile.transform_to_reference_frame(coordinates), *args, **kwargs)
            if isinstance(result, TransformedCoordinates):
                result = profile.transform_from_reference_frame(result)
            return result
        return func(profile, coordinates, *args, **kwargs)

    return wrapper


class CoordinatesException(Exception):
    """Exception thrown when coordinates assertion fails"""

    def __init__(self, message):
        super(CoordinatesException, self).__init__(message)


class Profile(object):
    """Abstract Profile, describing an object with x, y cartesian coordinates"""

    def __init__(self, centre=(0, 0)):
        self.centre = centre

    # noinspection PyMethodMayBeStatic
    def transform_to_reference_frame(self, coordinates):
        """
        Translate Cartesian image coordinates to the lens profiles's reference frame (for a circular profiles this
        returns the input coordinates)

        Parameters
        ----------
        coordinates : (float, float)
            The x and y coordinates of the image

        Returns
        ----------
        The coordinates after the elliptical translation
        """
        raise AssertionError("Transform to reference frame should be overridden")

    @classmethod
    def from_profile(cls, profile, **kwargs):
        """
        Creates any profiles from any other profiles, keeping all attributes from the original profiles that can be passed
        into the constructor of the new profiles. Any none optional attributes required by the new profiles's constructor
        and not available as attributes of the original profiles must be passed in as key word arguments. Arguments
        matching attributes in the original profiles may be passed in to override those attributes.

        Examples
        ----------
        p = profiles.Profile(centre=(1, 1))
        elliptical_profile = profiles.EllipticalProfile.from_profile(p, axis_ratio=1, phi=2)

        elliptical_profile = profiles.EllipticalProfile(1, 2)
        profiles.Profile.from_profile(elliptical_profile).__class__ == profiles.Profile

        Parameters
        ----------
        profile: Profile
            A child of the profiles class
        kwargs
            Key word constructor arguments for the new profiles
        Returns
        -------

        """
        arguments = vars(profile)
        arguments.update(kwargs)
        init_args = inspect.getargspec(cls.__init__).args
        arguments = {argument[0]: argument[1] for argument in arguments.items() if argument[0] in init_args}
        return cls(**arguments)

    # noinspection PyMethodMayBeStatic
    def transform_from_reference_frame(self, coordinates):
        """

        Parameters
        ----------
        coordinates: TransformedCoordinates
            Coordinates that have been transformed to the reference frame of the profiles
        Returns
        -------
        coordinates: (float, float)
            Coordinates that are back in the original reference frame
        """
        raise AssertionError("Transform from reference frame should be overridden")

    @property
    def x_cen(self):
        return self.centre[0]

    @property
    def y_cen(self):
        return self.centre[1]

    def coordinates_to_centre(self, coordinates):
        """
        Converts image coordinates to profiles's centre

        Parameters
        ----------
        coordinates : (float, float)
            The x and y coordinates of the image

        Returns
        ----------
        The coordinates at the mass profiles centre
        """
        return coordinates[0] - self.x_cen, coordinates[1] - self.y_cen

    def coordinates_from_centre(self, coordinates):
        return coordinates[0] + self.x_cen, coordinates[1] + self.y_cen

    def coordinates_to_radius(self, coordinates):
        """
        Convert the coordinates to a radius

        Parameters
        ----------
        coordinates : (float, float)
            The image coordinates (x, y)

        Returns
        -------
        The radius at those coordinates
        """
        shifted_coordinates = self.coordinates_to_centre(coordinates)
        return math.sqrt(shifted_coordinates[0] ** 2 + shifted_coordinates[1] ** 2)


class EllipticalProfile(Profile):
    """Generic elliptical profiles class to contain functions shared by light and mass profiles"""

    def __init__(self, axis_ratio, phi, centre=(0, 0)):
        """
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
    def cos_phi(self):
        return self.angles_from_x_axis()[0]

    @property
    def sin_phi(self):
        return self.angles_from_x_axis()[1]

    def angles_from_x_axis(self):
        """
        Determine the sin and cosine of the angle between the profiles ellipse and positive x-axis, \
        defined counter-clockwise from x.

        Returns
        -------
        The sin and cosine of the angle
        """
        phi_radians = math.radians(self.phi)
        return math.cos(phi_radians), math.sin(phi_radians)

    @transform_coordinates
    def coordinates_to_eccentric_radius(self, coordinates):
        """
        Convert the coordinates to a radius in elliptical space.

        Parameters
        ----------
        coordinates : (float, float)
            The image coordinates (x, y)
        Returns
        -------
        The radius at those coordinates
        """

        return math.sqrt(self.axis_ratio) * math.sqrt(
            coordinates[0] ** 2 + (coordinates[1] / self.axis_ratio) ** 2)

    def coordinates_angle_to_profile(self, theta):
        """
        Compute the sin and cosine of the angle between the shifted coordinates and elliptical profiles

        Parameters
        ----------
        theta : Float

        Returns
        ----------
        The sin and cosine of the angle between the shifted coordinates and profiles ellipse.
        """
        theta_coordinate_to_profile = math.radians(theta - self.phi)
        return math.cos(theta_coordinate_to_profile), math.sin(theta_coordinate_to_profile)

    def coordinates_angle_from_x(self, coordinates):
        """
        Compute the angle between the coordinates and positive x-axis, defined counter-clockwise. Elliptical profiles
        are symmetric after 180 degrees, so angles above 180 are converted to their equivalent value from 0.
        (e.g. 225 degrees counter-clockwise from the x-axis is equivalent to 45 degrees counter-clockwise)

        Parameters
        ----------
        coordinates : (float, float)
            The x and y coordinates of the image.

        Returns
        ----------
        The angle between the coordinates and the x-axis and profiles centre
        """
        shifted_coordinates = self.coordinates_to_centre(coordinates)
        return math.degrees(np.arctan2(shifted_coordinates[1], shifted_coordinates[0]))

    def rotate_coordinates_from_profile(self, coordinates_elliptical):
        """Rotate elliptical coordinates from the reference frame of the profiles back to the image-plane Cartsian grid
         (coordinates are not shifted away from the lens profiles centre)."""
        x_elliptical = coordinates_elliptical[0]
        x = (x_elliptical * self.cos_phi - coordinates_elliptical[1] * self.sin_phi)
        y = (+x_elliptical * self.sin_phi + coordinates_elliptical[1] * self.cos_phi)
        return x, y

    @transform_coordinates
    def coordinates_to_elliptical_radius(self, coordinates):
        """
        Convert coordinates which are already transformed to an elliptical radius.

        Parameters
        ----------
        coordinates : (float, float)
            The image coordinates (x, y)
        Returns
        -------
        The radius at those coordinates
        """
        return math.sqrt(coordinates[0] ** 2 + (coordinates[1] / self.axis_ratio) ** 2)

    def coordinates_radius_to_x_and_y(self, coordinates, radius):
        """Decomposed a coordinate at a given radius r into its x and y vectors

        Parameters
        ----------
        coordinates : (float, float)
            The image coordinates (x, y)
        radius : float
            The radius r from the centre of the coordinate reference frame.

        Returns
        ----------
        The coordinates after the decomposed into x and y components"""
        theta_from_x = math.degrees(np.arctan2(coordinates[1], coordinates[0]))
        cos_theta, sin_theta = self.coordinates_angle_to_profile(theta_from_x)
        return radius * cos_theta, radius * sin_theta

    def transform_from_reference_frame(self, coordinates_elliptical):
        """
        Rotate elliptical coordinates back to the original Cartesian grid (for a circular profiles this
        returns the input coordinates)

        Parameters
        ----------
        coordinates_elliptical : TransformedCoordinates(float, float)
            The x and y coordinates of the image translated to the elliptical coordinate system

        Returns
        ----------
        The coordinates (typically deflection angles) on a regular Cartesian grid
        """

        if not isinstance(coordinates_elliptical, TransformedCoordinates):
            raise CoordinatesException("Can't return cartesian coordinates to cartesian coordinates. Did you remember"
                                       " to explicitly make the elliptical coordinates TransformedCoordinates?")

        x, y = self.rotate_coordinates_from_profile(coordinates_elliptical)
        return self.coordinates_from_centre((x, y))

    def transform_to_reference_frame(self, coordinates):
        """
        Translate Cartesian image coordinates to the lens profiles's reference frame (for a circular profiles this
        returns the input coordinates)

        Parameters
        ----------
        coordinates : (float, float)
            The x and y coordinates of the image

        Returns
        ----------
        The coordinates after the elliptical translation
        """

        if isinstance(coordinates, TransformedCoordinates):
            raise CoordinatesException("Trying to transform already transformed coordinates")

        # Compute distance of coordinates to the lens profiles centre
        radius = self.coordinates_to_radius(coordinates)

        # Compute the angle between the coordinates and x-axis
        theta_from_x = self.coordinates_angle_from_x(coordinates)

        # Compute the angle between the coordinates and profiles ellipse
        cos_theta, sin_theta = self.coordinates_angle_to_profile(theta_from_x)

        # Multiply by radius to get their x / y distance from the profiles centre in this elliptical unit system
        return TransformedCoordinates((radius * cos_theta, radius * sin_theta))

    def eta_u(self, u, coordinates):
        return math.sqrt((u * ((coordinates[0] ** 2) + (coordinates[1] ** 2 / (1 - (1 - self.axis_ratio ** 2) * u)))))


class SphericalProfile(EllipticalProfile):
    """Generic circular profiles class to contain functions shared by light and mass profiles"""

    def __init__(self, centre=(0, 0)):
        """
        Parameters
        ----------
        centre: (float, float)
            The coordinates of the centre of the profiles
        """
        super(SphericalProfile, self).__init__(1.0, 0.0, centre)