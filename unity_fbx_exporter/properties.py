import bpy


class UnityFBXSettings(bpy.types.PropertyGroup):
    export_path: bpy.props.StringProperty(
        name="输出目录",
        description="FBX 导出的目标文件夹",
        subtype='DIR_PATH',
        default="//FBX_Export/",
    )

    export_mode: bpy.props.EnumProperty(
        name="导出模式",
        description="选择批量导出的拆分方式",
        items=[
            ('OBJECT', "每个物体", "每个选中物体导出为一个 FBX"),
            ('COLLECTION', "每个集合", "每个选中物体所属的集合导出为一个 FBX"),
            ('COMBINED', "合并为一个", "所有选中物体合并导出为一个 FBX"),
        ],
        default='OBJECT',
    )

    combined_name: bpy.props.StringProperty(
        name="合并文件名",
        description="合并导出模式下的 FBX 文件名",
        default="combined",
    )

    name_prefix: bpy.props.StringProperty(
        name="前缀",
        default="",
    )

    name_suffix: bpy.props.StringProperty(
        name="后缀",
        default="",
    )

    apply_transform: bpy.props.BoolProperty(
        name="导出前 Apply Transform",
        description="导出前应用位置/旋转/缩放，保证进 Unity 后变换干净",
        default=True,
    )

    apply_modifiers: bpy.props.BoolProperty(
        name="应用修改器",
        description="导出时应用物体上的修改器结果",
        default=True,
    )

    only_meshes: bpy.props.BoolProperty(
        name="只导出网格物体",
        description="跳过灯光、相机、空物体等非网格对象",
        default=True,
    )


classes = (UnityFBXSettings,)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.unity_fbx_settings = bpy.props.PointerProperty(
        type=UnityFBXSettings
    )


def unregister():
    del bpy.types.Scene.unity_fbx_settings
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
