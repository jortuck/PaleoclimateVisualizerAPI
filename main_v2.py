import time

from fastapi import FastAPI, HTTPException, Request, Response, Query, Path
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from scipy.stats import pearsonr
from util import abs_floor_minimum, to_degrees_east, generate_color_axis, get_first_key
from data import instrumental
from data_sets import variables, datasets, instrumental
from mangum import Mangum
import xarray as xr
from scipy.stats import pearsonr

app = FastAPI()
# add origins for cors
origins = [
    "http://localhost:5173",
    "https://pv.jortuck.com",
    "https://jortuck.github.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET"],
    allow_headers=["*"],
    max_age=600
)


def startup():
    for dataset in datasets.values():
        for variable_id in dataset.variables:
            reconstruction_data =  xr.open_dataset(dataset.variables[variable_id]+".zarr", engine="zarr")
            timeData = reconstruction_data[
                "time"].data
            dataset.timeStart = int(timeData.min())
            dataset.timeEnd = int(timeData.max())
            variables[variable_id].datasets.append(dataset.id)

startup()

@app.middleware("http")
async def cache(request: Request, call_next):
    response = await call_next(request)
    if request.url.path == "/health" and request.method == "GET":
        return response
    response.headers["Cache-Control"] = "public, max-age=259200"
    return response

# Simple end point for checking if the server is up.
@app.get("/health")
async def health():
    return {"status": "ok"}

# root shows possible data sets
@app.get("/")
async def root():
    return {"status": "ok"}

# Get a list of all variables available
@app.get("/variables")
async def get_variables():

    # when getting variables, drop datasets key as it is not need for this view
    return {
        "variables":list(variables.values()),
        "datasets":list(datasets.values()),
    }

# Get a specific variable and available datasets for that variable.
@app.get("/variables/{id}")
async def get_variables(id: str):
    if variables.keys().__contains__(id): # makes sure the user request a valid variable, else returns 404
        return variables[id]
    raise  HTTPException(status_code=404, detail="Variable not found.")


# get time series data for a specific lat/lon point
@app.get("/variables/{id}/timeseries")
async def get_variables(id: str, lat: Annotated[int, Query(le=90, ge=-90)]  = 0, lon: Annotated[int, Query(le=180, ge=-180)] = -150, download: bool = False):
    if variables.keys().__contains__(id): # makes sure the user request a valid variable, else returns 404
        lon = to_degrees_east(lon)
        variable = variables[id]
        result = []

        # TO-DO: make work for rare cases where there is no instrumental data for variable
        instrumental_data = xr.open_dataset(instrumental.variables[id]+".zarr", engine="zarr")
        instrumental_data = instrumental_data.sel(lat=lat, lon=lon, method="nearest")
        instrumental_variable = get_first_key(instrumental_data.keys())
        instrumental_data = instrumental_data.to_dataframe().reset_index()
        instrumental_data = instrumental_data.drop(columns=['lat', 'lon'])
        instrumental_data[instrumental_variable] = instrumental_data[instrumental_variable] - np.mean(instrumental_data[instrumental_variable])

        result.append({
            "name": instrumental.name,
            "dashStyle": 'Dash',
            "data": instrumental_data.values.tolist(),
        })

        for dataset in variable.datasets:
            reconstruction = xr.open_dataset(dataset.path+".zarr", engine="zarr")
            reconstruction = reconstruction.sel(lat=lat,lon=lon,method="nearest")
            reconstruction = reconstruction.to_dataframe().reset_index()
            reconstruction = reconstruction[['time', variable.id]]
            result.append({
                "name": dataset.name,
                "data": reconstruction.values.tolist(),
            })
        return {
            "name": f'Time Series For ({lat},{(lon + 180) % 360 - 180})',
            "values": result
        }
    raise  HTTPException(status_code=404, detail="Variable not found.")

handler = Mangum(app=app)
# docker build -t pvapi -f AWS.dockerfile .
