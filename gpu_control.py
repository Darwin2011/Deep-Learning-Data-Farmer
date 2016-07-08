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
        """
            Args:
                GPUID: gpu device N.O. as gpuid
        """
        self.gpuid = gpuid
        pass
   
    def sudo_wrapper(self, command):
        """
            return sudo + command as strings
        """
        return "sudo " + command
 
    def get_core_frequency(self, mode):
        """
            get core frequency as int
            Args:
                Mode: enum type in Enum("INSTANT", "APPLICATION", "APPLICATION_DEFAULT", "MAX")
                    e.g.
                    e = Enum("INSTANT", "APPLICATION", "APPLICATION_DEFAULT", "MAX")
                    instance.get_memory_frequency(e.INSTANT) 
        """
        command = "nvidia-smi -q -i %d -d CLOCK | grep -i Graphics | \
                awk '{print $(NF-1)}'" % (self.gpuid, )
        fp = os.popen(command)
        freq = fp.readlines()[mode.index]
        return int(freq)

    def get_memory_frequency(self, mode):
        """
            get memory frequency as int
            Args:
                Mode: enum type in Enum("INSTANT", "APPLICATION", "APPLICATION_DEFAULT", "MAX")
                    e.g.
                    e = Enum("INSTANT", "APPLICATION", "APPLICATION_DEFAULT", "MAX")
                    instance.get_memory_frequency(e.INSTANT)
            Returns:
                return memory frequency 
        """
        command = "nvidia-smi -q -i %d -d CLOCK | grep -i Memory | \
                awk '{print $(NF-1)}'" % (self.gpuid, )
        fp = os.popen(command)
        freq = fp.readlines()[mode.index]
        return int(freq)

    def set_persistant_mode(self, mode):
        """
            Set/Unset GPU frequency
            Args:
                Mode: int, 1 as persistant on and 0 as persistant off
            Returns:
                return True or False
        """
        command = "nvidia-smi -i %d -pm %d" % (self.gpuid, mode)
        command = self.sudo_wrapper(command)
        #return True as placeholder
        return True 

    def set_frequency(self, core_frequency, memory_frequency):
        """
            set GPU frequency
            Args:
                core_frequency: int, unit is MHZ
                memory_freqency: int, unit is MHZ
            Returns:
                True when successfully setting the clocks  
        """
        command = "nvidia-smi -i %d -ac %d,%d" % (self.gpuid, memory_frequency, core_frequency)
        command = self.sudo_wrapper(command)
        os.system(command)
        application_core_freq = self.get_core_frequency(self.__class__.graphics_mode.APPLICATION)
        application_memory_freq = self.get_memory_frequency(self.__class__.graphics_mode.APPLICATION)
        return (application_core_freq == core_frequency) and (memory_frequency == application_memory_freq)

if __name__ == '__main__':
    gpu = GPUDevice(0)
    graphics_mode = gpu.__class__.graphics_mode 
    print(gpu.set_persistant_mode(1))
    print(gpu.set_frequency(1002, 3505))
    print(gpu.get_core_frequency(graphics_mode.INSTANT))
    print(gpu.get_memory_frequency(graphics_mode.INSTANT))
