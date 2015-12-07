# -*- coding: utf-8 -*-

"""
Set up a HTTP proxy that forwards messages to a Mattermost Incoming Webhook.
"""

from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import logging
import signal
import os
import sys
from os.path import expanduser, abspath, exists, dirname, join
from ConfigParser import SafeConfigParser
import argparse
import json

import tornado.ioloop
import tornado.httpserver
import tornado.web
import tornado.netutil
import tornado.process
import tornado.httpclient
import tornado.gen

IOLoop = tornado.ioloop.IOLoop
HTTPServer = tornado.httpserver.HTTPServer
RequestHandler = tornado.web.RequestHandler
Application = tornado.web.Application
bind_sockets = tornado.netutil.bind_sockets
fork_processes = tornado.process.fork_processes
AsyncHTTPClient = tornado.httpclient.AsyncHTTPClient
HTTPRequest = tornado.httpclient.HTTPRequest
HTTPError = tornado.httpclient.HTTPError
coroutine = tornado.gen.coroutine

defaults = {
    'port': '8080',
    'default_path': '/hook',
    'hooks_path': '/hooks',
    'bind_localhost': 'false'
}

server = None


class MyHandler(RequestHandler):

    @coroutine
    def forward_to_hook(self, hook_url):
        headers = self.request.headers
        content_type = headers.get('content-type')
        try:
            if content_type is not None and 'json' in content_type:
                json_decoded = json.loads(self.request.body)
            else:
                payload = self.request.body_arguments.get('payload')
                json_decoded = json.loads(payload)
        except ValueError:
            self.clear()
            self.set_status(400, "Invalid JSON in HTTP request")
            self.finish()
            return

        http_client = AsyncHTTPClient()
        req = HTTPRequest(
            url=hook_url,
            method="POST",
            headers={'Content-Type': 'application/json'},
            body=json.dumps(json_decoded)
        )
        try:
            resp = yield http_client.fetch(req)
        except HTTPError as e:
            # HTTPError is raised for non-200 responses; the response can be found in e.response
            self.clear()
            if e.message:
                self.set_status(e.code, "Upstream error: {}".format(e.message))
            else:
                self.set_status(e.code, "Upstream error")
            if e.response:
                self.finish(e.response.body)
            else:
                self.finish()
        except Exception as e:
            # Other errors are possible, such as IOError.
            self.clear()
            self.set_status(500, str(e))
            self.finish()
        else:
            self.set_status(resp.code, resp.reason)
            for (name, value) in sorted(resp.headers.get_all()):
                self.add_header(name, value)
            self.finish(resp.body)


class DefaultPathHandler(MyHandler):
    def get(self):
        self.write("DefaultPathHandler: use POST method")

    @coroutine
    def post(self):
        yield self.forward_to_hook(self.application.mm_default_hook)


class HooksHandler(MyHandler):
    def get(self, secret_url):
        self.write("HooksHandler '{}': use POST method".format(secret_url))

    @coroutine
    def post(self, secret_url):
        yield self.forward_to_hook(self.application.mm_hooks + '/' + secret_url)


def make_application(config):
    default_path = config.get('proxy', 'default_path')
    hooks_path = config.get('proxy', 'hooks_path')
    app = Application(handlers=[
        (r"{}$".format(default_path), DefaultPathHandler),
        (r"{}/(.*)".format(hooks_path), HooksHandler)
    ])
    app.raw_config = config
    app.mm_default_hook = "{}/{}".format(config.get('mattermost', 'url'), config.get('mattermost', 'default_hook'))
    app.mm_hooks = config.get('mattermost', 'url')
    return app


def sig_handler(sig, frame):
    IOLoop.instance().add_callback(shutdown)


def shutdown():
    global server
    if server is not None:
        server.stop()
        IOLoop.instance().stop()


def main():
    global server

    parser = argparse.ArgumentParser(
        description="Start a HTTP proxy to forward incoming messages to Mattermost"
    )
    parser.add_argument('-c', '--config', default='', help="Configuration file path")
    args = parser.parse_args()

    conf_fname = args.config if args.config else os.environ.get('MM_PROXY_CONF')
    if conf_fname is None:
        conf_fname = abspath(expanduser('.pymatter/proxy.conf'))
        if not exists(conf_fname):
            conf_fname = abspath(join(dirname(dirname(__file__)), 'conf', 'proxy.conf'))
    if not exists(conf_fname):
        sys.stderr.write(b"No configuration provided\n")
        sys.exit(-1)

    logging.info("Using config file '%s'", conf_fname)

    config = SafeConfigParser(defaults)
    config.read([conf_fname])

    app = make_application(config)
    sockets = bind_sockets(config.getint('proxy', 'port'))
    server = HTTPServer(app)
    server.add_sockets(sockets)

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)
    IOLoop.current().start()

if __name__ == "__main__":
    main()
