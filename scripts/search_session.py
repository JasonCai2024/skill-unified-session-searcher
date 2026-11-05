#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search_session.py — 跨四大 AI 编程工具的一站式会话内容统一检索门面。

统一调度 Antigravity、Codex、MiniMax、WorkBuddy 的底层定位驱动器，
并与 agent-prompt-pattern-extractor 的模式知识库联动，提供全量与增量会话多维检索。

用法:
    python search_session.py --keyword "抖音"
    python search_session.py --keyword "边栏插件" --status active
    python search_session.py --pattern "P07" --limit 5
    python search_session.py --tool codex --workspace "TalentAI" --keyword "出题"
    python search_session.py --keyword "超时" --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
PROGRAMMING_ROOT = SKILL_ROOT.parent

# 底层 Locator 技能脚本路径
LOCATORS = {
    "antigravity": PROGRAMMING_ROOT / "skill-antigravity-session-locator" / "scripts" / "locate_session.py",
    "codex": PROGRAMMING_ROOT / "skill-codex-session-locator" / "scripts" / "locate_session.py",
    "minimax": PROGRAMMING_ROOT / "skill-minimax-code-session-locator" / "scripts" / "locate_session.py",
    "workbuddy": PROGRAMMING_ROOT / "skill-workbuddy-session-locator" / "scripts" / "locate_session.py",
    "dsh": PROGRAMMING_ROOT / "skill-dsh-session-locator" / "scripts" / "locate_session.py",
    "qoder": PROGRAMMING_ROOT / "skill-qoder-session-locator" / "scripts" / "locate_session.py",
}

# 模式库追踪数据库
TRACKER_DB = PROGRAMMING_ROOT / "agent-prompt-pattern-extractor" / "storage" / "tracker.sqlite"
EXTRACTS_DIR = PROGRAMMING_ROOT / "agent-prompt-pattern-extractor" / "storage" / "extracts"


@dataclass
class UnifiedSessionResult:
    tool: str
    session_id: str
    title: str
    workspace: str
    is_archived: bool
    status_label: str
    updated_at: str
    matched_snippets: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    report_path: Optional[str] = field(default=None)
    transcript_path: Optional[str] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def run_locator_cli(tool: str, script_path: Path, args: List[str]) -> List[Dict[str, Any]]:
    """以子进程安全调用底层定位器脚本并解析输出的 JSON。"""
    if not script_path.is_file():
        return []

    cmd = [sys.executable, str(script_path), "--json"] + args
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", timeout=60)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                return data.get("matches", [])
            elif isinstance(data, list):
                return data
    except Exception as e:
        sys.stderr.write(f"[WARN] 调用 {tool} 定位器异常: {e}\n")
    return []


def search_via_tracker_db(
    keyword: Optional[str] = None,
    tool_filter: Optional[str] = None,
    pattern_filter: Optional[str] = None,
    workspace_filter: Optional[str] = None,
    limit: int = 10
) -> List[UnifiedSessionResult]:
    """通过 tracker.sqlite 知识库与提炼报告进行秒级知识/模式检索。"""
    results: List[UnifiedSessionResult] = []
    if not TRACKER_DB.is_file():
        return results

    try:
        conn = sqlite3.connect(str(TRACKER_DB))
        conn.row_factory = sqlite3.Row
        
        sql = "SELECT * FROM session_tracking WHERE 1=1"
        params: List[Any] = []

        if tool_filter and tool_filter != "all":
            sql += " AND tool = ?"
            params.append(tool_filter.lower())

        if pattern_filter:
            p_codes = [p.strip().upper() for p in pattern_filter.split(",") if p.strip()]
            for pc in p_codes:
                sql += " AND extracted_patterns LIKE ?"
                params.append(f"%{pc}%")

        if workspace_filter:
            sql += " AND workspace LIKE ?"
            params.append(f"%{workspace_filter}%")

        sql += " ORDER BY archived_at DESC LIMIT ?"
        params.append(max(limit * 3, 50))

        rows = conn.execute(sql, params).fetchall()
        conn.close()

        for r in rows:
            sid = r["session_uid"]
            t = r["tool"]
            title = r["title"] or "(无标题)"
            ws = r["workspace"] or "(未关联工作区)"
            archived_at = r["archived_at"] or r["created_at"] or ""
            raw_patterns = r["extracted_patterns"] or ""
            pat_list = [p.strip() for p in raw_patterns.split(",") if p.strip()]
            report = r["output_report_path"]
            transcript = r["transcript_path"]

            snippets: List[str] = []

            # 如果提供了关键词，在提炼报告或标题中核查命中
            if keyword:
                kw_lower = keyword.lower()
                hit = False
                if kw_lower in title.lower():
                    hit = True
                    snippets.append(f"[标题命中] {title}")

                # 尝试读取对应的提炼报告提取上下文片段
                if report:
                    abs_rep = PROGRAMMING_ROOT / "agent-prompt-pattern-extractor" / report
                    if abs_rep.is_file():
                        try:
                            rep_text = abs_rep.read_text(encoding="utf-8", errors="replace")
                            for line in rep_text.splitlines():
                                if kw_lower in line.lower():
                                    hit = True
                                    clean_l = line.strip().strip(">").strip()
                                    if clean_l and clean_l not in snippets:
                                        snippets.append(clean_l[:200])
                                    if len(snippets) >= 3:
                                        break
                        except Exception:
                            pass

                if not hit:
                    continue

            results.append(UnifiedSessionResult(
                tool=t,
                session_id=sid,
                title=title,
                workspace=ws,
                is_archived=True,
                status_label="已归档",
                updated_at=archived_at[:19] if archived_at else "",
                matched_snippets=snippets,
                patterns=pat_list,
                report_path=report,
                transcript_path=transcript,
            ))

            if len(results) >= limit:
                break

    except Exception as e:
        sys.stderr.write(f"[WARN] 查询 tracker.sqlite 出错: {e}\n")

    return results


def search_via_locators(
    keyword: Optional[str] = None,
    tool_filter: Optional[str] = None,
    status_filter: str = "all",
    workspace_filter: Optional[str] = None,
    time_hint: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    limit: int = 10,
) -> List[UnifiedSessionResult]:
    """调度底层 4 个 Locator 脚本，执行物理日志全文检索与活跃会话嗅探。"""
    results: List[UnifiedSessionResult] = []
    tools_to_run = list(LOCATORS.keys())
    if tool_filter and tool_filter != "all" and tool_filter in LOCATORS:
        tools_to_run = [tool_filter]

    for t in tools_to_run:
        script = LOCATORS[t]
        if not script.is_file():
            continue

        cli_args: List[str] = []
        if keyword:
            cli_args.extend(["--keyword", keyword])
        if workspace_filter:
            cli_args.extend(["--workspace" if t in ("antigravity", "dsh", "qoder") else "--cwd", workspace_filter])
        if time_hint:
            cli_args.extend(["--time", time_hint])
        if after:
            cli_args.extend(["--after", after])
        if before:
            cli_args.extend(["--before", before])

        if status_filter == "archived":
            cli_args.append("--archived-only")
        elif status_filter == "active":
            cli_args.append("--active-only")

        cli_args.extend(["--limit", str(limit)])

        matches = run_locator_cli(t, script, cli_args)
        for m in matches:
            sid = m.get("session_id") or m.get("id") or ""
            title = m.get("title") or "(无标题)"
            ws = m.get("workspace") or m.get("cwd") or "(未关联工作区)"
            is_arc = m.get("is_archived", False)
            up_at = m.get("updated_at") or m.get("archived_at") or ""
            t_path = m.get("transcript_path") or m.get("rollout_path") or m.get("jsonl_path")

            snippets = []
            if keyword and t_path and os.path.exists(t_path):
                try:
                    with open(t_path, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            if keyword.lower() in line.lower():
                                snip = ""
                                try:
                                    obj = json.loads(line)
                                    snip = obj.get("content") or obj.get("text") or obj.get("input_text") or ""
                                    if isinstance(snip, list):
                                        snip = " ".join([str(x) for x in snip])
                                except Exception:
                                    pass
                                if not snip:
                                    snip = line
                                snip_clean = re.sub(r"<[^>]+>", "", str(snip)).strip()
                                snip_clean = re.sub(r"[\r\n\t]+", " ", snip_clean)
                                if snip_clean and snip_clean not in snippets:
                                    snippets.append(snip_clean[:180])
                                if len(snippets) >= 2:
                                    break
                except Exception:
                    pass

            results.append(UnifiedSessionResult(
                tool=t,
                session_id=sid,
                title=title,
                workspace=ws,
                is_archived=is_arc,
                status_label="已归档" if is_arc else "活跃",
                updated_at=str(up_at)[:19],
                matched_snippets=snippets,
                patterns=[],
                report_path=None,
                transcript_path=t_path,
            ))

    return results


def deduplicate_and_rank(results: List[UnifiedSessionResult], limit: int) -> List[UnifiedSessionResult]:
    """去重与综合排序：优先展示有匹配原句、更新时间最近的记录。"""
    seen = set()
    deduped = []
    for r in results:
        key = (r.tool, r.session_id)
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    def sort_key(item: UnifiedSessionResult):
        has_snippets = 1 if item.matched_snippets else 0
        has_patterns = len(item.patterns)
        return (has_snippets, has_patterns, item.updated_at)

    deduped.sort(key=sort_key, reverse=True)
    return deduped[:limit]


def render_markdown_table(results: List[UnifiedSessionResult], keyword: Optional[str] = None) -> str:
    """渲染结构化表格视图。"""
    if not results:
        return "\n> [未找到匹配会话] 请尝试扩大时间范围或调整搜索关键词。\n"

    lines = [
        "",
        f"### 🎯 会话检索结果（共匹配到 {len(results)} 个记录）",
        "",
        "| # | 工具类型 | 状态 | 会话标题 / 标识 | 关联工作区 | 时间 | 提示词模式 |",
        "| :---: | :---: | :---: | :--- | :--- | :---: | :---: |",
    ]

    for i, r in enumerate(results, 1):
        status_badge = f"`{r.status_label}`"
        pat_str = " ".join([f"`{p}`" for p in r.patterns]) if r.patterns else "-"
        t_clean = r.title.replace("|", "\\|").strip()
        if len(t_clean) > 35:
            t_clean = t_clean[:32] + "..."
        ws_clean = Path(r.workspace).name if r.workspace and r.workspace != "(未关联工作区)" else r.workspace
        lines.append(f"| {i} | **{r.tool.capitalize()}** | {status_badge} | {t_clean} | `{ws_clean}` | {r.updated_at[:10]} | {pat_str} |")

    lines.append("")
    # 附带展示匹配原句摘录
    has_any_snippets = any(r.matched_snippets for r in results)
    if has_any_snippets:
        lines.append("#### 📝 关键上下文原句摘录")
        lines.append("")
        for i, r in enumerate(results, 1):
            if r.matched_snippets:
                lines.append(f"- **#{i} [{r.tool.capitalize()}] {r.title}** (`{r.session_id[:16]}...`):")
                for snip in r.matched_snippets[:2]:
                    lines.append(f"  > \"{snip}\"")
                if r.report_path:
                    lines.append(f"  *提炼报告*: [{r.report_path}](file:///{PROGRAMMING_ROOT.as_posix()}/agent-prompt-pattern-extractor/{r.report_path})")
                lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="跨五大 AI 编程/智能体工具一站式会话内容统一检索门面")
    parser.add_argument("--keyword", "-k", type=str, default=None, help="全文搜索关键词或报错片段")
    parser.add_argument("--tool", "-t", type=str, choices=["all", "antigravity", "codex", "minimax", "workbuddy", "dsh", "qoder"], default="all", help="限定工具过滤")
    parser.add_argument("--status", "-s", type=str, choices=["all", "active", "archived"], default="all", help="状态过滤 (all/active/archived)")
    parser.add_argument("--workspace", "-w", type=str, default=None, help="工作区路径或项目关键词")
    parser.add_argument("--pattern", "-p", type=str, default=None, help="提示词模式代码 (如 P01, P07)")
    parser.add_argument("--time", type=str, default=None, help="自然语言时间窗提示 (如 'yesterday', '最近3个月')")
    parser.add_argument("--after", type=str, default=None, help="时间窗起点 (YYYY-MM-DD)")
    parser.add_argument("--before", type=str, default=None, help="时间窗终点 (YYYY-MM-DD)")
    parser.add_argument("--limit", "-n", type=int, default=10, help="最大返回数量 (默认 10)")
    parser.add_argument("--json", action="store_true", help="输出结构化 JSON 格式")

    args = parser.parse_args()

    all_results: List[UnifiedSessionResult] = []
    tracker_res: List[UnifiedSessionResult] = []

    # 1. 如果指定了 pattern 或检索已归档内容，优先通过知识库提炼元数据检索
    if args.pattern or args.status in ["all", "archived"]:
        tracker_res = search_via_tracker_db(
            keyword=args.keyword,
            tool_filter=args.tool,
            pattern_filter=args.pattern,
            workspace_filter=args.workspace,
            limit=args.limit
        )
        all_results.extend(tracker_res)

    # 2. 如果包含活跃会话或需要穿透原始日志全文（且未限定 pattern），调度各工具 Locator 驱动器
    if not args.pattern and (args.status in ["all", "active"] or not all_results or (args.keyword and not tracker_res)):
        locator_res = search_via_locators(
            keyword=args.keyword,
            tool_filter=args.tool,
            status_filter=args.status,
            workspace_filter=args.workspace,
            time_hint=args.time,
            after=args.after,
            before=args.before,
            limit=args.limit
        )
        all_results.extend(locator_res)

    # 3. 排序与去重
    final_results = deduplicate_and_rank(all_results, limit=args.limit)

    if args.json:
        out = {
            "query": {
                "keyword": args.keyword,
                "tool": args.tool,
                "status": args.status,
                "workspace": args.workspace,
                "pattern": args.pattern,
                "time": args.time
            },
            "match_count": len(final_results),
            "matches": [r.to_dict() for r in final_results]
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(render_markdown_table(final_results, keyword=args.keyword))


if __name__ == "__main__":
    main()
