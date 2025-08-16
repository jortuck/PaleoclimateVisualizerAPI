
from fastapi import FastAPI, HTTPException, Request, Response, Query, Path
from typing import Annotated, Callable
from fastapi.middleware.cors import CORSMiddleware

import numpy as np
from scipy.stats import pearsonr
from util import abs_floor_minimum, to_degrees_east, generate_color_axis, get_first_key
from data import VariableMetadata
from data_sets import variables, datasets, instrumental
import xarray as xr
from download import DownloadMode, TimeseriesDownload, netCDF_download, dataframe_download

app = FastAPI(openapi_url=None)
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

# get time series data for a specific lat/lon point
@app.get("/variables/{id}/timeseries")
async def get_variable_timeseries(id: str, startYear:int = None, endYear:int = None, lat: Annotated[int, Query(le=90, ge=-90)]  = 0, lon: Annotated[int, Query(le=180, ge=-180)] = -150, download:TimeseriesDownload = None, move_reference:bool = True):
    if variables.keys().__contains__(id):
        lon = to_degrees_east(lon)
        def select_point(xarray_dataset :xr.Dataset) -> xr.Dataset:
            return xarray_dataset.sel(lat=lat, lon=lon, method="nearest")
        return processTimeSeries(select_point,variables[id],f'({lat},{(lon + 180) % 360 - 180})',startYear,endYear,download, move_reference=move_reference)
    raise  HTTPException(status_code=404, detail="Variable not found.")

@app.get("/variables/{id}/timeseries-area")
async def get_variable_timeseries_area(
        id: str, startYear:int = None, endYear:int = None,
        n: Annotated[int, Query(le=90, ge=-90)]  = -60, s: Annotated[int, Query(le=90, ge=-90)]  = -80,
        start: Annotated[int, Query(le=180, ge=-180)] = 170, stop: Annotated[int, Query(le=180, ge=-180)] = -62,
        download:TimeseriesDownload = None, move_reference:bool = True):
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

        def select_area(xarray_dataset :xr.Dataset) -> xr.Dataset:
            print(xarray_dataset)
            return xarray_dataset.sel(lat=lats, lon=lons, method="nearest").mean(dim=['lat', 'lon'])
        return processTimeSeries(select_area,variable,f'({n},{s},{start},{stop})',startYear=startYear,endYear=endYear,download=download, move_reference=move_reference)
    raise  HTTPException(status_code=404, detail="Variable not found.")

def processTimeSeries(selectArea: Callable[[xr.Dataset], xr.Dataset], variable:VariableMetadata, area_name:str, startYear:int = None, endYear:int = None, download:TimeseriesDownload = None, move_reference:bool = True):
    # makes sure the user request a valid variable, else returns 404
    result = []
    # TO-DO: make work for rare cases where there is no instrumental data for variable
    instrumental_data = xr.open_dataset(instrumental.variables[variable.id]+".zarr", engine="zarr")
    instrumental_data = selectArea(instrumental_data)

    # select time range if specified
    if startYear is not None and endYear is not None:
        if startYear >= endYear:
            raise  HTTPException(status_code=400, detail="Start year cannot be greater than or equal to end year.")
        instrumental_data = instrumental_data.sel(time=slice(startYear, endYear))

    instrumental_variable = get_first_key(instrumental_data.keys())
    instrumental_data = instrumental_data.to_dataframe().reset_index()
    try:
        instrumental_data = instrumental_data.drop(columns=['lat', 'lon'])
    except KeyError:
        pass

    instrumental_data[instrumental_variable] = instrumental_data[instrumental_variable] - np.mean(instrumental_data[instrumental_variable])

    if variable.transform_timeseries:
        instrumental_data[instrumental_variable] = variable.transform_timeseries(instrumental_data[instrumental_variable])

    if download:
        download_frame = instrumental_data
        download_frame.rename(columns={instrumental_variable: f'ERA5_{instrumental_variable}'}, inplace=True)
        download_frame["time"] = download_frame["time"].astype(int)
    else:
        result.append({
            "name": instrumental.name,
            "dashStyle": 'Dash',
            "data": instrumental_data.values.tolist(),
        })
    for dataset in variable.datasets:
        dataset = datasets[dataset]
        reconstruction = xr.open_dataset(dataset.variables[variable.id]+".zarr", engine="zarr")
        reconstruction = selectArea(reconstruction)

        # move anomaly reference to 1979-2005
        if move_reference:
            reconstruction_subset = reconstruction.sel(time=slice(1979, 2005))
            climatology = reconstruction_subset.mean(dim='time')
            reconstruction = reconstruction - climatology

        dataset_var = get_first_key(reconstruction.keys())

        reconstruction = reconstruction.to_dataframe().reset_index()
        reconstruction = reconstruction[['time', dataset_var]]

        r, p_value = [None,None]
        if download is None:
            merged_df = instrumental_data.merge(reconstruction, how='inner', on='time')
            instrumental_aligned_values = merged_df.iloc[:, 1].values
            reconstruction_aligned_values =  merged_df.iloc[:, 2].values
            r, p_value = pearsonr(instrumental_aligned_values, reconstruction_aligned_values)
            r = np.around(r, decimals=4)
            p_value = np.around(p_value, decimals=4)
            if p_value == 0.0:
                p_value = "0.0000"

        if startYear is not None and endYear is not None:
            reconstruction = reconstruction[(reconstruction['time'] >= startYear) & (reconstruction['time'] <= endYear)]

        if variable.transform_timeseries:
            reconstruction[dataset_var] = variable.transform_timeseries(reconstruction[dataset_var])


        if download:
            reconstruction.rename(columns={dataset_var: f'{dataset.nameShort}_{dataset_var}'.replace(" ","_")}, inplace=True)
            download_frame = download_frame.merge(reconstruction,how="outer",on="time")
        else:
            result.append({
                "name": f'{dataset.name}, r={r}, p_value={p_value}',
                "data": reconstruction.values.tolist(),
            })

    if download:
        return dataframe_download(download_frame,download,f'timeseries_{startYear}_{endYear}_{variable.name}_{variable.annualUnit}_{area_name}')
    return {
        "name": f'Time Series For {area_name}',
        "values": result
    }

@app.get("/variables/{id}/trend/{dataset_id}")
def calculateTrend(id: str, dataset_id: str, response: Response, startYear:int = None, endYear:int = None, download:DownloadMode = None, move_reference:bool = False):
    if variables.keys().__contains__(id):
        variable = variables[id]
        if variable.datasets.__contains__(dataset_id):
            dataset = datasets[dataset_id]
            data = xr.open_dataset(dataset.variables[id]+".zarr",engine="zarr").squeeze()
            if move_reference:
                data_subset = data.sel(time=slice(1979, 2005))
                climatology = data_subset.mean(dim='time')
                data = data - climatology

            column = get_first_key(data.keys())
            if startYear is not None and endYear is not None:
                if startYear > endYear:
                    raise  HTTPException(status_code=400, detail="Start year cannot be greater than or equal to end year.")
            else:
                startYear = dataset.timeStart
                endYear = dataset.timeEnd

            # if they want full dataset, download before trim
            if download == DownloadMode.full:
                name = f'{startYear}_{endYear}_{dataset.name}_{variable.name}'
                return netCDF_download(data,name)

            data = data.sel(time=slice(startYear, endYear),drop=True)

            if download == DownloadMode.partial:
                name = f'{startYear}_{endYear}_{dataset.name}_{variable.name}'
                return netCDF_download(data,name)

            if startYear != endYear:
                trends = data.polyfit(dim='time', deg=1)
                slope = trends.sel(
                    degree=1).rename_vars({column+"_polyfit_coefficients":"value"})
                slope['value'] = np.around(slope['value'], 6)
                if variable.transform_trend:
                    slope['value'] = variable.transform_trend(slope['value'])

                # if the user wants to download the calculated trend
                if download == DownloadMode.trend:
                    name = f'{startYear}_{endYear}_{dataset.name}_{variable.name}_trends'
                    return netCDF_download(trends.sel(
                        degree=1).drop("degree"),name)
                df = slope.to_dataframe().reset_index().drop(columns=['degree'])
            else:
                df = data.to_dataframe().reset_index().drop(columns=['time'])
                df.rename(columns={column: 'value'}, inplace=True)
                if variable.transform_timeseries:
                    df["value"] = variable.transform_timeseries(df["value"])

            df["lon"] = (df["lon"] + 180) % 360 - 180
            bound = abs_floor_minimum(np.min(df["value"]), np.max(df["value"]))
            return {
                "bound": np.max([bound,1]).item(),
                "variable": variable.trendUnit if startYear != endYear else variable.annualUnit,
                "name": dataset.nameShort + f' Reconstruction '+(f'Trend {startYear}-{endYear}' if startYear != endYear else f'{startYear}'),
                "colorMap": generate_color_axis(variable.colorMap),
                "lats": list(df['lat']),
                "lons": list(df['lon']),
                "values": list(df['value'])}

        raise  HTTPException(status_code=404, detail="Dataset not found.")
    raise  HTTPException(status_code=404, detail="Variable not found.")
# docker build -t pvapi -f AWS.dockerfile .
