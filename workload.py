#!/usr/bin/env python
import os
import re
import sys
import pandas
from collections import OrderedDict
from cmd_generator import *
from subprocess import Popen, PIPE, STDOUT
from abc import ABCMeta, abstractmethod

"""
  Workload BaseClass
"""
class Workload(object):
    __metaclass__ = ABCMeta
   
    framework = None 
    host_build_script = None
    host_run_script = None
    docker_home = None
    docker_bench = None
    docker_run_script = None
    
    batch_size = { \
        'alexnet_group1' : (256, 1), \
        'alexnet_group2' : (256, 1), \
        'googlenet' : (32, 1), \
        'vgg_19' : (32, 1)
    }

    def __init__(self, container, request_id, nvprof):
        self.container = container
        self.request_id = request_id
        self.nvprof = nvprof
        self.results = [] 

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

    def copy(self):
        command = 'docker cp %s %s:%s' % (self.__class__.host_run_script, self.container, self.__class__.docker_bench)
        command = sudo_wrapper(command)
        print(command)
        os.popen(command)
                
    def get_log(self):
        tmp_dir = '/tmp/%s' % self.request_id
        os.mkdir(tmp_dir)
        command = 'docker cp %s:/tmp/log %s' % (self.container, tmp_dir)
        os.popen(command)
        command = 'zip -r log/%s.zip %s' % (self.request_id, tmp_dir)
        os.popen(command)

    @abstractmethod
    def generate_run_comamnd(self, topology, iterations, batch_size, gpuid, source):
      pass 


    @abstractmethod
    def parse_from_log(self, lines):
        pass

    def run_specific_config(self, topology, iterations, batch_size, gpuid, source, global_buffer):
        '''
            
	        Args:
                Topology: Deep Neural Network Structure 
                iterations: how many iterations in the test
                batch size: batch size in one training or classification procedure
                gpuid: GPUID start from 0
                source: 'bvlc' or 'nvidia'
            Returns:
                ret performance metrics 
        '''
        result = self.make_empty_result()
        result['framework'] = self.__class__.framework 
        result['topology'] = topology
        result['batch_size'] = batch_size
        result['source'] = source
        result['iterations'] = iterations
        assert(topology in self.__class__.topology.keys())
        command = self.sudo_docker_wrapper(self.generate_run_comamnd(topology, iterations, batch_size, gpuid, source))
        print(command)
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


class Tensorflow_Workload(Workload):
    framework = 'Tensorflow'
    host_build_script = 'scripts/build_caffe.sh'
    host_run_script = 'scripts/tensorflow_bench'
    docker_home = '/home/tensorflow'
    docker_bench = '/home/tensorflow/tensorflow_bench'
    docker_run_script = '/home/tensorflow/tensorflow_bench/run_single.sh'
    
    topology = { \
        'alexnet_group1' : 'benchmark_alexnet.py', \
        'googlenet' : 'benchmark_googlenet.py', \
        'vgg_19' : 'benchmark_vgg.py', \
    }

    def __init__(self, container, request_id, nvprof):
        super(Tensorflow_Workload, self).__init__(container, request_id, nvprof)

    def make(self):
        pass

    def build_in_docker(self):
        pass

    def parse_from_log(self, lines, result):
        for line in lines:
            m = re.match(r"(.*)Forward across(.*)steps, (.*)\+/\-(.*)", line)
            if m is not None:
                result['Average Forward Pass'] = float(m.group(3))
                continue
            m = re.match(r"(.*)Forward-backward across(.*)steps, (.*)\+/\-(.*)", line)
            if m is not None:
                result['Average Pass'] = float(m.group(3))
                continue
        result['score'] = 1.0 * result['batch_size'] / result['Average Forward Pass'] 
        result['training_images_per_second'] = 1.0 * result['batch_size'] / result['Average Pass'] 
        return result 
        
    def generate_run_comamnd(self, topology, iterations, batch_size, gpuid, source):
        command = '%s %s %d %d %d' % (self.__class__.docker_run_script, os.path.join(self.__class__.docker_bench, self.__class__.topology[topology]), gpuid, batch_size, iterations)
        return command 

class Caffe_Workload(Workload):
    framework = 'Caffe'
    host_build_script = 'scripts/build_caffe.sh'
    host_run_script = 'scripts/caffe_bench'
    docker_home = '/home/caffe'
    docker_bench = '/home/caffe/caffe_bench'
    docker_run_script = '/home/caffe/caffe_bench/run_single.sh'
    
    # Workaround fix.
    source = ["bvlc caffe", "nvidia caffe"]

    topology = { \
        'alexnet_group1' : 'alexnet_group1.prototxt', \
        'alexnet_group2' : 'alexnet_group2.prototxt', \
        'googlenet' : 'googlenet.prototxt', \
        'vgg_19' : 'vgg_19.prototxt', \
    }

    middle_dir = 'template'

    def __init__(self, container, request_id, nvprof):
        super(Caffe_Workload, self).__init__(container, request_id, nvprof)

    def make(self):
        pass
                
    def build_in_docker(self):
        pass


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

    def generate_run_comamnd(self, topology, iterations, batch_size, gpuid, source):
        template = os.path.join(self.__class__.docker_bench, self.__class__.middle_dir , self.__class__.topology[topology])
        command = '%s %s %d %d %d %s' % (self.__class__.docker_run_script, template, batch_size, iterations, gpuid, source)
        return command 
    
