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
    """
    Load an image from a tar archive or STDIN

    Options:
        -i, --input string   Read from tar archive file, instead of STDIN

    Args:
        image_path: the path of the image.

    Returns:
        the load an image command string.
    """
    result = sudo_wrapper("%s load -i " % DOCKER_COMMAND + image_path)
    farmer_log.info(result)
    return result

def show_images():
    """
    List images

    Returns:
        the command to list images.
    """
    result = sudo_wrapper("%s images" % DOCKER_COMMAND)
    farmer_log.info(result)
    return result

def run_docker(container, repository, tag):
    """
    Run a command in a new container

    Options:
        -t, --tty                         Allocate a pseudo-TTY
        -i, --interactive                 Keep STDIN open even if not attached
        -d, --detach                      Run container in background and print container ID
        --name string                     Assign a name to the container
    Args:
        container: the container id
        repository: the repository for images
        tag: the tag for the tag

    Returns:
        The command to run the binaries in the docker.
    """
    result = sudo_wrapper("%s run -t -i -d --name %s %s:%s /bin/bash" % (DOCKER_COMMAND, container,  repository, tag))
    farmer_log.info(result)
    return result

def stop_docker(container):
    """
    Stop one or more running containers

    Args:
        container: the container id.

    Returns:
        The command to stop the container.
    """
    result = sudo_wrapper("%s stop %s" % (DOCKER_COMMAND, container))
    return result

def kill_docker(container):
    """
    Kill one or more running container

    Args:
        container: the container id

    Returns:
        The command to kill the container.
    """
    result = sudo_wrapper("%s kill %s" % (DOCKER_COMMAND, container))
    return result    

def execute(command):
    """
    Open a pipe to/from a command returning a file object.
    Args:
        command: the command you want to execute.

    Returns:
        the ouput of the executing command.
    """
    output = os.popen(command)
    if output != None:
        farmer_log.info(output.read())
    return output

def get_random_container():
    """
    fetch a random container_id.
        This container id is generated according to the date and a random int during 10000000, 20000000
    Returns:
        the random container id.
    """
    now = datetime.datetime.now()
    nowStamp = now.strftime("%Y%m%d%H%M%S")
    randomStamp = random.randint(10000000, 20000000)
    return "container_%s_%d" % (nowStamp, randomStamp)

def get_fake_request_id():
    now = datetime.datetime.now()
    nowStamp = now.strftime("%Y%m%d%H%M%S")
    randomStamp = random.randint(10000000, 20000000)
    return "requested_id_%s_%d" % (nowStamp, randomStamp)

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
