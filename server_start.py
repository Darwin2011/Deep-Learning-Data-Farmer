#!/usr/bin/env python

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import dicttoxml
import threading
import os
from xml.dom.minidom import parseString
from gpu_control import *
from task_scheduler import *
import farmer_log
import hashlib

def md5(password):
    md5Obj = hashlib.md5()
    md5Obj.update(password)
    return md5Obj.hexdigest()

from tornado.options import define, options
define('port', default=8000, help='run on the given port', type=int)

scheduler = Task_Scheduler()

class TestIndex(tornado.web.RequestHandler):
    index_html = 'template/dashboard.html'

    def get(self):
        self.render(self.__class__.index_html)

class TestRequest(tornado.web.RequestHandler):
    test_request_html = 'template/test_request.html'
    request_id = 0
    lock = threading.Lock()
    def get(self):
        self.render(self.__class__.test_request_html, gpus = scheduler.gpu_monitor.gpulists)

    def post(self):
        self.__class__.lock.acquire()
        self.__class__.request_id += 1
        self.__class__.lock.release() 
        options = {}
        options['email']      = self.get_argument('email')
        batch_size            = self.get_argument('batch_size')
        options['batch_size'] = 0 if batch_size == 'auto' else batch_size
        options['iterations'] = self.get_argument('iterations')
        options['gpu_model']  = self.get_argument('gpu_model')
        options['topology']   = self.get_argument('topology')
        options['gpu_boost']  = self.get_argument('gpu_boost')
        options['cuda']       = self.get_argument('CUDA')
        options['cudnn']      = self.get_argument('CUDNN')
        options['framework']  = self.get_argument('framework')
        options['profiling']  = self.get_argument('profiling')

        timestamp      = datetime.datetime.now().strftime("%s")
        request_string = 'request_%s_%d' % (timestamp, self.__class__.request_id)
        options['request_id'] = request_string 
        dom = parseString(dicttoxml.dicttoxml(options, attr_type=False))

        if not os.path.exists("./xml"):
            os.mkdir("./xml")
        xml_string = dom.toprettyxml()
        filename = "%s_%d.xml" % (timestamp, self.__class__.request_id)
        filepath = os.path.join('xml', filename)
        with open(filepath, 'w') as f:
            f.write(xml_string)
        scheduler.assign_request(filepath)
        self.redirect('/result?request=%s' % request_string)

class TestStatus(tornado.web.RequestHandler):
    test_status_html = 'template/test_status.html'

    def get(self):
        self.render(self.__class__.test_status_html, gpus = scheduler.gpu_monitor.gpulists)

class TestHistory(tornado.web.RequestHandler):
    PAGE_SIZE = 20 
    test_history_html = 'template/test_history.html'

    def get(self):
        page_num = int(self.get_argument("page"))
        start_index = self.__class__.PAGE_SIZE * (page_num - 1)
        count = self.__class__.PAGE_SIZE + 1
        request_reports = scheduler.sql_wrapper.get_request_reports(start_index, count)
        is_last_page = False
        if len(request_reports) < count:
            is_last_page = True
        else:
            is_last_page = False
            request_reports.pop()
        self.render(self.__class__.test_history_html,\
                     request_reports = request_reports, page = page_num,\
                     is_last_page = is_last_page)

class TestResult(tornado.web.RequestHandler):
    test_result_html = 'template/test_result.html'

    def get(self):
        request_id = self.get_argument("request")
        self.render(self.__class__.test_result_html, results = scheduler.sql_wrapper.get_result_by_request_id(request_id), buffer_log = scheduler.requests[request_id]['raw_buffer'], request_id = request_id, state = str(scheduler.requests[request_id]['state']), gpu = scheduler.requests[request_id]['gpu_device'], request = scheduler.requests[request_id])


class TestDetail(tornado.web.RequestHandler):
    test_detail_html = 'template/test_detail.html'

    def get(self):
        # fake to get the request id
        request_id = self.get_argument("request")
        self.render(self.__class__.test_detail_html, results = scheduler.sql_wrapper.get_result_by_request_id(request_id))

class TestSignIn(tornado.web.RequestHandler):
    sign_in_html = "template/sign_in.html"

    def get(self):
        self.render(self.sign_in_html)

class TestRawLogResponse(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        request_id = self.get_argument("request")
        self.write(str(scheduler.requests[request_id]['raw_buffer']))
        self.finish()

class RequestState(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        request_id = self.get_argument("request")
        self.write(str(scheduler.requests[request_id]["state"]))
        self.finish()


class GPUState(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        request_id = self.get_argument("request")
        self.write(str(scheduler.response_gpu_state_request(request_id)))
        self.finish()

if __name__ == '__main__':
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers = [
        (r'/index',        TestIndex),            \
        (r'/request',      TestRequest),          \
        (r'/status',       TestStatus),           \
        (r"/result",       TestResult),           \
        (r"/rawlog",       TestRawLogResponse),   \
        (r"/rawlogbuffer", TestRawLogResponse),   \
        (r"/requeststate", RequestState),         \
        (r"/gpustate",     GPUState),             \
        (r"/history",      TestHistory),          \
        (r"/detail",       TestDetail),           \
        (r"/login",        TestSignIn),           \
        (r'/css/(.*)',     tornado.web.StaticFileHandler, {'path': 'template/css'}), \
        (r'/js/(.*)',      tornado.web.StaticFileHandler, {'path': 'template/js'}), \
        (r'/log/(.*)',     tornado.web.StaticFileHandler, {'path': './log'})
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
