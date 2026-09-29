import bpy

from .exporter import export, ExportError


class UNITYFBX_OT_export(bpy.types.Operator):
    bl_idname = "unityfbx.export"
    bl_label = "导出 FBX"
    bl_options = {'REGISTER'}

    def execute(self, context):
        settings = context.scene.unity_fbx_settings
        try:
            count = export(settings, context)
        except ExportError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        self.report({'INFO'}, f"导出完成，共 {count} 个 FBX")
        return {'FINISHED'}


class UNITYFBX_OT_open_folder(bpy.types.Operator):
    bl_idname = "unityfbx.open_folder"
    bl_label = "打开输出目录"
    bl_options = {'REGISTER'}

    def execute(self, context):
        settings = context.scene.unity_fbx_settings
        path = bpy.path.abspath(settings.export_path)
        bpy.ops.wm.path_open(filepath=path)
        return {'FINISHED'}


classes = (
    UNITYFBX_OT_export,
    UNITYFBX_OT_open_folder,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
