# About

This is the backend API for [Paleocliamte Visualizer](https://pv.jortuck.com).

You can view the front end source code at https://github.com/jortuck/PaleoclimateVisualizer

This API is build with Python and uses https://fastapi.tiangolo.com/.
> [!IMPORTANT]
> In order for the API to function properly, you must download the data it uses. 
The data is too large to be stored here on GitHub, but it can be downloaded from
[Google Drive](https://drive.google.com/drive/folders/1dW1CAt7yPliFiW7rz336NKfsXivgc8Nz?usp=sharing).
Please download the data folder, and place it in the root directory of the project.

## Running Locally For Development.

You must have Git and Python installed to run this project locally.

1. Open your terminal and clone the repository locally by running `git clone https://github.com/jortuck/PaleoclimateVisualizerAPI.git`
   - If you already have the project on your machine locally, run `git pull` in the project directory
   to update the project to the latest version.
2. Enter the project directory by running `cd ./PaleoclimateVisualizerAPI`.
3. If you have not already, 
4. Install the relevant dependencies.
   - **Conda Users:** `conda create --name <env> --file requirements.txt`
   - **PIP Users:** `pip install -r requirements.txt`
5. Run the app by using 

## Deployment

### VPS Or Other Private Server

### AWS Lambda 
