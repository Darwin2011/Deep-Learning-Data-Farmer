#!/usr/bin/env python

import os
from enum import Enum


class GPUDevice(object):
    """
        GPU devices class definition
        Attributes:
            Device ID
            Total Memory
            ...   
    """
    graphics_mode = Enum("INSTANT", "APPLICATION", "APPLICATION_DEFAULT", "MAX")
    
    def __init__(self, gpuid):
        self.gpuid = gpuid
        pass
   
    def sudo_wrapper(self, command):
        return "sudo " + command
 
    def get_core_frequency(self, mode):
        """
            get core frequency as int
        """
        command = "nvidia-smi -q -i %d -d CLOCK | grep -i Graphics | \
                awk '{print $(NF-1)}'" % (self.gpuid, )
        fp = os.popen(command)
        freq = fp.readlines()[mode.index]
        return int(freq)

    def get_memory_frequency(self, mode):
        """
            get memory frequency as int
        """
        command = "nvidia-smi -q -i %d -d CLOCK | grep -i Memory | \
                awk '{print $(NF-1)}'" % (self.gpuid, )
        fp = os.popen(command)
        freq = fp.readlines()[mode.index]
        return int(freq)

    def set_persistant_mode(self):
        command = "nvidia-smi -i %d -pm 1" % (self.gpuid, )
        command = self.sudo_wrapper(command)
        fp = os.popen(command)
        print(fp.read())
        

    def set_frequency(self, core_frequency, memory_frequency):
        """
            set GPU frequency
            Returns:
                True when successfully setting the clocks  
        """
        command = "nvidia-smi -i -ac %d,%d" % (memory_frequency, core_frequency)
        command = self.sudo_wrapper(command)
        os.system(command)
        # return True as placeholder
        return True

if __name__ == '__main__':
    gpu = GPUDevice(0)
    graphics_mode = Enum("INSTANT", "APPLICATION", "APPLICATION_DEFAULT", "MAX")
    print(gpu.get_core_frequency(graphics_mode.INSTANT))
    print(gpu.get_memory_frequency(graphics_mode.INSTANT))
    print(gpu.set_persistant_mode())
