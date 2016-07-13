#!/usr/bin/env python
import os
import re
import sys
import pandas
from server.server_start import result_content_html
class Workload(object):
   
    def __init__(self, container):
        self.container = container



class Caffe_Workload(Workload):

    build_script = 'scripts/build_caffe.sh'
    run_script = 'scripts/caffe_bench'
    docker_caffe_bench = '/home/caffe/caffe_bench'
    docker_run_script = '/home/caffe/caffe_bench/run_single.sh'
    

    topology = { \
        'alexnet_group1' : 'alexnet_group1.prototxt',
        'alexnet_group2' : 'alexnet_group2.prototxt',
        'googlenet' : 'googlenet.prototxt',
        'vgg_19' : 'vgg_19.prototxt',
        'lenet' : 'lenet.prototxt'
    }

    middle_dir = 'template'

    def __init__(self, container):
        super(Caffe_Workload, self).__init__(container)

    def sudo_wrapper(self, command):
        return 'sudo ' + command

    def sudo_docker_wrapper(self, command):
        return 'sudo docker exec %s %s' % (self.container, command)

    def make(self):
        pass

    def copy(self):
        command = 'docker cp %s %s:/home/caffe/' % (self.__class__.run_script, self.container)
        command = self.sudo_wrapper(command)
        os.popen(command)
         
    def build_in_docker(self):
        pass

    def run(self, topology, iterations, batch_size, gpuid, caffe_source):
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
        result['iterations'] = caffe_source
        if topology in self.__class__.topology.keys():
            template = os.path.join(self.__class__.docker_caffe_bench, self.__class__.middle_dir , self.__class__.topology[topology])
            command = '%s %s %d %d %d %s' % (self.__class__.docker_run_script, template, batch_size, iterations, gpuid, caffe_source)
            command = self.sudo_docker_wrapper(command)
            fp = os.popen(command)
            for line in fp:
                m = re.match('^Score', line.strip())
                if m is not None:
                    result['score'] = float(line.split(':')[-1])                     
                m = re.match('^Training Images Per Second', line.strip())
                if m is not None:
                    result['training images per second'] = float(line.split(':')[-1])
            return result


if __name__ == '__main__':
    cw = Caffe_Workload(sys.argv[1])
    cw.copy()
    results = []
    iterations = 1
    topology_bz_maps = {'alexnet_group1' : (256, 1), 'alexnet_group2' : (256, 1), 'googlenet' : (32, 1), 'vgg_19' : (32, 1)}
    for topology in ('alexnet_group1', 'alexnet_group2', 'googlenet', 'vgg_19'):
        bzs = topology_bz_maps[topology]
        for bz in bzs:
            result = cw.run(topology, iterations, bz, 0, 'upstream')
            results.append(result)
            result = cw.run(topology, iterations, bz, 0, 'nvidia')
            results.append(result)
    df = pandas.DataFrame(results)
    cols = df.columns.tolist()
    cols = ['topology', 'source', 'batch_size', 'iterations', 'score', 'training images per second']
    df = df[cols]
    df.to_html(result_content_html, index = False)
