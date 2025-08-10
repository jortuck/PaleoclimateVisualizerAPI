#  Build deps into the Lambda task root
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.13 AS builder

# Bring in uv without installing Python tooling into the final image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Faster cold starts + deterministic layers
ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_INSTALLER_METADATA=1 \
    UV_LINK_MODE=copy

WORKDIR ${LAMBDA_TASK_ROOT}

COPY ./pyproject.toml ./pyproject.toml

COPY ./uv.lock ./uv.lock

# Export pinned requirements and install them INTO the task root (no venv)
RUN uv export --frozen --no-emit-workspace --no-dev --no-editable -o requirements.txt && \
    uv pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"


FROM --platform=linux/amd64 scratch AS data_stage
COPY ./data /data


COPY ./data /data
 # lambda image
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.13

WORKDIR ${LAMBDA_TASK_ROOT}

# copy dependencies from builder layer
COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}

COPY ./main.py ./
COPY ./util.py ./
COPY ./data.py ./

COPY --from=data_stage /data ./data

CMD ["main.handler"]
