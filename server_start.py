#!/usr/bin/env python

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import dicttoxml
import threading
import os
import json
from xml.dom.minidom import parseString
from gpu_control import *
from task_scheduler import *
import farmer_log
import hashlib
import base64, uuid
from resource_manager import Resource_Manager
from task_manager import Task_Manager
from mail_wrapper import *
import string
import threading

def get_cookie_secret():
    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)

def md5(password):
    md5Obj = hashlib.md5()
    md5Obj.update(password)
    return md5Obj.hexdigest()

def version():
    with os.popen("git log -1") as verObj:
        for line in verObj:
            version = line[7:-1]
            return version

def generate_security_code(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

from tornado.options import define, options
define('port', default=8003, help='run on the given port', type=int)

scheduler = Task_Scheduler()
resMgr    = Resource_Manager()
taskMgr   = Task_Manager()
taskMgr.start()

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("mail")

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
            self.render(self.index_html, version = version())

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
        start_index = self.PAGE_SIZE * (page_num - 1)
        count = self.PAGE_SIZE + 1
        request_reports_mediator = scheduler.sql_wrapper.get_request_reports(start_index, count)
        is_last_page = False
        if len(request_reports_mediator) < count:
            is_last_page = True
        else:
            is_last_page = False
            request_reports_mediator.pop()
        self.render(self.test_history_html,\
                    request_reports = request_reports_mediator.to_request_objects(),\
                    page            = page_num,\
                    is_last_page    = is_last_page)

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
        mail     = self.get_argument('mail')
        password = self.get_argument('password')
        farmer_log.info("Sign up info: mail[%s] password[%s]" % (mail, password))
        user_id, mail_addr  = scheduler.exists_account(mail, password)
        farmer_log.info("user_id[%d] mail[%s]" % (user_id, mail_addr))
        if user_id != -1:
            self.set_secure_cookie("mail", mail_addr)
            self.set_secure_cookie("user_id", "%d" % user_id)
            self.redirect(self.get_argument("next",r"/dashboard"))
        else:
            self.write("The user name or password doesn't correct.")


class TestTasks(BaseHandler):
    tasks_html = "template/test_tasks.html"
    
    @tornado.web.authenticated
    def get(self):
        self.render(self.tasks_html, tasks = taskMgr.getTasksInfo())
        
class TasksService(BaseHandler):

    @tornado.web.authenticated
    @tornado.web.asynchronous 
    def get(self):
        tasklist = taskMgr.getTasksInfo()
        html_table_content = "".join(["<tr><td>%s</td><td>%s</td></tr>" % (task.task, task.state) for task in tasklist])
        html_table = "<table>" + "<tr><td><h4>task</h4></td><td><h4>state</h4></td></tr>" + html_table_content + "</table>"
        self.write(html_table)
        self.finish()

class TestSignUp(BaseHandler):
    sign_up_html = 'template/sign_up.html'
    def get(self):
        if self.get_current_user():
            self.redirect(r"/dashboard")
        else:
            self.render(self.sign_up_html)
    
    def post(self):
        user     = self.get_argument('user')
        email    = user + "@intel.com"
        password = self.get_argument('password')
        farmer_log.info("Sign up info: email[%s] user[%s] password[%s]" % (email, user, password))
        have_created = scheduler.create_account(user, password, email)
        if have_created:
            self.redirect('/sign_in')
        else:
            self.redirect('#')

class TestSignOut(BaseHandler):
    def get(self):
        self.clear_cookie("mail")
        self.clear_cookie("user_id")
        self.redirect("/sign_in")

class MailSecurityCodeSender(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        securityCode = generate_security_code()
        farmer_log.info("securityCode [%s]" % securityCode)
        self.set_secure_cookie("securityCode", md5(securityCode))
        receiver = self.get_argument("user", "")
        receiver += "@intel.com"
        farmer_log.info("receiver [%s]" % receiver)
        result = send_security_code("gpufarmer@intel.com", receiver, securityCode)
        self.write(str(result))
        self.finish()


class MailValidated(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        result = False
        securityCodeInMail    = self.get_argument('securityCode', "")
        securityCodeInCookies = self.get_secure_cookie('securityCode')
        if md5(securityCodeInMail) == securityCodeInCookies:
            result = True
            self.clear_cookie('securityCode')
        self.write(str(result))
        self.finish()

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

class ProfileDownloader(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self):
        request_id = self.get_argument("request")
        download_file = "%s.zip" % request_id
        self.set_header("Content-Type", "application/octet-stream")
        self.set_header("Content-Disposition", "attachment; filename=" + download_file)
        with open("./log/" + download_file, 'rb') as fileObj:
            farmer_log.info("open profile request(%s) file." % request_id)
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
        mail = self.get_argument("mail")
        isExist = scheduler.sql_wrapper.exists_mail(mail)
        farmer_log.info("The mail[%s] is exist[%r]" % (mail, isExist))
        self.write(str(isExist)) 
        self.finish()

class GPUState(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        request_id = self.get_argument("request")
        self.write(str(scheduler.response_gpu_state_request(request_id)))
        self.finish()

counter = 0
class Test(BaseHandler):
    test_html = "template/test.html"

    def get(self):
        return self.render(self.test_html)

    def post(self):
        global counter
        counter += 1
        farmer_log.info("test post")
        taskMgr.test(counter)
        taskMgr.show()
        return self.render(self.test_html)

if __name__ == '__main__':
    tornado.options.parse_command_line()
    
    settings = {
        "cookie_secret" : get_cookie_secret(),
        "xsrf_cookies"  : True,
        "login_url"     : r"/sign_in"
    }
    app = tornado.web.Application(handlers = [
        (r'/',                TestIndex),               \
        (r'/sign_in',         TestSignIn),              \
        (r'/sign_up',         TestSignUp),              \
        (r'/test',            Test),                    \
        (r'/tasksInfo',       TasksService),            \
        (r'/tasks',           TestTasks),               \
        (r'/dashboard',       TestDashboard),           \
        (r'/request',         TestRequest),             \
        (r'/status',          TestStatus),              \
        (r"/result",          TestResult),              \
        (r"/rawlog",          TestRawLogResponse),      \
        (r"/rawlogbuffer",    TestRawLogResponse),      \
        (r"/accountRes",      AccountResponse),         \
        (r"/signout",         TestSignOut),             \
        (r"/requeststate",    RequestState),            \
        (r"/gpustate",        GPUState),                \
        (r"/history",         TestHistory),             \
        (r"/detail",          TestDetail),              \
        (r"/binaries",        TestHPCBinaries),         \
        (r"/hpc_download",    HPCBinariesDownloader),   \
        (r"/profile_download", ProfileDownloader),      \
        (r'/download',        ResultReportDownloader),  \
        (r'/mail_validated',  MailValidated),           \
        (r'/sec_code_sender', MailSecurityCodeSender),  \
        (r'/css/(.*)',        tornado.web.StaticFileHandler, {'path': 'template/css'}), \
        (r'/js/(.*)',         tornado.web.StaticFileHandler, {'path': 'template/js'}), \
        (r'/log/(.*)',        tornado.web.StaticFileHandler, {'path': './log'})
    ], **settings)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start() 
