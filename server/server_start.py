import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web


from tornado.options import define, options
define("port", default=8000, help="run on the given port", type=int)


class TestRequest(tornado.web.RequestHandler):
    test_request_html = "template/test_request.html"

    def get(self):
        self.render(self.__class__.test_request_html)

    def post(self):
        batch_size = self.get_argument('batch_size')
        iterations = self.get_argument('iterations')
        topology = self.get_argument('topology')
        cuda = self.get_argument('CUDA')
        cudnn = self.get_argument('CUDNN')
        framework = self.get_argument('framework')
        self.write("received!")



if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers = [(r"/request", TestRequest), \
        (r'/css/(.*)', tornado.web.StaticFileHandler, {'path': 'template/css'}), \
        (r'/js/(.*)', tornado.web.StaticFileHandler, {'path': 'template/js'})
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
