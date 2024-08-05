FROM public.ecr.aws/lambda/python:3.12
ENV MPLCONFIGDIR=/tmp/matplotlib
RUN mkdir -p /tmp/matplotlib && chmod -R 777 /tmp/matplotlib
WORKDIR ${LAMBDA_TASK_ROOT}
RUN microdnf install gcc gcc-c++ make -y
COPY ./requirements.txt /requirements.txt
RUN pip install awslambdaric setuptools
RUN pip install --no-cache-dir --upgrade -r /requirements.txt
COPY ./main.py ./
COPY ./util.py ./
COPY ./data.py ./
COPY ./data ./data
CMD [ "main.handler" ]