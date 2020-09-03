FROM ubuntu:18.04 as base

MAINTAINER Carson Harmon <carson.harmon@trailofbits.com>

RUN apt-get update

RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y \
	clang-9 \
	git \
	build-essential \
	python3.7-dev \
	python3-pip \
	llvm-9-dev \
	libclang-9-dev \
	apt-transport-https \
	ca-certificates \
	gnupg \
	software-properties-common \
	wget

RUN wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null \
		| gpg --dearmor - \
		| tee /etc/apt/trusted.gpg.d/kitware.gpg >/dev/null && \
	apt-add-repository 'deb https://apt.kitware.com/ubuntu/ bionic main' && \
	apt-get update && \
	apt-get install -y cmake

RUN python3 -m pip install --upgrade pip

WORKDIR /
COPY . /tourniquet

WORKDIR /tourniquet

RUN pip3 install -e .[dev]
