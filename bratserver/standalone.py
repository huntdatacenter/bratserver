#!/usr/bin/env python3

# Minimal standalone brat server based on SimpleHTTPRequestHandler.

# Run as apache, e.g. as
#
#     APACHE_USER=`./apache-user.sh`
#     sudo -u $APACHE_USER python3 standalone.py

import os
import socket
import sys
import shutil
from cgi import FieldStorage
from http.server import HTTPServer, SimpleHTTPRequestHandler
from posixpath import normpath
from socketserver import ForkingMixIn
from urllib.parse import unquote

# Add brat installation directory in the paths
try:
    BRAT_INSTALLATION_PATH = os.environ['BRAT_INSTALLATION_PATH']
except Exception:
    # Path needs to be set for directory that contains ajax.cgi
    raise Exception('Environment variable was not set: BRAT_INSTALLATION_PATH')

sys.path.append(BRAT_INSTALLATION_PATH)

# Import config first to override attempts to load config from brat directory
from config import truthy  # noqa: E402
from config import WORK_DIR  # noqa: E402
from config import DATA_DIR  # noqa: E402

try:
    if not os.path.exists(WORK_DIR):
        os.makedirs(WORK_DIR, mode=0o744, exist_ok=True)
except Exception:
    raise Exception(f'Failed to create working directory: {WORK_DIR}')

try:
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, mode=0o744, exist_ok=True)
        try:
            src_path = os.path.join(BRAT_INSTALLATION_PATH, 'example-data', 'corpora')
            dst_path = os.path.join(DATA_DIR, 'examples')
            shutil.copytree(src_path, dst_path)
        except Exception:
            raise Exception(f'Failed to copy examples: {src_path} -> {dst_path}')
        try:
            src_path = os.path.join(BRAT_INSTALLATION_PATH, 'example-data', 'tutorials')
            dst_path = os.path.join(DATA_DIR, 'tutorials')
            shutil.copytree(src_path, dst_path)
        except Exception:
            raise Exception(f'Failed to copy tutorial: {src_path} -> {dst_path}')
except Exception:
    raise Exception(f'Failed to create annotation-data directory: {DATA_DIR}')

# Override project directory
import projectconfig

def __read_first_in_directory_tree(directory, filename):
    """
    Override search location of project configs

    Reason is DATA_DIR should not be expected to be part of BASE_DIR
    """
    # config will not be available command-line invocations;
    # in these cases search whole tree
    try:
        from config import BASE_DIR
    except BaseException:
        BASE_DIR = "/"
    try:
        from config import DATA_DIR
    except BaseException:
        DATA_DIR = BASE_DIR
    from os.path import split, join

    source, result = None, None

    # check from the given directory and parents, but not above DATA_DIR
    if directory is not None:
        # TODO: this check may fail; consider "foo//bar/data"
        while BASE_DIR in directory or DATA_DIR in directory:
            source = join(directory, filename)
            result = projectconfig.__read_or_default(source, None)
            if result is not None:
                break
            directory = split(directory)[0]

    return (result, source)

projectconfig.__read_first_in_directory_tree = __read_first_in_directory_tree


from common import ProtocolError


# -- Protect sensitive data
class DownloadNotAllowedError(ProtocolError):
    def json(self, json_dic):
        json_dic['exception'] = 'accessDenied'

    def __str__(self):
        return 'Error: Download is not allowed!'


if not truthy(os.getenv('BRAT_DOWNLOAD_ENABLED', False)):
    # -- Protect sensitive data
    import download

    def download_collection_override(collection, include_conf=False):
        raise DownloadNotAllowedError()

    def download_file_override(document, collection, extension):
        raise DownloadNotAllowedError()

    download.download_collection = download_collection_override
    download.download_file = download_file_override

# brat imports
# sys.path.append(os.path.join(os.path.dirname(__file__), 'server/src'))
from brat.server.src.server import serve  # noqa


_LOG_REQUESTS = truthy(os.getenv('BRAT_LOG_REQUESTS', 'true'))
_DEFAULT_SERVER_ADDR = os.getenv('BRAT_HOST', '')  # default if unset willbe 0.0.0.0
_DEFAULT_SERVER_PORT = os.getenv('BRAT_PORT', 8001)
_CONF_PRESET = os.getenv('BRAT_PRESET_CONF', 'example-conf')

# Populate DATA_DIR if empty
for item in [
    'annotation.conf',
    'kb_shortcuts.conf',
    'tools.conf',
    'visual.conf',
]:
    try:
        if not os.path.exists(item):
            src_path = os.path.join(BRAT_INSTALLATION_PATH, 'configurations', _CONF_PRESET, item)
            target_path = os.path.join(DATA_DIR, item)
            shutil.copy(src_path, target_path)
            os.chmod(target_path, 0o777)
    except Exception:
        raise Exception(f'Failed to copy config file: {src_path} -> {target_path}')


# os.makedirs(name, mode=0o777, exist_ok=True)

_PERMISSIONS = """
Allow: /ajax.cgi
Disallow: *.py
Disallow: *.cgi
Disallow: /.htaccess
Disallow: *.py~  # no emacs backups
Disallow: *.cgi~
Disallow: /.htaccess~
Allow: /
"""


class PermissionParseError(Exception):
    def __init__(self, linenum, line, message=None):
        self.linenum = linenum
        self.line = line
        self.message = ' (%s)' % message if message is not None else ''

    def __str__(self):
        return 'line %d%s: %s' % (self.linenum, self.message, self.line)


class PathPattern(object):
    def __init__(self, path):
        self.path = path
        self.plen = len(path)

    def match(self, s):
        # Require prefix match and separator/end.
        return s[:self.plen] == self.path and (self.path[-1] == '/' or
                                               s[self.plen:] == '' or
                                               s[self.plen] == '/')


class ExtensionPattern(object):
    def __init__(self, ext):
        self.ext = ext

    def match(self, s):
        return os.path.splitext(s)[1] == self.ext


class PathPermissions(object):
    """Implements path permission checking with a robots.txt-like syntax."""

    def __init__(self, default_allow=False):
        self._entries = []
        self.default_allow = default_allow

    def allow(self, path):
        # First match wins
        for pattern, allow in self._entries:
            if pattern.match(path):
                return allow
        return self.default_allow

    def parse(self, lines):
        # Syntax: "DIRECTIVE : PATTERN" where
        # DIRECTIVE is either "Disallow:" or "Allow:" and
        # PATTERN either has the form "*.EXT" or "/PATH".
        # Strings starting with "#" and empty lines are ignored.

        for ln, line in enumerate(lines):
            i = line.find('#')
            if i != -1:
                line = line[:i]
            line = line.strip()

            if not line:
                continue

            i = line.find(':')
            if i == -1:
                raise PermissionParseError(ln, lines[ln], 'missing colon')

            directive = line[:i].strip().lower()
            pattern = line[i + 1:].strip()

            if directive == 'allow':
                allow = True
            elif directive == 'disallow':
                allow = False
            else:
                raise PermissionParseError(
                    ln, lines[ln], 'unrecognized directive')

            if pattern.startswith('/'):
                patt = PathPattern(pattern)
            elif pattern.startswith('*.'):
                patt = ExtensionPattern(pattern[1:])
            else:
                raise PermissionParseError(
                    ln, lines[ln], 'unrecognized pattern')

            self._entries.append((patt, allow))

        return self


class BratHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Minimal handler for brat server."""

    permissions = PathPermissions().parse(_PERMISSIONS.split('\n'))

    def __init__(self, *args, **kwargs):
        """
        Initiate HTTP Request Handler.

        Pass path to brat installation to avoid using cwd (current working directory).
        """
        directory = kwargs.pop('directory', BRAT_INSTALLATION_PATH)
        super().__init__(*args, directory=directory, **kwargs)

    def log_request(self, code='-', size='-'):
        if _LOG_REQUESTS:
            SimpleHTTPRequestHandler.log_request(self, code, size)
        else:
            # just ignore logging
            pass

    def is_brat(self):
        # minimal cleanup
        path = self.path
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]

        if path == '/ajax.cgi':
            return True
        else:
            return False

    def run_brat_direct(self):
        """Execute brat server directly."""

        remote_addr = self.client_address[0]
        remote_host = self.address_string()
        cookie_data = ', '.join(
            [_f for _f in self.headers.get_all('cookie', []) if _f])

        query_string = ''
        i = self.path.find('?')
        if i != -1:
            query_string = self.path[i + 1:]

        saved = sys.stdin, sys.stdout, sys.stderr
        sys.stdin, sys.stdout = self.rfile, self.wfile

        # set env to get FieldStorage to read params
        env = {}
        env['REQUEST_METHOD'] = self.command
        content_length = self.headers.get('content-length')
        if content_length:
            env['CONTENT_LENGTH'] = content_length
        if query_string:
            env['QUERY_STRING'] = query_string
        os.environ.update(env)
        params = FieldStorage(fp=self.rfile)

        # Call main server
        cookie_hdrs, response_data = serve(params, remote_addr, remote_host,
                                           cookie_data)

        sys.stdin, sys.stdout, sys.stderr = saved

        # Package and send response
        if cookie_hdrs is not None:
            response_hdrs = [hdr for hdr in cookie_hdrs]
        else:
            response_hdrs = []
        response_hdrs.extend(response_data[0])

        self.send_response(200)
        for k, v in response_hdrs:
            self.send_header(k, v)
        self.end_headers()

        # Hack to support binary data and general Unicode for SVGs and JSON
        if isinstance(response_data[1], str):
            self.wfile.write(response_data[1].encode('utf-8'))
        else:
            self.wfile.write(response_data[1])
        return 0

    def allow_path(self):
        """Test whether to allow a request for self.path."""

        # Cleanup in part following SimpleHTTPServer.translate_path()
        path = self.path
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = unquote(path)
        path = normpath(path)
        parts = path.split('/')
        parts = [_f for _f in parts if _f]
        if '..' in parts:
            return False
        path = '/' + '/'.join(parts)

        return self.permissions.allow(path)

    def list_directory(self, path):
        """Override SimpleHTTPRequestHandler.list_directory()"""
        # TODO: permissions for directory listings
        self.send_error(403)

    def do_POST(self):
        """Serve a POST request.

        Only implemented for brat server.
        """

        if self.is_brat():
            self.run_brat_direct()
        else:
            self.send_error(501, "Can only POST to brat")

    def do_GET(self):
        """Serve a GET request."""
        if not self.allow_path():
            self.send_error(403)
        elif self.is_brat():
            self.run_brat_direct()
        else:
            SimpleHTTPRequestHandler.do_GET(self)

    def do_HEAD(self):
        """Serve a HEAD request."""
        if not self.allow_path():
            self.send_error(403)
        else:
            SimpleHTTPRequestHandler.do_HEAD(self)


class BratServer(ForkingMixIn, HTTPServer):
    def __init__(self, server_address):
        HTTPServer.__init__(self, server_address, BratHTTPRequestHandler)


def main(argv):
    # warn if root/admin
    try:
        if os.getuid() == 0:
            print("""
! WARNING: running as root. The brat standalone server is experimental   !
! and may be a security risk. It is recommend to run the standalone      !
! server as a non-root user with write permissions to the brat work/ and !
! data/ directories (e.g. apache if brat is set up using standard        !
! installation).                                                         !
""", file=sys.stderr)
    except AttributeError:
        # not on UNIX
        print("""
Warning: could not determine user. Note that the brat standalone
server is experimental and should not be run as administrator.
""", file=sys.stderr)

    if len(argv) > 1:
        try:
            port = int(argv[1])
        except ValueError:
            print("Failed to parse", argv[1], "as port number.", file=sys.stderr)
            return 1
    else:
        port = _DEFAULT_SERVER_PORT

    try:
        server = BratServer((_DEFAULT_SERVER_ADDR, port))
        print("Serving brat at http://%s:%d" % server.server_address, file=sys.stderr)
        server.serve_forever()
    except KeyboardInterrupt:
        # normal exit
        pass
    except socket.error as why:
        print("Error binding to port", port, ":", why[1], file=sys.stderr)
    except Exception as e:
        print("Server error", e, file=sys.stderr)
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
