#!usr/bin/env python


class requests(object):

    def __init__(self, gpuid, topologies, iterations, batch_size):
        self.gpuid = gpuid
        self.topologies = topologies
        self.iterations = iterations
        self.batch_size = batch_size
        self.iterations = iterations
        self.batch_size = batch_size


class ResultObject(object):

    def __init__(self, request_id, docker_id, gpu_model,\
                 email, framework, topology, batch_size, \
                 source, iteration, score, images_pre_sec):
        self.request_id     = request_id
        self.docker_id      = docker_id
        self.gpu_model      = gpu_model
        self.email          = email
        self.framework      = framework
        self.topology       = topology
        self.batch_size     = batch_size
        self.source         = source
        self.iteration      = iteration
        self.score          = score
        self.images_pre_sec = images_pre_sec


class RequestObject(object):

    def __init__(self, request_id, docker_id, gpu_model,\
                 mail_addr, framework, topology, batch_size, \
                 iteration, request_time):
        self.request_id     = request_id
        self.docker_id      = docker_id
        self.gpu_model      = gpu_model
        self.mail_addr      = mail_addr
        self.framework      = framework
        self.topology       = topology
        self.batch_size     = batch_size
        self.iteration      = iteration
        self.request_time   = request_time

class DataMediator():

    def __init__(self, header):
        self.header = header
        self.dataList = []

    def append(self, row):
        self.dataList.append(row)

    def __len__(self):
        return len(self.dataList)

    def pop(self):
        return self.dataList.pop()

    def to_data_frame(self):
        result = {}
        for index, entry in enumerate(self.header):
            result[entry] = [] 
        for item in self.dataList:
            for index, entry in enumerate(self.header):
                result[entry].append(item[index]) 
        return result
            
    def to_result_objects(self):
        result = []
        for item in self.dataList:
            result.append(ResultObject(item[self.header.index("REQUEST_ID")],    \
                                       item[self.header.index("DOCKER_ID")],     \
                                       item[self.header.index("GPU_MODEL")],     \
                                       item[self.header.index("MAIL_ADDRESS")],  \
                                       item[self.header.index("FRAMEWORK")],     \
                                       item[self.header.index("TOPOLOGY")],      \
                                       item[self.header.index("BATCH_SIZE")],    \
                                       item[self.header.index("SOURCE")],        \
                                       item[self.header.index("ITERATION")],     \
                                       item[self.header.index("SCORE")],         \
                                       item[self.header.index("IMAGES_PRE_SEC")])) 
        return result

    def to_request_objects(self):
        result = []
        for item in self.dataList:
            result.append(RequestObject(item[self.header.index("REQUEST_ID")],  \
                                        item[self.header.index("DOCKER_ID")],   \
                                        item[self.header.index("GPU_MODEL")],   \
                                        item[self.header.index("MAIL_ADDRESS")],\
                                        item[self.header.index("FRAMEWORK")],   \
                                        item[self.header.index("TOPOLOGY")],    \
                                        item[self.header.index("BATCH_SIZE")],  \
                                        item[self.header.index("ITERATION")],   \
                                        item[self.header.index("REQUEST_TIME")]))
        
        return result
