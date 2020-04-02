import bpy
import sys
import os

def setup_import_path():
    script_dir = os.path.dirname(bpy.context.space_data.text.filepath)
    if script_dir not in sys.path:
        sys.path.append(script_dir)

setup_import_path()

import tempscript
import importlib

importlib.reload(tempscript)
tempscript.execute()