from autolens import conf
from autolens.analysis import galaxy_prior as gp
from autolens.analysis import galaxy as g
from autolens.pixelization import pixelization
from autolens.profiles import mass_profiles, light_profiles, mass_and_light_profiles
from autolens.autopipe import model_mapper as mm
import pytest
import os


class MockPriorModel:
    def __init__(self, name, cls):
        self.name = name
        self.cls = cls
        self.centre = "centre for {}".format(name)
        self.phi = "phi for {}".format(name)


class MockModelMapper:
    def __init__(self):
        self.classes = {}

    def add_class(self, name, cls):
        self.classes[name] = cls
        return MockPriorModel(name, cls)


class MockModelInstance:
    pass


@pytest.fixture(name="mass_and_light")
def make_profile():
    return mass_and_light_profiles.EllipticalSersicRadialGradientMassAndLightProfile()


@pytest.fixture(name='test_config')
def make_test_config():
    return conf.DefaultPriorConfig(
        config_folder_path="{}/../{}/priors/default".format(os.path.dirname(os.path.realpath(__file__)),
                                                            "test_files/config"))


@pytest.fixture(name="mapper")
def make_mapper():
    return mm.ModelMapper()


@pytest.fixture(name="galaxy_prior_2")
def make_galaxy_prior_2(mapper, test_config):
    galaxy_prior_2 = gp.GalaxyPrior(variable_redshift=True, light_profile=light_profiles.EllipticalDevVaucouleurs,
                                    mass_profile=mass_profiles.EllipticalCoredIsothermal, config=test_config)
    mapper.galaxy_2 = galaxy_prior_2
    return galaxy_prior_2


@pytest.fixture(name="galaxy_prior")
def make_galaxy_prior(mapper, test_config):
    galaxy_prior_1 = gp.GalaxyPrior(variable_redshift=True, light_profile=light_profiles.EllipticalDevVaucouleurs,
                                    mass_profile=mass_profiles.EllipticalCoredIsothermal, config=test_config)
    mapper.galaxy_1 = galaxy_prior_1
    return galaxy_prior_1


class TestMassAndLightProfiles(object):
    def test_constant_profile(self, mass_and_light):
        prior = gp.GalaxyPrior(profile=mass_and_light)

        assert 1 == len(prior.constant_light_profiles)
        assert 1 == len(prior.constant_mass_profiles)

    def test_make_galaxy_from_constant_profile(self, mass_and_light):
        prior = gp.GalaxyPrior(profile=mass_and_light)

        galaxy = prior.instance_for_arguments({})

        assert galaxy.light_profiles[0] == mass_and_light
        assert galaxy.mass_profiles[0] == mass_and_light

    def test_make_galaxy_from_variable_profile(self):
        galaxy_prior = gp.GalaxyPrior(profile=mass_and_light_profiles.EllipticalSersicMassAndLightProfile)

        arguments = {
            galaxy_prior.profile.centre.centre_0: 1.0,
            galaxy_prior.profile.centre.centre_1: 2.0,
            galaxy_prior.profile.axis_ratio: 4.0,
            galaxy_prior.profile.phi: 5.0,
            galaxy_prior.profile.intensity: 6.0,
            galaxy_prior.profile.effective_radius: 7.0,
            galaxy_prior.profile.sersic_index: 8.0,
            galaxy_prior.profile.mass_to_light_ratio: 3.0
        }

        galaxy = galaxy_prior.instance_for_arguments(arguments)

        assert galaxy.light_profiles[0] == galaxy.mass_profiles[0]
        assert isinstance(galaxy.light_profiles[0], mass_and_light_profiles.EllipticalSersicMassAndLightProfile)

        assert galaxy.mass_profiles[0].centre == (1., 2.)
        assert galaxy.mass_profiles[0].axis_ratio == 4.
        assert galaxy.mass_profiles[0].phi == 5.
        assert galaxy.mass_profiles[0].intensity == 6.
        assert galaxy.mass_profiles[0].effective_radius == 7.
        assert galaxy.mass_profiles[0].sersic_index == 8.
        assert galaxy.mass_profiles[0].mass_to_light_ratio == 3.


class TestGalaxyPrior:
    def test_init_to_model_mapper(self, mapper, test_config):
        mapper.galaxy_1 = gp.GalaxyPrior(variable_redshift=True, light_profile=light_profiles.EllipticalDevVaucouleurs,
                                         mass_profile=mass_profiles.EllipticalCoredIsothermal, config=test_config)
        assert len(mapper.priors_ordered_by_id) == 13

    def test_multiple_galaxies(self, mapper, test_config):
        mapper.galaxy_1 = gp.GalaxyPrior(variable_redshift=True, light_profile=light_profiles.EllipticalDevVaucouleurs,
                                         mass_profile=mass_profiles.EllipticalCoredIsothermal, config=test_config)
        mapper.galaxy_2 = gp.GalaxyPrior(variable_redshift=True, light_profile=light_profiles.EllipticalDevVaucouleurs,
                                         mass_profile=mass_profiles.EllipticalCoredIsothermal, config=test_config)
        assert len(mapper.prior_models) == 2

    def test_align_centres(self, galaxy_prior, test_config):
        prior_models = galaxy_prior.prior_models

        assert prior_models[0].centre != prior_models[1].centre

        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, light_profile=light_profiles.EllipticalDevVaucouleurs,
                                      mass_profile=mass_profiles.EllipticalCoredIsothermal,
                                      align_centres=True, config=test_config)

        prior_models = galaxy_prior.prior_models

        assert prior_models[0].centre == prior_models[1].centre

    def test_align_phis(self, galaxy_prior, test_config):
        prior_models = galaxy_prior.prior_models

        assert prior_models[0].phi != prior_models[1].phi

        prior_models = gp.GalaxyPrior(variable_redshift=True, light_profile=light_profiles.EllipticalDevVaucouleurs,
                                      mass_profile=mass_profiles.EllipticalCoredIsothermal,
                                      align_orientations=True, config=test_config).prior_models
        assert prior_models[0].phi == prior_models[1].phi


class TestNamedProfiles:
    def test_get_prior_model(self):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, light_profile=light_profiles.EllipticalSersicLightProfile,
                                      mass_profile=mass_profiles.EllipticalSersicMass)

        assert isinstance(galaxy_prior.light_profile, mm.PriorModel)
        assert isinstance(galaxy_prior.mass_profile, mm.PriorModel)

    def test_set_prior_model(self):
        mapper = mm.ModelMapper()
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, light_profile=light_profiles.EllipticalSersicLightProfile,
                                      mass_profile=mass_profiles.EllipticalSersicMass)

        mapper.galaxy = galaxy_prior

        assert 16 == len(mapper.priors_ordered_by_id)

        galaxy_prior.light_profile = mm.PriorModel(light_profiles.LightProfile)

        assert 9 == len(mapper.priors_ordered_by_id)


class TestResultForArguments:
    def test_simple_instance_for_arguments(self):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, )
        arguments = {galaxy_prior.redshift.redshift: 0.5}
        galaxy = galaxy_prior.instance_for_arguments(arguments)

        assert galaxy.redshift == 0.5

    def test_complicated_instance_for_arguments(self):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, align_centres=True,
                                      light_profile=light_profiles.EllipticalSersicLightProfile,
                                      mass_profile=mass_profiles.SphericalIsothermal)

        arguments = {galaxy_prior.redshift.redshift: 0.5,
                     galaxy_prior.mass_profile.centre.centre_0: 1.0,
                     galaxy_prior.mass_profile.centre.centre_1: 2.0,
                     galaxy_prior.mass_profile.einstein_radius: 3.0,
                     galaxy_prior.light_profile.axis_ratio: 4.0,
                     galaxy_prior.light_profile.phi: 5.0,
                     galaxy_prior.light_profile.intensity: 6.0,
                     galaxy_prior.light_profile.effective_radius: 7.0,
                     galaxy_prior.light_profile.sersic_index: 8.0}

        galaxy = galaxy_prior.instance_for_arguments(arguments)

        assert galaxy.light_profiles[0].centre[0] == 1.0
        assert galaxy.light_profiles[0].centre[1] == 2.0

    def test_gaussian_prior_model_for_arguments(self):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, align_centres=True,
                                      light_profile=light_profiles.EllipticalSersicLightProfile,
                                      mass_profile=mass_profiles.SphericalIsothermal)

        redshift_prior = mm.GaussianPrior(1, 1)
        einstein_radius_prior = mm.GaussianPrior(4, 1)
        intensity_prior = mm.GaussianPrior(7, 1)

        arguments = {galaxy_prior.redshift.redshift: redshift_prior,
                     galaxy_prior.mass_profile.centre.centre_0: mm.GaussianPrior(2, 1),
                     galaxy_prior.mass_profile.centre.centre_1: mm.GaussianPrior(3, 1),
                     galaxy_prior.mass_profile.einstein_radius: einstein_radius_prior,
                     galaxy_prior.light_profile.axis_ratio: mm.GaussianPrior(5, 1),
                     galaxy_prior.light_profile.phi: mm.GaussianPrior(6, 1),
                     galaxy_prior.light_profile.intensity: intensity_prior,
                     galaxy_prior.light_profile.effective_radius: mm.GaussianPrior(8, 1),
                     galaxy_prior.light_profile.sersic_index: mm.GaussianPrior(9, 1)}

        gaussian_galaxy_prior_model = galaxy_prior.gaussian_prior_model_for_arguments(arguments)

        assert gaussian_galaxy_prior_model.redshift.redshift == redshift_prior
        assert gaussian_galaxy_prior_model.mass_profile.einstein_radius == einstein_radius_prior
        assert gaussian_galaxy_prior_model.light_profile.intensity == intensity_prior


class TestPixelization(object):
    def test_pixelization(self, test_config):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, pixelization=pixelization.Voronoi,
                                      config=test_config)

        arguments = {galaxy_prior.redshift.redshift: 2.0,
                     galaxy_prior.pixelization.pixels: 10,
                     galaxy_prior.pixelization.regularization_coefficients.regularization_coefficients_0: 5}

        galaxy = galaxy_prior.instance_for_arguments(arguments)

        assert galaxy.pixelization.pixels == 10
        assert galaxy.pixelization.regularization_coefficients == (5,)

    def test_fixed_pixelization(self, test_config):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, pixelization=pixelization.Voronoi(),
                                      config=test_config)

        arguments = {galaxy_prior.redshift.redshift: 2.0}

        galaxy = galaxy_prior.instance_for_arguments(arguments)

        assert galaxy.pixelization.pixels == 100
        assert galaxy.pixelization.regularization_coefficients == (1.,)


class TestHyperGalaxy(object):
    def test_hyper_galaxy(self, test_config):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, hyper_galaxy=g.HyperGalaxy, config=test_config)

        arguments = {galaxy_prior.redshift.redshift: 2.0,
                     galaxy_prior.hyper_galaxy.contribution_factor: 1,
                     galaxy_prior.hyper_galaxy.noise_factor: 2,
                     galaxy_prior.hyper_galaxy.noise_power: 3}

        galaxy = galaxy_prior.instance_for_arguments(arguments)

        assert galaxy.hyper_galaxy.contribution_factor == 1
        assert galaxy.hyper_galaxy.noise_factor == 2
        assert galaxy.hyper_galaxy.noise_power == 3

    def test_fixed_hyper_galaxy(self, test_config):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, hyper_galaxy=g.HyperGalaxy(), config=test_config)

        arguments = {galaxy_prior.redshift.redshift: 2.0}

        galaxy = galaxy_prior.instance_for_arguments(arguments)

        assert galaxy.hyper_galaxy.contribution_factor == 0.
        assert galaxy.hyper_galaxy.noise_factor == 0.
        assert galaxy.hyper_galaxy.noise_power == 1.


class TestFixedProfiles(object):
    def test_fixed_light_property(self):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True,
                                      light_profile=light_profiles.EllipticalSersicLightProfile())

        assert len(galaxy_prior.constant_light_profiles) == 1

    def test_fixed_light(self):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True,
                                      light_profile=light_profiles.EllipticalSersicLightProfile())

        arguments = {galaxy_prior.redshift.redshift: 2.0}

        galaxy = galaxy_prior.instance_for_arguments(arguments)

        assert len(galaxy.light_profiles) == 1

    def test_fixed_mass_property(self):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, mass_profile=mass_profiles.SphericalNFW())

        assert len(galaxy_prior.constant_mass_profiles) == 1

    def test_fixed_mass(self):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, nass_profile=mass_profiles.SphericalNFW())

        arguments = {galaxy_prior.redshift.redshift: 2.0}

        galaxy = galaxy_prior.instance_for_arguments(arguments)

        assert len(galaxy.mass_profiles) == 1

    def test_fixed_and_variable(self):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, mass_profile=mass_profiles.SphericalNFW(),
                                      light_profile=light_profiles.EllipticalSersicLightProfile(),
                                      variable_light=light_profiles.EllipticalSersicLightProfile)

        arguments = {galaxy_prior.redshift.redshift: 2.0,
                     galaxy_prior.variable_light.axis_ratio: 4.0,
                     galaxy_prior.variable_light.phi: 5.0,
                     galaxy_prior.variable_light.intensity: 6.0,
                     galaxy_prior.variable_light.effective_radius: 7.0,
                     galaxy_prior.variable_light.sersic_index: 8.0,
                     galaxy_prior.variable_light.centre.centre_0: 0,
                     galaxy_prior.variable_light.centre.centre_1: 0}

        galaxy = galaxy_prior.instance_for_arguments(arguments)

        assert len(galaxy.light_profiles) == 2
        assert len(galaxy.mass_profiles) == 1


class TestRedshift(object):
    def test_set_redshift_class(self):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, )
        galaxy_prior.redshift = g.Redshift(3)
        assert galaxy_prior.redshift.redshift == 3

    def test_set_redshift_float(self):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, )
        galaxy_prior.redshift = 3
        # noinspection PyUnresolvedReferences
        assert galaxy_prior.redshift.redshift == 3

    def test_set_redshift_constant(self):
        galaxy_prior = gp.GalaxyPrior(variable_redshift=True, )
        galaxy_prior.redshift = mm.Constant(3)
        # noinspection PyUnresolvedReferences
        assert galaxy_prior.redshift.redshift == 3


@pytest.fixture(name="galaxy")
def make_galaxy():
    return g.Galaxy(redshift=3, sersic=light_profiles.EllipticalSersicLightProfile(),
                    exponential=light_profiles.EllipticalExponential(),
                    spherical=mass_profiles.SphericalIsothermal())


class TestFromGalaxy(object):
    def test_redshift(self, galaxy):
        galaxy_prior = gp.GalaxyPrior.from_galaxy(galaxy)

        assert galaxy_prior.redshift.redshift == 3

    def test_profiles(self, galaxy):
        galaxy_prior = gp.GalaxyPrior.from_galaxy(galaxy)

        assert galaxy_prior.sersic == galaxy.sersic
        assert galaxy_prior.exponential == galaxy.exponential
        assert galaxy_prior.spherical == galaxy.spherical

    def test_recover_galaxy(self, galaxy):
        recovered = gp.GalaxyPrior.from_galaxy(galaxy).instance_for_arguments({})

        assert recovered.sersic == galaxy.sersic
        assert recovered.exponential == galaxy.exponential
        assert recovered.spherical == galaxy.spherical
        assert recovered.redshift == galaxy.redshift

    def test_override_argument(self, galaxy):
        recovered = gp.GalaxyPrior.from_galaxy(galaxy)
        assert recovered.hyper_galaxy is None

        recovered = gp.GalaxyPrior.from_galaxy(galaxy, hyper_galaxy=g.HyperGalaxy)
        assert recovered.hyper_galaxy is not None
