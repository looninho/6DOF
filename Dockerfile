# syntax=docker/dockerfile:1

# pymodbus and PySide6 in wsl docker conatiner
# with usb device attached from Windows 10 via WSL Ubuntu
# using IP address within CIDR range 
# (https://tehnoblog.org/ip-tools/ip-address-in-cidr-range/)
# 
# Maintainer : looninho@gmail.com
# DAte: 2023/03/01
# 

# FROM ghcr.io/pymodbus-dev/pymodbus:dev

FROM ubuntu:jammy

ENV XDG_RUNTIME_DIR /tmp/runtime-root

ENV RUNLEVEL 3

ENV LIBGL_ALWAYS_INDIRECT 1

ENV XCURSOR_SIZE 16

RUN apt update && apt upgrade && \
    apt install --no-install-recommends -y '^libxcb.*-dev' libx11-xcb-dev && \
    apt install --no-install-recommends -y libglu1-mesa-dev libxrender-dev && \
    apt install --no-install-recommends -y libxi-dev libxkbcommon-dev && \
    apt install --no-install-recommends -y libxkbcommon-x11-dev && \
    apt install --no-install-recommends -y libglib2.0-0 libfontconfig1  && \
    apt install --no-install-recommends -y libdbus-glib-1-2 libegl1 && \
    apt install --no-install-recommends -y python3-pip && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install APScheduler PySide6 pyqtgraph pyserial pymodbus

CMD ["/bin/bash"]

