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
import base64, uuid
from resource_manager import Resource_Manager
def get_cookie_secret():
    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)

def md5(password):
    md5Obj = hashlib.md5()
    md5Obj.update(password)
    return md5Obj.hexdigest()

from tornado.options import define, options
define('port', default=8001, help='run on the given port', type=int)

scheduler = Task_Scheduler()
resMgr    = Resource_Manager()

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")

class TestDashboard(BaseHandler):
    index_html = 'template/dashboard.html'

    @tornado.web.authenticated
    def get(self):
        self.render(self.__class__.index_html)

class TestIndex(BaseHandler):
    index_html = 'template/index.html'

    def get(self):
        if self.get_current_user():
            self.redirect(r"/dashboard")
        else:
            self.render(self.index_html)

class TestRequest(BaseHandler):
    test_request_html = 'template/test_request.html'
    request_id = 0
    lock = threading.Lock()

    @tornado.web.authenticated
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

class TestStatus(BaseHandler):
    test_status_html = 'template/test_status.html'

    def get(self):
        self.render(self.__class__.test_status_html, gpus = scheduler.gpu_monitor.gpulists)

class TestHistory(BaseHandler):
    PAGE_SIZE = 20 
    test_history_html = 'template/test_history.html'

    @tornado.web.authenticated
    def get(self):
        page_num = int(self.get_argument("page"))
        start_index = self.__class__.PAGE_SIZE * (page_num - 1)
        count = self.__class__.PAGE_SIZE + 1
        request_reports_mediator = scheduler.sql_wrapper.get_request_reports(start_index, count)
        is_last_page = False
        if len(request_reports_mediator) < count:
            is_last_page = True
        else:
            is_last_page = False
            request_reports_mediator.pop()
        self.render(self.__class__.test_history_html,\
                    request_reports = request_reports_mediator.to_request_objects(),\
                    page = page_num,\
                    is_last_page = is_last_page)

class TestResult(BaseHandler):
    test_result_html = 'template/test_result.html'

    @tornado.web.authenticated
    def get(self):
        request_id = self.get_argument("request")
        results = scheduler.sql_wrapper.get_result_by_request_id(request_id).to_result_objects()
        self.render(self.__class__.test_result_html, \
            results     = results, \
            buffer_log  = scheduler.requests[request_id]['raw_buffer'],\
            request_id  = request_id,\
            state       = str(scheduler.requests[request_id]['state']),\
            gpu         = scheduler.requests[request_id]['gpu_device'], \
            request     = scheduler.requests[request_id])


class TestDetail(BaseHandler):
    test_detail_html = 'template/test_detail.html'
    
    @tornado.web.authenticated
    def get(self):
        # fake to get the request id
        request_id = self.get_argument("request")
        results    = scheduler.sql_wrapper.get_result_by_request_id(request_id).to_result_objects()
        self.render(self.__class__.test_detail_html, results = results)

class TestHPCBinaries(BaseHandler):
    test_binaries_html = 'template/test_binaries.html'

    @tornado.web.authenticated
    def get(self):
        # fake to get the request id
        fileList   = resMgr.getBinariesList()
        self.render(self.test_binaries_html, fileList = fileList)

class TestSignIn(BaseHandler):
    sign_in_html = "template/sign_in.html"

    def get(self):
        if self.get_current_user():
            self.redirect(r"/dashboard")
        else:
            self.render(self.sign_in_html)

    def post(self):
        user     = self.get_argument('user')
        password = self.get_argument('password')
        farmer_log.info("Sign up info: user[%s] password[%s]" % (user, password))
        user_id, username  = scheduler.exists_account(user, password)
        farmer_log.info("user_id[%d] username[%s]" % (user_id, username))
        if user_id != -1:
            self.set_secure_cookie("username", username)
            self.set_secure_cookie("user_id", "%d" % user_id)
            self.redirect(self.get_argument("next",r"/dashboard"))
        else:
            self.write("The user name or password doesn't correct.")


class TestSignUp(BaseHandler):
    sign_up_html = 'template/sign_up.html'

    def get(self):
        if self.get_current_user():
            self.redirect(r"/dashboard")
        else:
            self.render(self.sign_up_html)
    
    def post(self):
        email    = self.get_argument('email')
        user     = self.get_argument('user')
        password = self.get_argument('password')
        farmer_log.info("Sign up info: email[%s] user[%s] password[%s]" % (email, user, password))
        have_created = scheduler.create_account(user, password, email)
        if have_created:
            self.redirect('/sign_in')
        else:
            self.redirect('#')

class TestSignOut(BaseHandler):
    def get(self):
        self.clear_cookie("username")
        self.redirect("/sign_in")

class ResultReportDownloader(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self):
        request_id = self.get_argument("request")
        download_file = scheduler.make_download_file(request_id)
        self.set_header("Content-Type", "application/octet-stream")
        self.set_header("Content-Disposition", "attachment; filename=" + download_file)
        with open("./xlsx/" + download_file, 'rb') as fileObj:
            farmer_log.info("open the request(%s) xlsx." % request_id)
            while True:
                data = fileObj.read(4096)
                if not data:
                    break
                self.write(data)
        self.finish()

class HPCBinariesDownloader(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self):
        binary_name = self.get_argument("binary")
        self.set_header("Content-Type", "application/octet-stream")
        self.set_header("Content-Disposition", "attachment; filename=" + binary_name)
        with open("./HPC_binaries/" + binary_name, 'rb') as fileObj:
            while True:
                data = fileObj.read(4096)
                if not data:
                    break
                self.write(data)
        self.finish()

class TestRawLogResponse(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        request_id = self.get_argument("request")
        self.write(str(scheduler.requests[request_id]['raw_buffer']))
        self.finish()

class RequestState(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        request_id = self.get_argument("request")
        self.write(str(scheduler.requests[request_id]["state"]))
        self.finish()

class AccountResponse(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        user = self.get_argument("user")
        isExist = scheduler.sql_wrapper.exists_user(user)
        farmer_log.info("The user[%s] is exist[%r]" % (user, isExist))
        self.write(str(isExist)) 
        self.finish()

class GPUState(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        request_id = self.get_argument("request")
        self.write(str(scheduler.response_gpu_state_request(request_id)))
        self.finish()

if __name__ == '__main__':
    tornado.options.parse_command_line()
    
    settings = {
        "cookie_secret" : get_cookie_secret(),
        "xsrf_cookies"  : True,
        "login_url"     : r"/sign_in"
    }
    app = tornado.web.Application(handlers = [
        (r'/',             TestIndex),              \
        (r'/sign_in',      TestSignIn),             \
        (r'/sign_up',      TestSignUp),             \

        (r'/dashboard',    TestDashboard),          \
        (r'/request',      TestRequest),            \
        (r'/status',       TestStatus),             \
        (r"/result",       TestResult),             \
        (r"/rawlog",       TestRawLogResponse),     \
        (r"/rawlogbuffer", TestRawLogResponse),     \
        (r"/accountRes",   AccountResponse),        \
        (r"/signout",      TestSignOut),            \
        (r"/requeststate", RequestState),           \
        (r"/gpustate",     GPUState),               \
        (r"/history",      TestHistory),            \
        (r"/detail",       TestDetail),             \
        (r"/binaries",     TestHPCBinaries),        \
        (r"/hpc_download", HPCBinariesDownloader),  \
        (r'/download',     ResultReportDownloader), \
        (r'/css/(.*)',     tornado.web.StaticFileHandler, {'path': 'template/css'}), \
        (r'/js/(.*)',      tornado.web.StaticFileHandler, {'path': 'template/js'}), \
        (r'/log/(.*)',     tornado.web.StaticFileHandler, {'path': './log'})
    ], **settings)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start() 
