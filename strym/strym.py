#!/usr/bin/env python
# coding: utf-8

# Author : Rahul Bhadani
# Initial Date: Nov 11, 2019
# About: strym class uses comma.ai panda package to capture can data from comma.ai panda device
#   and plot in the real time. Read associated README for full description
# License: MIT License


#   Permission is hereby granted, free of charge, to any person obtaining
#   a copy of this software and associated documentation files
#   (the "Software"), to deal in the Software without restriction, including
#   without limitation the rights to use, copy, modify, merge, publish,
#   distribute, sublicense, and/or sell copies of the Software, and to
#   permit persons to whom the Software is furnished to do so, subject
#   to the following conditions:

#   The above copyright notice and this permission notice shall be
#   included in all copies or substantial portions of the Software.

#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF
#   ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
#   TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
#   PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
#   SHALL THE AUTHORS, COPYRIGHT HOLDERS OR ARIZONA BOARD OF REGENTS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
#   AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#   OR OTHER DEALINGS IN THE SOFTWARE.



__author__ = 'Rahul Bhadani'
__email__  = 'rahulbhadani@email.arizona.edu'
__version__ = "0.0.0" # this is set to actual version later

## General Data processing and visualization Import

from packaging import version
import warnings

from pathlib import Path
version_src = ''

try:
    import importlib.resources as pkg_resources
    with pkg_resources.as_file(pkg_resources.files('strym').joinpath('version')) as rsrc:
        #print(pkg_resources.files('strym'))
        #print(pkg_resources.files('strym').joinpath('version'))
        #print(rsrc)
        version_src = rsrc
except ImportError:
    print("importlib_resources not found. Install through `pip install importlib-resources`")

v = Path(version_src).open(encoding = "utf-8").read().splitlines()
__version__ = v[0].strip()

def timeout(func, args=(), timeout_duration=2, default=None, **kwargs):
    """This spwans a thread and runs the given function using the args, kwargs and
    return the given default value if the timeout_duration is exceeded
    """
    import threading

    class InterruptableThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.result = default

        def run(self):
            try:
                self.result = func(*args, **kwargs)
            except:
                pass

    it = InterruptableThread()
    it.start()
    it.join(timeout_duration)
    return it.result

def get_latest_strym_version():
    from subprocess import check_output, CalledProcessError

    try:  # needs to work offline as well
        result = check_output(["yolk", "-V", "strym"])
        return result.split()[1].decode("utf-8")
    except CalledProcessError:
        return "0.0.0"


def check_for_latest_version():

    latest_version = timeout(
        get_latest_strym_version, timeout_duration=5, default="0.0.0"
    )
    if version.parse(__version__) < version.parse(latest_version):

        warnings.warn("{}\n{}\n{}\n{}\n{}\n{}".format(
            "There is a newer version of strym available on PyPI:\n",
            "Your version: \t",
            __version__,
            "Latest version: \t",
            latest_version,
            "Consider updating it by using command pip install --upgrade strym"
        ))


check_for_latest_version()
