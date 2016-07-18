#!/usr/bin/env python
import re
import os
from enum import Enum

class GPUProcess(object):
    """
        Process Runing on  GPU
    """

    def __init__(self):
        self.pid = None
        self.command = None
        self.sm_utilization = None
        self.memory_utilization = None

    def set_info(self, pid, command, sm_utilization, memory_utilization):
        self.pid = pid
        self.command = command
        self.sm_utilization = sm_utilization
        self.memory_utilization = memory_utilization


class GPUDevice(object):
    """
        GPU devices class definition
        Attributes:
            Device ID
            Total Memory
            ...   
    """
    graphics_mode = Enum("INSTANT", "APPLICATION", "APPLICATION_DEFAULT", "MAX")
    sm_free_threshold = 0.03
    memory_free_threshold = 0.05
    
    def __init__(self, hostname, gpuid):
        """
            Args:
                GPUID: gpu device N.O. as gpuid
        """
        self.hostname = hostname 
        self.gpuid = gpuid
        self.gpu_model = None
        self.gpu_uuid = None
        self.processes = []
        self.blocked = False     
        self.listener = None
        self.get_gpu_model()
        self.task_queues = []
        self.email = 'nobody'


    def sudo_wrapper(self, command):
        """
            Returns:
             sudo + command as strings
        """
        return "sudo " + command
 
    def get_gpu_model(self):
        """
            get gpu model
            Returns:
                GPU Model Name 
        """ 
        command = "nvidia-smi -L"
        comamnd = self.sudo_wrapper(command)
        fp = os.popen(command)
        for line in fp:
            line = line.strip()
            m = re.match("GPU(.*)\:(.*)\(UUID:(.*)\)", line)
            gpuid = int(m.group(1))
            gpu_model = m.group(2)
            gpu_uuid = m.group(3)
            if gpuid == self.gpuid:
                self.gpu_model = gpu_model.strip()
                self.gpu_uuid = gpu_uuid.strip()
                return (self.gpu_model, self.gpu_uuid) 
        return None
    
    def get_email(self):
        return self.email
 

    def set_email(self, email):
        self.email = email
        

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


    def get_autoboost(self):
        """
            get autoboost Status
            Returns:
                True if autoboost on else False        
        """
        command = "nvidia-smi -q -i %d | grep -i 'Auto Boost' | head -n 1 | awk '{print $NF}'" % (self.gpuid, )
        fp = os.popen(command)
        results = fp.read()
        return True if "On" in results else False
         

    def set_autoboost(self, mode):
        """
            set autoboost 
            Args:
                Mode: int, 1 as autoboost on and 0 as autoboost off
            Returns:
                True when successfully setting the clocks  
        """
        command = "nvidia-smi -i %d --auto-boost-default=%d" % (self.gpuid, mode)
        command = self.sudo_wrapper(command)
        os.system(command)
        return True if self.get_autoboost() == mode else False
        

    def get_utlization(self):
        """
            get utilization
            Args:
                Mode: int, 1 as autoboost on and 0 as autoboost off
            Returns:
                True when successfully setting the clocks  
        """
        core_command = "nvidia-smi -q -d utilization -i %d | grep Gpu | awk '{print $(NF-1)}'" % (self.gpuid, )
        fp = os.popen(self.sudo_wrapper(core_command))
        core_utilization = float(0.01 * int(fp.read()))
        mem_command = "nvidia-smi -q -d utilization -i %d | grep Memory | grep -vi sam | awk '{print $(NF-1)}'" % (self.gpuid, )
        fp = os.popen(self.sudo_wrapper(mem_command))
        mem_utilization = float(0.01 * int(fp.read()))
        return (core_utilization, mem_utilization)

    def get_sm_utilization(self):
        core_command = "nvidia-smi -q -d utilization -i %d | grep Gpu | awk '{print $(NF-1)}'" % (self.gpuid, )
        fp = os.popen(self.sudo_wrapper(core_command))
        core_utilization = float(0.01 * int(fp.read()))
        return core_utilization

    def get_memory_utilization(self):
        mem_command = "nvidia-smi -q -d utilization -i %d | grep Memory | grep -vi sam | awk '{print $(NF-1)}'" % (self.gpuid, )
        fp = os.popen(self.sudo_wrapper(mem_command))
        mem_utilization = float(0.01 * int(fp.read()))
        return mem_utilization
         
    def is_gpu_free(self):
        """
            judge whether GPU is free or not
            Returns:
                True when GPU is free        
        """
        (core_utilization, mem_utilization) = self.get_utlization()
        if core_utilization < self.__class__.sm_free_threshold and \
            mem_utilization < self.__class__.memory_free_threshold:
            return True
        else:
            return False

    def get_running_process(self):
        """
            get information of GPU running process
        """
        command = "nvidia-smi pmon -i %d --count 1 | grep -v '^#'" % (self.gpuid, )
        fp = os.popen(self.sudo_wrapper(command))
        self.processes = []
        for line in fp:
            line = line.strip()
            info = re.split(' +', line)[0:8]
            (gpu, pid, proces_type, sm, mem, enc, dec, command) = info             
            gp = GPUProcess()
            gp.set_info(pid, command, sm, mem)
            self.processes.append(gp)
        return self.processes 
   

class GPUMonitor(object):

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GPUMonitor, cls).__new__(cls)
        return cls.instance 

    def sudo_wrapper(self, command):
        """
            Returns:
             sudo + command as strings
        """
        return "sudo " + command

    def __init__(self):
        self.gpulists = []
        self.gpu_models_set = set()
        self.gpu_uuid_set = set()
        
    def has_gpu(self, gpu):
        return gpu.gpu_uuid in self.gpu_uuid_set

    def get_gpu_from_model(self, gpu_model):
        if gpu_model in self.gpu_models_set:
            for g in self.gpulists:
                if g.gpu_model == gpu_model:
                    return g 
        return None

    def register_listener(self, listener):
        for g in self.gpulists:
            g.listener = listener


    def init_local_gpu_lists(self):
        command = "nvidia-smi -L | awk -F: '{print $1}' | awk -F' ' '{print $2}'"
        command = self.sudo_wrapper(command)
        fp = os.popen(command)
        for gpu_id in fp:
            gpu_id.strip()
            self.add_gpu('127.0.0.1', int(gpu_id))
        
    def add_gpu(self, hostname, gpuid):
        gpu = GPUDevice(hostname, gpuid)
        if self.has_gpu(gpu):
            pass
        else:
            self.gpulists.append(gpu)
            self.gpu_models_set = set([g.gpu_model for g in self.gpulists])
            self.gpu_uuid_set = set([g.gpu_uuid for g in self.gpulists])
        
    def del_gpu(self, uuid):
        pass 


if __name__ == '__main__':
    gpu = GPUDevice("127.0.0.1", 0)
    graphics_mode = gpu.__class__.graphics_mode 
    print(gpu.set_persistant_mode(1))
    print(gpu.set_frequency(1002, 3505))
    print(gpu.get_core_frequency(graphics_mode.INSTANT))
    print(gpu.get_memory_frequency(graphics_mode.INSTANT))
    print(gpu.set_autoboost(1))
    print(gpu.get_autoboost())
    print(gpu.get_utlization())
    print(gpu.is_gpu_free())
    print(gpu.get_running_process())
    print(gpu.get_gpu_model())
    print('----------')
    gm = GPUMonitor()
    gm.init_local_gpu_lists()
    print(gm.gpu_uuid_set)
    print(gm.gpu_models_set)
