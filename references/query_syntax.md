# 统一会话多维检索语法与参数指南 (Query Syntax & Usage Guide)

## 一、 CLI 命令行完整参数说明

统一检索入口脚本：`python scripts/search_session.py [OPTIONS]`

| 参数名 | 缩写 | 类型 | 候选值 / 示例 | 默认值 | 作用说明 |
| :--- | :---: | :---: | :--- | :---: | :--- |
| `--keyword` | `-k` | `str` | `"抖音"`, `"IndexError"`, `"边栏"` | `None` | 全文搜索关键词、报错片段或代码名 |
| `--tool` | `-t` | `str` | `all`, `antigravity`, `codex`, `minimax`, `workbuddy` | `all` | 限定只查询特定 AI 编程工具 |
| `--status` | `-s` | `str` | `all`, `active`, `archived` | `all` | 限定查询活跃状态或已归档状态 |
| `--workspace`| `-w` | `str` | `"ForAgent"`, `"社交媒体"`, `"ServiceHub"` | `None` | 过滤关联的工作区路径或目录名 |
| `--pattern` | `-p` | `str` | `P01`, `P02`, `P03` ... `P09` | `None` | 过滤包含指定提示词思维模式的会话 |
| `--time` | - | `str` | `"today"`, `"yesterday"`, `"最近3天"`, `"最近3个月"` | `None` | 自然语言相对时间窗过滤 |
| `--after` | - | `str` | `2026-07-01` | `None` | 起始日期（含当天，ISO 格式） |
| `--before` | - | `str` | `2026-10-01` | `None` | 截止日期（含当天，ISO 格式） |
| `--limit` | `-n` | `int` | `5`, `10`, `20` | `10` | 结果返回的最大条数上限 |
| `--json` | - | `flag`| 存在即生效 | `False`| 以机器可读的结构化 JSON 输出 |

---

## 二、 提示词思维模式代码表 (Prompt Patterns Reference)

`--pattern` 参数支持直接查询由 `agent-prompt-pattern-extractor` 提炼沉淀的 8 种核心工程模式：

| 模式代码 | 模式全称 | 原序号 | 篇章定位 | 核心特征与适用检索场景 |
| :---: | :--- | :---: | :---: | :--- |
| **P01** | 需求探讨与目标明确模式 | 原 P03 | 单任务篇 · 目标孵化 (0 $\rightarrow$ 0.5) | 项目立项前探索目标形态、评估可行性、请教行业惯例并将成果整理为本地预研/知识文档的会话 |
| **P02** | 先审方案后执行模式 | 原 P04 | 单任务篇 · 方案设计 (0.5 $\rightarrow$ 1) | 目标明确后，严格执行方案先行审批门禁（只分析汇报不修改）、批准后再写代码的会话 |
| **P03** | 结构化任务布置模式 | 原 P01 | 单任务篇 · 清单施工 (1 $\rightarrow$ N) | 简单功能或方案获批后，下达包含发令段、资产段、正负清单与交付契约的确定性发令会话 |
| **P04** | 回复解读与原理追问模式 | 原 P07 | 单任务篇 · 飞行解码 (运行态) | 施工中针对生涩术语、设计动机与底层原理发起“是什么/为什么/怎么样”及通俗化追问的解码会话 |
| **P05** | 经验固化与流程升级模式 | 原 P05 | 资产篇 · 资产生产端 (写/Save) | 实施跑通后固化为可复用资产（技能/文档/智能体）或遇阻反哺升级底座规约的会话 |
| **P06** | 前置技能与规范加载模式 | 原 P06 | 资产篇 · 资产消费端 (读/Load) | 新会话前置显式挂载已有技能包/规范SOP/标杆项目以唤醒上下文的会话（P05产出资产的消费者） |
| **P07** | 多智能体角色制衡模式 | 原 P02 | 高阶篇 · 组织分权治理 (制衡) | 采用经办与审计角色分离、异步留言板通信、防盲从研判门禁的博弈制衡会话 |
| **P08** | 目标受众锁定模式 | 原 P10 | 高阶篇 · 交付内容工程 (表达) | 在图文笔记、短视频或方案创作中明确受众画像、作者站位与认知基线的三位一体表达会话 |

*注：P01~P08 为全新连续重编号；旧 P03 并入 P03 清单契约；旧 P08、P09 已正式废止注销。*

---

## 三、 自然语言提示词到命令映射矩阵

当使用者向 AI 助理提出检索请求时，AI 应映射为对应的 CLI 命令：

| 用户自然语言提问 | 识别意图与维度 | 映射的底层执行命令 |
| :--- | :--- | :--- |
| **“帮我找一下最近3个月关于修复抖音边栏插件的会话”** | 跨端全文 + 关键词 + 时间窗 | `python scripts/search_session.py -k "抖音" --time "最近3个月"` |
| **“查找所有体现了 P07 逆向工程调试模式的会话”** | 模式代码过滤 | `python scripts/search_session.py -p P07` |
| **“查看 Antigravity 当前正在运行的活跃会话”** | 工具限定 + 活跃状态 | `python scripts/search_session.py -t antigravity -s active` |
| **“我在社交媒体工作区都做过哪些会话，搜一下‘图文’”** | 工作区限定 + 关键词 | `python scripts/search_session.py -w "社交媒体" -k "图文"` |
| **“查找 2026 年 8 月以来在 Codex 上的所有归档记录”** | 工具限定 + 归档状态 + 日期范围 | `python scripts/search_session.py -t codex -s archived --after 2026-08-01` |
| **“以 JSON 格式输出包含 P09 知识沉淀的前 5 个会话”** | 模式代码 + 格式 + 限制 | `python scripts/search_session.py -p P09 -n 5 --json` |

---

## 四、 结构化 JSON 返回规范 (JSON Schema)

当附带 `--json` 参数时，脚本输出符合以下 Schema 的标准 JSON 文本：

```json
{
  "query": {
    "keyword": "抖音",
    "tool": "all",
    "status": "all",
    "workspace": null,
    "pattern": null,
    "time": "最近3个月"
  },
  "total": 3,
  "results": [
    {
      "tool": "antigravity",
      "session_id": "antigravity_43798356",
      "title": "开发 rss-twitter",
      "status": "archived",
      "workspace": "E:/BaiduSyncdisk/LocalHub/ServiceHub",
      "timestamp": "2026-09-25T14:32:10",
      "matched_snippets": [
        "这个功能在我的另一个叫抖音博主链接解析的飞书边栏插件中是实现了的...",
        "你看一下抖音博主主页视频订阅这个飞书边栏插件..."
      ],
      "report_path": "storage/extracts/2026-09/antigravity_43798356.md",
      "patterns": ["P01", "P02", "P03"]
    }
  ]
}
```
