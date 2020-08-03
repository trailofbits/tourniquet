FROM ubuntu:18.04 as base 

MAINTAINER Carson Harmon <carson.harmon@trailofbits.com> 

RUN apt-get update -y

RUN apt install -y \
	clang-9 \
	clang++-9 \ 
	cmake \
	git \
	zlib1g-dev \
	build-essential \
	python3.7-dev \
	python3-pip \
	libboost-all-dev \
	autoconf \
	libzmqpp-dev \
	automake \
	llvm 

RUN python3.7 -m pip install pip
RUN pip3 install setuptools 
	
WORKDIR /
COPY . /tourniquet 

WORKDIR /tourniquet

#RUN rm -rf build && mkdir -p build 

#WORKDIR /tourniquet/build

#RUN cmake -DCMAKE_C_COMPILER=clang-9 -DCMAKE_CXX_COMPILER=clang++-9 \
#-DLLVM_DYLIB_COMPONENTS=all .. && make -j5

#Python test 
#RUN pip3 install -e .
