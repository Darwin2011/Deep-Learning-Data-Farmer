#!/usr/bin/env python
import os
import re
import sys
import pandas
from collections import OrderedDict
from cmd_generator import *
from subprocess import Popen, PIPE, STDOUT
from abc import ABCMeta, abstractmethod

class Workload(object):
    __metaclass__ = ABCMeta
   
    def __init__(self, container, request_id, nvprof):
        self.container = container
        self.request_id = request_id
        self.nvprof = nvprof


    def make_empty_result(self):
        result = {}
        keys = ['framework', 'topology', 'batch_size', 'source', 'iterations', 'score', 'training_images_per_second']
        for key in keys:
            result[key] = None
        result['forward_timing'] = OrderedDict()
        result['backward_timing'] = OrderedDict()
        return result
            
    def sudo_docker_wrapper(self, command):
        return 'sudo docker exec %s %s' % (self.container, command)

    @abstractmethod
    def parse_from_log(self, lines):
        pass

 

class Caffe_Workload(Workload):

    build_script = 'scripts/build_caffe.sh'
    run_script = 'scripts/caffe_bench'
    docker_caffe_bench = '/home/caffe/caffe_bench'
    docker_run_script = '/home/caffe/caffe_bench/run_single.sh'
    
    batch_size = { \
        'alexnet_group1' : (256, 1), \
        'alexnet_group2' : (256, 1), \
        'googlenet' : (32, 1), \
        'vgg_19' : (32, 1)
    }
    # Workaround fix.
    source = ["bvlc caffe", "nvidia caffe"]

    topology = { \
        'alexnet_group1' : 'alexnet_group1.prototxt', \
        'alexnet_group2' : 'alexnet_group2.prototxt', \
        'googlenet' : 'googlenet.prototxt', \
        'vgg_19' : 'vgg_19.prototxt', \
        'lenet' : 'lenet.prototxt'
    }

    middle_dir = 'template'

    def __init__(self, container, request_id, nvprof):
        super(Caffe_Workload, self).__init__(container, request_id, nvprof)

    def make(self):
        pass

    def copy(self):
        command = 'docker cp %s %s:/home/caffe/' % (self.__class__.run_script, self.container)
        command = sudo_wrapper(command)
        os.popen(command)
                

    def get_log(self):
        tmp_dir = '/tmp/%s' % self.request_id
        os.mkdir(tmp_dir)
        command = 'docker cp %s:/tmp/log %s' % (self.container, tmp_dir)
        os.popen(command)
        command = 'zip -r log/%s.zip %s' % (self.request_id, tmp_dir)
        os.popen(command)
                
    def build_in_docker(self):
        pass


    def run_batch(self, topologies, iterations, batch_size, gpuid, global_buffer, source):
        results = []
        for topology in topologies:
            if batch_size == 0:
                bzs = self.__class__.batch_size[topology]
            else:
                bzs = [batch_size, ]
            for bz in bzs:
                result_item = self.run_specific_config(topology, iterations, bz, gpuid, source, global_buffer)
                results.append(result_item)
        if (self.nvprof):
            self.get_log()
        return results


    def parse_from_log(self, lines, result):
        for line in lines:
            # Get Average Forward Pass Time
            m = re.match('.*Average Forward pass.*', line.strip())
            if m is not None:
                result['Average Forward pass'] = float(line.split(' ')[-2])
                continue
            # Get Average Backward Pass Time
            m = re.match('.*Average Backward pass.*', line.strip())
            if m is not None:
                result['Average Backward pass'] = float(line.split(' ')[-2])
                continue
            m = re.match(r"(.*)\](.*)forward:(.*)ms", line)
            if m is not None:
                layer_name = m.group(2).strip()
                timing = float(m.group(3).strip())
                result['forward_timing'][layer_name] = timing
                continue
            m = re.match(r"(.*)\](.*)backward:(.*)ms", line)
            if m is not None:
                layer_name = m.group(2).strip()
                timing = float(m.group(3).strip())
                result['backward_timing'][layer_name] = timing
                continue
        result['score'] = 1000.0 * result['batch_size'] / result['Average Forward pass'] 
        result['training_images_per_second'] = 1000.0 * result['batch_size'] / (result['Average Backward pass'] + result['Average Forward pass'])
        return result 

 
    def run_specific_config(self, topology, iterations, batch_size, gpuid, caffe_source, global_buffer):
        '''
            
	        Args:
                Topology: Deep Neural Network Structure 
                iterations: how many iterations in the test
                batch size: batch size in one training or classification procedure
                gpuid: GPUID start from 0
                caffe_source: 'bvlc' or 'nvidia'
            Returns:
                ret performance metrics 
        '''
        result = self.make_empty_result()
        result['framework'] = 'Caffe'
        result['topology'] = topology
        result['batch_size'] = batch_size
        result['source'] = caffe_source
        result['iterations'] = iterations
        assert(topology in self.__class__.topology.keys())
        template = os.path.join(self.__class__.docker_caffe_bench, self.__class__.middle_dir , self.__class__.topology[topology])
        command = '%s %s %d %d %d %s' % (self.__class__.docker_run_script, template, batch_size, iterations, gpuid, caffe_source)
        command = self.sudo_docker_wrapper(command)
        local_buffer = []
        fp = Popen(command, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
        while True:
            line = fp.stdout.readline()
            global_buffer.extend(line)
            local_buffer.append(line) 
            if line == '' and fp.poll() != None:
                break
        self.parse_from_log(local_buffer, result)
        return result
    
if __name__ == '__main__':
    cw = Caffe_Workload(sys.argv[1])
    cw.copy()
    results = []
    iterations = 1
    topologies = ['alexnet_group1', 'alexnet_group2'] 
    cw.run_batch(topologies, iterations, [100], 0)
