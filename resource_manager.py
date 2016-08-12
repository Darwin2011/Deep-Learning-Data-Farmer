#!usr/bin/env python

import os
from common import BinaryInfo

class Resource_Manager():
    binaries_direct_path = "HPC_binaries"

    def __init__(self):
        dirList = ["xml" , "xlsx", "HPC_binaries"]
        for directory in dirList:
            if not os.path.exists(directory):
                os.makedir(directory)

    def getBinariesList(self):
        results = []
        with os.popen("du -h --time HPC_binaries/*") as fileList:
            for line in fileList:
                file_info = line.strip().split("\t")
                results.append(BinaryInfo(file_info[2].split("/")[1], file_info[0], file_info[1]))

        return results


