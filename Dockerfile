# Use an official Python runtime as a parent image
FROM ubuntu:18.04


RUN apt update 
ENV DEBIAN_FRONTEND=noninteractive 
RUN apt install -y  \
python2.7 \
python-pip \
nfs-common \
nfs-client \
ipython \
pyqt4-dev-tools \
python-qt4 \
libqt4-dev


WORKDIR /harp



# Copy the current directory contents into the container at /lama
ADD . /harp



# Make port 80 available to the world outside this container
EXPOSE 80

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN pip install pipenv==2018.11.14

# Was getting an error installing pyradiomics otherwise. See https://github.com/pypa/pipenv/issues/2924
RUN pipenv run pip install pip==18.0

RUN pipenv install --system
