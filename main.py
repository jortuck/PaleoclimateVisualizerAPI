from fastapi import FastAPI, HTTPException, Request, Response, Query, Path
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from scipy.stats import pearsonr
from util import absFloorMinimum, toDegreesEast, generateColorAxis
from data import variables, datasets, instrumental
from mangum import Mangum

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
        timeData = next(iter(datasets[key]["variables"].values())).variables["time"].data
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
            "colorMap": generateColorAxis(variables.get(variable)["colorMap"]),
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
            "colorMap": generateColorAxis(variables.get(variable)["colorMap"]),
            "lats": list(df['lat']),
            "lons": list(df["lon"]),
            "values": list(df["value"])}


# Assumes lon is -180 to 180, returns a time series for all reconstructions
@app.get("/timeseries/{variable}/{lat}/{lon}")
async def timeseries(variable: str, lat: Annotated[int, Path(le=90, ge=-90)],
                     lon: Annotated[int, Path(le=180, ge=-180)]):
    result = []
    lon = toDegreesEast(lon)

    era5_variable = variable
    if variable == "us" or variable == "u10":
        era5_variable = "u1000"

    era5_dataset = instrumental["era5"]["variables"][era5_variable]
    era5_data = era5_dataset.where(era5_dataset['time'] <= 2005, drop=True).sel(lat=lat, lon=lon)
    era5_df = era5_data.to_dataframe().reset_index()
    era5_df = era5_df.drop(columns=['lat', 'lon'])

    era5_df[era5_variable] = era5_df[era5_variable] - np.mean(era5_df[era5_variable])
    result.append({
        "name": instrumental["era5"]["name"],
        "dashStyle": 'Dash',
        "data": era5_df.values.tolist(),
    })

    for k in datasets.keys():
        if variable in datasets[k]["variables"]:
            dataset = datasets[k]["variables"][variable]
            dataset = dataset.squeeze()
            data = dataset.sel(lat=lat, lon=lon, method='nearest')
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


@app.get("/timeseries/{variable}/{n}/{s}/{start}/{stop}")
async def timeSeriesArea(variable: str, n: int, s: int, start: int, stop: int):
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

    era5_dataset = instrumental["era5"]["variables"][era5_variable]
    era5_dataset = era5_dataset.where(era5_dataset['time'] <= 2005, drop=True).where(
        (era5_dataset["lat"].isin(lats)) &
        (era5_dataset["lon"].isin(lons)),
        drop=True)
    era5_df = era5_dataset.to_dataframe().reset_index()

    era5_df[era5_variable] = era5_df[era5_variable] - np.mean(era5_df[era5_variable])
    era5_df = era5_df.groupby("time").mean().reset_index()
    era5_df.drop(columns=['lat', 'lon'], inplace=True)

    result.append({
        "name": instrumental["era5"]["name"],
        "dashStyle": 'Dash',
        "data": era5_df.values.tolist(),
    })
    # look into inplace and memory profiler
    for k in datasets.keys():
        if variable in datasets[k]["variables"]:
            dataset = datasets[k]["variables"][variable]
            dataset = dataset.squeeze()
            data = dataset.where(
                (dataset["lat"].isin(lats)) &
                (dataset["lon"].isin(lons)),
                drop=True)
            df = data.to_dataframe().reset_index()
            df = df.groupby("time").mean().reset_index()
            df.drop(columns=['lat', 'lon'], inplace=True)
            allValues = df.values.tolist()
            df = df[df["time"] >= np.min(era5_df["time"])]
            r, p_value = pearsonr(df[variable], era5_df[era5_variable])
            result.append({
                "name": f'{datasets[k]["name"]}, r={np.around(r, 2)}, p_value={np.around(p_value, 6)}',
                "data": allValues,
            })
    return {
        "name": f'Time Series For Area ({n},{s},{start},{stop})',
        "values": result
    }


handler = Mangum(app=app)
