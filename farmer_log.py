#!/usr/bin/env python

import logging

farmer_logger = logging.getLogger("farmer_log")

# Create the handler for writing file
file_hander = logging.FileHandler('/tmp/test.log')

# Create the handler for console
console_hander = logging.StreamHandler()

#define the log format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_hander.setFormatter(formatter)
console_hander.setFormatter(formatter)

farmer_logger.addHandler(file_hander)
farmer_logger.addHandler(console_hander)
farmer_logger.setLevel(logging.DEBUG)

def warning(content):
    farmer_logger.warning(content)

def debug(content):
    farmer_logger.debug(content)

def error(content):
    farmer_logger.error(content)

def info(content):
    farmer_logger.info(content)



if __name__ == "__main__":
    warning("Hello world")
    debug("Hello world")
    error("Hello world")
    info("Hello world")