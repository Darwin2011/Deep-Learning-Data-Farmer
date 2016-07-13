#!/usr/bin/env python
"""
    This file defines how to generate the docker command.
"""
import farmer_log

DOCKER_COMMAND = "nvidia-docker"

def sudo_wrapper(command):
    return "sudo " + command

def load_image(image_path):
    result = sudo_wrapper("%s load -i " % DOCKER_COMMAND + image_path)
    farmer_log.info(result)
    return result

def show_images():
    result = sudo_wrapper("%s images" % DOCKER_COMMAND)
    farmer_log.info(result)
    return result

def run_workload(repository, tag):
    result = sudo_wrapper("%s run -t -i %s:%s /bin/bash" % (DOCKER_COMMAND, repository, tag))
    farmer_log.info(result)
    return result

def modify_docker():
    DOCKER_COMMAND = "docker"

def modify_nvidia_docker():
    DOCKER_COMMAND = "nvidia-docker"


if __name__ == "__main__":
    print sudo_wrapper("and command")
    print load_image("image.tar.gz")
    print show_images()
    print run_workload("rep", "tag")

    modify_docker()
    print sudo_wrapper("and command")
    print load_image("image.tar.gz")
    print show_images()
    print run_workload("rep", "tag")