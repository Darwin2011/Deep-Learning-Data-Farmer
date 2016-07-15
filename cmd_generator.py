#!/usr/bin/env python
"""
    This file defines how to generate the docker command.
"""
# TODO: ADD DOCKER helper documents
import os
import farmer_log
import datetime
import random

DOCKER_COMMAND = "nvidia-docker"
#DOCKER_COMMAND = "docker"

def sudo_wrapper(command):
    return "sudo " + command
    #return command

def load_image(image_path):
    result = sudo_wrapper("%s load -i " % DOCKER_COMMAND + image_path)
    farmer_log.info(result)
    return result

def show_images():
    result = sudo_wrapper("%s images" % DOCKER_COMMAND)
    farmer_log.info(result)
    return result

def run_docker(container, repository, tag):
    result = sudo_wrapper("%s run -t -i -d --name %s %s:%s /bin/bash" % (DOCKER_COMMAND, container,  repository, tag))
    farmer_log.info(result)
    return result

def remove_docker(container):
    result = sudo_wrapper("%s rm %s" % (DOCKER_COMMAND, container))

def kill_docker(container):
    result = sudo_wrapper("%s kill %s" % (DOCKER_COMMAND, container))

def execute(command):
    #TODO
    output = os.popen(command)
    if output != None:
        farmer_log.info(output.read())
    return output

def get_random_container():
    now = datetime.datetime.now()
    nowStamp = now.strftime("%Y%m%d%H%M%S")
    randomStamp = random.randint(10000000, 20000000)
    return "container_%s_%d" % (nowStamp, randomStamp)

def modify_docker():
    DOCKER_COMMAND = "docker"

def modify_nvidia_docker():
    DOCKER_COMMAND = "nvidia-docker"


if __name__ == "__main__":
    print sudo_wrapper("and command")
    print load_image("image.tar.gz")
    print show_images()

    modify_docker()
    print sudo_wrapper("and command")
