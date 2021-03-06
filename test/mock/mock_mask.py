import numpy as np

from autolens.imaging import mask


class MockSubGridCoords(np.ndarray):
    def __new__(cls, sub_grid_coords, *args, **kwargs):
        return sub_grid_coords.view(cls)

    def __init__(self, sub_grid_coords, sub_to_image, sub_grid_size):
        # noinspection PyArgumentList
        super().__init__()
        self.sub_grid_coords = sub_grid_coords
        self.sub_to_image = sub_to_image
        self.no_pixels = sub_to_image.shape[0]
        self.sub_grid_size = sub_grid_size
        self.sub_grid_length = int(sub_grid_size ** 2.0)
        self.sub_grid_fraction = 1.0 / self.sub_grid_length


class MockGridCollection(object):

    def __init__(self, image, sub, blurring=None):
        self.image = mask.ImageGrid(image)
        self.sub = sub
        self.blurring = mask.ImageGrid(blurring) if blurring is not None else None


class MockBorderCollection(object):

    def __init__(self, image, sub):

        self.image = image
        self.sub = sub

    @classmethod
    def from_mask_and_subgrid_size(cls, mask, subgrid_size, polynomial_degree=3, centre=(0.0, 0.0)):
        image_border = ImageGridBorder.from_mask(mask, polynomial_degree, centre)
        sub_border = SubGridBorder.from_mask(mask, subgrid_size, polynomial_degree, centre)
        return BorderCollection(image_border, sub_border)

    def relocated_grids_from_grids(self, grids):
        return MockGridCollection(image=self.image.relocated_grid_from_grid(grids.image),
                              sub=MockSubGridCoords(self.sub.relocated_grid_from_grid(grids.sub), grids.sub.sub_to_image,
                                                    grids.sub.sub_grid_size),
                              blurring=None)
