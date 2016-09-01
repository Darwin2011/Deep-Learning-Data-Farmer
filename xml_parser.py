#!usr/bin/env python

import xml.etree.ElementTree as ET
import farmer_log
from os import path

"""
Target XML Format
<root>
        <framework>all</framework>
        <batch_size>default</batch_size>
        <cudnn>cudnn-5.1</cudnn>
        <cuda>cuda-7.5</cuda>
        <iterations>100</iterations>
        <gpu_model>Tesla M40</gpu_model>
        <gpu_boost>Off</gpu_boost>
        <email>yan.dai@intel.com</email>
        <topology>all</topology>
</root>
"""

class XMLParser(object):

    cudnn_strings = {'5.0' : 'cudnn-7.5-linux-x64-v5.0-rc'}  
    cuda_strings = {'7.5' : 'cuda_7.5.18'}  

    def __init__(self, filePath):
        self.filepath = filePath
        self.config_dicts = {}
        

    def parse_xml(self):
        tree = ET.parse(self.filepath)
        root = tree.getroot()
        for child in root:
            self.config_dicts[child.tag] = child.text
        self.update_as_rules()
        return self.config_dicts
            
 
    def update_as_rules(self):
        if self.config_dicts['framework'] == 'bvlc caffe' or self.config_dicts['framework'] == 'nvidia caffe':
            self.config_dicts['source'] = self.config_dicts['framework'].split('_')[0]
            self.config_dicts['framework'] = ['caffe', ]
        if self.config_dicts['batch_size'] == 'default':
            self.config_dicts['batch_size'] = 0
        self.config_dicts['batch_size'] = int(self.config_dicts['batch_size'])
        self.config_dicts['cudnn'] = float(self.config_dicts['cudnn'].split('-')[-1])
        self.config_dicts['cuda'] = float(self.config_dicts['cuda'].split('-')[-1])
        self.config_dicts['iterations'] = int(self.config_dicts['iterations'])
        if self.config_dicts['topology'] == "all":
            self.config_dicts['topology'] = ['alexnet_group1', 'alexnet_group2', 'googlenet', 'vgg_19']
        else:
            self.config_dicts['topology'] = [self.config_dicts['topology']]
        self.config_dicts['cudnn_string'] = self.__class__.cudnn_strings[str(self.config_dicts['cudnn'])] 
        self.config_dicts['cuda_string'] = self.__class__.cuda_strings[str(self.config_dicts['cuda'])] 
        self.config_dicts['profiling'] = True if self.config_dicts['profiling'] == 'true' else False
        self.config_dicts['tensorflow'] = False
        self.config_dicts['caffe'] = False
        for fw in self.config_dicts['framework']:
            self.config_dicts[fw] = True

if __name__ == "__main__":
    xmlparser = XMLParser('/tmp/1.xml')
    print(xmlparser.parse_xml())
