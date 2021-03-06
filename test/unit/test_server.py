import sys
import unittest

from .. import *
from .mock_server import MockRequest, MockServer
from dvci import git_utils
from dvci import server


class TestGitBranchHTTPHandler(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('server')
        git_init()
        with git_utils.Commit('branch', 'add file') as commit:
            commit.add_file(git_utils.FileInfo('index.html', 'main page'))
            commit.add_file(git_utils.FileInfo('dir/index.html', 'sub page'))

        class Handler(server.GitBranchHTTPHandler):
            branch = 'branch'

            # Use a buffered response in Python 3.6+, since it's easier for
            # testing.
            if sys.version_info >= (3, 6):
                wbufsize = -1

            def log_message(self, *args):
                pass

        self.server = MockServer(('0.0.0.0', 8888), Handler)

    def test_root(self):
        req = MockRequest()
        self.server.handle_request(req)
        self.assertRegex(
            req.response,
            b'HTTP/1.0 200 OK\r\n' +
            b'Server: DvciHTTP.*\r\n' +
            b'Date: .*\r\n' +
            b'Content-Type: text/html\r\n\r\n' +
            b'main page$'
        )

    def test_file(self):
        req = MockRequest(path=b'/index.html')
        self.server.handle_request(req)
        self.assertRegex(
            req.response,
            b'HTTP/1.0 200 OK\r\n' +
            b'Server: DvciHTTP.*\r\n' +
            b'Date: .*\r\n' +
            b'Content-Type: text/html\r\n\r\n' +
            b'main page$'
        )

    def test_dir(self):
        req = MockRequest(path=b'/dir/')
        self.server.handle_request(req)
        self.assertRegex(
            req.response,
            b'HTTP/1.0 200 OK\r\n' +
            b'Server: DvciHTTP.*\r\n' +
            b'Date: .*\r\n' +
            b'Content-Type: text/html\r\n\r\n' +
            b'sub page$'
        )

    def test_dir_redirect(self):
        req = MockRequest(path=b'/dir')
        self.server.handle_request(req)
        self.assertRegex(
            req.response,
            b'HTTP/1.0 301 Moved Permanently\r\n' +
            b'Server: DvciHTTP.*\r\n' +
            b'Date: .*\r\n' +
            b'Location: /dir/\r\n\r\n$'
        )

    def test_head(self):
        req = MockRequest(b'HEAD', b'/index.html')
        self.server.handle_request(req)
        self.assertRegex(
            req.response,
            b'HTTP/1.0 200 OK\r\n' +
            b'Server: DvciHTTP.*\r\n' +
            b'Date: .*\r\n' +
            b'Content-Type: text/html\r\n\r\n$'
        )

    def test_404(self):
        req = MockRequest(path=b'/nonexist')
        self.server.handle_request(req)
        self.assertRegex(
            req.response,
            b'HTTP/1.0 404 File not found\r\n' +
            b'Server: DvciHTTP.*\r\n' +
            b'Date: .*\r\n'
        )

    def test_404_root(self):
        with git_utils.Commit('branch', 'remove file') as commit:
            commit.delete_files(['index.html'])

        req = MockRequest(path=b'/')
        self.server.handle_request(req)
        self.assertRegex(
            req.response,
            b'HTTP/1.0 404 File not found. Did you.*\r\n' +
            b'Server: DvciHTTP.*\r\n' +
            b'Date: .*\r\n'
        )
