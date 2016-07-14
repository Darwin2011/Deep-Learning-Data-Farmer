#!usr/bin/env python
import os
import workload
from XMLParser import XMLParser
from MySql_wrapper import Mysql_wrapper
from cmd_generator import *
from workload import Caffe_Workload
import pandas
import cmd_generator
from docker_control import Docker_Monitor

class GPU_Scheduler:

    def __init__(self):
        self.parser = XMLParser("DockerConfig.xml")
        self.sql_wrapper = Mysql_wrapper("localhost", "root", "RACQ4F6c")
        self.docker_control = Docker_Monitor()

    def prepare_env(self):
        self.parser.parse()
        self.sql_wrapper.init_database()
        self.docker_control.get_local_images(self.sql_wrapper)

    def build_image(self):
        pass

    def test_scheduler(self):
        index = self.docker_control.get_image_index(self.parser)
        if -1 == index:
            # TODO
            self.build_image()
            index = self.docker_control.get_image_index(self.parser)
        image = self.docker_control.get_image(index)
        container = get_random_container()
        execute(run_docker(container, image.repository, image.tag))
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
        execute(kill_docker(container))

if __name__ == "__main__":
    scheduler = GPU_Scheduler()
    scheduler.build_image()
    scheduler.prepare_env()
    scheduler.test_scheduler()