FROM google/cloud-sdk:latest AS gcloud-cli
WORKDIR /data-downloader
# The Cloud Build service account is automatically authenticated here
RUN gcloud projects get-iam-policy your-project-id --flatten="bindings[].members" --format='table(bindings.role)' --filter="bindings.members:cloudbuild.gserviceaccount.com"
RUN gsutil -m cp -r gs://pvapi/data /data-downloader/data
FROM python:3.13
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /code
COPY ./pyproject.toml /code/pyproject.toml
RUN uv sync --compile-bytecode
COPY ./main.py /code/
COPY ./util.py /code/
COPY ./data.py /code/
COPY ./data_sets.py /code/
COPY ./download.py /code/
COPY --from=gcloud-cli /data-downloader/data /code/data
EXPOSE 80
CMD ["uv","run","fastapi", "run", "main.py", "--port", "80", "--proxy-headers"]
