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
COPY ./data-downloader/data /code/data
EXPOSE 80
CMD ["uv","run","fastapi", "run", "main.py", "--port", "80", "--proxy-headers"]
