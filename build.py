import os
from shutil import copy, make_archive

from totcommon.builder import builder
from src._constants import VERSION, NAME, ORGNAME, URL

builder(NAME, ORGNAME, URL, VERSION)

# include the VGCT executable definition sidecar (builder() only bundles
# the CompilePal configs, so copy this one in and refresh the release archive).
distDir = './dist/' + NAME + '-v' + str(VERSION)
exeDir = distDir + '/' + NAME

sidecar = './plugins/vgct/' + NAME + '.vgct.json'
if os.path.isfile(sidecar):
    copy(sidecar, exeDir)

    try:
        os.remove(distDir + '.zip')
    except OSError:
        pass
    make_archive(distDir, 'zip', distDir)
