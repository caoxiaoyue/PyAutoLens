from auto_lens.analysis import model_mapper
import pytest
from auto_lens.profiles import geometry_profiles, light_profiles, mass_profiles

import os

data_path = "{}/../".format(os.path.dirname(os.path.realpath(__file__)))


@pytest.fixture(name='uniform_simple')
def make_uniform_simple():
    return model_mapper.UniformPrior(lower_limit=0., upper_limit=1.)


@pytest.fixture(name='uniform_half')
def make_uniform_half():
    return model_mapper.UniformPrior(lower_limit=0.5, upper_limit=1.)


@pytest.fixture(name='test_config')
def make_test_config():
    return model_mapper.Config(
        config_folder_path="{}/../{}".format(os.path.dirname(os.path.realpath(__file__)), "test_files/config"))


class TestUniformPrior(object):
    def test__simple_assumptions(self, uniform_simple):
        assert uniform_simple.value_for(0.) == 0.
        assert uniform_simple.value_for(1.) == 1.
        assert uniform_simple.value_for(0.5) == 0.5

    def test__non_zero_lower_limit(self, uniform_half):
        assert uniform_half.value_for(0.) == 0.5
        assert uniform_half.value_for(1.) == 1.
        assert uniform_half.value_for(0.5) == 0.75


class MockClass(object):
    def __init__(self, one, two):
        self.one = one
        self.two = two


class MockConfig(model_mapper.Config):
    def __init__(self, d=None):
        super(MockConfig, self).__init__("")
        if d is not None:
            self.d = d
        else:
            self.d = {}

    def get_for_nearest_ancestor(self, cls, attribute_name):
        return self.get(None, cls.__name__, attribute_name)

    def get(self, _, class_name, var_name):
        try:
            return self.d[class_name][var_name]
        except KeyError:
            return ["u", 0, 1]


class MockProfile(object):
    def __init__(self, centre=(0.0, 0.0), intensity=0.1):
        self.centre = centre
        self.intensity = intensity


# noinspection PyUnresolvedReferences
class TestModelingCollection(object):
    def test__argument_extraction(self):
        collection = model_mapper.ModelMapper(MockConfig())
        collection.add_class("mock_class", MockClass)
        assert 1 == len(collection.prior_models)

        assert len(collection.priors_ordered_by_id) == 2

    def test_config_limits(self):
        collection = model_mapper.ModelMapper(MockConfig({"MockClass": {"one": ["u", 1., 2.]}}))

        collection.add_class("mock_class", MockClass)

        assert collection.mock_class.one.lower_limit == 1.
        assert collection.mock_class.one.upper_limit == 2.

    def test_config_prior_type(self):
        collection = model_mapper.ModelMapper(MockConfig({"MockClass": {"one": ["g", 1., 2.]}}))

        collection.add_class("mock_class", MockClass)

        assert isinstance(collection.mock_class.one, model_mapper.GaussianPrior)

        assert collection.mock_class.one.mean == 1.
        assert collection.mock_class.one.sigma == 2.

    def test_attribution(self):
        collection = model_mapper.ModelMapper(MockConfig())

        collection.add_class("mock_class", MockClass)

        assert hasattr(collection, "mock_class")
        assert hasattr(collection.mock_class, "one")

    def test_tuple_arg(self):
        collection = model_mapper.ModelMapper(MockConfig())

        collection.add_class("mock_profile", MockProfile)

        assert 3 == len(collection.priors_ordered_by_id)


# noinspection PyUnresolvedReferences
class TestModelInstance(object):

    def test_simple_model(self):
        collection = model_mapper.ModelMapper(MockConfig())

        collection.add_class("mock_class", MockClass)

        model_map = collection.from_unit_vector([1., 1.])

        assert isinstance(model_map.mock_class, MockClass)
        assert model_map.mock_class.one == 1.
        assert model_map.mock_class.two == 1.

    def test_two_object_model(self):
        collection = model_mapper.ModelMapper(MockConfig())

        collection.add_class("mock_class_1", MockClass)
        collection.add_class("mock_class_2", MockClass)

        model_map = collection.from_unit_vector([1., 0., 0., 1.])

        assert isinstance(model_map.mock_class_1, MockClass)
        assert isinstance(model_map.mock_class_2, MockClass)

        assert model_map.mock_class_1.one == 1.
        assert model_map.mock_class_1.two == 0.

        assert model_map.mock_class_2.one == 0.
        assert model_map.mock_class_2.two == 1.

    def test_swapped_prior_construction(self):
        collection = model_mapper.ModelMapper(MockConfig())

        collection.add_class("mock_class_1", MockClass)
        collection.add_class("mock_class_2", MockClass)

        collection.mock_class_2.one = collection.mock_class_1.one

        model_map = collection.from_unit_vector([1., 0., 0.])

        assert isinstance(model_map.mock_class_1, MockClass)
        assert isinstance(model_map.mock_class_2, MockClass)

        assert model_map.mock_class_1.one == 1.
        assert model_map.mock_class_1.two == 0.

        assert model_map.mock_class_2.one == 1.
        assert model_map.mock_class_2.two == 0.

    def test_prior_replacement(self):
        collection = model_mapper.ModelMapper(MockConfig())

        collection.add_class("mock_class", MockClass)

        collection.mock_class.one = model_mapper.UniformPrior(100, 200)

        model_map = collection.from_unit_vector([0., 0.])

        assert model_map.mock_class.one == 100.

    def test_tuple_arg(self):
        collection = model_mapper.ModelMapper(MockConfig())

        collection.add_class("mock_profile", MockProfile)

        model_map = collection.from_unit_vector([1., 0., 0.])

        assert model_map.mock_profile.centre == (1., 0.)
        assert model_map.mock_profile.intensity == 0.

    def test_modify_tuple(self):
        collection = model_mapper.ModelMapper(MockConfig())

        collection.add_class("mock_profile", MockProfile)

        collection.mock_profile.centre.centre_0 = model_mapper.UniformPrior(1., 10.)

        model_map = collection.from_unit_vector([1., 1., 1.])

        assert model_map.mock_profile.centre == (10., 1.)

    def test_match_tuple(self):
        collection = model_mapper.ModelMapper(MockConfig())

        collection.add_class("mock_profile", MockProfile)

        collection.mock_profile.centre.centre_1 = collection.mock_profile.centre.centre_0

        model_map = collection.from_unit_vector([1., 0.])

        assert model_map.mock_profile.centre == (1., 1.)
        assert model_map.mock_profile.intensity == 0.


# noinspection PyUnresolvedReferences
class TestRealClasses(object):

    def test_combination(self):
        collection = model_mapper.ModelMapper(MockConfig(), source_light_profile=light_profiles.EllipticalSersic,
                                              lens_mass_profile=mass_profiles.EllipticalCoredIsothermal,
                                              lens_light_profile=light_profiles.EllipticalCoreSersic)

        model_map = collection.from_unit_vector(
            [1 for _ in range(len(collection.priors_ordered_by_id))])

        assert isinstance(model_map.source_light_profile, light_profiles.EllipticalSersic)
        assert isinstance(model_map.lens_mass_profile, mass_profiles.EllipticalCoredIsothermal)
        assert isinstance(model_map.lens_light_profile, light_profiles.EllipticalCoreSersic)


# noinspection PyUnresolvedReferences
class TestConfigFunctions:

    def test_loading_config(self, test_config):
        config = test_config

        assert ['u', 0, 1.0] == config.get("geometry_profiles", "Profile", "centre_0")
        assert ['u', 0, 1.0] == config.get("geometry_profiles", "Profile", "centre_1")

    def test_model_from_unit_vector(self, test_config):
        collection = model_mapper.ModelMapper(test_config,
                                              geometry_profile=geometry_profiles.Profile)

        model_map = collection.from_unit_vector([1., 1.])

        assert model_map.geometry_profile.centre == (1., 1.0)

    def test_model_from_physical_vector(self, test_config):
        collection = model_mapper.ModelMapper(test_config,
                                              geometry_profile=geometry_profiles.Profile)

        model_map = collection.from_physical_vector([10., 50.])

        assert model_map.geometry_profile.centre == (10., 50.0)

    def test_inheritance(self, test_config):
        collection = model_mapper.ModelMapper(test_config,
                                              geometry_profile=geometry_profiles.EllipticalProfile)

        model_map = collection.from_unit_vector([1., 1., 1., 1.])

        assert model_map.geometry_profile.centre == (1.0, 1.0)

    def test_true_config(self, test_config):
        config = test_config

        collection = model_mapper.ModelMapper(config=config,
                                              sersic_light_profile=light_profiles.EllipticalSersic,
                                              elliptical_profile_1=geometry_profiles.EllipticalProfile,
                                              elliptical_profile_2=geometry_profiles.EllipticalProfile,
                                              spherical_profile=geometry_profiles.SphericalProfile,
                                              exponential_light_profile=light_profiles.EllipticalExponential)

        model_map = collection.from_unit_vector(
            [1 for _ in range(len(collection.priors_ordered_by_id))])

        assert isinstance(model_map.elliptical_profile_1, geometry_profiles.EllipticalProfile)
        assert isinstance(model_map.elliptical_profile_2, geometry_profiles.EllipticalProfile)
        assert isinstance(model_map.spherical_profile, geometry_profiles.SphericalProfile)

        assert isinstance(model_map.sersic_light_profile, light_profiles.EllipticalSersic)
        assert isinstance(model_map.exponential_light_profile, light_profiles.EllipticalExponential)


# noinspection PyUnresolvedReferences
class TestHyperCube:

    def test__in_order_of_class_constructor__one_profile(self, test_config):
        collection = model_mapper.ModelMapper(
            test_config,
            geometry_profile=geometry_profiles.EllipticalProfile)

        assert collection.physical_values_ordered_by_class([0.5, 0.5, 0.5, 0.5]) == [1.0, 0.5, 0.5, 1.0]

    def test__in_order_of_class_constructor__multiple_profiles(self, test_config):
        collection = model_mapper.ModelMapper(
            test_config,
            profile_1=geometry_profiles.EllipticalProfile, profile_2=geometry_profiles.Profile,
            profile_3=geometry_profiles.EllipticalProfile)

        unit_vector = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]

        assert collection.physical_values_ordered_by_class(unit_vector) == [1.0, 0.5, 0.5, 1.0, 0.5, 0.5, 1.0, 0.5, 0.5,
                                                                            1.0]

    def test__in_order_of_class_constructor__multiple_profiles_bigger_range_of_unit_values(self, test_config):
        collection = model_mapper.ModelMapper(
            test_config,
            profile_1=geometry_profiles.EllipticalProfile, profile_2=geometry_profiles.Profile,
            profile_3=geometry_profiles.EllipticalProfile)

        unit_vector = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

        assert collection.physical_values_ordered_by_class(unit_vector) == [0.6, 0.1, 0.2, 0.8, 0.5, 0.6, 1.8, 0.7, 0.8,
                                                                            2.0]

    def test__order_maintained_with_prior_change(self, test_config):
        collection = model_mapper.ModelMapper(
            test_config,
            profile_1=geometry_profiles.EllipticalProfile, profile_2=geometry_profiles.Profile,
            profile_3=geometry_profiles.EllipticalProfile)

        unit_vector = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]

        before = collection.physical_values_ordered_by_class(unit_vector)

        collection.profile_1.axis_ratio = model_mapper.UniformPrior(0, 2)

        assert collection.physical_values_ordered_by_class(unit_vector) == before


# noinspection PyUnresolvedReferences
class TestModelInstancesRealClasses:

    def test__in_order_of_class_constructor__one_profile(self, test_config):
        collection = model_mapper.ModelMapper(
            test_config,
            profile_1=geometry_profiles.EllipticalProfile)

        model_map = collection.from_unit_vector([0.25, 0.5, 0.75, 1.0])

        assert model_map.profile_1.centre == (0.25, 0.5)
        assert model_map.profile_1.axis_ratio == 1.5
        assert model_map.profile_1.phi == 2.0

    def test__in_order_of_class_constructor___multiple_profiles(self, test_config):
        collection = model_mapper.ModelMapper(
            test_config,
            profile_1=geometry_profiles.EllipticalProfile, profile_2=geometry_profiles.Profile,
            profile_3=geometry_profiles.EllipticalProfile)

        model_map = collection.from_unit_vector([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

        assert model_map.profile_1.centre == (0.1, 0.2)
        assert model_map.profile_1.axis_ratio == 0.6
        assert model_map.profile_1.phi == 0.8

        assert model_map.profile_2.centre == (0.5, 0.6)

        assert model_map.profile_3.centre == (0.7, 0.8)
        assert model_map.profile_3.axis_ratio == 1.8
        assert model_map.profile_3.phi == 2.0

    def test__check_order_for_different_unit_values(self, test_config):
        collection = model_mapper.ModelMapper(
            test_config,
            profile_1=geometry_profiles.EllipticalProfile, profile_2=geometry_profiles.Profile,
            profile_3=geometry_profiles.EllipticalProfile)

        collection.profile_1.centre.centre_0 = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_1.centre.centre_1 = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_1.axis_ratio = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_1.phi = model_mapper.UniformPrior(0.0, 1.0)

        collection.profile_2.centre.centre_0 = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_2.centre.centre_1 = model_mapper.UniformPrior(0.0, 1.0)

        collection.profile_3.centre.centre_0 = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_3.centre.centre_1 = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_3.axis_ratio = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_3.phi = model_mapper.UniformPrior(0.0, 1.0)

        model_map = collection.from_unit_vector([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

        assert model_map.profile_1.centre == (0.1, 0.2)
        assert model_map.profile_1.axis_ratio == 0.3
        assert model_map.profile_1.phi == 0.4

        assert model_map.profile_2.centre == (0.5, 0.6)

        assert model_map.profile_3.centre == (0.7, 0.8)
        assert model_map.profile_3.axis_ratio == 0.9
        assert model_map.profile_3.phi == 1.0

    # TODO : It doesnt totally make sense to me why this one works tbh...

    def test__check_order_for_different_unit_values_and_set_priors_equal_to_one_another(self, test_config):
        collection = model_mapper.ModelMapper(
            test_config,
            profile_1=geometry_profiles.EllipticalProfile, profile_2=geometry_profiles.Profile,
            profile_3=geometry_profiles.EllipticalProfile)

        collection.profile_1.centre.centre_0 = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_1.centre.centre_1 = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_1.axis_ratio = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_1.phi = model_mapper.UniformPrior(0.0, 1.0)

        collection.profile_2.centre.centre_0 = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_2.centre.centre_1 = model_mapper.UniformPrior(0.0, 1.0)

        collection.profile_3.centre.centre_0 = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_3.centre.centre_1 = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_3.axis_ratio = model_mapper.UniformPrior(0.0, 1.0)
        collection.profile_3.phi = model_mapper.UniformPrior(0.0, 1.0)

        collection.profile_1.axis_ratio = collection.profile_1.phi
        collection.profile_3.centre.centre_1 = collection.profile_2.centre.centre_1

        model_map = collection.from_unit_vector([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])

        assert model_map.profile_1.centre == (0.2, 0.3)
        assert model_map.profile_1.axis_ratio == 0.4
        assert model_map.profile_1.phi == 0.4

        assert model_map.profile_2.centre == (0.5, 0.6)

        assert model_map.profile_3.centre == (0.7, 0.6)
        assert model_map.profile_3.axis_ratio == 0.8
        assert model_map.profile_3.phi == 0.9

    def test__check_order_for_physical_values(self, test_config):
        collection = model_mapper.ModelMapper(
            test_config,
            profile_1=geometry_profiles.EllipticalProfile, profile_2=geometry_profiles.Profile,
            profile_3=geometry_profiles.EllipticalProfile)

        model_map = collection.from_physical_vector(
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

        assert model_map.profile_1.centre == (0.1, 0.2)
        assert model_map.profile_1.axis_ratio == 0.3
        assert model_map.profile_1.phi == 0.4

        assert model_map.profile_2.centre == (0.5, 0.6)

        assert model_map.profile_3.centre == (0.7, 0.8)
        assert model_map.profile_3.axis_ratio == 0.9
        assert model_map.profile_3.phi == 1.0

    def test__from_prior_medians__one_model(self, test_config):
        collection = model_mapper.ModelMapper(
            test_config,
            profile_1=geometry_profiles.EllipticalProfile)

        model_map = collection.from_prior_medians()

        model_2 = collection.from_unit_vector([0.5, 0.5, 0.5, 0.5])

        assert model_map.profile_1.centre == model_2.profile_1.centre == (0.5, 0.5)
        assert model_map.profile_1.axis_ratio == model_2.profile_1.axis_ratio == 1.0
        assert model_map.profile_1.phi == model_2.profile_1.phi == 1.0

    def test__from_prior_medians__multiple_models(self, test_config):
        collection = model_mapper.ModelMapper(
            test_config,
            profile_1=geometry_profiles.EllipticalProfile, profile_2=geometry_profiles.Profile,
            profile_3=geometry_profiles.EllipticalProfile)

        model_map = collection.from_prior_medians()

        model_2 = collection.from_unit_vector([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])

        assert model_map.profile_1.centre == model_2.profile_1.centre == (0.5, 0.5)
        assert model_map.profile_1.axis_ratio == model_2.profile_1.axis_ratio == 1.0
        assert model_map.profile_1.phi == model_2.profile_1.phi == 1.0

        assert model_map.profile_2.centre == model_2.profile_2.centre == (0.5, 0.5)

        assert model_map.profile_3.centre == model_2.profile_3.centre == (0.5, 0.5)
        assert model_map.profile_3.axis_ratio == model_2.profile_3.axis_ratio == 1.0
        assert model_map.profile_3.phi == model_2.profile_3.phi == 1.0

    def test__from_prior_medians__one_model__set_one_parameter_to_another(self, test_config):
        collection = model_mapper.ModelMapper(
            test_config,
            profile_1=geometry_profiles.EllipticalProfile)

        collection.profile_1.axis_ratio = collection.profile_1.phi

        model_map = collection.from_prior_medians()

        model_2 = collection.from_unit_vector([0.5, 0.5, 0.5])

        assert model_map.profile_1.centre == model_2.profile_1.centre == (0.5, 0.5)
        assert model_map.profile_1.axis_ratio == model_2.profile_1.axis_ratio == 1.0
        assert model_map.profile_1.phi == model_2.profile_1.phi == 1.0


# noinspection PyUnresolvedReferences
class TestUtility(object):

    def test_class_priors_dict(self):
        collection = model_mapper.ModelMapper(MockConfig(), mock_class=MockClass)

        assert list(collection.class_priors_dict.keys()) == ["mock_class"]
        assert len(collection.class_priors_dict["mock_class"]) == 2

        collection = model_mapper.ModelMapper(MockConfig(), mock_class_1=MockClass, mock_class_2=MockClass)

        collection.mock_class_1.one = collection.mock_class_2.one
        collection.mock_class_1.two = collection.mock_class_2.two

        assert collection.class_priors_dict["mock_class_1"] == collection.class_priors_dict["mock_class_2"]

    def test_value_vector_for_hypercube_vector(self):
        collection = model_mapper.ModelMapper(MockConfig(), mock_class=MockClass)

        collection.mock_class.two = model_mapper.UniformPrior(upper_limit=100.)

        assert collection.physical_values_ordered_by_class([1., 0.5]) == [1., 50.]


class TestPriorReplacement(object):
    def test_prior_replacement(self):
        mapper = model_mapper.ModelMapper(MockConfig(), mock_class=MockClass)
        result = mapper.prior_results_for_gaussian_tuples(
            [(10, 3), (5, 3)])

        assert isinstance(result.mock_class.one, model_mapper.GaussianPrior)

    def test_replace_priors_with_gaussians_from_tuples(self):
        mapper = model_mapper.ModelMapper(MockConfig(), mock_class=MockClass)
        result = mapper.prior_results_for_gaussian_tuples([(10, 3), (5, 3)])

        assert isinstance(result.mock_class.one, model_mapper.GaussianPrior)

    def test_replacing_priors_for_profile(self):
        mapper = model_mapper.ModelMapper(MockConfig(), mock_class=MockProfile)
        result = mapper.prior_results_for_gaussian_tuples(
            [(10, 3), (5, 3), (5, 3)])

        assert isinstance(result.mock_class.centre.priors[0][1], model_mapper.GaussianPrior)
        assert isinstance(result.mock_class.centre.priors[1][1], model_mapper.GaussianPrior)
        assert isinstance(result.mock_class.intensity, model_mapper.GaussianPrior)
