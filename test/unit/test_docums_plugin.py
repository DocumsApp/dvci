import os
import unittest
from collections import namedtuple
from unittest import mock

from .. import *
from dvci.docums_utils import docs_version_var


class MockPlugins:
    BasePlugin = object


# Mock importing `docums.plugins`, since it can't be imported normally.
real_import = __import__
with mock.patch('builtins.__import__', lambda name, *args, **kwargs: (
    MockPlugins if name == 'docums.plugins' else
    real_import(name, *args, **kwargs)
)):
    from dvci import docums_plugin


class TestGetThemeDir(unittest.TestCase):
    def test_docums_theme(self):
        theme_dir = docums_plugin.get_theme_dir('docums')
        self.assertEqual(os.path.basename(theme_dir), 'docums')

    def test_bootswatch_theme(self):
        theme_dir = docums_plugin.get_theme_dir('yeti')
        self.assertEqual(os.path.basename(theme_dir), 'docums')

    def test_unknown_theme(self):
        self.assertRaises(ValueError, docums_plugin.get_theme_dir, 'nonexist')


class TestDocumsPluginOnConfig(unittest.TestCase):
    def test_site_url(self):
        with mock.patch('os.environ', {docs_version_var: '1.0'}):
            p = docums_plugin.DvciPlugin()
            p.config = {'canonical_version': None}
            config = {'site_url': 'https://example.com/'}
            p.on_config(config)
            self.assertEqual(config['site_url'], 'https://example.com/1.0')

    def test_no_site_url(self):
        with mock.patch('os.environ', {docs_version_var: '1.0'}):
            p = docums_plugin.DvciPlugin()
            p.config = {'canonical_version': None}
            config = {'site_url': ''}
            p.on_config(config)
            self.assertEqual(config['site_url'], '')

    def test_explicit_canonical(self):
        with mock.patch('os.environ', {docs_version_var: '1.0'}):
            p = docums_plugin.DvciPlugin()
            p.config = {'canonical_version': 'latest'}
            config = {'site_url': 'https://example.com/'}
            p.on_config(config)
            self.assertEqual(config['site_url'], 'https://example.com/latest')

        with mock.patch('os.environ', {docs_version_var: '1.0'}):
            p = docums_plugin.DvciPlugin()
            p.config = {'canonical_version': ''}
            config = {'site_url': 'https://example.com/'}
            p.on_config(config)
            self.assertEqual(config['site_url'], 'https://example.com/')

    def test_no_version(self):
        with mock.patch('os.environ', {}):
            p = docums_plugin.DvciPlugin()
            p.config = {'canonical_version': None}
            config = {'site_url': 'https://example.com/'}
            p.on_config(config)
            self.assertEqual(config['site_url'], 'https://example.com/')


class TestDocumsPluginOnFiles(unittest.TestCase):
    MockTheme = namedtuple('MockTheme', ['name'])

    def make_plugin(self, version_selector=True):
        p = docums_plugin.DvciPlugin()
        p.config = {'version_selector': version_selector, 'css_dir': 'css',
                    'javascript_dir': 'js'}
        return p

    def make_config(self, theme, extra_css=[], extra_javascript=[]):
        return {'theme': self.MockTheme(theme),
                'site_dir': os.path.abspath(test_data_dir),
                'extra_css': list(extra_css),
                'extra_javascript': list(extra_javascript)}

    def test_docums_theme(self):
        cfg = self.make_config('docums')
        files = self.make_plugin().on_files([], cfg)
        self.assertEqual([i.src_path for i in files],
                         ['version-select.css', 'version-select.js'])

    def test_unrecognized_theme(self):
        cfg = self.make_config('unrecognized')
        files = self.make_plugin().on_files([], cfg)
        self.assertEqual(files, [])

    def test_duplicate_files(self):
        cfg = self.make_config('docums', ['css/version-select.css'])
        with self.assertRaises(docums_plugin.PluginError):
            self.make_plugin().on_files([], cfg)

    def test_no_version_select(self):
        cfg = self.make_config('docums')
        files = self.make_plugin(False).on_files([], cfg)
        self.assertEqual(files, [])
