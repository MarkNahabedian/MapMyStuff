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


HOBBY_SHOP_DIR = "c:/Users/Mark Nahabedian/HobbyShop/"

STATIC_RESOURCES = [
    "floor_plan.html",
    "floor_plan.svg",
    "furnashings/things.json",
    "merged_floor_plan.html",
    "placement.js",
    "floor_plan_cleanup/cleaned_up.svg",
    "floor_plan_cleanup/0-inkscape-output.svg",
    "floor_plan_cleanup/0.svg"
    ]


CONTENT_TYPE = {
    "css": "text/css",
    "html": "text/html",
    "js": "text/javascript",
    "json": "application/json",
    "svg": "image/svg+xml",
    }


DEFAULT_PAGE_TEMPLATE = '''<html>
  <head>
    <title>MIT Hobby Shop</title>
  </head>
  <body>
    <h1>MIT Hobby Shop</h1>
    <ul>
    </ul>
  </body>
</html>'''


class MyRequestHandler(http.server.BaseHTTPRequestHandler):
  def do_HEAD(self):
    logger().info("HEAD")
    self.send_response(200, "Ok")
    self.send_header('Content-type','text/html')
    self.end_headers()
    self.flush_headers()

  def do_GET(self):
    self.error_message_format = "eRRoR"
    logger().info("GET " + self.path)
    try:
      if self.path == '/favicon.ico':
        self.send_error(404, 'Resource not found')
        return
      for filename in STATIC_RESOURCES:
        if self.path[1:] == filename:
          self.send_file(os.path.join(HOBBY_SHOP_DIR, filename))
          return
      self.default()
    except Exception as e:
      logger().info("exception " + str(e))
      # Callees are responsible for their own error responses.
      pass

  def default(self):
    logger().info("Default response")
    self.send_response(200, "Ok")
    self.send_header('Content-type','text/html')
    self.end_headers()
    self.flush_headers()
    doc = xml.dom.minidom.parseString(DEFAULT_PAGE_TEMPLATE)
    ul = doc.getElementsByTagName("ul")[0]
    for filename in STATIC_RESOURCES:
      li = doc.createElement("li")
      ul.appendChild(li)
      a = doc.createElement("a")
      li.appendChild(a)
      a.setAttribute("href", filename)
      a.appendChild(doc.createTextNode(filename))
    self.wfile.write(bytes(doc.toxml("utf8")))
    self.wfile.flush()

  def send_file(self, path):
    logger().info("Send File %s" % path)
    try:
      with open(path) as f:
        contents = f.read()
        self.send_response(200, "Ok")
        self.send_header('Content-type',
                         CONTENT_TYPE[path.rsplit(".", 1)[-1]])
        self.end_headers()
        self.flush_headers()
        self.wfile.write(bytes(contents, "utf8"))
        self.wfile.flush()
    except Exception as e:
      self.send_error(404, str(e))


def run(port):
  server_address = ('', port)
  httpd = http.server.HTTPServer(server_address, MyRequestHandler)
  try: 
    logger().info("Starting Webserver.")
    httpd.serve_forever()
  finally:
    logger().info("Webserver Exited.")


if __name__ == '__main__':
  logging.basicConfig(filename='webserver.log', level=logging.INFO)
  run(8000)
  logging.shutdown()

