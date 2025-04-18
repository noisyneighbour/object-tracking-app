FROM mambaorg/micromamba:ubuntu20.04

WORKDIR /app
COPY . .

USER root
RUN mkdir -p /app/checkpoints /checkpoints && \
    chown -R mambauser:mambauser /app/checkpoints /checkpoints
USER mambauser

RUN micromamba install -f environment.yml  && micromamba clean --all --yes

RUN micromamba install -n base -c conda-forge wget && \
    mkdir -p /app/data && \
    micromamba run -n base wget https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights -O /app/data/yolov4.weights


RUN micromamba run -n base python save_model.py --model yolov4 --output /checkpoints/yolov4-416

# Final test command
RUN micromamba run -n base python -c "import tensorflow as tf; print(tf.reduce_sum(tf.random.normal([1000, 1000])))"