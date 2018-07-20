from collections import defaultdict
import os.path
import re

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler


def pep503_normalize_name(name):
    return re.sub(r"[-_.]+", "-", name).lower()

def remove_extension(name):
    if name.endswith(('gz', 'bz2')):
        name, _ = name.rsplit('.', 1)
    name, _ = name.rsplit('.', 1)
    return name


def guess_name_version_from_filename(filename):
    # These don't have a well-defined format like wheels do, so they are
    # sort of "best effort", with lots of tests to back them up.
    # The most important thing is to correctly parse the name.
    name = remove_extension(filename)
    version = None

    if '-' in name:
        if name.count('-') == 1:
            name, version = name.split('-')
        else:
            parts = name.split('-')
            for i in range(len(parts) - 1, 0, -1):
                part = parts[i]
                if '.' in part and re.search('[0-9]', part):
                    name, version = '-'.join(parts[0:i]), '-'.join(parts[i:])
    return pep503_normalize_name(name), version


def main(folder, base_url, *args):
    html5 = """<!DOCTYPE html><html><body>{}</body></html>"""

    class PyPiRequestHandler(BaseHTTPRequestHandler):

        def _read_folder(self):
            releases = defaultdict(list)
            def visit(base, dirname, names):
                for name in names:
                    try:
                        project_name, project_version = guess_name_version_from_filename(name)
                    except ValueError as exc:
                        continue
                    releases[project_name].append(name)
            os.path.walk(folder, visit, folder)
            return releases

        def start_response(self, code=200, message="OK"):
            self.send_response(code, message)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        def do_GET(self):
            releases = self._read_folder()
            if self.path == "/":
                self.start_response()
                self.wfile.write(html5.format("".join('<a href="/{0}/">{0}</a><br>'.format(release)
                                            for release in releases.iterkeys())))
                return
            else:
                project = pep503_normalize_name(self.path.strip("/"))
                if project in releases:
                    self.start_response()
                    self.wfile.write(html5.format("".join('<a href="{0}/{1}">{1}</a><br>'.format(base_url, release)
                                                  for release in releases[project])))
                    return
            self.start_response(404, "Not found")

    server_address = ('', 8000)
    httpd = HTTPServer(server_address, PyPiRequestHandler)
    httpd.serve_forever()
    return 0

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        sys.exit(main(*sys.argv[1:]))
    else:
        sys.exit(1)

