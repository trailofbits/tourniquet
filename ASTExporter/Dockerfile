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
	python3-dev \
	python3.7-dev \
	libboost-all-dev \
	autoconf \
	libzmqpp-dev \
	automake \
	llvm 
	
WORKDIR /
COPY . /ASTExporter 

WORKDIR /ASTExporter

RUN rm -rf build && mkdir -p build 

WORKDIR /ASTExporter/build

#RUN cmake -DCMAKE_C_COMPILER=clang-9 -DCMAKE_CXX_COMPILER=clang++-9 \
#-DLLVM_DYLIB_COMPONENTS=all .. && make -j5
