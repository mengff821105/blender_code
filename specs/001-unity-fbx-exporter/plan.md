# Implementation Plan: Blender 到 Unity 批量 FBX 导出插件

**Branch**: `001-unity-fbx-exporter` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-unity-fbx-exporter/spec.md`

## Summary

在已有的五文件插件骨架（`unity_fbx_exporter/`，骨架里程碑已完成）上实现一个 Blender 4.2 LTS
插件：用户选中物体后，以"每个物体 / 每个集合 / 合并为一个"三种模式批量导出符合 Unity 坐标
约定（-Z forward, Y up）的 FBX。技术路线是调用 Blender 官方内置 FBX 导出器
（`bpy.ops.export_scene.fbx`），通过临时选择覆盖（context override）逐组导出，用模态
Operator 串行调度保证大批量时界面可响应，所有设置通过 Scene 级 PropertyGroup 持久化。

## Technical Context

**Language/Version**: Python 3.11（Blender 4.2 LTS 内置发行版，不依赖系统 Python）

**Primary Dependencies**: 仅 Blender 官方内置模块：`bpy`、`bpy.ops.export_scene.fbx`、
`bpy.path`；标准库 `os`、`re`、`pathlib`。不引入任何第三方包。

**Storage**: 无独立数据库。用户设置存于 Scene 级 PointerProperty（随 .blend 场景保存）；
导出产物为用户指定目录下的 FBX 文件。

**Testing**: 两层验证——① `tests/smoke_test.py` 无头冒烟脚本，用
`blender --background --python tests/smoke_test.py` 跑通三种模式与主要边界；
② `quickstart.md` 中的手动验收（含真实 Unity 项目导入验证）。v1 不引入 pytest 等框架。

**Target Platform**: Blender 4.2 LTS 及以上（Windows 优先，macOS/Linux 仅用跨平台 API）；
导出文件面向官方支持期内的 Unity LTS。

**Project Type**: Blender 编辑器插件（desktop add-on），多文件 Python 包。

**Performance Goals**: 50 个物体规模的批量导出过程中界面保持可响应（模态调度，每事件
导出一个文件）；单文件导出耗时等于官方 FBX 导出器原生耗时，插件本身不增加可感知开销。

**Constraints**: 离线运行、无网络请求；只使用官方稳定 API；插件禁用/卸载无残留报错；
内存中不保留场景数据副本，导出结束即释放临时状态。

**Scale/Scope**: 单场景单次导出对象上限按 50 个物体/集合设计并验证；设置项 10 个以内；
对外 Operator 2 个（export、open_folder）、面板 1 个。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 宪法原则 | 本计划的落实方式 | 结论 |
|---|---|---|
| I. 规格优先 | 本计划严格映射 spec.md 的 FR-001~FR-013，4 项澄清结论全部进入研究决策 | PASS |
| II. 个人设备与合规边界 | 选题为通用 3D 管线工具，与汽车/雇主业务零关联；无公司资产、无网络功能 | PASS |
| III. LTS 兼容基线 | 最低版本 Blender 4.2 LTS，仅用官方稳定 API，`bl_info` 声明版本范围 | PASS |
| IV. 分层与低维护架构 | properties / naming+validation / exporter 核心 / operators / panel 分层；核心逻辑不 import 任何 UI 模块，可被无头脚本直接调用 | PASS |
| V. 可独立验证的增量交付 | 6 个里程碑，每个任务 ≤1 个晚上；每任务一次 Conventional Commit；无头脚本支持反复验证 | PASS |
| VI. 防御式错误处理 | 统一 `ExportError` + 中文消息目录；导出前校验；try/finally 还原选择；模态支持 ESC 取消 | PASS |

无违例项，Complexity Tracking 表不填写。

## Project Structure

### Documentation (this feature)

```text
specs/001-unity-fbx-exporter/
├── spec.md              # 已完成（含 4 项澄清）
├── plan.md              # 本文件
├── research.md          # Phase 0：技术决策
├── data-model.md        # Phase 1：实体与状态
├── quickstart.md        # Phase 1：端到端验证指南
├── contracts/
│   └── operator-contract.md   # Operator/面板/中文消息契约
├── checklists/
│   └── requirements.md  # 已完成
└── tasks.md             # /speckit.tasks 产出（本命令不创建）
```

### Source Code (repository root)

```text
unity_fbx_exporter/
├── __init__.py          # bl_info、注册顺序（已存在，按需调整）
├── properties.py        # UnityFBXSettings PropertyGroup（已存在，按数据模型补字段）
├── naming.py            # 【新增】非法字符清洗、前后缀拼接、重名序号
├── validation.py        # 【新增】选中对象/目录/文件名/版本校验，ExportError 与消息目录
├── grouping.py          # 【新增】三种模式的分组逻辑（物体/集合/合并），纯函数可无头测试
├── exporter.py          # 【改造】单组 FBX 导出 + 选择快照/还原 + Apply Transform
├── operators.py         # 【改造】导出模态 Operator（进度/取消）、打开目录
├── panel.py             # 【改造】按契约渲染设置与状态提示
└── 开发笔记.md           # 过程笔记（非交付物）

tests/
└── smoke_test.py        # 无头冒烟脚本：建临时场景 → 分组 → 导出 → 断言文件与内容
```

**Structure Decision**: 沿用已建立的单插件多文件包结构，把原计划塞进 `exporter.py` 的
命名、校验、分组三类纯逻辑拆成独立模块（`naming.py`/`validation.py`/`grouping.py`），
它们不依赖 `bpy.ops`，可在无头脚本中直接断言，满足宪法原则 IV 的"核心可脱离界面验证"。
`tests/` 目录与 `tests/smoke_test.py` 在 M2 第一个任务中显式创建；脚本头部负责把仓库根
目录加入 `sys.path` 并以包形式 import（`from unity_fbx_exporter import grouping ...`），
不依赖 Blender 的 addons 安装状态，保证后台模式可独立运行。

## Milestones

> M1 骨架已完成并提交；M2-M6 每个对应约 1 个晚上（2-3 小时），任务编号在 tasks.md 展开。

| 里程碑 | 目标 | 验收条件（映射 spec） |
|---|---|---|
| M1 骨架（已完成） | 五文件结构、设置项、面板可显示并持久化 | 设置保存重开仍在；插件可启用禁用 |
| M2 命名与校验基础 | naming.py + validation.py + ExportError 消息目录 + register() 版本门 | 无头脚本断言：非法字符替换、重名序号、空选择/坏目录被拦截；低版本 Blender 启用时被版本门拦截（FR-008/FR-012/FR-013） |
| M3 单物体导出闭环 | exporter.py 单组导出 + Unity 预设 + 选择快照还原 | 选中 1 个 Cube 导出 FBX，选择状态不变；Unity 导入轴向/缩放正确（FR-002/FR-010，US1） |
| M4 三种分组模式 | grouping.py + 三种模式贯通 + 前后缀 + 网格过滤 + 集合实例例外 | 无头脚本覆盖三模式、嵌套集合、多集合链接、空物体跳过（FR-001/003/006，US1-3） |
| M5 模态调度与场景安全 | 模态 Operator、进度报告、ESC 取消、Apply Transform 可撤销、打开目录 | 50 物体导出界面不卡死；撤销生效；异常全中文提示（FR-004/005/009/011，US5-6） |
| M6 打包与端到端验收 | zip 正式安装、README、Unity 空项目全量验收 | quickstart 全部场景通过，SC-001~SC-006 达标 |

## Phase 0/1 产出索引

- 技术决策与备选方案：见 [research.md](research.md)
- 实体、字段、状态机：见 [data-model.md](data-model.md)
- Operator/面板/消息契约：见 [contracts/operator-contract.md](contracts/operator-contract.md)
- 端到端验证步骤：见 [quickstart.md](quickstart.md)
