# Contract: Operator、面板与消息契约

**Feature**: 001-unity-fbx-exporter | **Date**: 2026-11-07

本文件是插件对外可见行为的契约：注册名、面板结构、消息文案、报告格式。
实现阶段不得偏离；如需变更必须先改本文件与 spec（宪法原则 I）。

## 1. 注册标识

### Operators

| bl_idname | bl_label | bl_options | 职责 |
|---|---|---|---|
| `unityfbx.export` | 导出 FBX | REGISTER | 校验→分组→模态批量导出 |
| `unityfbx.open_folder` | 打开输出目录 | REGISTER | 跨平台打开 export_path |

### Panel

| 属性 | 值 |
|---|---|
| 类名 | `VIEW3D_PT_unity_fbx` |
| bl_space_type / region_type | VIEW_3D / UI |
| bl_category | `UnityFBX`（N 面板标签页） |
| bl_label | Unity FBX Exporter |

### PropertyGroup

| 注册名 | 类型 | 挂载点 |
|---|---|---|
| `unity_fbx_settings` | UnityFBXSettings | Scene |

## 2. 面板布局契约（自上而下）

```text
[输出]
  目录选择框 (export_path, DIR_PATH)
  [打开输出目录] 按钮
────
[导出模式]
  下拉框 (export_mode)：每个物体 / 每个集合 / 合并为一个
  （仅 COMBINED 时显示）合并文件名输入框 (combined_name)
────
[命名]
  前缀 (name_prefix) | 后缀 (name_suffix)
────
[选项]
  ☑ 导出前 Apply Transform (apply_transform)
  ☑ 应用修改器 (apply_modifiers)
  ☑ 只导出网格物体 (only_meshes)
────
[导出 FBX] 主按钮（EXPORT 图标）
```

所有标签使用中文；属性的 `description` 用中文悬停说明。面板不做业务校验，
仅按模式显隐控件；校验全部在 Operator 内触发。

## 3. 中文消息目录（validation.py 统一维护）

| 消息键 | 文案 | 触发场景 | report 级别 |
|---|---|---|---|
| MSG_NO_SELECTION | 请先选择至少一个物体 | 选中为空 | ERROR |
| MSG_NO_VALID_OBJECT | 选中的对象都被过滤规则跳过，没有可导出的网格 | 过滤后为空 | ERROR |
| MSG_PATH_RELATIVE_UNSAVED | 当前场景未保存，无法使用相对目录；请先保存场景或改用绝对路径 | 未保存场景+相对路径 | ERROR |
| MSG_PATH_NOT_WRITABLE | 输出目录不可写或无法创建：{path} | 目录创建/写权限失败 | ERROR |
| MSG_COMBINED_NAME_EMPTY | 合并文件名不能为空 | COMBINED 模式名称清洗后为空 | ERROR |
| MSG_EMPTY_COLLECTION | 集合“{name}”为空，已跳过 | 空集合 | INFO（计入报告） |
| MSG_FILENAME_SANITIZED | 文件名包含非法字符，已替换为：{new_name} | 命名清洗发生 | INFO（计入警告） |
| MSG_DUPLICATE_NUMBERED | 文件名冲突，已自动重命名为：{new_name} | 序号追加发生 | INFO（计入警告） |
| MSG_EXPORT_REPORT | 导出完成：成功 {ok} 个，跳过 {skipped} 个，警告 {warnings} 条 | 正常结束 | INFO |
| MSG_EXPORT_CANCELLED | 导出已取消：已完成 {ok} 个，剩余任务未执行 | ESC 取消 | WARNING |
| MSG_VERSION_MISMATCH | 本插件要求 Blender {min_version} 或更高版本 | 版本拦截 | ERROR |

`{xxx}` 为运行期占位符。核心模块只抛 `ExportError(消息键或最终文案)`，
Operator 负责 report，UI 文案不允许散落在 exporter/grouping 中。

## 4. 导出结果报告契约

导出结束后状态栏报告遵循 MSG_EXPORT_REPORT 格式；同时在面板底部（本次会话内）
显示三行摘要：

- 成功文件：`{filename}` 逐行列出（超过 10 个折叠为"等 N 个文件"）；
- 跳过对象：物体名 + reason_text；
- 警告：MSG_FILENAME_SANITIZED / MSG_DUPLICATE_NUMBERED 的实际文案。

## 5. FBX 导出参数契约（对 bpy.ops.export_scene.fbx 的固定传参）

| 参数 | 值 | 说明 |
|---|---|---|
| filepath | 每组计算出的绝对路径 | |
| use_selection | True | 只导出临时选中的组成员 |
| axis_forward | '-Z' | Unity 预设，固定不可配 |
| axis_up | 'Y' | 同上 |
| apply_unit_scale | True | |
| global_scale | 1.0 | |
| bake_space_transform | 跟随 apply_transform 开关 | 开=True，关=False |
| use_mesh_modifiers | 跟随 apply_modifiers 开关 | |
| object_types | only_meshes 开：`{'MESH','EMPTY'}`；关：默认全集 | EMPTY 保留以容纳集合实例 |
| add_leaf_bones | False | Unity 不需要叶骨骼，避免多余节点 |

其余参数使用导出器默认值；版本升级导致参数废弃时，必须在 plan/research 留痕后再改。

## 6. 撤销与状态还原契约

- `transform_apply` 通过 `bpy.ops.object.transform_apply` 执行，必须出现在撤销栈；
- 选择/活动物体快照在 ExportJob 开始时采集，所有退出路径（成功、校验失败、异常、取消）
  都必须经过同一个 finally 还原函数；
- 插件自身不创建任何持久 datablock；模态结束后 ExportJob 引用立即释放。

## 7. 无头脚本可调用契约

`grouping.py`、`naming.py`、`validation.py`、`exporter.py` 中的函数签名必须满足：
只依赖传入的 settings/context 参数与 bpy 数据层，不 import panel/operators，
可在 `blender --background` 进程中直接 import 并断言。
