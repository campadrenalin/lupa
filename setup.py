
import sys
import os
from distutils.core import setup, Extension

VERSION = '0.20'
LUAJIT_SOURCE = 'http://luajit.org/download/LuaJIT-2.0.0.tar.gz'

extra_setup_args = {}

# support 'test' target if setuptools/distribute is available

if 'setuptools' in sys.modules:
    extra_setup_args['test_suite'] = 'lupa.tests.suite'
    extra_setup_args["zip_safe"] = False

basedir = os.path.abspath(os.path.dirname(__file__))

def luajit_fetch(location, source):
    import tarfile
    try:
        from urllib import urlretrieve
    except:
        from urllib.request import urlretrieve

    filename = os.path.join('.', os.path.basename(source))
    filename, headers = urlretrieve(source, filename)

    tf = tarfile.TarFile.open(filename)
    tf.extractall(location)

def luajit_build(location):
    '''
    Build LuaJIT in specified dir
    '''
    import subprocess

    subprocess.check_call([
        'make',
        '-C', location,
        '-j', '4',
        'CFLAGS=-fPIC',
    ])

def luajit_find(location):
    return [x for x in os.listdir(location) if x.lower().startswith('luajit')]

def luajit_find_targz(location):
    return [x for x in luajit_find(location) if x.lower().endswith('.tar.gz')]

def luajit_find_dir(location):
    return [x for x in luajit_find(location) if os.path.isdir(x)]


def find_lua_build():
    '''
    Link against local luajit build, fetching and creating if necessary.
    '''

    os_path = os.path
    if not (luajit_find_dir(basedir) and luajit_find_targz(basedir)):
        # Fetch and build
        print("Could not find existing luajit folder, fetching")
        localjit = [luajit_fetch(basedir, LUAJIT_SOURCE)]

    for filename in luajit_find_dir(basedir):
        filepath = os_path.join(basedir, filename, 'src')
        if os_path.isdir(filepath):
            libfile = os_path.join(filepath, 'libluajit.a')
            if not os_path.isfile(libfile):
                luajit_build(filename)
            if os_path.isfile(libfile):
                print("found LuaJIT build in %s" % filepath)
                print("building statically")
                return dict(extra_objects=[libfile], include_dirs=[filepath]), None

            # Also check for lua51.lib, which is the Windows equivilant of libluajit.a
            libfile = os_path.join(filepath, 'lua51.lib')
            if os_path.isfile(libfile):
                print("found LuaJIT build in %s" % filepath)
                print("building statically")
                # And return the dll file name too, as we need to include it in the install directory
                return dict(extra_objects=[libfile], include_dirs=[filepath]), 'lua51.dll'
    raise ValueError("No localjit directory found")


def has_option(name):
    if name in sys.argv[1:]:
        sys.argv.remove(name)
        return True
    return False

ext_args, dll_file = find_lua_build()

ext_modules = [
    Extension(
        'lupa._lupa',
        sources = ['lupa/_lupa.c'],
        **ext_args
        )
    ]

def read_file(filename):
    with open(os.path.join(basedir, filename)) as f:
        return f.read()

def write_file(filename, content):
    with open(os.path.join(basedir, filename), 'w') as f:
        f.write(content)

long_description = '\n\n'.join([
    read_file(text_file)
    for text_file in ['README.rst', 'INSTALL.rst', 'CHANGES.rst']])

write_file(os.path.join('lupa', 'version.py'), "__version__ = '%s'\n" % VERSION)

# Include lua51.dll in the lib folder if we are on windows
if dll_file is not None:
    extra_setup_args['package_data'] = {'lupa': [dll_file]}

if sys.version_info >= (2,6):
    extra_setup_args['license'] = 'MIT style'


# call distutils

setup(
    name = "lupa",
    version = VERSION,
    author = "Stefan Behnel",
    author_email = "stefan_ml@behnel.de",
    maintainer = "Lupa-dev mailing list",
    maintainer_email = "lupa-dev@freelists.org",
    url = "https://github.com/scoder/lupa",
    download_url = "http://pypi.python.org/packages/source/l/lupa/lupa-%s.tar.gz" % VERSION,

    description="Python wrapper around LuaJIT",

    long_description = long_description,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Cython',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Other Scripting Engines',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
    ],

    packages = ['lupa'],
#    package_data = {},
    ext_modules = ext_modules,
    **extra_setup_args
)
