import nuke
import os
import logging

logging.info('Attempting to initialize Node Tag')
import nodeTag
nuke.pluginAddPath(os.path.dirname(nodeTag.__file__).replace('\\', '/'))
