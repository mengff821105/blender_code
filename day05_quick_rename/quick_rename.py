bl_info = {
    "name": "Quick Rename",
    "author": "mengff",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar(N面板) > QuickR",
    "category": "Object",
}

import bpy


class OBJECT_OT_add_prefix(bpy.types.Operator):
    bl_idname = "object.quick_add_prefix"
    bl_label = "Add Prefix"
    bl_options = {'REGISTER', 'UNDO'}

    prefix: bpy.props.StringProperty(name="Prefix", default="SM_")

    def execute(self, context):
        n = 0
        for obj in context.selected_objects:
            if not obj.name.startswith(self.prefix):
                obj.name = self.prefix + obj.name
                n += 1
        self.report({'INFO'}, f"Renamed {n} objects")
        return {'FINISHED'}


class VIEW3D_PT_quick_rename(bpy.types.Panel):
    bl_label = "Quick Rename"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "QuickR"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.quick_add_prefix")


classes = (OBJECT_OT_add_prefix, VIEW3D_PT_quick_rename)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
