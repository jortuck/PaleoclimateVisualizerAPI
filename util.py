import math
from matplotlib import cm
import numpy as np


def absFloorMinimum(x, y):
    """
    Takes an x and y value, find the one with the largest absolute value, and returns that value
    floored.
    """
    x = math.fabs(x)
    y = math.fabs(y)
    return math.floor(math.fabs(x if x > y else y))


def toDegreesEast(lon: int):
    """
    Converts a lon value from -180° E to 180° E, to 0° E to 360° E
    """
    if lon < 0:
        lon = lon + 360
    return lon


def get_colormap_colors(colormap, num_colors=256):
    """
    Retrieve a list of color stops from a specified colormap.
    This function extracts a series of colors from a given matplotlib colormap and returns them as a
    list of tuples. Each tuple contains a stop position (normalized between 0 and 1) and its
    corresponding color in RGBA format.

    :param colormap: Name of the matplotlib color map.
    :param num_colors: The number of colors you want the map split up into.
    """
    cmap = cm.get_cmap(colormap, num_colors)
    colors = [cmap(i) for i in range(cmap.N)]
    stops = np.linspace(0, 1, num_colors)
    stop_color_pairs = list(zip(stops, colors))
    return stop_color_pairs


def generateColorAxis(colormap_name: str) -> list:
    result = list()
    stop_color_values = get_colormap_colors(colormap_name)
    for stop, color in stop_color_values:
        str_color = "rgba(" + str(int(color[0] * 255)) + "," + str(int(color[1] * 255)) + "," + str(
            int(color[2] * 255)) + ",0.9)"
        result.append([stop, str_color])
    return result
