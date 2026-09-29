import bpy


class VIEW3D_PT_unity_fbx(bpy.types.Panel):
    bl_label = "Unity FBX Exporter"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "UnityFBX"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.unity_fbx_settings

        layout.label(text="输出")
        layout.prop(settings, "export_path")
        layout.operator("unityfbx.open_folder", icon='FILE_FOLDER')

        layout.separator()
        layout.label(text="导出模式")
        layout.prop(settings, "export_mode", text="")
        if settings.export_mode == 'COMBINED':
            layout.prop(settings, "combined_name")

        layout.separator()
        layout.label(text="命名")
        row = layout.row(align=True)
        row.prop(settings, "name_prefix")
        row.prop(settings, "name_suffix")

        layout.separator()
        layout.label(text="选项")
        col = layout.column()
        col.prop(settings, "apply_transform")
        col.prop(settings, "apply_modifiers")
        col.prop(settings, "only_meshes")

        layout.separator()
        layout.operator("unityfbx.export", icon='EXPORT')


classes = (VIEW3D_PT_unity_fbx,)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
