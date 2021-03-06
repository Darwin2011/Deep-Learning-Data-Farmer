#!/bin/bash
#set -x

cd /home/caffe/caffe_bench

template_name=$1
batch_size=$2
iterations=$3
gpuid=$4
template_filename=`echo $template_name | awk -F/ '{print $NF}'`
template_filename_without_ext=`echo $template_filename | awk -F'.' '{print $1}'`
Caffe_Source=$5
nvprof=$6
Caffe_BIN=""
log_dir=""
if [ "$Caffe_Source" = "bvlc" ]; then 
    echo "Use Upstream Caffe"
    Caffe_BIN="/home/caffe/bvlc_caffe_test/build/tools/caffe"
    log_dir="bvlc_caffe_log"
else
    echo "Use NVidia Caffe"  
    Caffe_BIN="/home/caffe/nvidia_caffe_test/build/tools/caffe"
    log_dir="nvidia_caffe_log"
fi;

mkdir -p ${log_dir}
sed -e "s/BATCH_SIZE/${batch_size}/g" ${template_name} > deploy.prototxt


logfile=${template_filename_without_ext}_${batch_size}_${Caffe_Source}".log" 
if [ "$nvprof" = "0" ]; then
    $Caffe_BIN time --model=deploy.prototxt --iterations=${iterations} --gpu ${gpuid} #> ./${log_dir}/${template_filename}_${batch_size}".log" 2>&1
else
    mkdir -p /tmp/log
    nvprof --csv --log-file "/tmp/log/"${logfile} $Caffe_BIN time --model=deploy.prototxt --iterations=${iterations} --gpu ${gpuid}
fi;


#mv deploy.prototxt ./${log_dir}/${template_filename}_${batch_size}_deploy.prototxt

#average_forward=`cat ./${log_dir}/${template_filename}_${batch_size}".log" | grep "Average Forward pass" | awk '{print $(NF-1)}'`
#average_backward=`cat ./${log_dir}/${template_filename}_${batch_size}".log" | grep "Average Backward pass" | awk '{print $(NF-1)}'`
#score=`echo $average_forward $batch_size | awk '{print 1000.0 * $2 / $1}'`
#training_image_per_second=`echo $average_forward $average_backward $batch_size | awk '{print 1000.0 * $3 / ($1 + $2)}'`
#echo "Score : "${score}
#echo "Training Images Per Second : "${training_image_per_second}
