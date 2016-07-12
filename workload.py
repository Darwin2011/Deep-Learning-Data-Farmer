#!/usr/bin/env python
import os
import re
import sys

class Workload(object):
   
    def __init__(self, container):
        self.container = container



class Caffe_Workload(Workload):

    build_script = "scripts/build_caffe.sh"
    run_script = "scripts/caffe_bench"
    docker_caffe_bench = "/home/caffe/caffe_bench"
    docker_run_script = "/home/caffe/caffe_bench/run_single.sh"
    

    topology = { \
        "alexnet_group1" : "alexnet_group1.prototxt",
        "alexnet_group2" : "alexnet_group2.prototxt",
        "googlenet" : "googlenet.prototxt",
        "vgg_19" : "vgg_19.prototxt",
        "lenet" : "lenet.prototxt"
    }

    middle_dir = "template"

    def __init__(self, container):
        super(Caffe_Workload, self).__init__(container)

    def sudo_wrapper(self, command):
        return "sudo " + command

    def sudo_docker_wrapper(self, command):
        return "sudo docker exec %s %s" % (self.container, command)

    def make(self):
        pass

    def copy(self):
        command = "docker cp %s %s:/home/caffe/" % (self.__class__.run_script, self.container)
        command = self.sudo_wrapper(command)
        os.popen(command)
         
    def build_in_docker(self):
        pass

    def run(self, topology, iterations, batch_size, gpuid, caffe_source):
        """
            
	        Args:
                Topology: Deep Neural Network Structure 
                iterations: how many iterations in the test
                batch size: batch size in one training or classification procedure
                gpuid: GPUID start from 0
                caffe_source: "bvlc" or "nvidia"
            Returns:
                ret performance metrics 
        """
	
        result = {}
        if topology in self.__class__.topology.keys():
            template = os.path.join(self.__class__.docker_caffe_bench, self.__class__.middle_dir , self.__class__.topology[topology])
            command = "%s %s %d %d %d %s" % (self.__class__.docker_run_script, template, batch_size, iterations, gpuid, caffe_source)
            command = self.sudo_docker_wrapper(command)
            fp = os.popen(command)
            for line in fp:
                m = re.match("^Score", line.strip())
                if m is not None:
                    result['score'] = float(line.split(':')[-1])                     
                m = re.match("^Training Images Per Second", line.strip())
                if m is not None:
                    result['training images per second'] = float(line.split(':')[-1])
            return result


if __name__ == "__main__":
    cw = Caffe_Workload(sys.argv[1])
    cw.copy()
    result = cw.run("alexnet_group1", 100, 256, 1, "nvidia")
    print(result)
