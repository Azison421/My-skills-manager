# Claude Code 技能仓库

按用途分类管理所有技能，帮助 Agent 快速找到合适的工具。

## 分类总览

| 分类 | 技能数 | 说明 |
|------|--------|------|
| [UI设计](ui-design/README.md) | 7 | 视觉设计、品牌标识、UI组件、设计系统。 |
| [办公套装](office-suite/README.md) | 4 | 文档处理：Word、PDF、PowerPoint、Excel。 |
| [写作套装](writing/README.md) | 2 | 写作辅助与中文文本编辑。 |
| [开发流程](dev-workflow/README.md) | 6 | 规划、架构评审、TDD、Issue管理。 |
| [工具与自动化](tools/README.md) | 3 | 技能发现、浏览器自动化、技能创建。 |

## 运作机制

- 每个分类文件夹包含用途相近的技能，方便 Agent 按需检索。
- 新技能放入 `skills/` 根目录后，下次启动 Claude Code 时会自动归类到对应文件夹。
- 无法自动归类的技能会被放入 `_uncategorized/`，等待人工审核。
- 手动运行 `python scripts/categorize.py` 可立即触发归类。

## 快速查找

| 需求 | 去这里 |
|------|--------|
| 设计UI、Banner、Logo 或品牌 | [UI设计](ui-design/README.md) |
| 创建或编辑 Word/PDF/PPT/Excel 文件 | [办公套装](office-suite/README.md) |
| 写作文档、去除AI写作痕迹 | [写作套装](writing/README.md) |
| 架构规划、TDD、创建Issue/PRD | [开发流程](dev-workflow/README.md) |
| 浏览器自动化、发现/创建技能 | [工具与自动化](tools/README.md) |

---
*由 `scripts/categorize.py` 自动生成*
