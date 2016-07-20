"""
    Copyright (c) 2016 Hubert Jarosz. All rights reserved.
    Licensed under the MIT license. See LICENSE file in the project root for full license information.
"""

import sys
import subprocess

try:
    import src.deployer
    import pathlib
except (ImportError, SyntaxError):
    if sys.version_info[:2] < (3, 4):
        raise Exception("This software needs Python 3.4 or newer!")
    else:
        raise

try:
    subprocess.Popen(["git"], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except:
    raise Exception("You must install git!")
try:
    subprocess.Popen(["scp"], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except:
    raise Exception("You must install scp!")

d = src.deployer.Deployer(pathlib.Path(__file__).resolve().parent / "config.ini")

try:
    d.run()
except KeyboardInterrupt:
    sys.exit()
