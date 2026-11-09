#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
决策卡回执校验 + dry-run 变更计划（可复现，0 积分）

用法：
  /opt/homebrew/bin/python3 tools/apply_decisions.py --demo
  /opt/homebrew/bin/python3 tools/apply_decisions.py --text "C01=accept_convergence\nQ1=4.3.stable"
  /opt/homebrew/bin/python3 tools/apply_decisions.py --receipt path/to/receipt.txt
  /opt/homebrew/bin/python3 tools/apply_decisions.py --receipt path/to/receipt.txt --apply

回执是 key=value 文本（# 开头为注释）。默认**只打印校验摘要，不写任何文件**；
加 --apply 才写 docs/decision-receipt.json（答复证据）与 docs/decision-plan.json（变更计划）。

硬保护（脚本内置断言，不许绕过）：
  - 只写上面两个文件，绝不改 01/02/04/06/07/08 正文
  - 绝不把 design-freeze-draft.json 的 frozen 置 true
  - 绝不生成图标 / 不建工程 / 不产出 design-freeze.json
  - 计划一律标 mode=dry-run；真正落地由助手在用户确认后按计划执行
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARD = ROOT / "docs/decision-card.json"
DRAFT = ROOT / "docs/design-freeze-draft.json"
RECEIPT_OUT = ROOT / "docs/decision-receipt.json"
PLAN_OUT = ROOT / "docs/decision-plan.json"
ALLOWED_WRITES = {RECEIPT_OUT, PLAN_OUT}
HARD_GATES = ("Q1", "Q3", "Q5", "Q8")

DEMO = """# 决策卡回执 · demo（来自 docs/09 §7）
C01=accept_convergence
Q1=4.3.stable
Q3=stage_battle
Q5=accept_roguelite
Q8=autoload_json
Q24=procedural_plus_pixelfx
Q21=128
Q25=proposal_v1
Q26=proposal_b
Q27=proposal_3slots_8types
Q28=proposal_local_only
Q2_4_6_9=keep_assumptions
Q15=defer
Q19=default
Q22=confirm_4
Q23=auto
"""


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return p.name


def parse(text: str) -> tuple[dict[str, str], list[str]]:
    answers: dict[str, str] = {}
    issues: list[str] = []
    for n, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            issues.append(f"第 {n} 行不是 key=value：{s[:60]}")
            continue
        k, v = s.split("=", 1)
        k, v = k.strip(), v.strip()
        if not k:
            issues.append(f"第 {n} 行 key 为空")
            continue
        if k in answers:
            issues.append(f"第 {n} 行重复 key：{k}（已保留后者）")
        answers[k] = v
    return answers, issues


def validate(answers: dict[str, str], card: dict) -> tuple[list[str], list[str], dict]:
    """返回 (errors, warnings, stats)。errors 会让 --apply 拒绝落盘。"""
    errors: list[str] = []
    warnings: list[str] = []
    by_id = {i["id"]: i for i in card["items"]}
    known = set(by_id)

    for k in answers:
        if k not in known:
            errors.append(f"未知决策编号：{k}（决策卡没有这一项）")

    for k, it in by_id.items():
        v = answers.get(k, "")
        if not v:
            continue
        if it.get("type") == "text":
            continue
        allowed = {o["value"] for o in it.get("options", [])}
        if v not in allowed:
            errors.append(f"{k} 的取值不合法：{v}（允许：{', '.join(sorted(allowed))}）")

    gates = {g: answers.get(g, "").strip() for g in HARD_GATES}
    unresolved = [g for g, v in gates.items() if not v]

    # ---- 依赖 / 互斥 / 返工风险（告警，不阻止落盘） ----
    a = answers
    if a.get("C01") == "sequence_frames_decided" and a.get("Q24") not in ("", "all_sprite_sheets"):
        warnings.append("C01 认定「序列帧已定」，但 Q24 选了非全序列帧方案 —— 两者互斥，需重选其一")
    if a.get("C01") == "sequence_frames_decided" and a.get("Q24") == "":
        warnings.append("C01 认定序列帧已定 → Q24 应关闭；请在回执里显式给 Q24=all_sprite_sheets 或改写 C01")
    if a.get("Q26") == "proposal_b" and a.get("Q5") != "accept_roguelite":
        warnings.append("Q26 方案 B 新增 legacy_effects 字段，依赖 Q5 解除存档结构；Q5 未确认前不能落地（R27）")
    if a.get("Q28") == "proposal_local_only":
        warnings.append("Q28 本地埋点需把 01 §4「无数据收集」改为「不联网不上传、本地可关闭」，属已明确假设修订（R29）；另需把 M6 并入 01 §15（R30）")
    if a.get("Q28") == "cloud_upload":
        warnings.append("Q28 允许上传与 01 A4「纯单机 / 无联网 / 无数据收集」正面冲突，需重写 01 §3/§4 并另做合规说明")
    if a.get("Q27") == "eight_slots":
        warnings.append("Q27 坚持 8 槽与 01 §8「第 2/3 槽」冲突，需重写 UI / 存档 / 境界解锁链（R28 结构性返工）")
    if a.get("Q22") == "revert_to_3":
        warnings.append("Q22 回到 3 种怪会作废剑魂 15 帧与 3 张源图，并回改 06/07 口径")
    if a.get("Q3") == "pure_1v1":
        warnings.append("Q3 纯 1v1 需重写 01 §5/§9、节点树与关卡结构，是全部选项里返工代价最高的")
    if a.get("Q24") == "pixelfx_only":
        warnings.append("Q24 纯 pixelfx 会撞 06 §4 的 8 形状语言（R16），且该库无 release/tag，成熟度待复核")
    if a.get("Q25") == "custom" or a.get("Q15") == "provide_baseline" or a.get("Q2_4_6_9") == "revise" or a.get("Q19") == "custom":
        warnings.append("有选项标注「另附清单」，需用户补齐具体修改内容才能执行")

    stats = {
        "knownItems": len(by_id),
        "answered": sum(1 for k in by_id if answers.get(k, "").strip()),
        "unanswered": sorted(k for k in by_id if not answers.get(k, "").strip()),
        "hardGates": gates,
        "hardGatesUnresolved": unresolved,
        "hardGatesResolved": len(HARD_GATES) - len(unresolved),
        "allGatesCleared": not unresolved,
    }
    return errors, warnings, stats


def build_plan(answers: dict[str, str], card: dict, stats: dict) -> dict:
    by_id = {i["id"]: i for i in card["items"]}
    file_changes = []
    for k, v in answers.items():
        if not v or k not in by_id:
            continue
        file_changes.append({"id": k, "answer": v, "onResolve": by_id[k]["onResolve"]})

    closed = [k for k, v in answers.items() if v and k in by_id]
    unlocked = []
    if answers.get("Q25") == "proposal_v1":
        unlocked.append("12 件词缀图标（16×16 菱形框）→ build_icons.py 程序化，0 积分")
    if answers.get("Q26") in ("proposal_b", "proposal_a_numeric"):
        unlocked.append("6 件灵韵图标（六边框）→ build_icons.py 程序化，0 积分")
    if answers.get("Q27") == "proposal_3slots_8types":
        unlocked.append("补 3 个 slot_* ID 契约；已产 8 件 icon_gear_* 保持不改名")
    if answers.get("Q21") in ("96", "128"):
        unlocked.append("B3 两个 Boss 可开工（需按所选尺寸走 regularize_sprites.py --size）")
    if answers.get("Q24"):
        unlocked.append("B4 剩余 4 技能 / 命中特效 / 5 组 overlay 可开工")
    if answers.get("Q28"):
        unlocked.append("M6 埋点字段可落入 02 §5 与 01 §15")
    if stats["allGatesCleared"]:
        unlocked.append("四个硬门禁齐备 → 可进入 08 §5 的 v0.2 合并与冻结门禁检查（仍需用户整体确认策划案）")

    band = {"procedural_plus_pixelfx": "B 85–200（推荐）",
            "all_sprite_sheets": "A 190–450",
            "pixelfx_only": "低于 B 档，量级待实测"}.get(answers.get("Q24", ""), "随 Q24 联动，待实测")
    if answers.get("C01") == "sequence_frames_decided" and answers.get("Q24") != "all_sprite_sheets":
        band = "冲突待澄清：C01 认定序列帧已定，但 Q24 不是全序列帧（本轮不给积分档）"

    return {
        "mode": "dry-run",
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "source": "tools/apply_decisions.py",
        "cardSpec": "docs/decision-card.json",
        "proposalSpec": "docs/09-内容命名提案.md",
        "willNot": [
            "不改 01/02/04/06/07/08 任何正文",
            "不把 design-freeze-draft.json 的 frozen 置 true",
            "不产出 docs/design-freeze.json（正式冻结清单）",
            "不生成任何图标 / 不建 Godot 工程",
            "不把「预选推荐值」当作用户确认",
        ],
        "applyMode": "由助手在用户确认后按本计划逐条执行；脚本本身不执行落地",
        "closedQuestions": sorted(closed),
        "remainingUnanswered": stats["unanswered"],
        "hardGatesCleared": stats["allGatesCleared"],
        "fileChanges": file_changes,
        "unlockedWork": unlocked,
        "creditsBand": band,
        "risksToCarry": ["R27 extra_pool 口径断裂（随 Q26 方案）",
                         "R28 3 槽 ≠ 8 品类（随 Q27）",
                         "R29 埋点 vs 无数据收集（随 Q28）",
                         "R30 M6 未并入 01 §15 正式验收表"],
        "stillPending": [
            "C01 若采纳收敛需改写 00 §2 与 design-freeze-draft.json → conflicts",
            "18 件图标仍待用户确认提案后才生成",
            "R9 字体最终核验、R22 阴兵对比度、hitboxOffsetX=16px、剑魂 8fps 节奏、Godot 编辑器验证",
            "策划案整体确认 → 01 v0.2 → design-freeze.json 置 frozen=true → 才建工程",
        ],
        "note": "本计划是「拿到答复后该改什么」的清单，不是执行结果；全部数值与积分均为量级估算，待实测。",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="决策卡回执校验 + dry-run 变更计划")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--demo", action="store_true", help="用内置示例回执自检（不写文件）")
    g.add_argument("--text", help="直接传回执文本")
    g.add_argument("--receipt", help="回执文本文件路径")
    ap.add_argument("--apply", action="store_true", help="写出 receipt/plan 两份 JSON（仍不执行落地）")
    args = ap.parse_args()

    card = json.loads(CARD.read_text(encoding="utf-8"))
    if args.demo:
        text = DEMO
        print("[demo] 使用内置示例回执\n")
    elif args.text:
        text = args.text.replace("\\n", "\n")
    else:
        p = Path(args.receipt)
        if not p.is_absolute():
            p = ROOT / p
        if not p.exists():
            print(f"回执文件不存在：{p}", file=sys.stderr)
            return 2
        text = p.read_text(encoding="utf-8")

    answers, parse_issues = parse(text)
    errors, warnings, stats = validate(answers, card)
    errors = parse_issues + errors
    plan = build_plan(answers, card, stats)

    print("=== 回执校验 ===")
    print(f"决策项：{stats['answered']}/{stats['knownItems']} 已答；"
          f"硬门禁：{stats['hardGatesResolved']}/4 已填"
          f"（{'已齐备' if stats['allGatesCleared'] else '未齐备：' + ','.join(stats['hardGatesUnresolved'])}）")
    print(f"可关闭：{', '.join(sorted(plan['closedQuestions'])) or '无'}")
    print(f"未回答：{', '.join(stats['unanswered']) or '无'}")
    print(f"积分档：{plan['creditsBand']}")
    print(f"错误 {len(errors)} 条 / 告警 {len(warnings)} 条")
    for e in errors:
        print("  ✗ " + e)
    for w in warnings:
        print("  ! " + w)

    # 硬保护：无论何时都断言台账仍为 draft / 未冻结
    draft = json.loads(DRAFT.read_text(encoding="utf-8"))
    assert draft.get("frozen") is False and draft.get("status") == "draft", \
        "design-freeze-draft.json 已被改成冻结状态，脚本拒绝继续"
    assert not (ROOT / "docs/design-freeze.json").exists(), \
        "正式冻结清单已存在，本脚本不参与阶段二，拒绝继续"

    if errors:
        print("\n结论：INVALID —— 回执有误，未写出任何文件。")
        return 1

    if args.apply:
        receipt = {
            "version": "0.1",
            "status": "received-not-applied",
            "receivedAt": datetime.now().isoformat(timespec="seconds"),
            "source": "tools/apply_decisions.py",
            "raw": text.strip(),
            "answers": answers,
            "validation": {"errors": [], "warnings": warnings, "stats": stats},
            "note": "这是用户答复的证据，不是已执行结果；落地按 docs/decision-plan.json 由助手逐条执行。",
            "frozenTouched": False,
            "baselineDocsTouched": False,
        }
        for path, obj in ((RECEIPT_OUT, receipt), (PLAN_OUT, plan)):
            assert path in ALLOWED_WRITES, "越权写入：" + str(path)
            path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
            print("写出：" + rel(path))
        print("\n结论：VALID（dry-run）—— 已记录答复与变更计划，未改任何基线、未冻结、未建工程。")
    else:
        print("\n结论：VALID（dry-run）—— 未写任何文件。加 --apply 可记录答复与变更计划。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
