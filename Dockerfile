FROM ubuntu:20.04 as base

MAINTAINER Carson Harmon <carson.harmon@trailofbits.com>

RUN apt-get update -y

RUN DEBIAN_FRONTEND="noninteractive" apt install -y \
	clang-9 \
	cmake \
	git \
	build-essential \
	python3.8-dev \
	python3-pip \
	llvm

RUN python3 -m pip install --upgrade pip

WORKDIR /
COPY . /tourniquet

WORKDIR /tourniquet

RUN pip3 install -e .[dev]
