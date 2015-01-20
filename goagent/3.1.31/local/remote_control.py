#!/usr/bin/env python
# coding:utf-8




import BaseHTTPServer
import urlparse
import json
import os
import re

import logging
from common import common


class RemoveContralServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):


    def address_string(self):
        return '%s:%s' % self.client_address[:2]

    def do_CONNECT(self):
        self.wfile.write(b'HTTP/1.1 403\r\nConnection: close\r\n\r\n')

    def do_GET(self):
        path = urlparse.urlparse(self.path).path
        if path == "/log":
            return self.req_log_handler()
        elif path == "/status":
            return self.req_status_handler()
        else:
            logging.warn('Control Req %s "%s %s ', self.address_string(), self.command, self.path)

        # check for '..', which will leak file
        if re.search(r'(\.{2})', self.path) is not None:
            self.wfile.write(b'HTTP/1.1 404\r\n\r\n')
            logging.warn('%s %s %s haking', self.address_string(), self.command, self.path )
            return


        filename = os.path.normpath('./' + path)
        if self.path.startswith(('http://', 'https://')):
            data = b'HTTP/1.1 200\r\nCache-Control: max-age=86400\r\nExpires:Oct, 01 Aug 2100 00:00:00 GMT\r\nConnection: close\r\n'

            data += b'\r\n'
            self.wfile.write(data)
            logging.info('%s "%s %s HTTP/1.1" 200 -', self.address_string(), self.command, self.path)
        elif os.path.isfile(filename):
            if filename.endswith('.pac'):
                mimetype = 'text/plain'
            else:
                mimetype = 'application/octet-stream'
            #self.send_file(filename, mimetype)
        else:
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
            logging.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def send_file(self, filename, mimetype):
        # logging.info('%s "%s %s HTTP/1.1" 200 -', self.address_string(), self.command, self.path)
        data = ''
        with open(filename, 'rb') as fp:
            data = fp.read()
        if data:
            self.wfile.write(('HTTP/1.1 200\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
            self.wfile.write(data)

    def req_log_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        cmd = "get_last"
        if reqs["cmd"]:
            cmd = reqs["cmd"][0]
        if cmd == "set_buffer_size" :
            if not reqs["buffer_size"]:
                data = '{"res":"fail", "reason":"size not set"}'
                mimetype = 'text/plain'
                self.wfile.write(('HTTP/1.1 200\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
                self.wfile.write(data)
                return

            buffer_size = reqs["buffer_size"][0]
            logging.set_buffer_size(buffer_size)
        elif cmd == "get_last":
            max_line = int(reqs["max_line"][0])
            data = logging.get_last_lines(max_line)
        elif cmd == "get_new":
            last_no = int(reqs["last_no"][0])
            data = logging.get_new_lines(last_no)
        else:
            logging.error('PAC %s "%s %s ', self.address_string(), self.command, self.path)

        mimetype = 'text/plain'
        self.wfile.write(('HTTP/1.1 200\r\nAccess-Control-Allow-Origin: *\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
        self.wfile.write(data)

    def req_status_handler(self):
        import platform,sys
        win32_ver = platform.win32_ver()
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        gws_ip_num = len(common.google_ip.gws_ip_list)
        res_arr = {"gws_ip_num": gws_ip_num,
                   "sys_platform":sys.platform,
                   "os_system":platform.system(),
                   "os_version":platform.version(),
                   "os_release":platform.release(),
                   "goagent_version": common.__version__,
                   "python_version": common.python_version,
                   "proxy_listen":common.LISTEN_IP + ":" + str(common.LISTEN_PORT),
                   "gae_appid":common.GAE_APPIDS,
                   "pac_url":common.pac_url}
        data = json.dumps(res_arr)

        mimetype = 'text/plain'
        self.wfile.write(('HTTP/1.1 200\r\nAccess-Control-Allow-Origin: *\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
        self.wfile.write(data)

