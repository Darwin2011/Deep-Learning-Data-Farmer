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


class Task_Scheduler(object):

    TASK_STATE = Enum("Pendding", "Running", "Finish")
    
    def __init__(self):
        self.sql_wrapper    = Mysql_wrapper('localhost', 'root', 'tracing', 'automations')
        self.docker_control = Docker_Monitor()
        self.gpu_monitor    = GPUMonitor()
        self.gpu_monitor.init_local_gpu_lists()
        self.gpu_monitor.register_listener(self)
        self.requests = {}
        self.pending_requests = []
        self.prepare_env()
        self.lock = threading.Lock()

    def prepare_env(self):
        self.sql_wrapper.init_database()
        self.docker_control.get_local_images(self.sql_wrapper)

    def build_image(self):
        pass

    def create_account(self, user, password, mail):
        result = False
        if self.sql_wrapper.exists_mail(mail):
            result = False
        else:
            self.sql_wrapper.create_account(user, password, mail)
            result = True
        return result

    def exists_account(self, mail, password):
        return self.sql_wrapper.account_login(mail, password)

    def parse_new_request_from_xml(self, filepath):
        xml_parser = XMLParser(filepath)
        request = xml_parser.parse_xml()
        gpu_device = self.gpu_monitor.get_gpu_from_model(request['gpu_model'])
        if gpu_device is None:
            farmer_log.error('Internal Fatal Error, Wrong GPU Model Name')
            raise Exception('Internal Fatal Error')
        # Add some keys request dicts
        request['gpu_id'] = gpu_device.gpuid
        request['gpu_device'] = gpu_device
        request['history_temperature'] = []
        request['history_freq'] = []
        request['history_power'] = []
        request['raw_buffer'] = bytearray()
        return request 

    def assign_request(self, filepath):
        """
            scheduler tries to assign one request to one specified GPU
        """
        # This lock is to protect assign_request. There're multiple process/threads may execute assign requests.
        # So I use one lock here for safety.
        self.lock.acquire()
        request = self.parse_new_request_from_xml(filepath)
        request["state"] = self.__class__.TASK_STATE.Pendding
        self.requests[request['request_id']] = request
        self.pending_requests.append(request)
        self.lock.release()
        t = threading.Thread(target=self.schedule)
        t.start()

    def schedule(self):
        """
            Only one thread can be run here
        """
        self.lock.acquire()
        for request in self.pending_requests:
            if self.request_runnable(request):
                request['gpu_device'].blocked = True 
                request["state"] = self.__class__.TASK_STATE.Running
                self.test_start(request)
                request['gpu_device'].blocked = False
                self.pending_requests.remove(request)
        self.lock.release()
                
    
    def request_runnable(self, request):
        return False if request['gpu_device'].blocked else True
       
 
    def test_start(self, request):
        index = self.docker_control.get_image_index(request['cuda_string'], request['cudnn_string'], request['caffe'], request['tensorflow'])
        if index == -1:
            # TODO
            self.build_image()
            # TODO
            # docker control inert docker_image_info into database
            index = self.docker_control.get_image_index(request['cuda_string'], request['cudnn_string'], request['caffe'], request['tensorflow'])
        gpuid = request['gpu_id']
        gpuid = 1
        request_id = request['request_id']
        image = self.docker_control.get_image(index)
        container = get_random_container()
        execute(run_docker(container, image.repository, image.tag))
        test_workload = Caffe_Workload(container, request_id, request['profiling'])
        test_workload.copy()
        results = test_workload.run_batch(request['topology'], request['iterations'], request['batch_size'], gpuid, request['raw_buffer'], request['source'])
        self.sql_wrapper.inert_item_in_request_reports(request_id, container,
           request["gpu_model"], request["email"], request["framework"],
           request["topology"], request["batch_size"], request["iterations"])
        for result in results:
            self.sql_wrapper.inert_item_in_result_reports(\
                request_id, \
                container, \
                request["gpu_model"], \
                result['framework'], \
                result['topology'],\
                result['batch_size'],\
                result['source'],\
                result['iterations'],\
                result['score'],\
                result['training_images_per_second']
            )
        execute(stop_docker(container))
        request["state"] = self.__class__.TASK_STATE.Finish
        return True

    def response_gpu_state_request(self, request_id):
        request = self.requests[request_id]
        gpu_device = request['gpu_device']
        return gpu_device.response_status_as_json(request)    

    def make_download_file(self, request_id):
        dataMediator = self.sql_wrapper.get_result_by_request_id(request_id)
        dataFrame = pandas.DataFrame(dataMediator.to_data_frame())
        filename = request_id + ".xlsx"
        dataFrame.to_excel("./xlsx/" + filename, index = False)
        return filename

if __name__ == "__main__":
    scheduler = Task_Scheduler()
    scheduler.assign_request(sys.argv[1])
    print("print buffer")
