# This file loops over all the datasets defined in data.py, then converts them to zarr.
from data import datasets, instrumental
import xarray as xr
for key in datasets.keys():
    for set in datasets[key]["variables"].values():
        dataset = xr.open_dataset(set)
        dataset.to_zarr(set+".zarr", mode="w")
for key in instrumental.keys():
    for set in instrumental[key]["variables"].values():
        dataset = xr.open_dataset(set)
        dataset.to_zarr(set+".zarr",mode="w")