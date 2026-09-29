bl_info = {
    "name": "Unity FBX Exporter",
    "author": "mengff",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > UnityFBX",
    "description": "Batch export objects or collections to Unity-friendly FBX files",
    "category": "Import-Export",
}

from . import properties
from . import exporter
from . import operators
from . import panel

modules = (
    properties,
    exporter,
    operators,
    panel,
)


def register():
    for mod in modules:
        mod.register()


def unregister():
    for mod in reversed(modules):
        mod.unregister()
