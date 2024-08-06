import xarray as xr

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
    "u10":
        {
            "variable": "u10",
            "colorMap": "PuOr_r",
            "name": "Near Surface Zonal Wind Speed Anomaly",
            "nameShort": "U10",
            "multiplier": 100,
            "trendUnit": "m/s/century",
            "annualUnit": "m/s"
        },
    "v10":
        {
            "variable": "v10",
            "colorMap": "PuOr_r",
            "name": "Meridional Wind Speed Anomaly",
            "nameShort": "V10",
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
datasets = {
    "cesm": {
        "name": "iCESM Last Millennium Ensemble",
        "nameShort": "CESM LM",
        "variables": {
            "psl": "./data/cesm/psl.nc",
            "tas": "./data/cesm/tas.nc",
            "u10": "./data/cesm/u10.nc",
            "v10": "./data/cesm/v10.nc",
        }
    },
    "hadcm3": {
        "name": "HadCM3 Last Millennium Ensemble",
        "nameShort": "HadCM3 LM",
        "variables": {
            "psl": "./data/hadcm3/psl.nc",
            "tas": "./data/hadcm3/tas.nc",
            "us": "./data/hadcm3/us.nc",
        }
    },
    "lens": {
        "name": "CESM1 Large Ensemble",
        "nameShort": "LENS",
        "variables": {
            "psl": "./data/lens/psl.nc",
            "tas": "./data/lens/tas.nc",
            "us": "./data/lens/us.nc",
        }
    },
    "lens2": {
        "name": "CESM1 Large Ensemble 2",
        "nameShort": "LENS 2",
        "variables": {
            "psl": "./data/lens2/psl.nc",
            "tas": "./data/lens2/tas.nc",
            "u10": "./data/lens2/u10.nc",
            "v10": "./data/lens2/v10.nc",
        }
    },
    "pace": {
        "name": "CESM1 Pacific Pacemaker Ensemble",
        "nameShort": "PACE",
        "variables": {
            "psl": "./data/pace/psl.nc",
            "tas": "./data/pace/tas.nc",
            "u10": "./data/pace/u10.nc",
            "v10": "./data/pace/v10.nc",
        }
    },
    "pace2": {
        "name": "CESM1 Pacific Pacemaker Ensemble 2",
        "nameShort": "PACE 2",
        "variables": {
            "psl": "./data/pace2/psl.nc",
            "tas": "./data/pace2/tas.nc",
            "u10": "./data/pace2/u10.nc",
            "v10": "./data/pace2/v10.nc",
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
            "psl": "./data/era5/psl.nc",
            "tas": "./data/era5/tas.nc",
            "u1000": "./data/era5/u1000.nc",
            "v10": "./data/era5/v10.nc",
        }
    }
}