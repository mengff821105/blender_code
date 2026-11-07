# Tasks: Blender 到 Unity 批量 FBX 导出插件

**Input**: Design documents from `/specs/001-unity-fbx-exporter/`

**Prerequisites**: plan.md、spec.md、research.md、data-model.md、contracts/operator-contract.md、quickstart.md

**Tests**: plan.md R10 与 quickstart 已明确要求无头冒烟测试，故包含测试任务（`tests/smoke_test.py`，`blender --background` 运行，无第三方框架）。

**Organization**: 按 spec 的 6 个用户故事分阶段，每阶段可独立验收。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、不依赖未完成任务）
- **[Story]**: US1-US6 对应 spec.md 用户故事；Setup/Foundational/Polish 阶段不带 Story 标签
- 每个任务控制在 1 个晚上（约 2-3 小时）内；完成即按 Conventional Commits 提交并在本文件勾选

## Path Conventions

- 插件代码：仓库根 `unity_fbx_exporter/`
- 规格文档：`specs/001-unity-fbx-exporter/`
- 测试：仓库根 `tests/smoke_test.py`

## 已完成基线（M1 骨架，不在下方任务内）

- [x] 五文件骨架：`__init__.py` / `properties.py` / `exporter.py`（占位）/ `operators.py` / `panel.py`
- [x] UnityFBXSettings 八项设置挂 Scene PointerProperty，场景保存重开持久化（FR-007 基础）
- [x] N 面板 UnityFBX 标签、导出/打开目录两个 Operator 注册名
- [x] junction 开发链接到 Blender 4.2 addons 目录

---

## Phase 1: Setup（共享基础设施）

**Purpose**: 测试引导与面板契约对齐

- [ ] T001 创建 `tests/` 目录与 `tests/smoke_test.py` 骨架：文件头部把仓库根加入 `sys.path`，以 `from unity_fbx_exporter import ...` 形式导入，不依赖 addons 安装状态；末尾定义 `SMOKE TEST PASSED` 输出与非零退出码约定（plan F4 修复项）
- [ ] T002 [P] 按 contracts §2 核对 `unity_fbx_exporter/panel.py` 现有控件：分区标题（输出/导出模式/命名/选项）、中文标签与 description 悬停文案、COMBINED 时才显示 combined_name；不符之处就地修正

---

## Phase 2: Foundational（阻塞性基础，M2）

**Purpose**: 错误体系、消息目录、命名规则、版本门、纯函数测试。本阶段完成前不得进入用户故事实现。

**⚠️ CRITICAL**: 全部用户故事依赖本阶段的 validation/naming 模块

- [ ] T003 创建 `unity_fbx_exporter/validation.py`：定义 `class ExportError(Exception)`，并按 contracts §3 建立全部 11 条消息常量（MSG_NO_SELECTION … MSG_VERSION_MISMATCH），核心模块只抛 ExportError 不接触 UI
- [ ] T004 [P] 在 `validation.py` 实现 `validate_selection(objects, settings)`：空选择抛 MSG_NO_SELECTION、过滤后为空抛 MSG_NO_VALID_OBJECT
- [ ] T005 [P] 在 `validation.py` 实现 `validate_output_path(path, scene)`：`bpy.path.abspath` 解析；场景未保存且为相对路径时抛 MSG_PATH_RELATIVE_UNSAVED；目录不存在时尝试创建，失败抛 MSG_PATH_NOT_WRITABLE（research R9）
- [ ] T006 [P] 在 `validation.py` 实现 `validate_combined_name(settings)`：COMBINED 模式下名称清洗后为空时抛 MSG_COMBINED_NAME_EMPTY（data-model F6 顺序约定：validation 先于 naming 兜底）
- [ ] T007 [P] 创建 `unity_fbx_exporter/naming.py` 实现 `sanitize_filename(name)`：`\ / : * ? " < > |` 与控制符替换为 `_`，空格与中文保留（research R8）
- [ ] T008 在 `naming.py` 实现 `build_filename(source, prefix, suffix, output_dir, used_names)`：拼接 prefix+清洗名+suffix，源名为空兜底 `export`；会话占用集 + 磁盘现状双重去重，序号 `_1/_2` 固定追加在完整文件名最末尾（FR-012、澄清 Q3），返回 (文件名, 警告列表)
- [ ] T009 在 `unity_fbx_exporter/__init__.py` 的 `register()` 加入版本门：`bpy.app.version < (4, 2, 0)` 时抛 RuntimeError 引用 MSG_VERSION_MISMATCH（FR-013 双保险第二道，contracts §3 备注）
- [ ] T010 在 `tests/smoke_test.py` 编写命名与校验断言：非法字符替换、`SM_bolt_v1_1.fbx` 序号位置、空选择/坏目录/空合并名均抛 ExportError 且文案为中文
- [ ] T011 运行 `blender --background --python tests/smoke_test.py`，确认输出 `SMOKE TEST PASSED` 且退出码 0；修复全部失败后提交，M2 结束

**Checkpoint**: 纯逻辑层可脱离 UI 独立验证，用户故事可以开始

---

## Phase 3: User Story 1 - 按物体批量导出（Priority: P1）🎯 MVP（M3）

**Goal**: 选中物体逐个导出 Unity 参数正确的 FBX，选择状态原样还原

**Independent Test**: 选中 1 个 Cube 导出成功并通过 Unity 导入轴向/缩放检查；quickstart V2、V8、V9

- [ ] T012 [US1] 改造 `unity_fbx_exporter/exporter.py`，实现 `export_group(group, filepath, settings, context)`：按 contracts §5 固定传参调用 `bpy.ops.export_scene.fbx`（axis_forward='-Z'、axis_up='Y'、apply_unit_scale=True、global_scale=1.0、add_leaf_bones=False、use_selection=True）
- [ ] T013 [US1] 在 `exporter.py` 实现选择快照/还原：记录 `context.selected_objects` 与 `active_object`，全函数 try/finally 还原，所有退出路径共用同一还原函数（FR-010、contracts §6）
- [ ] T014 [US1] 在 `exporter.py` 实现 Apply Transform 分支：settings.apply_transform 为真时对组内物体执行 `bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)`，依赖 Operator 调用天然进入撤销栈（FR-011、research R4）
- [ ] T015 [US1] 在 `exporter.py` 接线修改器与过滤参数：use_mesh_modifiers 跟随 apply_modifiers；object_types 在 only_meshes 开时为 `{'MESH','EMPTY'}`、关时为默认全集（FR-005/006、contracts §5）
- [ ] T016 [US1] 改造 `unity_fbx_exporter/operators.py` 的 `UNITYFBX_OT_export`：同步形态串联 validate → 单组导出 → report，捕获 ExportError 输出中文 ERROR；删除原占位 ExportError 抛出
- [ ] T017 [US1] 在 `tests/smoke_test.py` 增加 OBJECT 模式断言：单 Cube 导出文件存在、文件名正确、导出后选择集合与活动物体不变
- [ ] T018 [US1] 手动 + Unity 验收：Blender 内 V2/V9；新建空白 Unity 项目导入 FBX，验证 -Z/Y 轴向、Scale Factor=1；用非均匀缩放物体执行 research R2 遗留的双烘焙验证，若有偏差按预案把该开关下 bake_space_transform 改 False 并回写 research.md

**Checkpoint**: US1 独立可用，MVP 成立

---

## Phase 4: User Story 2 - 按集合批量导出（Priority: P1）（M4 上半）

**Goal**: 选中物体反查集合分组，每集合一个自包含 FBX

**Independent Test**: quickstart V3 全项；嵌套集合、多集合链接、无集合物体跳过

- [ ] T019 [P] [US2] 创建 `unity_fbx_exporter/grouping.py`：按 data-model 定义 ExportGroup、SkippedItem、ExportJob 数据结构与状态字段（groups/skipped/warnings/state/completed_count），不 import 任何 UI 模块
- [ ] T020 [US2] 在 `grouping.py` 实现 `build_object_groups(objects, settings)`：OBJECT 模式每物体一个 ExportGroup，单文件内去重
- [ ] T021 [US2] 在 `grouping.py` 实现 `build_collection_groups(objects, settings)`：基于 `obj.users_collection` 反查归属，递归 `collection.children` 让父集合包含全部后代；无集合物体进 skipped（reason_code=NO_COLLECTION）；空集合进 skipped（EMPTY_COLLECTION）（research R5、澄清 Q1）
- [ ] T022 [US2] 在 T021 内实现多集合链接规则：物体进入每个所属集合的分组，跨文件允许重复、单文件不重复，重复导出次数写入 Job.warnings（澄清 Q4）
- [ ] T023 [P] [US2] 在 `grouping.py` 实现 `filter_objects(objects, settings)`：only_meshes 开时保留 MESH 与 `instance_type=='COLLECTION'` 的 EMPTY，跳过 LIGHT/CAMERA/普通 EMPTY 并生成 SkippedItem（NON_MESH）（research R6、澄清 Q2）
- [ ] T024 [US2] 在 `operators.py`/`exporter.py` 打通 COLLECTION 管线：分组 → naming 计算文件名 → 逐组 export_group，汇总 skipped 与 warnings
- [ ] T025 [US2] 在 `tests/smoke_test.py` 构建集合夹具（A、B、B_Sub 嵌套、多链接物体、无集合物体、空集合、灯光/相机/EMPTY/集合实例），断言分组数量、成员归属、跳过计数与集合实例保留

**Checkpoint**: US1 与 US2 均可独立工作

---

## Phase 5: User Story 3 - 合并为单个 FBX（Priority: P2）（M4 下半）

**Goal**: 全部选中物体打包一个文件，文件名用户必填

**Independent Test**: quickstart V4、V5

- [ ] T026 [US3] 在 `grouping.py` 实现 `build_combined_group(objects, settings)`：全部通过过滤的物体进一个 ExportGroup，source_name 取 combined_name；空名依赖 T006 的 validation 先拦截
- [ ] T027 [US3] 在 `operators.py` 接线 COMBINED 分支（含 validate_combined_name 调用顺序），确认 `panel.py` 仅该模式显示文件名输入框
- [ ] T028 [US3] 在 `tests/smoke_test.py` 断言：合并只产出 1 个 FBX、含全部物体、空名时抛 MSG_COMBINED_NAME_EMPTY

**Checkpoint**: 三种导出模式全部贯通

---

## Phase 6: User Story 4 - 命名与导出选项控制（Priority: P2）

**Goal**: 前后缀、三个开关、非法字符与重名规则全模式生效并产出警告

**Independent Test**: quickstart V6、V7

- [ ] T029 [P] [US4] 按 contracts §2 完善 `properties.py` 各字段 description 中文悬停说明，核对 `panel.py` 前缀/后缀同行布局与三个开关顺序
- [ ] T030 [US4] 在导出管线统一接入 naming.build_filename：三种模式全部走同一命名入口，sanitize/序号产生的警告收集进 Job.warnings（MSG_FILENAME_SANITIZED、MSG_DUPLICATE_NUMBERED）
- [ ] T031 [US4] 在 `tests/smoke_test.py` 断言命名矩阵：`bolt* final` 清洗结果、前缀 `SM_`+后缀 `_v1`、同目录二次导出产生 `SM_bolt_v1_1.fbx`
- [ ] T032 [US4] 手动验收 V7：only_meshes 开/关各导出一次，核对跳过报告计数与集合实例保留行为

**Checkpoint**: 产物命名与过滤行为可预测、有提示

---

## Phase 7: User Story 5 - 输出目录管理与错误反馈（Priority: P2）

**Goal**: 目录记忆、全部异常中文提示、结果报告、打开目录

**Independent Test**: quickstart V1、V10、V11、V12

- [ ] T033 [P] [US5] 验证并补强设置持久化：保存重开场景后 export_path 与全部开关恢复（V12）；在 `properties.py` 补齐默认值 `//FBX_Export/` 的相对路径说明
- [ ] T034 [US5] 在 `operators.py`/`exporter.py` 实现结果汇总：按 MSG_EXPORT_REPORT 格式输出成功数/跳过数/警告数；在 `panel.py` 增加本次会话摘要区（成功文件超 10 个折叠为"等 N 个文件"，contracts §4）
- [ ] T035 [US5] 落地 T005 的目录策略到导出主流程：自动创建目录、无权限时安全中止且无半成品文件（V10）
- [ ] T036 [US5] 加固 `UNITYFBX_OT_open_folder`：`bpy.ops.wm.path_open` 调用，目录不存在时报 MSG_PATH_NOT_WRITABLE 同级中文提示（research R12、V11）
- [ ] T037 [US5] 在 `tests/smoke_test.py` 补异常断言：未选物体、不可写目录、未保存场景相对路径三种场景均抛 ExportError 且无文件产生

**Checkpoint**: 异常路径全部有人话提示，正常路径有完整报告

---

## Phase 8: User Story 6 - 撤销与场景安全（Priority: P3）（M5）

**Goal**: 模态批量调度不卡界面、可取消、场景零污染

**Independent Test**: quickstart V8、V13；50 物体响应性

- [ ] T038 [US6] 把 `UNITYFBX_OT_export` 改造为模态 Operator：execute 内构建 ExportJob 队列后返回 RUNNING_MODAL，modal 用 timer 事件每次处理一个 group，`window_manager.progress_begin/update` 显示进度（research R7、data-model 状态机）
- [ ] T039 [US6] 实现取消语义：ESC 置 CANCELLING，当前单个文件导出完成后停止排队，finally 还原选择，报告 MSG_EXPORT_CANCELLED 与已完成数；禁止强行中断 FBX 写出
- [ ] T040 [US6] 场景安全核查：确认 transform_apply 可 Ctrl+Z（V8）、插件不创建持久 datablock、模态结束释放 Job 引用；在 `exporter.py` 统一还原函数上做全退出路径走查
- [ ] T041 [US6] 50 物体批量导出实测 V13：界面保持可响应、进度可见、ESC 可取消，记录耗时与现象到 `unity_fbx_exporter/开发笔记.md`

**Checkpoint**: 全部用户故事功能完整且场景安全

---

## Phase 9: Polish & Cross-Cutting Concerns（M6 打包验收）

**Purpose**: 正式交付形态与端到端验收

- [ ] T042 [P] 打包验收：移除 junction 后用 zip 正式安装，执行启用/禁用/卸载全流程，确认无残留报错（quickstart 前置、宪法原则 III）
- [ ] T043 [P] 编写插件 `unity_fbx_exporter/README.md`：安装步骤、界面说明、兼容版本 Blender 4.2+、三种模式用法、已知限制（非目标 glTF/多预设/云同步）
- [ ] T044 全量手动回归 quickstart V1-V14：逐项记录结果；V14 秒表计时填入实测值（SC-001）；安排一次非开发者盲测记录 5 分钟首次导出（SC-003）
- [ ] T045 Unity 空白项目第三层验收：5 项检查（轴向、Scale Factor=1、修改器结果、apply_transform 后缩放 (1,1,1)、集合实例完整），截图或记录存入 `specs/001-unity-fbx-exporter/` 验收记录
- [ ] T046 终验与收尾：无头冒烟全绿；`bl_info` 版本定 0.1.0；更新 `开发笔记.md`；对照 spec FR-001~FR-013 与 SC-001~SC-006 逐条勾选，准备 `/speckit.converge`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1（Setup）：无依赖，立即开始
- Phase 2（Foundational）：依赖 T001；阻塞全部用户故事
- Phase 3（US1，MVP）：依赖 Phase 2，无其他故事依赖
- Phase 4（US2）：依赖 Phase 2 与 T013（选择还原）；T019/T023 可与 US1 后期并行
- Phase 5（US3）：依赖 Phase 2 与 grouping 基础 T019
- Phase 6（US4）：依赖 naming（T007/T008）与三模式管线（T024/T027）
- Phase 7（US5）：依赖 validation（T004-T006）与报告数据源
- Phase 8（US6）：依赖全部功能管线就位后再做模态化
- Phase 9（Polish）：所有目标故事完成后执行

### User Story Dependencies

- US1（P1）：Foundational 后即可启动，是 MVP
- US2（P1）：复用 US1 的 export_group 与选择还原，分组逻辑独立可先行编写
- US3（P2）：复用同一导出管线，仅新增一种分组
- US4（P2）：横切命名与开关，依赖三模式存在
- US5（P2）：横切校验与报告，validation 已在基础层就位
- US6（P3）：最后做，把同步管线升级为模态，不改变既有功能契约

### Parallel Opportunities

- T002 与 T001 不同文件可并行
- T004/T005/T006（validation 不同函数）与 T007（naming）可并行
- T019（grouping 数据结构）、T023（filter_objects）可与 US1 的 T012-T015 并行
- T029（properties/panel 文案）与 T033（持久化核查）可并行
- T042/T043 可并行

---

## Parallel Example: Phase 2 基础层

```text
并行批次 A：T003（消息目录）先行
并行批次 B：T004 + T005 + T006 + T007（不同函数/文件）
串行收口：T008（依赖 T007）→ T009（依赖 T003）→ T010（依赖全部）→ T011
```

---

## Implementation Strategy

### MVP First（仅 User Story 1）

1. 完成 Phase 1 + Phase 2
2. 完成 Phase 3（US1）并停下来独立验证：单物体导出 + Unity 导入正确
3. 此时产品已具备核心价值，可录制第一条开发日志视频

### Incremental Delivery

1. 基础层 → US1（MVP，能用）
2. US2 + US3（三种模式齐活）
3. US4 + US5（专业度：命名、过滤、报告、错误处理）
4. US6（模态化，解决大批量体验）
5. Polish（打包、文档、全量验收）
6. 每个阶段结束跑一次无头冒烟，保证旧功能不回归

### 里程碑映射

| 里程碑 | 任务范围 | 预计晚上数 |
|---|---|---|
| M2 | T001-T011 | 2 |
| M3 | T012-T018 | 2 |
| M4 | T019-T032 | 3 |
| M5 | T033-T041 | 2 |
| M6 | T042-T046 | 2 |

---

## Notes

- [P] 任务 = 不同文件、无未完成依赖；个人开发时"并行"指同一晚上可自由切换，不要求真并发
- 每完成一个任务：勾选复选框 + 一次 git 提交，信息含任务号（如 `feat(validation): T005 output path checks`）
- 实现中发现规格漏洞：先改 spec/plan/contracts 再写代码（宪法原则 I），并在 commit message 注明文档变更
- 避免：模糊任务、同文件冲突、破坏故事独立性的跨故事依赖
