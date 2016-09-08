#!/bin/bash



benchmark=$1
export CUDA_VISIBLE_DEVICES=$2
batch_size=$3
iteration=$4
python ${benchmark} -b ${batch_size} -i ${iteration}
