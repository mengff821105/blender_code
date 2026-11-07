# Research: 技术决策记录

**Feature**: 001-unity-fbx-exporter | **Date**: 2026-11-07

每条决策按 Decision / Rationale / Alternatives 记录，供 tasks 阶段直接引用。

## R1. 导出通道：官方内置 FBX 导出器

- **Decision**: 使用 `bpy.ops.export_scene.fbx(filepath=..., use_selection=True, ...)`，逐组临时选择后导出。
- **Rationale**: FBX IO 是 Blender 官方随附组件，4.2 LTS 稳定支持；它已经处理好 FBX SDK 封装、
  材质与骨骼的边界情况，自己写二进制 FBX 不现实。加 `use_selection=True` 可以让一个场景里
  只导出当前选中对象，天然适配"逐组导出"。
- **Alternatives**:
  - 第三方库（如 pyfbx）：生态弱、维护不稳定，违反宪法原则 III 的稳定 API 约束，否决。
  - glTF 导出器：spec 已明确 glTF 为非目标。
  - 复制场景到临时 datablock 再全量导出：状态管理复杂、还原成本高，否决。

## R2. Unity 坐标预设参数

- **Decision**: 固定传参 `axis_forward='-Z'`、`axis_up='Y'`、`apply_unit_scale=True`、
  `global_scale=1.0`、`bake_space_transform=True`（与 Apply Transform 开关联动，见 R4）。
- **Rationale**: Unity 的坐标系是左手 -Z forward、Y up；Blender 默认导出参数在不同版本
  历史上有差异，显式传参不依赖用户默认配置，保证"一次导入无需修正"（对应 FR-002、SC-002）。
- **Alternatives**:
  - 让用户自己在导出对话框改参数：违背产品价值（消除手工重复），否决。
  - 只在文档里写推荐参数：用户漏配即产生差评，否决。

## R3. 逐组导出的上下文处理：选择快照 + 临时覆盖 + try/finally 还原

- **Decision**:
  1. 导出前记录 `[obj for obj in context.selected_objects]` 与 `context.active_object`；
  2. 每组用 `bpy.ops.object.select_all(action='DESELECT')` 后只选组内对象，设置 active；
  3. 调用 FBX 导出；
  4. `finally` 中恢复原选择集合与 active 对象。
- **Rationale**: `export_scene.fbx` 的 `use_selection` 依赖当前上下文选择，这是官方稳定路径；
  try/finally 保证出错或取消时场景状态也能还原（FR-010、US6）。
- **Alternatives**:
  - `context.temp_override(...)`：适合在 Operator 内替换上下文成员，但选择切换仍需显式做，
    收益不大；保留为实现时的可选优化，不写死。
  - 复制物体到独立临时场景导出：内存与 databound 清理风险高，50 物体规模无必要，否决。

## R4. Apply Transform 与修改器的语义

- **Decision**:
  - "导出前 Apply Transform"开启时：对组内物体执行
    `bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)`，
    该操作通过 Operator 调用自动进入 Blender 撤销栈（支持 Ctrl+Z，FR-011）；
  - "应用修改器"映射到 FBX 导出器的 `use_mesh_modifiers=True/False`，由导出器在导出数据上
    生效，不修改场景原物体。
- **Rationale**: transform_apply 是场景级持久改动，必须可撤销；修改器应用交给导出器参数，
  避免改动用户原资产，两个开关的副作用边界清晰。
- **Alternatives**:
  - 复制物体后对副本 apply：datablock 残留风险，且 FBX 导出器本身已支持修改器参数，否决。
  - 手动写矩阵烘焙：重复造轮子且易错，否决。

## R5. 集合分组算法（对应澄清 Q1、Q4）

- **Decision**:
  - 输入永远是 `context.selected_objects`；
  - 集合模式：遍历选中物体，取 `obj.users_collection` 中"最直接的用户集合"。具体规则：
    以场景视图层中该物体出现的第一个集合实例链为归属；同一物体链接到多个同级集合时，
    它进入每个所属集合的分组（允许跨文件重复、单文件去重，澄清 Q4）；
  - 父集合分组包含其全部后代物体（含嵌套子集合成员），通过集合递归 `collection.children`
    收集；
  - `obj.users_collection` 为空（仅在场景主集合之外）的物体跳过并计数提示。
- **Rationale**: 完全基于稳定的 `users_collection`/`children` API，不依赖大纲视图选择状态，
  与澄清结论一致；纯函数实现放 `grouping.py`，无头脚本可直接断言。
- **Alternatives**:
  - 读大纲视图勾选状态：API 不稳定且违反澄清 Q1 的交互约定，否决。
  - 多集合物体只归第一个集合：违反澄清 Q4 的自包含原则，否决。

## R6. 网格过滤与集合实例例外（对应澄清 Q2）

- **Decision**: 开关开启时保留 `obj.type == 'MESH'` 与 `obj.type == 'EMPTY' and
  obj.instance_type == 'COLLECTION'`；跳过 LIGHT、CAMERA、普通 EMPTY 等，跳过数计入报告。
- **Rationale**: 集合实例承载实际资产，过滤掉会导致 FBX 缺件；普通 EMPTY 无网格数据，
  按澄清结论跳过。
- **Alternatives**: 全部 EMPTY 一律跳过——会破坏集合实例工作流，已被澄清否决。

## R7. 大批量导出的响应性：模态 Operator 串行调度

- **Decision**: 导出 Operator 以 `execute` 构建任务队列后切模态（`modal`），每次 timer
  事件处理一个导出任务，期间更新 `window_manager.progress_begin/update`；支持 ESC 取消，
  取消时在 finally 中还原选择并报告已完成数量。
- **Rationale**: 50 个物体若在一个 execute 内同步执行，Blender 界面会整体卡住（违反 SC-006）；
  模态 + 单任务/事件是 Blender 官方推荐的长任务模式。
- **Alternatives**:
  - 后台线程：bpy 数据 API 非线程安全，禁止。
  - 纯同步 execute：实现简单但卡死界面，仅作为 M3 阶段的临时形态，M5 必须替换。

## R8. 文件名规则（对应澄清 Q3）

- **Decision**:
  1. 非法字符 `\\ / : * ? " < > |` 及控制符替换为 `_`；空格与中文保留；
  2. 拼接顺序固定：`前缀 + 源名称 + 后缀`；
  3. 冲突检测在**同一次导出会话内 + 目标目录磁盘现状**双重去重，序号从 `_1` 起追加在
     完整文件名最末尾（澄清 Q3），即 `SM_bolt_v1_1.fbx`。
- **Rationale**: 规则单一可预测；会话内去重防止两个同名物体互相覆盖，磁盘去重防止覆盖
  历史文件（FR-012）。
- **Alternatives**: 时间戳后缀——可读性差且 spec 假设中已排除自动时间戳命名，否决。

## R9. 设置持久化与未保存场景处理

- **Decision**: 设置挂 `bpy.types.Scene.unity_fbx_settings`（场景级，随 .blend 保存，FR-007）；
  相对路径用 `bpy.path.abspath` 解析；场景未保存且路径为相对路径时拦截，提示先保存场景
  或改用绝对路径（Edge Case 已列）。
- **Rationale**: Scene 级 PropertyGroup 是 Blender 官方持久化机制，无需自己管配置文件；
  未保存场景没有 .blend 基准路径，abspath 行为不可靠，提前拦截比静默失败好。
- **Alternatives**: addon Preferences 全局保存——无法按项目区分目录，留作 v2 多预设时再考虑。

## R10. 无头冒烟测试策略

- **Decision**: `tests/smoke_test.py` 以
  `blender --background --python tests/smoke_test.py` 运行：脚本内建临时场景（Cube、
  圆柱、带修改器物体、两层集合、多集合链接物体、灯光/相机/EMPTY/集合实例），直接调用
  `grouping`/`naming`/`validation` 纯函数与 `exporter` 核心函数，断言文件数量、命名、
  分组内容、异常消息。
- **Rationale**: 不依赖 UI 点击即可在命令行反复回归，符合宪法原则 V；Blender 后台模式
  是官方支持的测试方式，零第三方依赖。
- **Alternatives**: pytest + bpy stub——环境配置重，个人项目阶段收益不足，v2 再评估。

## R11. 错误体系与中文消息

- **Decision**: 定义 `ExportError(Exception)`，`validation.py` 维护消息常量目录
  （如 `MSG_NO_SELECTION = "请先选择至少一个物体"`）；Operator 层捕获后统一
  `self.report({'ERROR'}, ...)`，核心模块不接触 UI。
- **Rationale**: 满足宪法原则 IV（逻辑不引用界面）与原则 VI（中文可理解提示、无未捕获堆栈）。
- **Alternatives**: 核心层直接调 `self.report`——分层被破坏、无法无头测试，否决。

## R12. 打开输出目录

- **Decision**: 使用 `bpy.ops.wm.path_open(filepath=abs_path)`；目录不存在时按钮禁用或
  点击后报"目录不存在"，不尝试自动创建（创建目录只在真正导出时按需执行）。
- **Rationale**: `wm.path_open` 是跨平台官方 API，自动选择 Windows 资源管理器/macOS Finder/
  Linux 文件管理器。
