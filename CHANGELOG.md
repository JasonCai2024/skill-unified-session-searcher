# Changelog

本文件记录 `skill-unified-session-searcher` 的所有用户可见变更。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增
- 待补充后续规划功能（如嵌入式语义向量检索集成）

## [1.0.0] - 2026-10-04

### 新增
- **初始版本发布**：构建跨四大 AI 编程工具的高级统一检索门面技能 `skill-unified-session-searcher`。
- **核心检索脚本 (`scripts/search_session.py`)**：
  - 实现双轨协同调度路由器（知识库元数据快轨 + 底层定位器物理穿透深轨）。
  - 支持多维参数正交组合过滤：`--keyword`, `--tool`, `--status`, `--workspace`, `--pattern`, `--time`, `--after`, `--before`, `--limit`, `--json`。
  - 实现基于 `(tool, session_id)` 的全局去重与启发式五维加权打分模型。
  - 支持自然语言相对时间解析（如“最近3个月”、“昨天”）。
  - 支持直观 Markdown 表格渲染、关键原句摘录与标准 JSON 输出。
- **架构与语法规格文档**：
  - 编写 `references/architecture.md`（详述系统分层架构与双轨路由机制）。
  - 编写 `references/query_syntax.md`（完整 CLI 参数表、P01~P09 模式代码对照与 JSON Schema）。
- **标准交付组件**：
  - 编写符合规范的 `SKILL.md`，兼容 Claude Code 与 SkillHub 双元数据。
  - 编写包含 7 大核心要素的根目录 `README.md`。
  - 提供环境配置模版 `.env.example` 与安全规则 `.gitignore`。

[Unreleased]: https://github.com/JasonCai2024/skill-unified-session-searcher
[1.0.0]: https://github.com/JasonCai2024/skill-unified-session-searcher/releases/tag/v1.0.0
