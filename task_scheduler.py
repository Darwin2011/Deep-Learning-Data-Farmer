#!usr/bin/env python
import os
import sys
import workload
from xml_parser import *
from MySql_wrapper import Mysql_wrapper
from cmd_generator import *
from workload import Caffe_Workload
import pandas
import cmd_generator
import time
import threading
from docker_control import Docker_Monitor
from threading import Thread
from gpu_control import *
from enum import Enum

TASK_STATE = Enum("Pendding", "Running", "Finish")

class Task_Scheduler(object):

    def __init__(self):
        self.sql_wrapper    = Mysql_wrapper('localhost', 'root', 'tracing', 'animations')
        self.docker_control = Docker_Monitor()
        self.gpu_monitor    = GPUMonitor()
        self.gpu_monitor.init_local_gpu_lists()
        self.gpu_monitor.register_listener(self)
        self.requests = {}
        self.prepare_env()
        self.lock = threading.Lock()

    def prepare_env(self):
        self.sql_wrapper.init_database()
        self.docker_control.get_local_images(self.sql_wrapper)

    def build_image(self):
        pass

    def parse_new_request_from_xml(self, filepath):
        xml_parser = XMLParser(filepath)
        config = xml_parser.parse_xml()
        gpu_device = self.gpu_monitor.get_gpu_from_model(config['gpu_model'])
        if gpu_device is None:
            farmer_log.error('Internal Fatal Error, Wrong GPU Model Name')
            raise Exception('Internal Fatal Error')
        config['gpu_id'] = gpu_device.gpuid
        config['gpu_device'] = gpu_device
        return config

    def assign_request(self, filepath):
        """
            scheduler tries to assign one request to one specified GPU
        """
        self.lock.acquire()
        config = self.parse_new_request_from_xml(filepath)
        config["state"] = TASK_STATE.Pendding
        config['raw_buffer'] = bytearray()
        self.requests[config['request_id']] = config
        self.lock.release()
        thread = Thread(target = self.run) 
        thread.start()
 
    def run(self):
        for key in self.requests.keys():
            request = self.requests[key]
            if self.request_runnable(request):
                status = self.test_start(request)
                if status:
                    request['gpu_device'].blocked = False
                #can be poped after inserting into database
                #self.requests.pop(request['request_id'], None)
                
    
    def request_runnable(self, config):
        return False if config['gpu_device'].blocked else True
       
 
    def test_start(self, config):
        index = self.docker_control.get_image_index(config['cuda_string'], config['cudnn_string'], config['caffe'], config['tensorflow'])
        if index == -1:
            # TODO
            self.build_image()
            # TODO
            # docker control inert docker_image_info into database
            index = self.docker_control.get_image_index(config['cuda_string'], config['cudnn_string'], config['caffe'], config['tensorflow'])
        gpuid = config['gpu_id'] 
        image = self.docker_control.get_image(index)
        container = get_random_container()
        config["state"] = TASK_STATE.Running
        execute(run_docker(container, image.repository, image.tag))
        test_workload = Caffe_Workload(container)
        test_workload.copy()
        results = test_workload.run_batch(config['topology'], config['iterations'], config['batch_size'], gpuid, config['raw_buffer'])
        farmer_log.info(results)
        farmer_log.info(config) 
        request_id = config['request_id']
        self.sql_wrapper.inert_item_in_request_reports(request_id, container,
           config["gpu_model"], config["email"], config["framework"],
           config["topology"], config["batch_size"], config["source"], config["iteration"])
        for result in results:
            self.sql_wrapper.inert_item_in_result_reports(\
                request_id, \
                container, \
                gpuid, \
                config['email'], \
                result['framework'], \
                result['topology'],\
                result['batch_size'],\
                result['source'],\
                result['iterations'],\
                result['score'],\
                result['training images per second']
            )
        execute(stop_docker(container))
        config["state"] = TASK_STATE.Finish
        return True

if __name__ == "__main__":
    scheduler = Task_Scheduler()
    scheduler.assign_request(sys.argv[1])
    print("print buffer")
