FROM python:3.7

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apt update
RUN apt install gcc
RUN apt install ffmpeg --assume-yes 
RUN pip3 install -r requirements.txt


COPY . .

CMD ["python", "main.py"]

