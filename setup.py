import os
import re
import subprocess
from setuptools import setup, find_packages, Command

from dvci.app_version import version

root_dir = os.path.abspath(os.path.dirname(__file__))


class Coverage(Command):
    description = 'run tests with code coverage'
    user_options = [
        ('test-suite=', 's',
         "test suite to run (e.g. 'some_module.test_suite')"),
    ]

    def initialize_options(self):
        self.test_suite = None

    def finalize_options(self):
        pass

    def run(self):
        env = dict(os.environ)
        pythonpath = os.path.join(root_dir, 'test', 'scripts')
        if env.get('PYTHONPATH'):
            pythonpath += os.pathsep + env['PYTHONPATH']
        env.update({
            'PYTHONPATH': pythonpath,
            'COVERAGE_FILE': os.path.join(root_dir, '.coverage'),
            'COVERAGE_PROCESS_START': os.path.join(root_dir, '.coveragerc'),
        })

        subprocess.run(['coverage', 'erase'], check=True)
        subprocess.run(
            ['coverage', 'run', 'setup.py', 'test'] +
            (['-q'] if self.verbose == 0 else []) +
            (['-s', self.test_suite] if self.test_suite else []),
            env=env, check=True
        )
        subprocess.run(['coverage', 'combine'], check=True,
                       stdout=subprocess.DEVNULL)


custom_cmds = {
    'coverage': Coverage,
}

try:
    from flake8.main.application import Application as Flake8

    class LintCommand(Command):
        description = 'run flake8 on source code'
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def distribution_files(self):
            return ['setup.py', 'dvci', 'test']

        def run(self):
            flake8 = Flake8()
            flake8.initialize([])
            flake8.run_checks(list(self.distribution_files()))
            flake8.formatter.start()
            flake8.report_errors()
            flake8.report_statistics()
            flake8.report_benchmarks()
            flake8.formatter.stop()
            try:
                flake8.exit()
            except SystemExit as e:
                # If successful, don't exit. This allows other commands to run
                # too.
                if e.code:
                    raise

    custom_cmds['lint'] = LintCommand
except ImportError:
    pass

with open(os.path.join(root_dir, 'README.md'), 'r') as f:
    # Read from the file and strip out the badges.
    long_desc = re.sub(r'(^# dvci)\n\n(.+\n)*', r'\1', f.read())

setup(
    name='dvci',
    version=version,

    description=('Manage multiple versions of your Docums-powered ' +
                 'documentation'),
    long_description=long_desc,
    long_description_content_type='text/markdown',
    keywords='docums multiple versions',
    url='https://github.com/khanhduy1407/dvci',

    author='NKDuy',
    author_email='kn145660@gmail.com',
    license='BSD',

    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',

        'Topic :: Documentation',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],

    packages=find_packages(exclude=['test', 'test.*']),
    include_package_data=True,

    install_requires=(['docums >= 1.0.0.0', 'jinja2', 'pyyaml >= 5.1', 'verspec']),
    extras_require={
        'dev': ['coverage', 'flake8 >= 3.0', 'flake8-quotes', 'shtab'],
        'test': ['coverage', 'flake8 >= 3.0', 'flake8-quotes', 'shtab'],
    },

    entry_points={
        'console_scripts': [
            'dvci = dvci.driver:main',
        ],
        'docums.plugins': [
            'dvci = dvci.docums_plugin:DvciPlugin',
        ],
        'dvci.themes': [
            'docums = dvci.themes.docums',
            'readthedocs = dvci.themes.readthedocs',

            # Bootswatch themes
            'bootstrap = dvci.themes.docums',
            'cerulean = dvci.themes.docums',
            'cosmo = dvci.themes.docums',
            'cyborg = dvci.themes.docums',
            'darkly = dvci.themes.docums',
            'flatly = dvci.themes.docums',
            'journal = dvci.themes.docums',
            'litera = dvci.themes.docums',
            'lumen = dvci.themes.docums',
            'lux = dvci.themes.docums',
            'materia = dvci.themes.docums',
            'minty = dvci.themes.docums',
            'pulse = dvci.themes.docums',
            'sandstone = dvci.themes.docums',
            'simplex = dvci.themes.docums',
            'slate = dvci.themes.docums',
            'solar = dvci.themes.docums',
            'spacelab = dvci.themes.docums',
            'superhero = dvci.themes.docums',
            'united = dvci.themes.docums',
            'yeti = dvci.themes.docums',

            # Bootswatch classic themes
            'amelia = dvci.themes.docums',
            'readable = dvci.themes.docums',
            'docums-classic = dvci.themes.docums',
            'amelia-classic = dvci.themes.docums',
            'bootstrap-classic = dvci.themes.docums',
            'cerulean-classic = dvci.themes.docums',
            'cosmo-classic = dvci.themes.docums',
            'cyborg-classic = dvci.themes.docums',
            'flatly-classic = dvci.themes.docums',
            'journal-classic = dvci.themes.docums',
            'readable-classic = dvci.themes.docums',
            'simplex-classic = dvci.themes.docums',
            'slate-classic = dvci.themes.docums',
            'spacelab-classic = dvci.themes.docums',
            'united-classic = dvci.themes.docums',
            'yeti-classic = dvci.themes.docums',
        ],
    },

    test_suite='test',
    cmdclass=custom_cmds,
    zip_safe=False,
)
