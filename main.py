from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import xarray as xr
import numpy as np
import json

reconstructions = ["cesm", "hadcm3", "lens", "pace"]
variables = ["psl", "tas", "us"]

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


# pre-calculate trends because it's an expensive operation and they dont change

trends = {}


# returns the trends as a raw json string
def calculateTrend(reconstruction: str, variable: str):
    dataset = datasets[reconstruction]["variables"][variable]
    variable = dataset[variable]
    trends = variable.polyfit(dim='time', deg=1)
    slope = trends.sel(
        degree=1)  # add .where(trends['lat'] <= 0, drop=True) to drop north hemisphere
    slope['polyfit_coefficients'] = np.around(slope['polyfit_coefficients'], 6)
    df = slope.to_dataframe().reset_index().drop(columns=['degree', 'member']);
    df.rename(columns={'polyfit_coefficients': 'value'}, inplace=True)
    df["lon"] = (df["lon"] + 180) % 360 - 180  # convert 0-360 to -180-180
    return df.to_json(orient='records')


# calculates trends for each data set and stores them in trends
for reconstruction in datasets.keys():
    for variable in list(datasets[reconstruction]["variables"].keys()):
        key = reconstruction + variable
        trends[key] = calculateTrend(reconstruction, variable)
print("Finished Calculating Trends")


# returns the json string of the precacluated trend
@app.get("/trends/{reconstruction}/{variable}")
async def getTrend(reconstruction: str, variable: str):
    if (not list(datasets.keys()).__contains__(reconstruction) or not list(
            datasets[reconstruction]["variables"].keys()).__contains__(variable)):
        raise HTTPException(status_code=404, detail="Invalid dataset selection")
    return Response(content=trends[reconstruction + variable], media_type="application/json")


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
    return df.to_dict(orient='records')


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
