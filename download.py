from enum import Enum
import xarray as xr
import tempfile
from fastapi.responses import FileResponse
import pandas as pd
class DownloadMode(str, Enum):
    trend = "trend"
    full = "full"
    partial = "partial"

class TimeseriesDownload(str, Enum):
    mat = "mat"
    csv = "csv"
    xls = "xls"

def netCDF_download(data: xr.Dataset, name: str) -> FileResponse:
    temp = tempfile.NamedTemporaryFile(suffix='nc',delete=False)
    data.to_netcdf(temp.name)
    return FileResponse(
        temp.name,
        media_type='application/netcdf',
        filename=f"{name}.nc".replace(' ','_')
    )

def dataframe_download(data_frame: pd.DataFrame,download:TimeseriesDownload,  name: str) -> FileResponse:
    temp = tempfile.NamedTemporaryFile(suffix=download,delete=False)
    match download:
        case TimeseriesDownload.csv:
            data_frame.to_csv(temp, index=False)
            return FileResponse(
                temp.name,
                media_type='text/csv',
                filename=f"{name}.csv".replace(' ','_')
            )
        case TimeseriesDownload.mat:
            mat_dict = {'data': data_frame.to_records(index=False)}
            savemat(temp.name, mat_dict)
            return FileResponse(
                temp.name,
                media_type='application/x-matlab-data',
                filename=f"{name}.mat".replace(' ','_')
            )
        case TimeseriesDownload.xls:
            data_frame.to_excel(temp, index=False)
            return FileResponse(
                temp.name,
                media_type='application/vnd.ms-excel',
                filename=f"{name}.xls".replace(' ','_')
            )