from autolens.imaging import mask
import time

lsst_mask = mask.Mask.circular(shape_arc_seconds=(10.0, 10.0), pixel_scale=0.2, radius_mask=4.0)
euclid_mask = mask.Mask.circular(shape_arc_seconds=(10.0, 10.0), pixel_scale=0.1, radius_mask=4.0)
hst_mask = mask.Mask.circular(shape_arc_seconds=(10.0, 10.0), pixel_scale=0.05, radius_mask=4.0)
hst_up_mask = mask.Mask.circular(shape_arc_seconds=(10.0, 10.0), pixel_scale=0.03, radius_mask=4.0)
ao_mask = mask.Mask.circular(shape_arc_seconds=(10.0, 10.0), pixel_scale=0.01, radius_mask=4.0)

repeats = 1
def tick_toc(func):
    def wrapper():
        start = time.time()
        for _ in range(repeats):
            func()

        diff = time.time() - start
        print("{}: {}".format(func.__name__, diff))

    return wrapper

@tick_toc
def lsst_current_solution():
    lsst_mask.coordinate_grid

@tick_toc
def euclid_current_solution():
    euclid_mask.coordinate_grid

@tick_toc
def hst_current_solution():
    hst_mask.coordinate_grid

@tick_toc
def hst_up_current_solution():
    hst_up_mask.coordinate_grid

@tick_toc
def ao_current_solution():
    ao_mask.coordinate_grid

if __name__ == "__main__":
    lsst_current_solution()
    euclid_current_solution()
    hst_current_solution()
    hst_up_current_solution()
    ao_current_solution()