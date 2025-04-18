FROM mambaorg/micromamba:ubuntu20.04

WORKDIR /app
COPY . .


RUN micromamba install -f environment.yml  && micromamba clean --all --yes

RUN apt-get update && apt-get install -y wget && \
    wget https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights -O /app/data/yolov4.weights

RUN mkdir -p /app/checkpoints/yolov4-416
RUN micromamba run -n base python save_model.py --model yolov4

# Final test command
RUN micromamba run -n base python -c "import tensorflow as tf; print(tf.reduce_sum(tf.random.normal([1000, 1000])))"