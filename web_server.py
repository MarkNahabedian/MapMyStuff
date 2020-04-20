# A simple web server to use as a test pllatform.

import sys
assert sys.version_info >= (3, 2)

import http.server
import html
import logging
import os.path
import xml.dom.minidom
from urllib.parse import urlparse, parse_qs


def logger():
  return logging.getLogger(__name__)


def run(port):
  server_address = ('', port)
  httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
  try: 
    logger().info("Starting Webserver.")
    httpd.serve_forever()
  finally:
    logger().info("Webserver Exited.")


if __name__ == '__main__':
  logging.basicConfig(filename='webserver.log', level=logging.INFO)
  run(8000)
  logging.shutdown()

