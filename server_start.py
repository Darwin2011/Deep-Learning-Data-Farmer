#!/usr/bin/env python

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import dicttoxml
from xml.dom.minidom import parseString
from gpu_control import *
from GPU_Scheduler import * 

from tornado.options import define, options
define('port', default=8000, help='run on the given port', type=int)

scheduler = GPU_Scheduler()

class TestRequest(tornado.web.RequestHandler):
    test_request_html = 'template/test_request.html'

    def get(self):
        self.render(self.__class__.test_request_html, gpus = scheduler.gpu_monitor.gpulists)

    def post(self):
        options = {}
        options['email'] = self.get_argument('email')
        batch_size = self.get_argument('batch_size')
        options['batch_size'] = 0 if batch_size == 'auto' else batch_size 
        options['iterations'] = self.get_argument('iterations')
        options['gpu_model'] = self.get_argument('gpu_model')
        options['topology'] = self.get_argument('topology')
        options['gpu_boost'] = self.get_argument('gpu_boost')
        options['cuda'] = self.get_argument('CUDA')
        options['cudnn'] = self.get_argument('CUDNN')
        options['framework'] = self.get_argument('framework')
        dom = parseString(dicttoxml.dicttoxml(options, attr_type=False))
        print(dom.toprettyxml())

class TestStatus(tornado.web.RequestHandler):
    test_status_html = 'template/test_status.html'

    def get(self):
        self.render(self.__class__.test_status_html, gpus = scheduler.gpu_monitor.gpulists)


if __name__ == '__main__':
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers = [
        (r'/request', TestRequest), \
        (r'/status', TestStatus), \
        (r'/css/(.*)', tornado.web.StaticFileHandler, {'path': 'template/css'}), \
        (r'/js/(.*)', tornado.web.StaticFileHandler, {'path': 'template/js'})
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
