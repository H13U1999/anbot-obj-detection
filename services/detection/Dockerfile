FROM python:3.11

WORKDIR /app

COPY requirements.txt requirements.txt

# torch is pinned below 2.6: 2.6 flipped `torch.load`'s weights_only default to True,
# which makes this vintage of yolov5 fail to unpickle models.yolo.Model from the
# .pt checkpoint. 2.5.1 also has no cp314 wheels, hence the Python 3.11 base above.
RUN pip3 install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install -r requirements.txt
RUN apt update
RUN apt install python3-tk  libgl1 -y

COPY . .

CMD ["python3", "app.py"]

