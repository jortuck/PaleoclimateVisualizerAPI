from fastapi import FastAPI, HTTPException, Request, Response, Query, Path
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from scipy.stats import pearsonr
from util import abs_floor_minimum, to_degrees_east, generate_color_axis, get_first_key
from data import variables, datasets, instrumental
from mangum import Mangum
import xarray as xr

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
    sets = []
    for key in datasets.keys():
        timeData = xr.open_dataset(next(iter(datasets[key]["variables"].values()))+".zarr",engine="zarr").variables[
            "time"].data
        timeStart = int(timeData.min())
        timeEnd = int(timeData.max())
        dictionary = {
            "reconstruction": str(key),
            "name": datasets[key]["name"],
            "nameShort": datasets[key]["nameShort"],
            "timeStart": timeStart,
            "timeEnd": timeEnd,
            "variables": list(datasets[key]["variables"].keys())
        }
        sets.append(dictionary)
    variablesArray = []
    for var in variables.keys():
        variablesArray.append(variables[var])
    return {"reconstructions": sets, "variables": list(variables.values())}


@app.get("/trends/{reconstruction}/{variable}")
def calculateTrend(reconstruction: str, variable: str, response: Response, startYear: int = 1900,
                   endYear: int = 2005):
    # Check to make sure it's a valid reconstruction
    if not datasets.keys().__contains__(reconstruction):
        raise HTTPException(status_code=404, detail=f'Reconstruction {reconstruction} not found')
    # Check to make sure variable exists on reconstruction
    if not datasets[reconstruction]["variables"].__contains__(variable):
        raise HTTPException(status_code=404, detail=f'Variable {variable} not found')

    data = xr.open_dataset(datasets[reconstruction]["variables"][variable]+".zarr",engine="zarr").squeeze()
    column = get_first_key(data.keys())
    data = data.sel(time=slice(startYear,endYear),drop=True)
    trends = data.polyfit(dim='time', deg=1)
    slope = trends.sel(
        degree=1).rename_vars({column+"_polyfit_coefficients":"value"})
    slope['value'] = np.around(slope['value'], 6) * variables[variable]["multiplier"]

    df = slope.to_dataframe().reset_index().drop(columns=['degree']);
    df["lon"] = (df["lon"] + 180) % 360 - 180  # convert 0-360 to -180-180
    bound = abs_floor_minimum(np.min(df["value"]), np.max(df["value"]))
    return {"min": -bound,
            "max": bound,
            "variable": variables[variable]["trendUnit"],
            "name": datasets[reconstruction][
                        "nameShort"] + f' Reconstruction Trend {startYear}-{endYear}',
            "colorMap": generate_color_axis(variables.get(variable)["colorMap"]),
            "lats": list(df['lat']),
            "lons": list(df['lon']),
            "values": list(df['value'])}


@app.get("/values/{reconstruction}/{variable}/{year}")
async def values(reconstruction: str, variable: str, year: int):
    if (not list(datasets.keys()).__contains__(reconstruction) or not list(
            datasets[reconstruction]["variables"].keys()).__contains__(variable)):
        raise HTTPException(status_code=404, detail="Invalid dataset selection")

    dataset = xr.open_dataset(datasets[reconstruction]["variables"][variable]+".zarr",engine="zarr")
    data = dataset.sel(time=year)
    column = get_first_key(dataset.keys())
    data[column] = np.around(data[column].astype('float64'), 6)
    df = data.to_dataframe().reset_index().drop(columns=['member', 'time']);
    df.rename(columns={column: 'value'}, inplace=True)
    df["lon"] = (df["lon"] + 180) % 360 - 180  # convert 0-360 to -180-180
    if variable == "psl":
        df["value"]= df["value"] / 100
    return {"min": np.min(df["value"]),
            "max": np.max(df["value"]),
            "variable": variables[column]["annualUnit"],
            "name": datasets[reconstruction]["nameShort"] + " Reconstruction " + str(year),
            "colorMap": generate_color_axis(variables.get(column)["colorMap"]),
            "lats": list(df['lat']),
            "lons": list(df["lon"]),
            "values": list(df["value"])}


# Assumes lon is -180 to 180, returns a time series for all reconstructions
@app.get("/timeseries/{variable}/{lat}/{lon}")
async def timeseries(variable: str, lat: Annotated[int, Path(le=90, ge=-90)],
                     lon: Annotated[int, Path(le=180, ge=-180)],time_start: int = 1800, time_end: int = 2005):
    result = []

    lon = to_degrees_east(lon)

    era5_dataset = xr.open_dataset(instrumental["era5"]["variables"][variable]+".zarr",engine="zarr")
    era5_variable = get_first_key(era5_dataset.keys())
    era5_data = era5_dataset.sel(lat=lat, lon=lon).sel(time=slice(time_start, time_end))
    era5_df = era5_data.to_dataframe().reset_index()
    era5_df = era5_df.drop(columns=['lat', 'lon'])

    if variable == "psl":
        era5_df[era5_variable] = era5_df[era5_variable]/100

    era5_df[era5_variable] = era5_df[era5_variable] - np.mean(era5_df[era5_variable])

    result.append({
        "name": instrumental["era5"]["name"],
        "dashStyle": 'Dash',
        "data": era5_df.values.tolist(),
    })

    for k in datasets.keys():
        if variable in datasets[k]["variables"]:
            dataset = xr.open_dataset(datasets[k]["variables"][variable]+".zarr",engine="zarr")
            dataset = dataset.squeeze()
            column = get_first_key(dataset.keys())
            data = dataset.sel(lat=lat, lon=lon, method='nearest').sel(time=slice(time_start, time_end))
            df = data.to_dataframe().reset_index()
            df = df.drop(columns=['lat', 'lon'])

            if variable == "psl":
                df[column] = df[column] / 100

            allValues = df.values.tolist()
            df = df[df["time"] >= np.min(era5_df["time"])]

            x = df[column].dropna()
            y = era5_df[era5_variable].dropna()
            if len(x) >= 2 and len(y) >= 2:
                r, p_value = pearsonr(x, y)
                r = np.around(r, 2)
                p_value = np.around(p_value, 4)
            else:
                r, p_value = "None", "None"



            result.append({
                "name": f'{datasets[k]["name"]}, r={r}, p_value={p_value}',
                "data": allValues,
            })
    return {
        "name": f'Time Series For ({lat},{(lon + 180) % 360 - 180})',
        "values": result
    }


@app.get("/timeseries/{variable}/{n}/{s}/{start}/{stop}")
async def timeSeriesArea(variable: str, n: int, s: int, start: int, stop: int, time_start: int = 1800, time_end: int = 2005):
    result = []
    lats = np.arange(np.min([n, s]), np.max([n, s]) + 1)
    start = to_degrees_east(start)
    stop = to_degrees_east(stop)
    if start < stop:
        lons = np.arange(np.min([start, stop]), np.max([start, stop]) + 1)
    elif start == stop:
        lons = np.array([start])
    else:
        lons = np.concatenate((np.arange(start, 361), np.arange(0, stop + 1)))
    era5_dataset = xr.open_dataset(instrumental["era5"]["variables"][variable]+".zarr",engine="zarr")
    era5_variable = get_first_key(era5_dataset.keys())
    time_condition = era5_dataset['time'] <= 2005
    lat_condition = era5_dataset['lat'].isin(lats)
    lon_condition = era5_dataset['lon'].isin(lons)
    era5_dataset = era5_dataset.sel(lat=lats, lon=lons, method="nearest").sel(time=slice(time_start, time_end))
    era5_dataset[era5_variable] = era5_dataset[era5_variable] - np.mean(era5_dataset[era5_variable])
    era5_df = era5_dataset.groupby('time').mean(dim=["lat","lon"]).to_dataframe().reset_index()
    result.append({
        "name": instrumental["era5"]["name"],
        "dashStyle": 'Dash',
        "data": era5_df.values.tolist(),
    })

    for k in datasets.keys():
        if variable in datasets[k]["variables"]:
            dataset = xr.open_dataset(datasets[k]["variables"][variable]+".zarr",engine="zarr").squeeze()
            column = get_first_key(dataset.keys())
            data = dataset.where(lat_condition & lon_condition, drop=True).sel(time=slice(time_start, time_end))
            data = data.groupby('time').mean(dim=["lat","lon"]).to_dataframe().reset_index()

            x = data[data['time'] >= 1979][column].dropna().values
            y = era5_df[era5_variable].dropna().values

            if len(x) >= 2 and len(y) >= 2:
                r, p_value = pearsonr(x, y)
                r = np.around(r, 2)
                p_value = np.around(p_value, 4)
            else:
                r, p_value = "None", "None"



            result.append({
                "name": f'{datasets[k]["name"]}, r={r}, p_value={p_value}',
                "data": data.values.tolist(),
            })
    return {
        "name": f'Time Series For Area ({n},{s},{start},{stop})',
        "values": result
    }


handler = Mangum(app=app)
# docker build -t pvapi -f AWS.dockerfile .
