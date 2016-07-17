#!/usr/bin/env python

import os
import re
from MySql_wrapper import Mysql_wrapper
from XMLParser import XMLParser


class Docker_Image(object):

    def __init__(self, repository, tag, image_id, created_time, size):
        self.repository = repository
        self.tag = tag
        self.image_id = image_id
        self.created_time = created_time
        self.size = size
        self.cuda_version = None
        self.cuda_strings_version = None
        self.cudnn_version = None
        self.cudnn_strings_version = None
        self.caffe_installed = False
        self.tensorflow_installed = False

    def get_image_property(self, cuda_version, cuda_strings_version, cudnn_version, cudnn_strings_version, tensorflow_installed, caffe_installed):
        self.cuda_version = cuda_version 
        self.cuda_strings_version = cuda_strings_version
        self.cudnn_version = cudnn_version
        self.cudnn_strings_version = cudnn_strings_version
        self.tensorflow_installed = tensorflow_installed
        self.caffe_installed = caffe_installed
        
class Docker_Monitor(object):
    """
        
    """
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Docker_Monitor, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.images = []

    def get_local_images(self, sql_wrapper):
        del self.images[:]
        command = "sudo docker images | grep -v none | grep -vi REPOSITORY"
        command = "docker images | grep -v none | grep -vi REPOSITORY"
        fp = os.popen(command)
        for line in fp:
            (repository, tag, image_id, created_time, size) = re.split(' {3,}', line.strip())
            image = Docker_Image(repository, tag, image_id, created_time, size)
            row = sql_wrapper.get_detailed_info_from_db(repository, tag)
            if row is not None:
                (index, repository, tag, cuda_version, cuda_strings_version, cudnn_version, cudnn_strings_version, tensorflow_installed, caffe_installed) = row
                image.get_image_property(cuda_version, cuda_strings_version, cudnn_version, cudnn_strings_version, tensorflow_installed, caffe_installed)
                # needs to be checked when image exists
                self.images.append(image)
        fp.close()

    def get_image(self, index):
        if index < 0 or index > len(self.images):
            return
        return self.images[index]

    def get_image_index(self, cuda_version_string, cudnn_version_string, caffe_installed, tensorflow_installed):
        """
        get the index of the item we looking for.
        If we won't find. the return -1.
            Paratmeter : the parser who have the flag value
        """
        result_index = -1
        for index, image in enumerate(self.images):
            if image.cuda_strings_version == cuda_version_string and \
                image.cudnn_strings_version == cudnn_version_string:
                if (caffe_installed == False or (caffe_installed == True and image.caffe_installed == True)) and \
                    (tensorflow_installed == False or (tensorflow_installed == True and image.tensorflow_installed == True)):
                    return index
        return result_index

if __name__ == "__main__":
    dm = Docker_Monitor('localhost', 'root', 'tracing')
    dm.get_local_images(Mysql_wrapper("localhost", "root", "tracing"))
    print(dm.images[0].__dict__)
    parser = XMLParser("DockerConfig.xml")
    parser.parse()
    index = dm.get_image_index(parser)
    print(index)
    print (dm.get_image(index).__dict__)
