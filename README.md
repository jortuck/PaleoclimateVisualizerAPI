# About

This is the backend API for [Paleocliamte Visualizer](https://pv.jortuck.com).

You can view the front end source code at https://github.com/jortuck/PaleoclimateVisualizer

This API is build with Python and uses https://fastapi.tiangolo.com/.
> [!IMPORTANT]
> In order for the API to function properly, you must download the data it uses.
> The data is too large to be stored here on GitHub, but it can be downloaded from
[Google Drive](https://drive.google.com/drive/folders/1dW1CAt7yPliFiW7rz336NKfsXivgc8Nz?usp=sharing).
> Please download the data folder, and place it in the root directory of the project.

## Running Locally For Development.

You must have Git and Python installed to run this project locally.

1. Open your terminal and clone the repository locally by running
   `git clone https://github.com/jortuck/PaleoclimateVisualizerAPI.git`
    - If you already have the project on your machine locally, run `git pull` in the project
      directory
      to update the project to the latest version.
2. Enter the project directory by running `cd ./PaleoclimateVisualizerAPI`.
3. If you have not already, please download the required data for the project
   from [Google Drive](https://drive.google.com/drive/folders/1dW1CAt7yPliFiW7rz336NKfsXivgc8Nz?usp=sharing).
   Place the data folder in the root directory of the project. There is a zip you can download and
   decompress as well.
4. Install the relevant dependencies.
    - **Conda Users:** `conda create --name <env> --file requirements.txt`
    - **PIP Users:** `pip install -r requirements.txt`
5. Run the app by running `uvicorn main:app --reaload` in the root directory of the project.
    - If using VSCode, a run configuration comes shipped with the repository (must have
      the [Python Debugger](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy)
      extension installed)

## Deployment

### VPS Or Other Private Server

### AWS Lambda

Due to the size of the data, the API cannot be deployed as a standard Lambda microservice. Instead,
it must be first uploaded to [Amazon Elastic Container Registry](https://aws.amazon.com/ecr/), then
deployed to Lambda.

> [!NOTE]
> - Amazon charges for the storage used in AWS ECR. It should only be
    around \$0.30 per month, but I would 
    recommend setting a budget alert of \$5.00 incase a misconfiguration causes a spike in price.
    The API itself
    should not exceed the free tier of AWS Lambda, but again, have a budget alert set just in
    case.
> - Due to the nature of AWS Lambda, cold stars may occur if the API has not been used in some time.
    This could result in requests taking up to 60 seconds, however the time should reduce once the function is warm.
> - These instructions assume you already have some basic knowledge of how AWS works. In order to continue,
>   you must have the [AWS CLI](https://aws.amazon.com/cli/) installed on your local machine, and it must be 
>   authenticated with the following permissions: `AmazonEC2FullAccess` and `AmazonEC2ContainerRegistryFullAccess`.

#### Creating & Uploading To The Container Repository


