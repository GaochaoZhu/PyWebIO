import json
import logging

import tornado.ioloop
import tornado.web

from .httpbased import HttpContext, HttpHandler
from .tornado import set_ioloop, _setup_server, open_webbrowser_on_server_started
from .utils import cdn_validation
from ..utils import get_free_port

logger = logging.getLogger(__name__)


class TornadoHttpContext(HttpContext):
    backend_name = 'tornado'

    def __init__(self, handler: tornado.web.RequestHandler):
        self.handler = handler
        self.response = b''

    def request_obj(self):
        """返回当前请求对象"""
        return self.handler.request

    def request_method(self):
        """返回当前请求的方法，大写"""
        return self.handler.request.method.upper()

    def request_headers(self):
        """返回当前请求的header字典"""
        return self.handler.request.headers

    def request_url_parameter(self, name, default=None):
        """返回当前请求的URL参数"""
        return self.handler.get_query_argument(name, default=default)

    def request_json(self):
        """返回当前请求的json反序列化后的内容，若请求数据不为json格式，返回None"""
        try:
            return json.loads(self.handler.request.body.decode('utf8'))
        except Exception:
            return None

    def set_header(self, name, value):
        """为当前响应设置header"""
        self.handler.set_header(name, value)

    def set_status(self, status: int):
        """为当前响应设置http status"""
        self.handler.set_status(status)

    def set_content(self, content, json_type=False):
        """设置相应的内容

        :param content:
        :param bool json_type: content是否要序列化成json格式，并将 content-type 设置为application/json
        """
        # self.response.content accept str and byte
        if json_type:
            self.set_header('content-type', 'application/json')
            self.response = json.dumps(content)
        else:
            self.response = content

    def get_response(self):
        """获取当前的响应对象，用于在私图函数中返回"""
        return self.response

    def get_client_ip(self):
        """获取用户的ip"""
        return self.handler.request.remote_ip

    def get_path(self):
        """Get the path patton of the http request uri"""
        return self.handler.request.path


def webio_handler(applications, cdn=True,
                  session_expire_seconds=None,
                  session_cleanup_interval=None,
                  allowed_origins=None, check_origin=None):
    """Get the ``RequestHandler`` class for running PyWebIO applications in Tornado.
    The ``RequestHandler``  communicates with the browser by HTTP protocol.

    The arguments of ``webio_handler()`` have the same meaning as for :func:`pywebio.platform.tornado_http.start_server`

    .. versionadded:: 1.2
    """
    cdn = cdn_validation(cdn, 'error')  # if CDN is not available, raise error

    handler = HttpHandler(applications=applications, cdn=cdn,
                          session_expire_seconds=session_expire_seconds,
                          session_cleanup_interval=session_cleanup_interval,
                          allowed_origins=allowed_origins, check_origin=check_origin)

    class MainHandler(tornado.web.RequestHandler):
        def options(self):
            return self.get()

        def post(self):
            return self.get()

        def get(self):
            context = TornadoHttpContext(self)
            self.write(handler.handle_request(context))

    return MainHandler


def start_server(applications, port=8080, host='localhost',
                 debug=False, cdn=True, static_dir=None,
                 allowed_origins=None, check_origin=None,
                 auto_open_webbrowser=False,
                 session_expire_seconds=None,
                 session_cleanup_interval=None,
                 websocket_max_message_size=None,
                 websocket_ping_interval=None,
                 websocket_ping_timeout=None,
                 **tornado_app_settings):
    """Start a Tornado server to provide the PyWebIO application as a web service.

    The Tornado server communicates with the browser by HTTP protocol.

    :param int session_expire_seconds: Session expiration time, in seconds(default 60s).
       If no client message is received within ``session_expire_seconds``, the session will be considered expired.
    :param int session_cleanup_interval: Session cleanup interval, in seconds(default 120s).
       The server will periodically clean up expired sessions and release the resources occupied by the sessions.

    The rest arguments of ``start_server()`` have the same meaning as for :func:`pywebio.platform.tornado.start_server`

    .. versionadded:: 1.2
    """

    if port == 0:
        port = get_free_port()

    if not host:
        host = '0.0.0.0'

    cdn = cdn_validation(cdn, 'warn')

    kwargs = locals()

    set_ioloop(tornado.ioloop.IOLoop.current())  # to enable bokeh app

    app_options = ['debug', 'websocket_max_message_size', 'websocket_ping_interval', 'websocket_ping_timeout']
    for opt in app_options:
        if kwargs[opt] is not None:
            tornado_app_settings[opt] = kwargs[opt]

    cdn = cdn_validation(cdn, 'warn')  # if CDN is not available, warn user and disable CDN

    handler = webio_handler(applications, cdn,
                            session_expire_seconds=session_expire_seconds,
                            session_cleanup_interval=session_cleanup_interval,
                            allowed_origins=allowed_origins, check_origin=check_origin)

    _, port = _setup_server(webio_handler=handler, port=port, host=host, static_dir=static_dir, **tornado_app_settings)

    print('Listen on %s:%s' % (host or '0.0.0.0', port))
    if auto_open_webbrowser:
        tornado.ioloop.IOLoop.current().spawn_callback(open_webbrowser_on_server_started, host or 'localhost', port)

    tornado.ioloop.IOLoop.current().start()
