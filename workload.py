#!/usr/bin/env python
import os
import re
import sys
import pandas
from cmd_generator import *
from subprocess import Popen, PIPE, STDOUT


class Workload(object):
   
    def __init__(self, container):
        self.container = container



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

    source = ["upstream", "nvidia"]

    topology = { \
        'alexnet_group1' : 'alexnet_group1.prototxt', \
        'alexnet_group2' : 'alexnet_group2.prototxt', \
        'googlenet' : 'googlenet.prototxt', \
        'vgg_19' : 'vgg_19.prototxt', \
        'lenet' : 'lenet.prototxt'
    }

    middle_dir = 'template'

    def __init__(self, container):
        super(Caffe_Workload, self).__init__(container)

    def sudo_docker_wrapper(self, command):
        return 'sudo docker exec %s %s' % (self.container, command)

    def make(self):
        pass

    def copy(self):
        command = 'docker cp %s %s:/home/caffe/' % (self.__class__.run_script, self.container)
        command = sudo_wrapper(command)
        os.popen(command)
         
    def build_in_docker(self):
        pass


    def run_batch(self, topologies, iterations, batch_size, gpuid, raw_buffer):
        results = []
        for topology in topologies:
            if batch_size == 0:
                bzs = self.__class__.batch_size[topology]
            else:
                bzs = [batch_size, ]
            for bz in bzs:
                for source in self.__class__.source:
                    result_item = self.run_specific_config(topology, iterations, bz, gpuid, source, raw_buffer)
                    results.append(result_item)
        return results
             
    def run_specific_config(self, topology, iterations, batch_size, gpuid, caffe_source, raw_buffer):
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
	
        result = {}
        result['topology'] = topology
        result['batch_size'] = batch_size
        result['source'] = caffe_source
        result['iterations'] = iterations
        if topology in self.__class__.topology.keys():
            template = os.path.join(self.__class__.docker_caffe_bench, self.__class__.middle_dir , self.__class__.topology[topology])
            command = '%s %s %d %d %d %s' % (self.__class__.docker_run_script, template, batch_size, iterations, gpuid, caffe_source)
            command = self.sudo_docker_wrapper(command)
            fp = Popen(command, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
            while True:
                line = fp.stdout.readline()
                raw_buffer.extend(line)
                m = re.match('.*Average Forward pass.*', line.strip())
                if m is not None:
                    result['Average Forward pass'] = float(line.split(' ')[-2])
                m = re.match('.*Average Backward pass.*', line.strip())
                if m is not None:
                    result['Average Backward pass'] = float(line.split(' ')[-2])
                if line == '' and fp.poll() != None:
                    break
            result['score'] = 1000.0 * batch_size / result['Average Forward pass'] 
            result['training images per second'] = 1000.0 * batch_size / (result['Average Backward pass'] + result['Average Forward pass'])
        return result
    
    def merge_result(self, result1, result2):
        if result1['topology'] == result2['topology'] and \
            result1['batch_size'] == result2['batch_size'] and \
            result1['iterations'] == result2['iterations'] and \
            result1['source'] != result2['source'] :
            result1[result1['source'] + ' score'] = result1['score']
            result1[result1['source'] + ' training images per second'] = result1['training images per second']
            result2[result2['source'] + ' score'] = result2['score']
            result2[result2['source'] + ' training images per second'] = result2['training images per second']
            updated_result = result1.copy()
            updated_result.update(result2)
            del updated_result['source']
            return updated_result    
        return None


if __name__ == '__main__':
    cw = Caffe_Workload(sys.argv[1])
    cw.copy()
    results = []
    iterations = 1
    topologies = ['alexnet_group1', 'alexnet_group2'] 
    cw.run_batch(topologies, iterations, [100], 0)
