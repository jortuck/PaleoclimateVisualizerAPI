from memory_profiler import profile
from fastapi import FastAPI, HTTPException, Request, Response, Query, Path
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from scipy.stats import pearsonr
from util import absFloorMinimum, toDegreesEast, generateColorAxis
from data import variables, datasets, instrumental
from mangum import Mangum
import xarray as xr
import polars as pl
@profile
def timeSeriesArea(variable: str, n: int, s: int, start: int, stop: int):
    result = []
    lats = np.arange(np.min([n, s]), np.max([n, s]) + 1)
    start = toDegreesEast(start)
    stop = toDegreesEast(stop)
    if start < stop:
        lons = np.arange(np.min([start, stop]), np.max([start, stop]) + 1)
    elif start == stop:
        lons = np.array([start])
    else:
        lons = np.concatenate((np.arange(start, 361), np.arange(0, stop + 1)))

    era5_variable = variable
    if variable == "us" or variable == "u10":
        era5_variable = "u1000"
    elif variable == "v10":
        era5_variable = "v1000"

    era5_dataset = xr.open_dataset(instrumental["era5"]["variables"][era5_variable]+".zarr",engine="zarr")
    time_condition = era5_dataset['time'] <= 2005
    lat_condition = era5_dataset['lat'].isin(lats)
    lon_condition = era5_dataset['lon'].isin(lons)
    era5_dataset = (era5_dataset.where(time_condition, drop=True)
                    .where(lat_condition & lon_condition, drop=True))
    era5_df = era5_dataset.groupby('time').mean(dim=["lat","lon"]).to_dataframe().reset_index()
    result.append({
        "name": instrumental["era5"]["name"],
        "dashStyle": 'Dash',
        "data": era5_df.values.tolist(),
    })

    for k in datasets.keys():
        if variable in datasets[k]["variables"]:
            dataset = xr.open_dataset(datasets[k]["variables"][variable]+".zarr",engine="zarr")
            dataset = dataset.squeeze()
            data = dataset.where(lat_condition & lon_condition, drop=True)
            data = data.groupby('time').mean(dim=["lat","lon"]).to_dataframe().reset_index()
            r, p_value = pearsonr(data[data['time'] >= 1979][variable].values, era5_df[era5_variable])
            result.append({
                "name": f'{datasets[k]["name"]}, r={np.around(r, 2)}, p_value={np.around(p_value, 6)}',
                "data": data.values.tolist(),
            })
    return {
        "name": f'Time Series For Area ({n},{s},{start},{stop})',
        "values": result
    }

timeSeriesArea("psl",1,-2,1,2)