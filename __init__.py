bl_info = {
    "name": "C3 Add-On",
    "author": "abdoumatrix",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "TOPBAR",
    "description": "Import/Export C3 Model format",
    "category": "Import-Export",
}

import bpy
from . import c3_operators
from . import c3_ui

def register():
    c3_operators.register()
    c3_ui.register()

def unregister():
    c3_ui.unregister()
    c3_operators.unregister()

if __name__ == "__main__":
    register()
