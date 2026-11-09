#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设计冻结清单编号合法性 + 产物侧回指覆盖率统计（可复现）

用法：
  /opt/homebrew/bin/python3 tools/check_traceability.py

两份清单的分工（第 15 轮起）：
  - docs/design-freeze-draft.json  阶段一历史快照，仍须保持 frozen=false / status=draft
  - docs/design-freeze.json        **当前权威冻结清单**，status 必须为 frozen，
                                  所有条目 confirmed=true，编号合法且唯一

检查项：
  - draft 仍为 draft（防止把台账误当正式冻结清单）
  - draft 的 confirmed 编号格式合法、唯一、source 文件真实存在
  - draft 的 hardGates / openQuestions / conflicts 交叉引用完整
  - 正式冻结清单存在且 frozen、条目合法唯一、全部 confirmed
  - 产物侧 DF-xx 回指覆盖率：assets/ + tools/ + scripts/ + scenes/ + project.godot
    （排除 assets/_preview/ 预览页 —— R36：那里的 DF-xx 是给人看的说明文字）

输出：docs/traceability-report.json + 控制台摘要；报告只写项目内相对路径。
覆盖率低是真实进度，禁止手工塞标记凑数。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs/design-freeze-draft.json"
FROZEN = ROOT / "docs/design-freeze.json"
OUT = ROOT / "docs/traceability-report.json"
ID_PAT = re.compile(r"DF-\d{2,}")
FULL_PAT = re.compile(r"^DF-\d{2,}$")
# 只认「@trace 编号」这种显式工程回指；文档/脚本里随口提到的 DF-xx 说明文字不算
# （R36 的教训：算进去会让覆盖率虚高，与真实进度不符）。
TRACE_PAT = re.compile(r"@trace[ \t]+([^\r\n#]+)")
TEXT_SUFFIXES = {".md", ".gd", ".json", ".py", ".csv", ".html", ".txt",
                 ".tscn", ".tres", ".cfg", ".godot"}
VALID_TYPES = {"hardGate", "contentBlocker", "deferred"}


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return p.name


def implementation_refs() -> set[str]:
    """只扫产物侧：素材目录、工具、工程脚本与场景、工程配置。

    故意排除 docs/ 台账自身（列了全部编号，算进去覆盖率恒为 100%）。
    R36：同时排除 assets/_preview/ —— 预览页与决策卡 HTML 内嵌的说明文字
    （如「DF-xx 已据此实现」）是文档，不是工程实现回指。
    第 15 轮：阶段二已建最小验证工程，故新增 scripts/ / scenes/ / project.godot。
    """
    refs: set[str] = set()
    preview = ROOT / "assets/_preview"
    bases: list[Path] = [ROOT / d for d in ("assets", "tools", "scripts", "scenes")]
    bases.append(ROOT / "project.godot")

    for base in bases:
        if base.is_file():
            files = [base]
        elif base.is_dir():
            files = [p for p in base.rglob("*") if p.is_file()]
        else:
            continue
        for p in files:
            if p.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if preview in p.parents:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for chunk in TRACE_PAT.findall(text):
                for token in re.split(r"[\s,;]+", chunk.strip()):
                    if FULL_PAT.match(token):
                        refs.add(token)
    return refs


def frozen_check(refs: set[str]) -> dict:
    """核对当前权威冻结清单，并按它的条目统计工程侧覆盖率。"""
    if not FROZEN.exists():
        return {"exists": False, "verdict": "MISSING",
                "issue": "缺少 docs/design-freeze.json（阶段二不允许开工）"}
    f = json.loads(FROZEN.read_text(encoding="utf-8"))
    items = f.get("items", [])
    fids = [str(i.get("id", "")) for i in items]
    invalid = [i for i in fids if not FULL_PAT.match(i)]
    duplicate = len(set(fids)) != len(fids)
    unconfirmed = [str(i.get("id")) for i in items if not i.get("confirmed")]
    covered = sorted(set(fids) & refs)
    ok = (f.get("status") == "frozen" and bool(items)
          and not invalid and not duplicate and not unconfirmed)
    return {
        "exists": True,
        "path": rel(FROZEN),
        "status": f.get("status"),
        "version": f.get("version"),
        "engine": f.get("engine"),
        "items": len(items),
        "invalidIds": invalid,
        "duplicateIds": duplicate,
        "unconfirmedIds": unconfirmed,
        "coverage": {
            "covered": len(covered), "total": len(fids),
            "rate": round(len(covered) / len(fids), 4) if fids else 0.0,
            "coveredIds": covered,
        },
        "note": ("最小验证工程只实现 DF-04 / DF-12 / DF-13 / DF-15 等少数几条；"
                 "其余条目属正式工程范围，低覆盖率是真实进度，禁止塞标记凑数。"),
        "verdict": "PASS" if ok else "FAIL",
    }


def main() -> int:
    if not SRC.exists():
        print(json.dumps({"error": "缺少 docs/design-freeze-draft.json"}, ensure_ascii=False))
        return 1

    d = json.loads(SRC.read_text(encoding="utf-8"))
    issues: list[str] = []

    # 1. draft 冻结状态硬校验（该文件永远是历史快照）
    if d.get("frozen") is not False:
        issues.append("frozen 必须为 false（本文件是 draft，不是正式冻结清单）")
    if d.get("status") != "draft":
        issues.append("status 必须为 draft")

    # 2. 已确认项编号与来源
    confirmed = d.get("confirmed", [])
    ids = [c.get("id", "") for c in confirmed]
    invalid_ids = [i for i in ids if not FULL_PAT.match(i)]
    if invalid_ids:
        issues.append(f"编号格式不合规: {invalid_ids}")
    if len(set(ids)) != len(ids):
        issues.append("confirmed 存在重复编号")

    missing_sources: list[str] = []
    source_total = 0
    for c in confirmed:
        for s in c.get("source", []):
            source_total += 1
            if not (ROOT / s).exists():
                missing_sources.append(f"{c['id']} → {s}")
    if missing_sources:
        issues.append(f"来源文件不存在: {missing_sources}")

    # 3. 决策欠债完整度
    oq = d.get("openQuestions", [])
    oq_ids = [q.get("id", "") for q in oq]
    if len(set(oq_ids)) != len(oq_ids):
        issues.append("openQuestions 存在重复编号")
    undocumented = [q.get("id") for q in oq
                    if not q.get("blocks") or not q.get("onResolve")]
    if undocumented:
        issues.append(f"未决项缺 blocks/onResolve: {undocumented}")
    bad_types = [q.get("id") for q in oq if q.get("type") not in VALID_TYPES]
    if bad_types:
        issues.append(f"未决项 type 非法: {bad_types}")
    by_type: dict[str, int] = {}
    for q in oq:
        by_type[q.get("type", "?")] = by_type.get(q.get("type", "?"), 0) + 1

    # 4. 硬门禁交叉引用
    gates = d.get("hardGates", [])
    oq_map = {q.get("id"): q for q in oq}
    gate_missing = [g for g in gates if g not in oq_map]
    gate_mistyped = [g for g in gates
                     if g in oq_map and oq_map[g].get("type") != "hardGate"]
    if gate_missing:
        issues.append(f"硬门禁未出现在 openQuestions: {gate_missing}")
    if gate_mistyped:
        issues.append(f"硬门禁 type 不是 hardGate: {gate_mistyped}")
    declared = d.get("debtSummary", {})
    if declared.get("total") != len(oq):
        issues.append("debtSummary.total 与 openQuestions 实际条数不一致")

    # 5. 冲突项处置
    conflicts = d.get("conflicts", [])
    unresolved = [c.get("id") for c in conflicts if not c.get("resolution")]
    if unresolved:
        issues.append(f"冲突项未写处置: {unresolved}")

    # 6. 产物侧覆盖率（阶段二口径：以正式冻结清单为准）
    refs = implementation_refs()
    covered = sorted(set(ids) & refs)
    coverage = round(len(covered) / len(ids), 4) if ids else 0.0
    frozen = frozen_check(refs)
    if frozen["verdict"] != "PASS":
        issues.append("正式冻结清单校验未通过: " + str(frozen.get("issue", frozen["verdict"])))

    report = {
        "source": rel(SRC),
        "sourceRole": "阶段一历史快照（draft），不是当前权威",
        "status": d.get("status"),
        "frozen": d.get("frozen"),
        "authoritative": frozen,
        "confirmedCount": len(confirmed),
        "idValidity": {"valid": len(ids) - len(invalid_ids), "total": len(ids),
                       "rate": round((len(ids) - len(invalid_ids)) / len(ids), 4) if ids else 0,
                       "invalid": invalid_ids},
        "sourceExists": {"found": source_total - len(missing_sources), "total": source_total,
                         "missing": missing_sources},
        "openQuestions": {"count": len(oq), "documented": len(oq) - len(undocumented),
                          "rate": round((len(oq) - len(undocumented)) / len(oq), 4) if oq else 0,
                          "byType": by_type},
        "hardGates": {"declared": len(gates), "missing": gate_missing,
                      "mistyped": gate_mistyped},
        "conflicts": {"count": len(conflicts), "unresolved": unresolved},
        "implementationCoverage": {
            "covered": len(covered), "total": len(ids), "rate": coverage,
            "coveredIds": covered,
            "scope": "assets/ + tools/ + scripts/ + scenes/ + project.godot（排除 assets/_preview/，R36）",
            "note": (f"产物侧 DF-xx 回指 {len(covered)}/{len(ids)}；"
                     "第 15 轮起工程已建，覆盖率不再等于 0。未覆盖条目属正式工程范围，"
                     "是真实进度而非缺陷；禁止手工塞标记凑数。"),
        },
        "issues": issues,
        "verdict": "PASS" if not issues else "FAIL",
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": report["verdict"],
        "draft": {"status": d.get("status"), "frozen": d.get("frozen")},
        "authoritative": {"status": frozen["status"], "items": frozen["items"],
                          "coverage": frozen["coverage"]["rate"],
                          "coveredIds": frozen["coverage"]["coveredIds"],
                          "verdict": frozen["verdict"]},
        "issues": issues,
        "report": rel(OUT),
    }, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
