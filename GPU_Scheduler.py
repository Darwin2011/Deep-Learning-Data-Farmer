#!usr/bin/env python
import os
import workload
from XMLParser import XMLParser
from MySql_wrapper import Mysql_wrapper
from cmd_generator import *
from workload import Caffe_Workload
import pandas
import cmd_generator

class GPU_Scheduler:

    def __init__(self):
        self.parser = XMLParser("DockerConfig.xml")
        self.sql_wrapper = Mysql_wrapper("localhost", "root", "RACQ4F6c")
        self.sql_wrapper.init_database()

    def prepare_env(self):
        if self.has_images_existed():
            container_id = cmd_generator.get_random_container()
            run_docker_command = cmd_generator.run_docker(container_id, )
            #TODO
        else:
            self.build_image()


    def has_images_existed(self):
        cudeString = self.parser.getCudeVersionString()
        cudnnString = self.parser.getCudnnVersionString()
        return self.sql_wrapper.has_image_in_db_by_cuda_cuddn(cudeString, cudnnString)

    def build_image(self):
        pass

    def test_scheduler(self, container):
        test_workload = Caffe_Workload(container)
        test_workload.copy()
        results = []
        iterations = 1
        topology_bz_maps = {'alexnet_group1' : (256, 1), 'alexnet_group2' : (256, 1), 'googlenet' : (32, 1), 'vgg_19' : (32, 1)}
        for topology in ('alexnet_group1', 'alexnet_group2', 'googlenet', 'vgg_19'):
            bzs = topology_bz_maps[topology]
            for bz in bzs:
                result = test_workload.run(topology, iterations, bz, 0, 'upstream')
                results.append(result)
                result = test_workload.run(topology, iterations, bz, 0, 'nvidia')
                results.append(result)
        df = pandas.DataFrame(results)

if __name__ == "__main__":
    scheduler = GPU_Scheduler()
    scheduler.build_image()
    scheduler.has_images_existed()
    scheduler.prepare_env()