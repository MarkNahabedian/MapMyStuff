# A simple web server to use as a test pllatform.

import sys
assert sys.version_info >= (3, 2)

import socket
import http.server
import html
import logging
import os.path
import xml.dom.minidom
from urllib.parse import urlparse, parse_qs


def logger():
  return logging.getLogger(__name__)


class NoCacheRequestHandler (http.server.SimpleHTTPRequestHandler):
  # Cribbed from https://gist.github.com/aallan/9416763d42534ae99f6f0228f54160c9
  def end_headers(self):
    self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
    self.send_header("Pragma", "no-cache")
    self.send_header("Expires", "0")
    super().end_headers()


def run(port):
  server_address = ('', port)
  logger().info("http://%s:%d/" % (socket.gethostname(), port))
  httpd = http.server.HTTPServer(server_address, NoCacheRequestHandler)
  try: 
    logger().info("Starting Webserver on port %d." %  port)
    httpd.serve_forever()
  finally:
    logger().info("Webserver Exited.")


if __name__ == '__main__':
  logging.basicConfig(filename='webserver.log', level=logging.INFO)
  run(8000)
  logging.shutdown()

