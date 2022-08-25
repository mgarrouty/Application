FROM python:3.10-slim

WORKDIR /usr/src/app

RUN pip3 install --upgrade pip setuptools

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

ADD . .

EXPOSE 8888

CMD [ "python", "./app.py"]