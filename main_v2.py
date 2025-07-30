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
    # time.sleep(2)
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
async def get_variable_timeseries(id: str, startYear:int = None, endYear:int = None, lat: Annotated[int, Query(le=90, ge=-90)]  = 0, lon: Annotated[int, Query(le=180, ge=-180)] = -150, download: bool = False):
    if variables.keys().__contains__(id): # makes sure the user request a valid variable, else returns 404
        lon = to_degrees_east(lon)
        variable = variables[id]
        result = []

        # TO-DO: make work for rare cases where there is no instrumental data for variable
        instrumental_data = xr.open_dataset(instrumental.variables[id]+".zarr", engine="zarr")
        instrumental_data = instrumental_data.sel(lat=lat, lon=lon, method="nearest")

        # select time range if specified
        if startYear is not None and endYear is not None:
            if startYear >= endYear:
                raise  HTTPException(status_code=400, detail="Start year cannot be greater than or equal to end year.")
            instrumental_data = instrumental_data.sel(time=slice(startYear, endYear))

        instrumental_variable = get_first_key(instrumental_data.keys())
        instrumental_data = instrumental_data.to_dataframe().reset_index()
        instrumental_data = instrumental_data.drop(columns=['lat', 'lon'])
        instrumental_data[instrumental_variable] = instrumental_data[instrumental_variable] - np.mean(instrumental_data[instrumental_variable])

        if variable.transform_timeseries:
            instrumental_data[instrumental_variable] = variable.transform_timeseries(instrumental_data[instrumental_variable])

        result.append({
            "name": instrumental.name,
            "dashStyle": 'Dash',
            "data": instrumental_data.values.tolist(),
        })

        for dataset in variable.datasets:
            dataset = datasets[dataset]
            reconstruction = xr.open_dataset(dataset.variables[variable.id]+".zarr", engine="zarr")

            if startYear is not None and endYear is not None:
                reconstruction = reconstruction.sel(time=slice(startYear, endYear))

            dataset_var = get_first_key(reconstruction.keys())
            reconstruction = reconstruction.sel(lat=lat,lon=lon,method="nearest")
            reconstruction = reconstruction.to_dataframe().reset_index()
            reconstruction = reconstruction[['time', dataset_var]]

            if variable.transform_timeseries:
                reconstruction[dataset_var] = variable.transform_timeseries(reconstruction[dataset_var])

            result.append({
                "name": dataset.name,
                "data": reconstruction.values.tolist(),
            })
        return {
            "name": f'Time Series For ({lat},{(lon + 180) % 360 - 180})',
            "values": result
        }
    raise  HTTPException(status_code=404, detail="Variable not found.")


@app.get("/variables/{id}/timeseries-area")
async def get_variable_timeseries_area(
        id: str, startYear:int = None, endYear:int = None,
        n: Annotated[int, Query(le=90, ge=-90)]  = -60, s: Annotated[int, Query(le=90, ge=-90)]  = -80,
        start: Annotated[int, Query(le=180, ge=-180)] = 170, stop: Annotated[int, Query(le=180, ge=-180)] = -62,
        download: bool = False):
    if variables.keys().__contains__(id): # makes sure the user request a valid variable, else returns 404
        lats = np.arange(np.min([n, s]), np.max([n, s]) + 1)

        start = to_degrees_east(start)
        stop = to_degrees_east(stop)

        if start < stop:
            lons = np.arange(np.min([start, stop]), np.max([start, stop]) + 1)
        elif start == stop:
            lons = np.array([start])
        else:
            lons = np.concatenate((np.arange(start, 361), np.arange(0, stop + 1)))


        variable = variables[id]
        result = []

        # TO-DO: make work for rare cases where there is no instrumental data for variable
        instrumental_data = xr.open_dataset(instrumental.variables[id]+".zarr", engine="zarr")
        lat_condition = instrumental_data['lat'].isin(lats)
        lon_condition = instrumental_data['lon'].isin(lons)
        instrumental_data = instrumental_data.sel(lat=lats, lon=lons, method="nearest")

        # select time range if specified
        if startYear is not None and endYear is not None:
            if startYear >= endYear:
                raise  HTTPException(status_code=400, detail="Start year cannot be greater than or equal to end year.")
            instrumental_data = instrumental_data.sel(time=slice(startYear, endYear))

        instrumental_variable = get_first_key(instrumental_data.keys())
        instrumental_data = instrumental_data.groupby('time').mean(dim=["lat","lon"]).to_dataframe().reset_index()
        instrumental_data[instrumental_variable] = instrumental_data[instrumental_variable] - np.mean(instrumental_data[instrumental_variable])

        if variable.transform_timeseries:
            instrumental_data[instrumental_variable] = variable.transform_timeseries(instrumental_data[instrumental_variable])

        result.append({
            "name": instrumental.name,
            "dashStyle": 'Dash',
            "data": instrumental_data.values.tolist(),
        })

        for dataset in variable.datasets:
            dataset = datasets[dataset]
            reconstruction = xr.open_dataset(dataset.variables[variable.id]+".zarr", engine="zarr")

            if startYear is not None and endYear is not None:
                reconstruction = reconstruction.sel(time=slice(startYear, endYear))

            dataset_var = get_first_key(reconstruction.keys())
            reconstruction = reconstruction.where(lat_condition & lon_condition, drop=True)
            reconstruction = reconstruction.groupby('time').mean(dim=["lat","lon"]).to_dataframe().reset_index()
            reconstruction = reconstruction[['time', dataset_var]]

            if variable.transform_timeseries:
                reconstruction[dataset_var] = variable.transform_timeseries(reconstruction[dataset_var])

            result.append({
                "name": dataset.name,
                "data": reconstruction.values.tolist(),
            })
        return {
            "name": f'Time Series For Area ({n},{s},{start},{stop})',
            "values": result
        }
    raise  HTTPException(status_code=404, detail="Variable not found.")

@app.get("/variables/{id}/trend/{dataset_id}")
def calculateTrend(id: str, dataset_id: str, response: Response, startYear:int = None, endYear:int = None):
    if variables.keys().__contains__(id):
        variable = variables[id]
        if variable.datasets.__contains__(dataset_id):
            dataset = datasets[dataset_id]
            data = xr.open_dataset(dataset.variables[id]+".zarr",engine="zarr").squeeze()
            column = get_first_key(data.keys())
            if startYear is not None and endYear is not None:
                if startYear >= endYear:
                    raise  HTTPException(status_code=400, detail="Start year cannot be greater than or equal to end year.")
            else:
                startYear = dataset.timeStart
                endYear = dataset.timeEnd
            data = data.sel(time=slice(startYear, endYear),drop=True)
            trends = data.polyfit(dim='time', deg=1)
            slope = trends.sel(
                degree=1).rename_vars({column+"_polyfit_coefficients":"value"})
            slope['value'] = np.around(slope['value'], 6)
            if variable.transform_trend:
                slope['value'] = variable.transform_trend(slope['value'])
            df = slope.to_dataframe().reset_index().drop(columns=['degree']);
            df["lon"] = (df["lon"] + 180) % 360 - 180
            bound = abs_floor_minimum(np.min(df["value"]), np.max(df["value"]))
            return {"min": -bound,
                    "max": bound,
                    "variable":variable.trendUnit,
                    "name": dataset.nameShort + f' Reconstruction Trend {startYear}-{endYear}',
                    "colorMap": generate_color_axis(variable.colorMap),
                    "lats": list(df['lat']),
                    "lons": list(df['lon']),
                    "values": list(df['value'])}

        raise  HTTPException(status_code=404, detail="Dataset not found.")
    raise  HTTPException(status_code=404, detail="Variable not found.")
handler = Mangum(app=app)
# docker build -t pvapi -f AWS.dockerfile .
