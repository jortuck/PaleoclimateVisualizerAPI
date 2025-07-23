# data sets for the backend are defined and described here
from typing import Dict

from data_v2 import VariableMetadata, Dataset, DatasetType

# variables
variables: Dict[str, VariableMetadata] = {
    "psl": VariableMetadata(
        id="psl",
        name="Mean Sea Level Pressure Anomaly",
        nameShort="SLP",
        colorMap="RdBu_r",
        multiplier=1,
        trendUnit="hPa/century",
        annualUnit="hPa"
    ),
    "u10": VariableMetadata(
        id="u10",
        name="Near Surface Zonal Wind Speed Anomaly",
        nameShort="U10",
        colorMap="PuOr_r",
        multiplier=100,
        trendUnit="m/s/century",
        annualUnit="m/s"
    ),
    "v10": VariableMetadata(
        id="v10",
        name="Meridional Wind Speed Anomaly",
        nameShort="V10",
        colorMap="BrBG_r",
        multiplier=100,
        trendUnit="m/s/century",
        annualUnit="m/s"
    ),
    "tas": VariableMetadata(
        id="tas",
        name="Near Surface Air Temperature Anomaly",
        nameShort="TAS",
        colorMap="PiYG_r",
        multiplier=100,
        trendUnit="K/century",
        annualUnit="K"
    ),
}

datasets: Dict[str, Dataset] = {
    "cesm": Dataset(
        id="cesm",
        name="iCESM Last Millennium Ensemble",
        nameShort="CESM LM",
        variables={
            "psl": "./data/cesm/psl.nc",
            "tas": "./data/cesm/tas.nc",
            "u10": "./data/cesm/u10.nc",
            "v10": "./data/cesm/v10.nc",
        },

    ),
    "hadcm3": Dataset(
        id="hadcm3",
        name="HadCM3 Last Millennium Ensemble",
        nameShort="HadCM3 LM",
        variables={
            "psl": "./data/hadcm3/psl.nc",
            "tas": "./data/hadcm3/tas.nc",
            "u10": "./data/hadcm3/us.nc",
        },

    ),
    "lens": Dataset(
        id="lens",
        name="CESM1 Large Ensemble",
        nameShort="LENS",
        variables={
            "psl": "./data/lens/psl.nc",
            "tas": "./data/lens/tas.nc",
            "u10": "./data/lens/us.nc",
        },
    ),
    "lens2": Dataset(
        id="lens2",
        name="CESM2 Large Ensemble",
        nameShort="LENS 2",
        variables={
            "psl": "./data/lens2/psl.nc",
            "tas": "./data/lens2/tas.nc",
            "u10": "./data/lens2/u10.nc",
            "v10": "./data/lens2/v10.nc",
        },
    ),
    "pace": Dataset(
        id="pace",
        name="CESM1 Pacific Pacemaker Ensemble",
        nameShort="PACE",
        variables={
            "psl": "./data/pace/psl.nc",
            "tas": "./data/pace/tas.nc",
            "u10": "./data/pace/u10.nc",
            "v10": "./data/pace/v10.nc",
        },
    ),
    "pace2": Dataset(
        id="pace2",
        name="CESM2 Pacific Pacemaker Ensemble",
        nameShort="PACE 2",
        variables={
            "psl": "./data/pace2/psl.nc",
            "tas": "./data/pace2/tas.nc",
            "u10": "./data/pace2/u10.nc",
            "v10": "./data/pace2/v10.nc",
        },
    )
}

instrumental: Dataset =  Dataset(
        id="era5",
        name="ERA5",
        nameShort="ERA5",
        timeStart=1900,
        timeEnd=2005,
        type=DatasetType.INSTRUMENTAL,
        variables={
            "psl": "./data/era5/psl.nc",
            "tas": "./data/era5/tas.nc",
            "u10": "./data/era5/u1000.nc",
            "v10": "./data/era5/v10.nc",
        }
    )


