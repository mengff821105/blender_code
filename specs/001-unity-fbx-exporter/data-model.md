# Data Model: 实体、字段与状态

**Feature**: 001-unity-fbx-exporter | **Date**: 2026-11-07

本插件无独立数据库，持久化数据只有 Blender Scene 上的一个 PropertyGroup；运行期数据在
每次导出会话内临时构建、结束即释放。

## 实体 1：导出设置 UnityFBXSettings（持久化）

挂载点：`bpy.types.Scene.unity_fbx_settings`（PointerProperty，随 .blend 场景保存）。

| 字段 | 类型 | 默认值 | 校验/约束 | 对应需求 |
|---|---|---|---|---|
| export_path | StringProperty（subtype=DIR_PATH） | `//FBX_Export/` | 非空；abspath 可解析；未保存场景不允许相对路径 | FR-007/008 |
| export_mode | EnumProperty | `OBJECT` | 枚举值仅 `OBJECT`/`COLLECTION`/`COMBINED` | FR-001 |
| combined_name | StringProperty | `combined` | COMBINED 模式下必填，经文件名清洗后非空 | US3 |
| name_prefix | StringProperty | 空串 | 经非法字符清洗，可为空 | FR-003 |
| name_suffix | StringProperty | 空串 | 同上 | FR-003 |
| apply_transform | BoolProperty | True | 布尔 | FR-004 |
| apply_modifiers | BoolProperty | True | 布尔 | FR-005 |
| only_meshes | BoolProperty | True | 布尔 | FR-006 |

字段变更不做即时校验；统一在导出前由 `validation.py` 校验并给出中文错误。

## 实体 2：导出任务 ExportJob（运行期，不持久化）

一次点击导出 = 一个 ExportJob，由 `grouping.py` 构建、模态 Operator 消费。

| 属性 | 含义 |
|---|---|
| settings | 本次使用的 UnityFBXSettings 快照引用 |
| groups | `list[ExportGroup]`，导出顺序即列表顺序 |
| skipped | `list[SkippedItem]`：被过滤/跳过对象及原因 |
| warnings | `list[str]`：文件名替换、多集合重复导出等提示 |
| state | 状态机当前值（见下） |
| completed_count | 已完成文件数 |

### 状态机

```text
INITIALIZED → VALIDATING → READY → EXPORTING ──全部成功──→ COMPLETED
                  │                          │
                  └─校验失败→ FAILED         └─ESC/异常→ CANCELLING → CANCELLED
```

- VALIDATING 失败：不产生任何文件，直接 FAILED，消息中文展示；
- CANCELLING：在当前单个文件导出完成后停止排队（不强行中断 FBX 写出，避免半成品），
  finally 还原选择状态；
- COMPLETED/CANCELLED 都输出结果报告（成功数、跳过数、警告）。

## 实体 3：导出分组 ExportGroup（运行期）

| 字段 | 含义 |
|---|---|
| source_name | 源名称：物体名 / 集合名 / 用户填写的合并名 |
| objects | 组内物体列表（单文件内去重；同一物体可出现在不同组——澄清 Q4） |
| target_filename | 经命名规则计算后的最终文件名（含冲突序号，不含目录） |

三种模式的构建规则：

- OBJECT：每个选中（且通过过滤）的物体一个 group，source_name = 物体名；
- COLLECTION：按 R5 集合归属算法聚合，source_name = 集合名；无集合物体进 skipped；
- COMBINED：全部通过过滤的物体一个 group，source_name = combined_name。

## 实体 4：命名规则 NamingRule（纯函数，无状态）

输入：source_name、prefix、suffix、目标目录、会话内已用文件名集合。

处理顺序：

1. 非法字符（`\ / : * ? " < > |` 与控制符）→ `_`；空格、中文保留；
2. 组合 `base = prefix + cleaned_name + suffix`，空串兜底为 `export`；
3. 磁盘已存在或会话内已占用 → 末尾追加 `_1`、`_2` …（澄清 Q3）；
4. 输出 `target_filename`，若发生过清洗或加序号，同步产生一条 warning。

## 实体 5：跳过项 SkippedItem（运行期）

| 字段 | 含义 |
|---|---|
| object_name | 物体名 |
| reason_code | 枚举：`NON_MESH`/`NO_COLLECTION`/`EMPTY_COLLECTION` |
| reason_text | 固定中文文案（消息目录） |

## 关系总览

```text
UnityFBXSettings (持久)
        │ 导出点击时读取
        ▼
validation 校验 ──失败──► ExportError(中文消息)
        │ 通过
        ▼
grouping 构建 ExportJob（含 ExportGroup[]、SkippedItem[]）
        │
        ▼
naming 为每个 group 计算 target_filename（读写会话占用集）
        │
        ▼
exporter 逐 group：选择快照→临时选择→FBX 导出→finally 还原
        │
        ▼
结果报告（成功数/跳过数/警告）写回 UI
```
