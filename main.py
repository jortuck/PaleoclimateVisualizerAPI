from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import xarray as xr
import numpy as np
import json
from matplotlib import cm

variableColorMaps = {"psl": "RdBu_r", "us": "PuOr_r", "tas": "viridis"}


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


datasets = {
    "cesm": {
        "name": "iCESM Last Millennium Ensemble",
        "variables": {
            "psl": xr.open_dataset("./data/cesm/psl.nc"),
            "tas": xr.open_dataset("./data/cesm/tas.nc"),
            "us": xr.open_dataset("./data/cesm/us.nc"),
        }
    },
    "hadcm3": {
        "name": "HadCM3 Last Millennium Ensemble",
        "variables": {
            "psl": xr.open_dataset("./data/hadcm3/psl.nc"),
            "tas": xr.open_dataset("./data/hadcm3/tas.nc"),
            "us": xr.open_dataset("./data/hadcm3/us.nc"),
        }
    },
    "lens": {
        "name": "CESM1 Large Ensemble",
        "variables": {
            "psl": xr.open_dataset("./data/lens/psl.nc"),
            "tas": xr.open_dataset("./data/lens/tas.nc"),
            "us": xr.open_dataset("./data/lens/us.nc"),
        }
    },
    "pace": {
        "name": "CESM1 Pacific Pacemaker Ensemble",
        "variables": {
            "psl": xr.open_dataset("./data/pace/psl.nc"),
            "tas": xr.open_dataset("./data/pace/tas.nc"),
            "us": xr.open_dataset("./data/pace/us.nc"),
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


# root shows possible data sets
@app.get("/")
async def root():
    sets = []
    for key in datasets.keys():
        dictionary = {str(key): {
            "variables": list(datasets[key]["variables"].keys())
        }}
        sets.append(dictionary)
    return {"reconstructions": sets}


@app.get("/trends/{reconstruction}/{rvariable}")
def calculateTrend(reconstruction: str, rvariable: str):
    dataset = datasets[reconstruction]["variables"][rvariable]
    variable = dataset[rvariable]
    trends = variable.polyfit(dim='time', deg=1)
    slope = trends.sel(
        degree=1)  # add .where(trends['lat'] <= 0, drop=True) to drop north hemisphere
    slope['polyfit_coefficients'] = np.around(slope['polyfit_coefficients'], 6)
    df = slope.to_dataframe().reset_index().drop(columns=['degree', 'member']);
    df.rename(columns={'polyfit_coefficients': 'value'}, inplace=True)
    df["lon"] = (df["lon"] + 180) % 360 - 180  # convert 0-360 to -180-180
    return {"min": np.min(df["value"]), "max": np.max(df["value"]),
            "colorMap": generateColorAxis(variableColorMaps.get(rvariable)),
            "lats": list(df['lat']),
            "lons":  list(df['lon']),
            "values": list(df['value'])}



@app.get("/values/{reconstruction}/{variable}/{year}")
async def values(reconstruction: str, variable: str, year: int):
    if (not list(datasets.keys()).__contains__(reconstruction) or not list(
            datasets[reconstruction]["variables"].keys()).__contains__(variable)):
        raise HTTPException(status_code=404, detail="Invalid dataset selection")

    dataset = datasets[reconstruction]["variables"][variable]
    data = dataset.sel(time=year)
    # add .where(trends['lat'] <= 0, drop=True) to drop north hemisphere
    data[variable] = np.around(data[variable].astype('float64'), 6)
    df = data.to_dataframe().reset_index().drop(columns=['member', 'time']);
    df.rename(columns={variable: 'value'}, inplace=True)
    df["lon"] = (df["lon"] + 180) % 360 - 180  # convert 0-360 to -180-180
    return {"min": np.min(df["value"]),
            "max": np.max(df["value"]),
            "colorMap": generateColorAxis(variableColorMaps.get(variable)),
            "lats": list(df['lat']),
            "lons":list(df["lon"]),
            "values":list(df["value"])}


# Assumes lon is -180-180, returns a time series for a specific reconstruction
@app.get("/timeseries/{reconstruction}/{variable}/{lat}/{lon}")
async def timeseries(reconstruction: str, variable: str, lat: int, lon: int):
    if (not list(datasets.keys()).__contains__(reconstruction) or not list(
            datasets[reconstruction]["variables"].keys()).__contains__(variable)):
        raise HTTPException(status_code=404, detail="Invalid dataset selection")

    lon = (lon + 180) % 360
    dataset = datasets[reconstruction]["variables"][variable]
    data = dataset.sel(lat=lat, lon=lon, member=0)
    return {"time": np.ndarray.tolist(data.variables["time"].data),
            "values": np.ndarray.tolist(data.variables[variable].data)
            }


# Assumes lon is -180-180, returns a time series for all reconstructions
@app.get("/timeseries/{variable}/{lat}/{lon}")
async def timeseries(variable: str, lat: int, lon: int):
    result = []
    for k in datasets.keys():
        lon = (lon + 180) % 360
        dataset = datasets[k]["variables"][variable]
        data = dataset.sel(lat=lat, lon=lon, member=0)
        result.append({
            "name": datasets[k]["name"],
            "data": np.ndarray.tolist(data.variables[variable].data),
        })
    return {"values": result}
