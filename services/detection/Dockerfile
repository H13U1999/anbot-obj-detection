FROM python:3

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install -r requirements.txt
RUN apt update
RUN apt install python3-tk  libgl1 -y

COPY . .

CMD ["python3", "app.py"]

