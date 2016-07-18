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

    def __init__(self, request_id, docker_id, gpu_module,\
                 mail_addr, framework, topology, batch_size,\
                 iteration, score, images_pre_sec):
        self.request_id     = request_id
        self.docker_id      = docker_id
        self.gpu_module     = gpu_module
        self.mail_addr      = mail_addr
        self.framework      = framework
        self.topology       = topology
        self.batch_size     = batch_size
        self.iteration      = iteration
        self.score          = score
        self.images_pre_sec = images_pre_sec