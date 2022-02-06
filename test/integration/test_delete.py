import os
import unittest

from . import assertPopen, assertOutput
from .. import *
from dvci import git_utils


class DeleteTestCase(unittest.TestCase):
    def _deploy(self, branch=None, versions=['1.0', '2.0'], prefix=''):
        extra_args = ['-b', branch] if branch else []
        if prefix:
            extra_args.extend(['--prefix', prefix])
        for i in versions:
            assertPopen(['dvci', 'deploy', i] + extra_args)

    def _test_delete(self, expected_message=None, directory='.'):
        message = assertPopen(['git', 'log', '-1', '--pretty=%B']).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            self.assertRegex(message, r'^Removed \S+( in .*)? with dvci \S+$')

        assertDirectory(directory, {
            'versions.json',
            '2.0',
            '2.0/index.html'
        }, allow_extra=True)


class TestDelete(DeleteTestCase):
    def setUp(self):
        self.stage = stage_dir('delete')
        git_init()
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)
        check_call_silent(['git', 'add', 'docums.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def test_delete_versions(self):
        self._deploy()
        assertPopen(['dvci', 'delete', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_delete()

    def test_delete_all(self):
        self._deploy()
        assertPopen(['dvci', 'delete', '--all'])
        check_call_silent(['git', 'checkout', 'gh-pages'])

        message = assertPopen(['git', 'log', '-1', '--pretty=%B']).rstrip()
        self.assertRegex(message, r'^Removed everything with dvci \S+$')
        self.assertFalse(os.path.exists('version.json'))

    def test_from_subdir(self):
        self._deploy()
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['dvci', 'delete', '1.0'], returncode=1)
            assertPopen(['dvci', 'delete', '1.0', '-F', '../docums.yml'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_delete()

    def test_from_subdir_explicit_branch(self):
        self._deploy()
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['dvci', 'delete', '1.0', '-b', 'gh-pages', '-r',
                         'origin'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_delete()

    def test_branch(self):
        self._deploy('branch')
        assertPopen(['dvci', 'delete', '1.0', '-b', 'branch'])
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_delete()

    def test_commit_message(self):
        self._deploy()
        assertPopen(['dvci', 'delete', '1.0', '-m', 'commit message'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_delete('commit message')

    def test_prefix(self):
        self._deploy(prefix='prefix')
        assertPopen(['dvci', 'delete', '1.0', '--prefix', 'prefix'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_delete(directory='prefix')

    def test_push(self):
        self._deploy()
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])
        stage_dir('delete_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['dvci', 'delete', '1.0', '-p'])
        clone_rev = git_utils.get_latest_commit('gh-pages')

        with pushd(self.stage):
            origin_rev = git_utils.get_latest_commit('gh-pages')
            self.assertEqual(origin_rev, clone_rev)

    def test_remote_empty(self):
        stage_dir('delete_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        self._deploy(versions=['1.0'])
        old_rev = git_utils.get_latest_commit('gh-pages')

        assertPopen(['dvci', 'delete', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), old_rev)

    def test_local_empty(self):
        self._deploy(versions=['1.0'])
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('delete_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['dvci', 'delete', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_ahead_remote(self):
        self._deploy(versions=['1.0'])
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('deploy_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        self._deploy(versions=['2.0'])
        old_rev = git_utils.get_latest_commit('gh-pages')

        assertPopen(['dvci', 'delete', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), old_rev)
        self.assertEqual(git_utils.get_latest_commit('gh-pages^^'), origin_rev)

    def test_behind_remote(self):
        self._deploy(versions=['1.0'])

        stage_dir('delete_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            self._deploy(versions=['2.0'])
            origin_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertPopen(['dvci', 'delete', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_diverged_remote(self):
        self._deploy(versions=['1.0'])

        stage_dir('delete_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            self._deploy(versions=['2.0'])
            origin_rev = git_utils.get_latest_commit('gh-pages')

        self._deploy(versions=['2.1'])
        clone_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertOutput(self, ['dvci', 'delete', '1.0'], output=(
            'error: gh-pages has diverged from origin/gh-pages\n' +
            '  Pass --ignore to ignore this or --rebase to rebase onto ' +
            'remote\n'
        ), returncode=1)
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)

        assertPopen(['dvci', 'delete', '1.0', '--ignore'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), clone_rev)

        assertPopen(['dvci', 'delete', '1.0', '--rebase'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)


class TestDeleteOtherRemote(DeleteTestCase):
    def setUp(self):
        self.stage_origin = stage_dir('delete_remote')
        git_init()
        copytree(os.path.join(test_data_dir, 'remote'), self.stage_origin)
        check_call_silent(['git', 'add', 'docums.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])

    def _clone(self):
        self.stage = stage_dir('delete_remote_clone')
        check_call_silent(['git', 'clone', self.stage_origin, '.'])
        git_config()

    def _test_rev(self, branch):
        clone_rev = git_utils.get_latest_commit(branch)
        with pushd(self.stage_origin):
            self.assertEqual(git_utils.get_latest_commit(branch), clone_rev)

    def test_default(self):
        self._deploy()
        self._clone()
        check_call_silent(['git', 'remote', 'rename', 'origin', 'myremote'])

        assertPopen(['dvci', 'delete', '1.0', '-p'])
        check_call_silent(['git', 'checkout', 'mybranch'])
        self._test_delete()
        self._test_rev('mybranch')

    def test_explicit_branch(self):
        self._deploy(branch='pages')
        self._clone()
        check_call_silent(['git', 'remote', 'rename', 'origin', 'myremote'])

        assertPopen(['dvci', 'delete', '1.0', '-p', '-b', 'pages'])
        check_call_silent(['git', 'checkout', 'pages'])
        self._test_delete()
        self._test_rev('pages')

    def test_explicit_remote(self):
        self._deploy()
        self._clone()
        check_call_silent(['git', 'remote', 'rename', 'origin', 'remote'])

        assertPopen(['dvci', 'delete', '1.0', '-p', '-r', 'remote'])
        check_call_silent(['git', 'checkout', 'mybranch'])
        self._test_delete()
        self._test_rev('mybranch')
