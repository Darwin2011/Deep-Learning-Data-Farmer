#!/usr/bin/env python

import os
import re
import MySQLdb
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

    def get_image_property(self, cuda_version, cuda_strings_version, cudnn_version, cudnn_strings_version, caffe_installed, tensorflow_installed):
        self.cuda_version = cuda_version 
        self.cuda_strings_version = cuda_strings_version
        self.cudnn_version = cudnn_version
        self.cudnn_strings_version = cudnn_strings_version
        self.caffe_installed = caffe_installed
        self.tensorflow_installed = tensorflow_installed
        
def Singleton(cls, *args, **kw):
    instances = {}
    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton

@Singleton
class Docker_Monitor(object):
    """
        
    """
    def __init__(self, host, user, passwd, database, table):
        self.images = []
        self.db_connection = \
            MySQLdb.connect(host = "%s" % (host, ), user = "%s" % (user, ), passwd = "%s" % (passwd, ), db = "%s" % (database, ))
        self.table = table

    def get_local_images(self):
        def get_detailed_info_from_db(db_connection, table, repository, tag):
            cursor = db_connection.cursor()
            sql_command = "SELECT * FROM %s WHERE REPOSITORY = '%s' AND TAG = '%s'" % (table, repository, tag)
            cursor.execute(sql_command)
            db_connection.commit()
            numrows = int(cursor.rowcount)
            if numrows == 1:
                row = cursor.fetchone()
                return row
            else:
                return None
            
        command = "sudo docker images | grep -v none | grep -vi REPOSITORY"
        fp = os.popen(command)
        for line in fp:
            (repository, tag, image_id, created_time, size) = re.split(' {3,}', line.strip())
            image = Docker_Image(repository, tag, image_id, created_time, size)
            row = get_detailed_info_from_db(self.db_connection, self.table, repository, tag)
            if row is not None:
                (index, repository, tag, cuda_version, cuda_strings_version, cudnn_version, cudnn_strings_version, tensorflow_installed, caffe_installed) = row
                image.get_image_property(cuda_version, cuda_strings_version, cudnn_version, cudnn_strings_version, tensorflow_installed, caffe_installed)
                # needs to be checked when image exists
                self.images.append(image)
        fp.close()

    def get_image(self, index):
        if index < 0:
            return
        return self.images[index]

    def get_image_index(self, parser):
        """
        get the index of the item we looking for.
        If we won't find. the return -1.
            Paratmeter : the parser who have the flag value
        """
        result_index     = -1
        looking_for_item = [xmlParser.getCudeVersionString(),   \
                            xmlParser.getCudnnVersionString(),  \
                            xmlParser.is_tenseflow_installed(), \
                            xmlParser.is_caffe_installed()]

        for index, image in enumerate(self.images):

            image_item = [image.cuda_strings_version,  \
                          image.cudnn_strings_version, \
                          image.tensorflow_installed,  \
                          image.caffe_installed]
            if looking_for_item[0] == image_item[0] and \
               looking_for_item[1] == image_item[1] and \
               looking_for_item[2] == image_item[2] and \
               looking_for_item[3] == image_item[3]:
                result_index = index

        return result_index

if __name__ == "__main__":
    dm = Docker_Monitor('localhost', 'root', 'tracing', 'automations', 'docker_images')
    dm.get_local_images()
    print(dm.images[0].__dict__)
    parser = XMLParser("DockerConfig.xml")
    parser.parse()
    index = dm.get_image_index(parser)
    print (dm.get_image(index).__dict__)
