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
            # r, p = pearsonr(timeData,instrumental_data)
            dataset.timeStart = int(timeData.min())
            dataset.timeEnd = int(timeData.max())

            instrumental_data = xr.open_dataset(instrumental.variables[variable_id] + ".zarr", engine="zarr").sel(time=slice(dataset.timeStart, dataset.timeEnd))
            instrumental_data = instrumental_data.sel(
                lat=reconstruction_data.lat,
                lon=reconstruction_data.lon
            )

            era5_variable = get_first_key(instrumental_data.keys())
            print(instrumental_data)
            variables[variable_id].datasets.append(dataset.as_one(variable_id))

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


@app.get("/variables")
async def get_variables():
    time.sleep(5)

    return list(variables.values())

@app.get("/variables/{id}")
async def get_variables(id: str):
    time.sleep(5)
    if variables.keys().__contains__(id):
        return variables[id]
    raise  HTTPException(status_code=404, detail="Variable not found")


handler = Mangum(app=app)
# docker build -t pvapi -f AWS.dockerfile .
