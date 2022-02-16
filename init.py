import traceback

import nuke
import os
import logging

try:
    logging.info('Attempting to initialize Node Tag')
    import nodeTag
    nuke.pluginAddPath(os.path.dirname(nodeTag.__file__).replace('\\', '/'))
except Exception:
    logging.error(traceback.format_exc())
