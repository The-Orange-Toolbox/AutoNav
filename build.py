import PyInstaller.__main__
import datetime
import glob
import os
from sys import platform
from shutil import copyfile, copy, make_archive


orgName = 'The Orange Toolbox'
exeName = 'BuildCube'
builddate = datetime.datetime.now().strftime('%b %d %Y')
version = "1.0"
distDir = './dist/' + exeName + '-v' + str(version)
exeDir = distDir + '/' + exeName

# Write version info into _constants.py resource file
with open('src/_constants.py', 'w') as f:
    f.write("ORGNAME = \"{}\"\n".format(orgName))
    f.write("NAME = \"{}\"\n".format(exeName))
    f.write("VERSION = \"{}\"\n".format(version))
    f.write("BUILD_DATE = \"{}\"\n".format(builddate))

args = ['src/__main__.py',
        '-p', 'src',
        '-n', exeName,
        '-F',
        '--distpath', exeDir]

# Build!
PyInstaller.__main__.run(args + assets)

# Copy other bundle files
copyfile('./README.md', distDir + '/readme.txt')
copy('./plugins/compilepal/meta.json', exeDir)
copy('./plugins/compilepal/parameters.json', exeDir)

# Zip the package
try:
    os.remove(distDir + '.zip')
except OSError:
    pass
make_archive(distDir, 'zip', distDir)
