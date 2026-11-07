# Quickstart: 端到端验证指南

**Feature**: 001-unity-fbx-exporter | **Date**: 2026-11-07

本指南验证 spec 中全部用户故事与成功标准（SC-001~SC-006）。分三层：
① 无头冒烟（命令行，开发期反复跑）→ ② Blender 内手动验收 → ③ Unity 项目导入验收。

## 前置条件

- Blender 4.2 LTS 已安装；记下可执行文件路径，例如：
  `C:\Program Files\Blender Foundation\Blender 4.2\blender.exe`
- 插件以开发模式可用：仓库目录已通过 junction 链接到
  `%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons\unity_fbx_exporter`
- （第三层）一个新建的空白 Unity 项目（URP 或 Built-in 均可），用于导入验收

## 第一层：无头冒烟测试

在仓库根目录执行（把路径换成你机器上的 blender.exe）：

```powershell
& "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" --background --python tests/smoke_test.py
```

脚本自建临时场景并断言，覆盖：

1. naming：非法字符替换、前后缀拼接、重名序号 `_1/_2` 位置（澄清 Q3）；
2. validation：空选择、坏目录、COMBINED 空名全部抛 ExportError 且文案为中文；
3. grouping：OBJECT / COLLECTION / COMBINED 三模式分组数量与成员；
   嵌套集合归并、多集合链接物体跨组重复（澄清 Q4）、无集合物体跳过；
4. only_meshes：LIGHT/CAMERA/普通 EMPTY 被跳过、集合实例保留（澄清 Q2）；
5. exporter：三种模式实际导出 FBX，断言文件数、文件名、选择状态还原。

**预期结果**：进程退出码 0，控制台最后一行打印 `SMOKE TEST PASSED`。

## 第二层：Blender 内手动验收

新建测试场景 `test_scene.blend`（与 spec Edge Cases 对齐）：

- 3 个独立物体：Cube、Cylinder、一个带镜像+细分修改器的物件；
- 集合 A（含 2 物体）、集合 B（含 1 物体 + 嵌套子集合 B_Sub 含 1 物体）；
- 1 个同时链接进 A、B 的物体；
- 灯光、相机、普通 EMPTY、一个集合实例各 1 个；
- 1 个名字含 `*` 和空格的物体，如 `bolt* final`。

| 编号 | 操作 | 预期 |
|---|---|---|
| V1 | 不选物体点导出 | 红色 ERROR 提示"请先选择至少一个物体"，无文件产生（FR-008） |
| V2 | 选 3 物体，OBJECT 模式导出 | 3 个 FBX，各含 1 物体；状态栏报告成功 3 个（US1） |
| V3 | 选集合 A/B 相关物体，COLLECTION 模式 | A、B 两个 FBX；B 文件含 B_Sub 后代；多链接物体在两文件中都存在；无集合物体被跳过并计数（US2、澄清 Q1/Q4） |
| V4 | COMBINED 模式，文件名为空 | 提示"合并文件名不能为空"（US3） |
| V5 | 填名 `engine_parts` 后导出 | 仅 1 个 engine_parts.fbx，含全部选中物体，相对位置不变 |
| V6 | 前缀 `SM_` 后缀 `_v1`，重复导出两次 | 第二次产出 `SM_bolt_v1_1.fbx` 序号文件（FR-012、澄清 Q3） |
| V7 | only_meshes 开/关各导一次 | 开：灯光相机普通 EMPTY 跳过且报告计数，集合实例保留；关：按原生行为（FR-006、澄清 Q2） |
| V8 | apply_transform 开，对非均匀缩放物体导出后 Ctrl+Z | 导出成功；撤销后物体缩放恢复导出前值（FR-011、US6） |
| V9 | 导出前后观察选择状态 | 选中集合与活动物体完全一致（FR-010） |
| V10 | 输出目录填一个不存在路径 | 自动创建成功；若无权限则中文报错且无半成品（FR-008） |
| V11 | 点"打开输出目录" | 系统文件管理器打开该目录（FR-009） |
| V12 | 保存场景重开 | 目录与全部开关恢复（FR-007） |
| V13 | 复制 50 个物体批量导出 | 界面不卡死，有进度提示，可 ESC 取消并报告已完成数（SC-006、R7） |

## 第三层：Unity 导入验收（M6）

1. 把 V2/V3/V5 产出的 FBX 拖入 Unity 项目 `Assets/ImportTest/`；
2. 选中每个 FBX 检查 Inspector：
   - 轴向无 90° 偏差，拖入场景后正面朝向正确（-Z forward）；
   - Scale Factor 为 1，物体不巨大化/微小化（FR-002、SC-002）；
3. 带修改器物体：网格形态为修改器计算后结果（FR-005）；
4. apply_transform 导出件：Transform 缩放为 (1,1,1)（FR-004）；
5. 集合实例导出件：实例化的集合资产完整可见（澄清 Q2）。

## 验收通过标准

- 第一层：`SMOKE TEST PASSED`；
- 第二层：V1-V13 全部符合预期，无控制台未捕获异常；
- 第三层：5 项检查全部通过；
- 对应 SC-001（30 秒内完成操作）、SC-003（5 分钟盲测）在 M6 邀请一位非开发者现场盲测记录。
