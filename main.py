from fastapi import FastAPI, HTTPException, Request, Response, Query, Path
from typing import Annotated
import math
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import xarray as xr
import numpy as np
import json
from scipy.stats import pearsonr
from matplotlib import cm

variableColorMaps = {"psl": "RdBu_r", "us": "PuOr_r", "tas": "PiYG_r"}
variables = {
    "psl":
        {
            "variable": "psl",
            "colorMap": "RdBu_r",
            "name": "Mean Sea Level Pressure Anomaly",
            "nameShort": "SLP",
            "multiplier": 1,
            "trendUnit": "hPa/century",
            "annualUnit": "hPa"
        },
    "us":
        {
            "variable": "us",
            "colorMap": "PuOr_r",
            "name": "Near Surface Zonal Wind Speed Anomaly",
            "nameShort": "US",
            "multiplier": 100,
            "trendUnit": "m/s/century",
            "annualUnit": "m/s"
        },
    "tas":
        {
            "variable": "tas",
            "colorMap": "PiYG_r",
            "name": "Near Surface Air Temperature Anomaly",
            "nameShort": "TAS",
            "multiplier": 100,
            "trendUnit": "K/century",
            "annualUnit": "K"
        },
}


# Takes an x and y value, find the one with the largest absolute value, and returns that value
# floored.
def absFloorMinimum(x, y):
    x = math.fabs(x)
    y = math.fabs(y)
    return math.floor(math.fabs(x if x > y else y))


def get_colormap_colors(colormap, num_colors=256):
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

def toDegreesEast(lon:int):
    """
    Converts a lon value from -180 to 180, to 0 to 360
    """
    if lon < 0:
        lon = lon+360
    return lon


datasets = {
    "cesm": {
        "name": "iCESM Last Millennium Ensemble",
        "nameShort": "CESM LM",
        "timeStart": 1900,
        "timeEnd": 2005,
        "variables": {
            "psl": xr.open_dataset("./data/cesm/psl.nc"),
            "tas": xr.open_dataset("./data/cesm/tas.nc"),
            "us": xr.open_dataset("./data/cesm/us.nc"),
        }
    },
    "hadcm3": {
        "name": "HadCM3 Last Millennium Ensemble",
        "nameShort": "HadCM3 LM",
        "timeStart": 1900,
        "timeEnd": 2005,
        "variables": {
            "psl": xr.open_dataset("./data/hadcm3/psl.nc"),
            "tas": xr.open_dataset("./data/hadcm3/tas.nc"),
            "us": xr.open_dataset("./data/hadcm3/us.nc"),
        }
    },
    "lens": {
        "name": "CESM1 Large Ensemble",
        "nameShort": "LENS",
        "timeStart": 1900,
        "timeEnd": 2005,
        "variables": {
            "psl": xr.open_dataset("./data/lens/psl.nc"),
            "tas": xr.open_dataset("./data/lens/tas.nc"),
            "us": xr.open_dataset("./data/lens/us.nc"),
        }
    },
    "pace": {
        "name": "CESM1 Pacific Pacemaker Ensemble",
        "nameShort": "PACE",
        "timeStart": 1900,
        "timeEnd": 2005,
        "variables": {
            "psl": xr.open_dataset("./data/pace/psl.nc"),
            "tas": xr.open_dataset("./data/pace/tas.nc"),
            "us": xr.open_dataset("./data/pace/us.nc"),
        }
    }
}

instrumental = {
    "era5": {
        "name": "ERA5",
        "nameShort": "ERA5",
        "timeStart": 1900,
        "timeEnd": 2005,
        "variables": {
            "psl": xr.open_dataset("./data/era5/psl.nc"),
            "tas": xr.open_dataset("./data/era5/tas.nc"),
            "us": xr.open_dataset("./data/era5/u1000.nc"),
        }
    }
}

app = FastAPI()

# add origins for cors
origins = [
    "http://localhost:5173",
    "https://pv.jortuck.com"
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
    response.headers["Cache-Control"] = "public, max-age=14400"
    return response


# root shows possible data sets
@app.get("/")
async def root():
    sets = []
    for key in datasets.keys():
        dictionary = {
            "reconstruction": str(key),
            "name": datasets[key]["name"],
            "nameShort": datasets[key]["nameShort"],
            "timeStart": datasets[key]["timeStart"],
            "timeEnd": datasets[key]["timeEnd"],
            "variables": list(datasets[key]["variables"].keys())
        }
        sets.append(dictionary)
    variablesArray = []
    for var in variables.keys():
        variablesArray.append(variables[var])
    return {"reconstructions": sets, "variables": variablesArray}


@app.get("/trends/{reconstruction}/{variable}")
def calculateTrend(reconstruction: str, variable: str, response: Response, startYear: int = 1900,
                   endYear: int = 2005):
    # response.headers["Content-Disposition"] = 'attachment; filename="filename.json"'
    dataset = datasets[reconstruction]["variables"][variable]

    data = dataset[variable]
    data = data.where(data['time'] >= startYear, drop=True).where(data['time'] <= endYear,
                                                                  drop=True)
    trends = data.polyfit(dim='time', deg=1)
    slope = trends.sel(
        degree=1)
    slope['polyfit_coefficients'] = np.around(slope['polyfit_coefficients'], 6)
    df = slope.to_dataframe().reset_index().drop(columns=['degree', 'member']);
    df.rename(columns={'polyfit_coefficients': 'value'}, inplace=True)
    df["value"] = df["value"] * variables[variable]["multiplier"]
    df["lon"] = (df["lon"] + 180) % 360 - 180  # convert 0-360 to -180-180
    bound = absFloorMinimum(np.min(df["value"]), np.max(df["value"]))
    return {"min": -bound,
            "max": bound,
            "variable": variables[variable]["trendUnit"],
            "name": datasets[reconstruction][
                        "nameShort"] + f' Reconstruction Trend {startYear}-{endYear}',
            "colorMap": generateColorAxis(variableColorMaps.get(variable)),
            "lats": list(df['lat']),
            "lons": list(df['lon']),
            "values": list(df['value'])}


@app.get("/values/{reconstruction}/{variable}/{year}")
async def values(reconstruction: str, variable: str, year: int):
    if (not list(datasets.keys()).__contains__(reconstruction) or not list(
            datasets[reconstruction]["variables"].keys()).__contains__(variable)):
        raise HTTPException(status_code=404, detail="Invalid dataset selection")

    dataset = datasets[reconstruction]["variables"][variable]
    data = dataset.sel(time=year)
    data[variable] = np.around(data[variable].astype('float64'), 6)
    df = data.to_dataframe().reset_index().drop(columns=['member', 'time']);
    df.rename(columns={variable: 'value'}, inplace=True)
    df["lon"] = (df["lon"] + 180) % 360 - 180  # convert 0-360 to -180-180
    return {"min": np.min(df["value"]),
            "max": np.max(df["value"]),
            "variable": variables[variable]["annualUnit"],
            "name": datasets[reconstruction]["nameShort"] + " Reconstruction " + str(year),
            "colorMap": generateColorAxis(variableColorMaps.get(variable)),
            "lats": list(df['lat']),
            "lons": list(df["lon"]),
            "values": list(df["value"])}


# Assumes lon is -180 to 180, returns a time series for all reconstructions
@app.get("/timeseries/{variable}/{lat}/{lon}")
async def timeseries(variable: str, lat: Annotated[int, Path(le=90, ge=-90)],
                     lon: Annotated[int, Path(le=180, ge=-180)]):
    result = []
    lon = toDegreesEast(lon);
    era5_dataset = instrumental["era5"]["variables"][variable]
    era5_data = era5_dataset.where(era5_dataset['time'] <= 2005, drop=True).sel(lat=lat, lon=lon)
    era5_df = era5_data.to_dataframe().reset_index()
    era5_df = era5_df.drop(columns=['lat', 'lon'])
    era5_variable = variable
    if variable == "us":
        era5_variable = "u1000"
    era5_df[era5_variable] = era5_df[era5_variable] - np.mean(era5_df[era5_variable])
    result.append({
        "name": instrumental["era5"]["name"],
        "dashStyle": 'Dash',
        "data": era5_df.values.tolist(),
    })

    for k in datasets.keys():
        dataset = datasets[k]["variables"][variable]
        data = dataset.sel(lat=lat, lon=lon, member=0)
        df = data.to_dataframe().reset_index()
        df = df.drop(columns=['lat', 'lon'])
        allValues = df.values.tolist()
        df = df[df["time"] >= np.min(era5_df["time"])]
        r, p_value = pearsonr(df[variable], era5_df[era5_variable])
        result.append({
            "name": f'{datasets[k]["name"]}, r={np.around(r, 2)}, p_value={np.around(p_value, 6)}',
            "data": allValues,
        })
    return {
        "name": f'Time Series For ({lat},{(lon + 180) % 360 - 180})',
        "values": result
    }


@app.get("/timeseries/{variable}/{n}/{s}/{e}/{w}")
def timeSeriesArea(variable: str, n: int, s: int, e: int, w: int):
    result = []
    lats = np.arange(np.min([n,s]),np.max([n,s])+1)

    if(e < w):
        lons = np.arange(np.min([e,w]),np.max([e,w])+1)
    else:
        lons = np.concatenate((np.arange(e,181),np.arange(-180,w+1)))
    era5_dataset = instrumental["era5"]["variables"][variable]
    era5_data = era5_dataset.where(era5_dataset['time'] <= 2005, drop=True).where(
        (era5_dataset["lat"].isin(lats)) &
        (era5_dataset["lon"].isin(lons)),
        drop=True)
    era5_df = era5_data.to_dataframe().reset_index()
    era5_variable = variable
    if variable == "us":
        era5_variable = "u1000"
    era5_df[era5_variable] = era5_df[era5_variable] - np.mean(era5_df[era5_variable])
    era5_df = era5_df.groupby("time").mean().reset_index()
    era5_df = era5_df.drop(columns=['lat', 'lon'])

    result.append({
        "name": instrumental["era5"]["name"],
        "dashStyle": 'Dash',
        "data": era5_df.values.tolist(),
    })

    for k in datasets.keys():
        dataset = datasets[k]["variables"][variable]
        data = dataset.sel(member=0).where(
            (dataset["lat"].isin(lats)) &
            (dataset["lon"].isin(lons)),
        drop=True)
        df = data.to_dataframe().reset_index()
        df = df.groupby("time").mean().reset_index()
        df = df.drop(columns=['lat', 'lon'])
        allValues = df.values.tolist()
        df = df[df["time"] >= np.min(era5_df["time"])]
        r, p_value = pearsonr(df[variable], era5_df[era5_variable])
        result.append({
            "name": f'{datasets[k]["name"]}, r={np.around(r, 2)}, p_value={np.around(p_value, 6)}',
            "data": allValues,
        })
    return {
        "name": f'Time Series For Area ({n},{s},{e},{w})',
        "values": result
    }
