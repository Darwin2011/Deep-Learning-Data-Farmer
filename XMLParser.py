#!usr/bin/env python

import xml.etree.ElementTree as ET

class XMLParser:
    _filePath = ""
    _gpuMode = ""
    _cudeVersion = ""
    _cudnnVersion = ""
    _topologyModelType = ""
    _framework = ""
    _batchSize = ""
    _dataSet = ""

    def __init__(self, filePath = None):
        self._filePath = filePath

    def parse(self):
        tree = ET.parse(self._filePath)
        root = tree.getroot()
        self._gpuMode = self.getAttr(root, "GPUMode")
        self._cudeVersion = self.getAttr(root, "CudeVersion")
        self._cudnnVersion = self.getAttr(root, "CudnnVersion")
        self._topologyModelType = self.getAttr(root, "TopologyMode")
        self._framework = self.getAttr(root, "Framework")
        self._batchSize = self.getAttr(root, "BatchSize")
        self._dataSet = self.getAttr(root, "DataSet")

    def getAttr(self, tree, name):
        path = 'DockerInfo[@name="%s"]' % name
        elem = tree.findall(path)
        return elem[0].attrib["value"]

    def getGPUMode(self):
        return self._gpuMode

    def getCudeVersion(self):
        return self._cudeVersion

    def getCudnnVersion(self):
        return self._cudnnVersion

    def getTopologyModeType(self):
        return self._topologyModelType

    def getFramework(self):
        return self._framework

    def getBatchSize(self):
        return self._batchSize

    def getDataSet(self):
        return self._dataSet

if __name__ == "__main__":
    parser = XMLParser("DockerConfig.xml")
    parser.parse()
    print parser.getGPUMode() + "\n" \
    + parser.getCudeVersion() + '\n' \
    + parser.getCudnnVersion() + '\n' \
    + parser.getTopologyModeType() + '\n' \
    + parser.getFramework() + '\n' \
    + parser.getBatchSize() + '\n' \
    + parser.getDataSet() + '\n'
