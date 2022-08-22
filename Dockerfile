FROM python:3.8
MAINTAINER jcciam@outlook.com
WORKDIR /app
RUN pip install flask flask_restful pyyaml requests gunicorn gevent -i https://mirrors.aliyun.com/pypi/simple/
COPY ./src .
CMD ["gunicorn", "app:app", "-c", "./gunicorn.conf.py"]