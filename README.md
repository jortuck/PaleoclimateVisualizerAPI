[![Front End Status](https://status.jortuck.com/api/badge/7/status?style=for-the-badge)](https://status.jortuck.com/status/pv)


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
> - You must have [Docker](https://www.docker.com/) installed on your machine to run this deployment.
> - I recommend putting your Lambda URL behind a [Cloudfront](https://aws.amazon.com/cloudfront/) distribution. 
> This will allow the API responses to be cached and served faster from Amazons global CDN, as well saving your function from needless executions! 

<details>
<summary>Already deployed this project before? Click here for instructions on how to update your existing repository and Lambda function.</summary>

This is a dropdown with text!
1. Head to the [Elastic Container Registry](https://console.aws.amazon.com/ecr/private-registry/repositories) on AWS.
2. On your repositories page, select the repository you have a created for the API, and click "View Push Commands".
Rune those four commands in order, in the project directory, to push it to your repository. If this is not working for you,
please make sure you have the pre-requisites listed in the note above. 
    - Depending on your internet speed, the upload could take up to fifteen minutes. After you run those four commands,
the image should be successfully uploaded given you did not receive any errors.
3. Go to your [AWS Lambda](https://console.aws.amazon.com/lambda/home) dashboard and open your function.
4. Underneath the "Image" tab, click the button that says "Deploy New Image", then click "Browse Images", then select
the latest one from your repository. Click "Save" and it should automatically update the function. 
</details>

#### Creating & Uploading To The Container Repository
1. Head to the [Elastic Container Registry](https://console.aws.amazon.com/ecr/private-registry/repositories) on AWS.
**Make sure your current region is set to the one you intend to deploy your Lambda function in.**
2. Click "Create" or "Create Repository". Make sure you are creating a private repository. You may
name the repository whatever you want and keep the standard encryption settings.
3. Return to the [Elastic Container Registry](https://console.aws.amazon.com/ecr/private-registry/repositories), select
the repository you just created, click actions in the top right, and select "Lifecycle Policies".
4. In the lifecycle policies page, click "Create Rule", give it a priority 1, a description of "delete old images"
and set the "Image Status" to "Any". Under "Match criteria", specify "Image count more than" and set the number to 1.
The rule action should automatically be set to "expire". Click "Save" and return back to your repositories page.
    - The purpose of this rule is to automatically delete old versions of the image in your registry when new versions are pushed.
   This will save you money by reducing the amount of storage your images take up. In addition, for this project it is not useful 
   to have several versions of the image available other than the latest.
5. On your repositories page, select the repository you have a created for the API, and click "View Push Commands".
Rune those four commands in order, in the project directory, to push it to your repository. If this is not working for you,
please make sure you have the pre-requisites listed in the note above. 
 - Depending on your internet speed, the upload could take up to fifteen minutes. After you run those four commands,
the image should be successfully uploaded given you did not receive any errors.

#### Deploying To Lambda
1. Go to your [AWS Lambda](https://console.aws.amazon.com/lambda/home) dashboard. **Make sure you are in
the same region your container was deployed in**. 
2. Click "Create Function", and select "Container Image".
3. Name your function whatever you want, and click "Browse Images". At the top, if you click "Select Repository",
you should see the one you just created from the previous instructions. Select that repository and select the top 
image with the tag "latest". Make sure the "Architecture" is set to "x86_64" and click "Create Function".
4. Once your function is created, click on it and select the "Configuration" tab. 
    - Under "General Configuration", click "Edit", and set the "Memory" to 4128 (or the highest allowed for your AWS account)
and set "Timeout" to one minute (this will allow for better cold starts). Then click "Save" at the bottom.
    - Under "Function URL", click "Create Function URL", set the "Auth type" to "NONE", then click save. You can now use
that URL to access the API.



