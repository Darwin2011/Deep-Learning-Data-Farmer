#!/bin/bash


mkdir build && cd build
cmake -DUSE_CUDNN=1 ..
make -j4 
