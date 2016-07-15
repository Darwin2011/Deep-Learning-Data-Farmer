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
from gpu_control import *

class GPU_Scheduler:

    def __init__(self):
        self.parser = XMLParser("DockerConfig.xml")
        self.sql_wrapper = Mysql_wrapper("localhost", "root", "tracing")
        self.docker_control = Docker_Monitor()
        self.gpu_monitor = GPUMonitor()
        self.gpu_monitor.init_local_gpu_lists()

    def prepare_env(self):
        self.parser.parse()
        self.sql_wrapper.init_database()
        self.docker_control.get_local_images(self.sql_wrapper)

    def build_image(self):
        pass

    def test_scheduler(self, gpumodel, topologies, iterations, batch_size):
        index = self.docker_control.get_image_index(self.parser)
        if -1 == index:
            # TODO
            self.build_image()
            index = self.docker_control.get_image_index(self.parser)
        gpu_device = self.gpu_monitor.get_gpu_from_model(gpumodel)
        if gpu_device is None:
            farmer_logger.error('Internal Fatal Error, Wrong GPU Model Name')
            raise Exception('Internal Fatal Error')
        else: 
            gpuid = gpu_device.gpuid 
            image = self.docker_control.get_image(index)
            container = get_random_container()
            print(container)
            execute(run_docker(container, image.repository, image.tag))
            test_workload = Caffe_Workload(container)
            test_workload.copy()
            test_workload.run_batch(topologies, iterations, batch_size, gpuid)
            execute(kill_docker(container))

if __name__ == "__main__":
    scheduler = GPU_Scheduler()
    scheduler.build_image()
    scheduler.prepare_env()
    scheduler.test_scheduler('GeForce GTX TITAN X', ['alexnet_group1', 'alexnet_group2'], 100, [2, 20])
