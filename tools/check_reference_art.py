#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""参考稿量化体检（第 28 轮）：A 组塔层背景 + B / C 组形状板。

问题背景
--------
第 25–27 轮收编的 `previews/ui/` 回稿，走的是 `check_ui_art.py` 的「界面图」体检口径：
尺寸 / 越界色 / 半透明 / 柔边 / 纯白。对 A 组背景与 B / C 组 sprite 形状板，这套口径
只能稳定报一个 `size_rule` FAIL，其余什么也没验证：

* A 组背景的「深墨系 / 浅宣纸系占比、四深度带亮度、中央战斗区暗像素」是第 27 轮用
  临时脚本算的，**口径没落盘**，换账号后无法复算，R22 的判断也没有可追溯依据。
* B / C 组形状板提示词里写死的硬指标（纯白底、网格格数、中心留白 >= 70%、
  同行两帧只允许 1px 脉动、1px 黑描边），现有脚本一项都不检查。

本工具把这两类指标固化成可复跑脚本，输出 `docs/reference-art-report.json`。

两类模式
--------
scene : A1–A4 四张塔层背景（默认读 `_palette24.png` 吸附版）
        深墨系 / 浅宣纸系 / 其他色组占比、上中下三带暗像素占比、
        中央战斗区（x 20–80% / y 35–75%）暗像素占比、R22 代理分级。
sheet : B / C 组形状板（按文件名前缀自动判网格：B- = 1x2，C1- = 2x2，C2- = 5x2）
        画幅、纯白底、越界色 / 半透明 / 柔边（复用第 22 轮冻结口径）、
        1px 黑描边、每格是否有内容、中心留白（overlay）、同行两帧脉动一致性。

用法
----
    python3 tools/check_reference_art.py all          # 复算 A 组 + 检查已有 B/C 组 + 合成图自检
    python3 tools/check_reference_art.py scene
    python3 tools/check_reference_art.py sheet [文件/目录 ...] [--grid R,C]
    python3 tools/check_reference_art.py --selftest   # 只跑合成好图 / 坏图判定能力验证
    python3 tools/check_reference_art.py --check      # 复算并与现有报告比对（不写文件）

口径边界（重要）
--------------
* 所有数值都是**对回稿 PNG 文件的事实统计**，不是引擎渲染结果、不是实机对比度实测。
* `r22ProxyLevel` 只是「深色背景会不会糊掉墨甲阴兵」的**代理指标**，R22 真实对比度
  仍待 GUI F5 与接入引擎后实测；本工具不解除 R22，也不改任何冻结数值。
* B / C 组体检结果按 R55 是**返工依据，不是入库闸门**；这些图仍只算参考稿。
* 本工具不碰 `project.godot` / `MinimalRun.tscn` / 冻结设计文档 / 抽卡规则 / 卡牌库。

依赖：Pillow。若当前 `python3` 缺 Pillow，脚本会自动探测本机另一个带 Pillow 的解释器
并重新执行自身（不改变任何工程文件）。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------- Pillow 自举
def _ensure_pil() -> None:
    try:
        import PIL  # noqa: F401
        return
    except ImportError:
        pass
    if os.environ.get("_XTOWER_REF_PIL") == "1":
        print("[FAIL] 找不到带 Pillow 的 Python 解释器；请先安装 pillow。", file=sys.stderr)
        raise SystemExit(2)
    import glob
    import shutil
    import subprocess

    candidates = [
        "/opt/homebrew/bin/python3",
        "/usr/local/bin/python3",
        "/usr/bin/python3",
    ]
    for pattern in ("/opt/homebrew/bin/python3.*", "/usr/local/bin/python3.*"):
        candidates.extend(sorted(glob.glob(pattern)))
    for name in ("python3.14", "python3.13", "python3.12", "python3.11"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    seen: set[str] = set()
    for exe in candidates:
        if exe in seen or not os.path.isfile(exe):
            continue
        seen.add(exe)
        try:
            ok = subprocess.run(
                [exe, "-c", "import PIL"], capture_output=True, timeout=10
            ).returncode == 0
        except (OSError, subprocess.SubprocessError):
            continue
        if ok:
            env = dict(os.environ)
            env["_XTOWER_REF_PIL"] = "1"
            os.execve(exe, [exe, str(Path(__file__).resolve())] + sys.argv[1:], env)
    print("[FAIL] 本机没有检测到带 Pillow 的 Python 解释器。", file=sys.stderr)
    raise SystemExit(2)


_ensure_pil()
from PIL import Image, ImageDraw  # noqa: E402

# 复用第 22 轮已冻结的体检口径（导入不会写报告，报告只在 check_ui_art.main 里写）
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_ui_art as cua  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "asset-manifest-pixel.json"
REPORT = ROOT / "docs" / "reference-art-report.json"
UI_DIR = ROOT / "previews" / "ui"

# ---------------------------------------------------------------- 冻结色板与口径
def _hex_to_rgb(s: str) -> tuple[int, int, int]:
    s = s.lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def load_palette() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pal = data["palette"]
    groups = {
        name: [_hex_to_rgb(v[t]) for t in ("dark", "main", "light")]
        for name, v in pal["groups"].items()
    }
    functional = {k: _hex_to_rgb(v) for k, v in pal["functional"].items()}
    colors = [c for g in groups.values() for c in g] + list(functional.values())
    return {"groups": groups, "functional": functional, "colors": colors}


PAL = load_palette()
COLORS = PAL["colors"]
INK_GROUP = set(PAL["groups"]["mo"]) | {PAL["functional"]["outline"]}
PAPER_GROUP = set(PAL["groups"]["xuanzhi"])
WHITE = PAL["functional"]["flash"]
BLACK = PAL["functional"]["outline"]


def _luma(c: tuple[int, int, int]) -> float:
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


# 暗像素 = 24 色板里亮度代理 < 60 的色（实际为 #000000 / #12161F / #2A3140）。
# 阈值写在这里而不是硬编码颜色列表，是为了让「换色板后口径仍可复算」。
DARK_LUMA_LIMIT = 60.0
DARK_SET = frozenset(c for c in COLORS if _luma(c) < DARK_LUMA_LIMIT)

# 战斗区与四深度带（分 fractions，与 docs/20 §2.3 / §4.1 一致）
COMBAT_ZONE = (0.20, 0.35, 0.80, 0.75)
BANDS = {
    "topQuarter": (0.0, 0.0, 1.0, 0.25),
    "middleHalf": (0.0, 0.25, 1.0, 0.75),
    "bottomQuarter": (0.0, 0.75, 1.0, 1.0),
}

R22_MEDIUM = 0.30
R22_HIGH = 0.60

_NEAREST: dict[tuple[int, int, int], tuple[int, int, int]] = {}


def nearest(c: tuple[int, int, int]) -> tuple[int, int, int]:
    """把任意 RGB 归到最近的 24 色锁定板色；同色只算一次。"""
    hit = _NEAREST.get(c)
    if hit is None:
        hit = min(COLORS, key=lambda p: (c[0] - p[0]) ** 2
                  + (c[1] - p[1]) ** 2 + (c[2] - p[2]) ** 2)
        _NEAREST[c] = hit
    return hit


def rgb_counter(im: Image.Image) -> Counter:
    """统计 RGB 像素直方图（不走 Pillow 已弃用的 getdata，避免版本告警）。"""
    buf = im.convert("RGB").tobytes()
    return Counter(zip(buf[0::3], buf[1::3], buf[2::3]))


def mapped_counts(im: Image.Image) -> tuple[Counter, int]:
    """返回 {最近板色: 像素数} 与总像素数；按唯一色归并，避免逐像素 20 次比较。"""
    raw = rgb_counter(im)
    mapped: Counter = Counter()
    for col, n in raw.items():
        mapped[nearest(col)] += n
    return mapped, sum(raw.values())


def _box(size: tuple[int, int], frac) -> tuple[int, int, int, int]:
    w, h = size
    return (int(frac[0] * w), int(frac[1] * h), int(frac[2] * w), int(frac[3] * h))


def _ratio(mapped: Counter, group) -> float:
    total = sum(mapped.values())
    return (sum(mapped[c] for c in group) / total) if total else 0.0


def r22_level(dark_ratio: float) -> str:
    if dark_ratio >= R22_HIGH:
        return "HIGH"
    if dark_ratio >= R22_MEDIUM:
        return "MEDIUM"
    return "LOW"


DEFINITIONS = {
    "nearestPaletteColor": "每个像素按欧氏距离归到 docs/asset-manifest-pixel.json 的 24 色锁定板最近色，再按色组计数",
    "darkSet": "24 色板中 0.299R+0.587G+0.114B < %.0f 的色，实为 %s"
               % (DARK_LUMA_LIMIT, sorted("#%02X%02X%02X" % c for c in DARK_SET)),
    "inkGroup": "墨三阶 #12161F #2A3140 #4A5568 + 描边 #000000",
    "paperGroup": "宣纸三阶 #8A8268 #C9BFA3 #E8DFC8",
    "combatZone": "x 20%-80% / y 35%-75%（docs/20 §4.1 中央战斗区）",
    "bands": "上 1/4 远景 / 中 1/2 中景 / 下 1/4 地面，按 docs/20 §2.3",
    "r22ProxyLevel": "战斗区暗像素 >= 60% 记 HIGH、>= 30% 记 MEDIUM，否则 LOW；只是回稿文件的亮度代理，不是实机对比度实测",
    "sheetGrid": "B- = 1x2（两 Boss）；C1- = 2x2（4 技能形状）；C2- = 5x2（5 组 overlay 各 2 帧）",
    "sheetCenter": "每格中央 60%x60% 区域内，非白内容像素占比 <= 30% 视为留白 >= 70%（仅 overlay）",
    "sheetPulse": "只对 C2 overlay 生效：同一行两帧内容像素数相对差 <= 25% 为 PASS、<= 50% 为 WARN、> 50% 为 FAIL；B 组两格是两个不同 Boss、C1 每行是两种不同技能，差异大是设计意图，记为 kind=distinct 不判等级",
    "baseMetrics": "越界色 / 半透明 / 柔边 / 纯白复用 tools/check_ui_art.py 的冻结阈值，不另起口径",
    "patchCompliance": "docs/20 §4.1 通用补充句的 9 条可机器核验硬指标；只对该补充句重出的版本（文件名含 R-）做验收，旧 A 组标 EXEMPT",
    "l4_area_under_10": "最下 10% 条带 + 左右边缘 5%（y 75%-90%）内暗像素数 / 全图像素数，作为『L4 前景剪影占画面 < 10%』的代理",
    "patchManualOnly": "四层能否沿水平线独立切图、有无跨层连续深色块、有无文字水印，机器不判，只能人工目检，不伪造 PASS",
}
NOTE = ("本报告的每一数值都是对 previews/ui/ 下 PNG 文件的事实统计，不是引擎渲染 / 实机对比度结论；"
        "R22 阴兵对比度、贴图内存、帧率、积分一律待实测。A/B/C 组图按 R55 只算参考稿，"
        "体检结果是返工依据而非入库闸门，不解除任何硬门禁。")

# ---------------------------------------------------------------- scene 模式
# docs/20 §4.1 通用补充句的**可机器核验**硬指标。
# 注意：「四层能否沿水平线独立切图」「是否存在跨层连续深色块」无法靠统计量诚实判定，
# 列为人工目检项，不伪造 PASS。
PATCH_RULES = [
    ("aspect_16x9",        "画幅 16:9（|w/h - 16/9| <= 0.02）",                 "le", 0.02),
    ("l1_dark_under_20",   "L1 上 1/4 深色像素 <= 20%",                          "le", 0.20),
    ("combat_paper_over_50", "中央战斗区浅宣纸色块 >= 50%",                        "ge", 0.50),
    ("combat_ink_under_30", "中央战斗区深色像素 <= 30%",                          "le", 0.30),
    ("l3_paper_over_40",   "L3 下 1/4 浅宣纸铺底 >= 40%",                         "ge", 0.40),
    ("l3_not_dark",        "L3 下 1/4 深色像素 <= 30%（禁止整片压暗）",            "le", 0.30),
    ("l4_area_under_10",   "L4 前景剪影占全画面 < 10%",                            "lt", 0.10),
    ("ink_under_55",       "全图深墨系 <= 55%",                                   "le", 0.55),
    ("paper_over_30",      "全图浅宣纸系 >= 30%",                                  "ge", 0.30),
]
MANUAL_ONLY = [
    "四深度层之间是否有清晰水平色阶分界、能沿水平线各自独立切图",
    "是否存在跨层的连续深色块 / 巨大对称深色塔影 / 上下深色夹击中部",
    "是否混入文字、水印、logo、UI 元素或人物角色",
]


def _region_metrics(im: Image.Image, frac) -> dict:
    sub, _ = mapped_counts(im.crop(_box(im.size, frac)))
    return {
        "ink": _ratio(sub, INK_GROUP),
        "paper": _ratio(sub, PAPER_GROUP),
        "dark": _ratio(sub, DARK_SET),
    }


def _l4_area_ratio(im: Image.Image) -> float:
    """最下 10% 条带 + 左右边缘 5%（y 75%–90%）的暗像素，占全画面比例。"""
    w, h = im.size
    regions = [
        (0, int(.90 * h), w, h),
        (0, int(.75 * h), int(.05 * w), int(.90 * h)),
        (int(.95 * w), int(.75 * h), w, int(.90 * h)),
    ]
    dark = 0
    for box in regions:
        sub, total = mapped_counts(im.crop(box))
        dark += sum(sub[c] for c in DARK_SET)
    return dark / (w * h)


def patch_compliance(path: Path, im: Image.Image, whole_ink: float,
                     whole_paper: float, l1: dict, l3: dict, zone: dict) -> dict:
    w, h = im.size
    values = {
        "aspect_16x9": abs(w / h - 16 / 9),
        "l1_dark_under_20": l1["ink"],
        "combat_paper_over_50": zone["paper"],
        "combat_ink_under_30": zone["ink"],
        "l3_paper_over_40": l3["paper"],
        "l3_not_dark": l3["ink"],
        "l4_area_under_10": _l4_area_ratio(im),
        "ink_under_55": whole_ink,
        "paper_over_30": whole_paper,
    }
    checks = []
    for cid, desc, op, threshold in PATCH_RULES:
        v = values[cid]
        ok = v <= threshold if op == "le" else (v >= threshold if op == "ge" else v < threshold)
        checks.append({"id": cid, "rule": desc, "value": round(v, 5),
                       "threshold": threshold, "operator": op, "pass": bool(ok)})
    # 只对「明确加了 §4.1 补充句重出的版本」做验收；旧四张按第 27 轮用户决策不追责。
    applicable = "R-" in path.name
    failed = [c["id"] for c in checks if not c["pass"]]
    return {
        "applicable": applicable,
        "verdict": ("EXEMPT" if not applicable else ("FAIL" if failed else "PASS")),
        "failed": failed,
        "checks": checks,
        "manualOnly": MANUAL_ONLY,
        "note": "EXEMPT = 第 27 轮用户已拍板旧 A 组不重出、不追 16:9 与四层切分；此处仍列出数值供对照，不作为返工单",
    }


def check_scene(path: Path) -> dict:
    im = Image.open(path)
    size = im.size
    whole, total = mapped_counts(im)
    ink = _ratio(whole, INK_GROUP)
    paper = _ratio(whole, PAPER_GROUP)
    bands, band_metrics = {}, {}
    for name, frac in BANDS.items():
        m = _region_metrics(im, frac)
        band_metrics[name] = {k: round(v, 5) for k, v in m.items()}
        bands[name] = round(m["dark"], 5)
    zone = _region_metrics(im, COMBAT_ZONE)
    zone_dark = zone["dark"]
    return {
        "file": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name,
        "variant": "repaint" if "R-" in path.name else "original",
        "size": list(size),
        "inkGroupRatio": round(ink, 5),
        "paperGroupRatio": round(paper, 5),
        "otherGroupRatio": round(max(0.0, 1.0 - ink - paper), 5),
        "bandDarkRatio": bands,
        "bandMetrics": band_metrics,
        "combatZoneDarkRatio": round(zone_dark, 5),
        "combatZoneMetrics": {k: round(v, 5) for k, v in zone.items()},
        "r22ProxyLevel": r22_level(zone_dark),
        "patchCompliance": patch_compliance(
            path, im, ink, paper,
            _region_metrics(im, BANDS["topQuarter"]),
            _region_metrics(im, BANDS["bottomQuarter"]), zone),
        "distinctColors": len(rgb_counter(im)),
    }


def collect_scene() -> list[Path]:
    # A2R- 是第 28 轮用户按 §4.1 补充句重出的喘息层；旧 A2 保留作改前对照，不覆盖。
    return sorted(UI_DIR.glob("A[1-4]-*palette24.png")) + \
           sorted(UI_DIR.glob("A[1-4]R-*palette24.png"))


def scene_summary(rows: list[dict]) -> dict:
    if not rows:
        return {}
    brightest = min(rows, key=lambda r: r["combatZoneDarkRatio"])["file"].split("/")[-1][:2]
    darkest = max(rows, key=lambda r: r["combatZoneDarkRatio"])["file"].split("/")[-1][:2]
    return {
        "brightest": brightest,
        "darkest": darkest,
        "r22ProxyHigh": [r["file"].split("/")[-1][:2] for r in rows
                         if r["r22ProxyLevel"] == "HIGH"],
        "repaintVariants": [r["file"].split("/")[-1] for r in rows if r["variant"] == "repaint"],
        "patchVerdicts": {r["file"].split("/")[-1]: r["patchCompliance"]["verdict"]
                          for r in rows if r["patchCompliance"]["applicable"]},
        "note": "按 r22ProxyLevel 排序，仅为回稿文件代理指标；R22 仍待实机实测",
    }

# ---------------------------------------------------------------- sheet 模式
GRID_BY_PREFIX = {"B-": (1, 2), "C1-": (2, 2), "C2-": (5, 2)}
SHEET_PREFIXES = tuple(GRID_BY_PREFIX)


def sheet_grid(path: Path, override: tuple[int, int] | None) -> tuple[int, int] | None:
    if override:
        return override
    for prefix, grid in GRID_BY_PREFIX.items():
        if path.name.startswith(prefix):
            return grid
    return None


def collect_sheet(targets: list[str]) -> list[Path]:
    if not targets:
        files: list[Path] = []
        for prefix in SHEET_PREFIXES:
            files.extend(UI_DIR.glob(prefix + "*.png"))
        # 同时有 original 与吸附版时，只体检吸附版；original 保留作证据
        snapped = {p.name.replace("_palette24.png", "") for p in files
                   if p.name.endswith("_palette24.png")}
        files = [p for p in files
                 if p.name.endswith("_palette24.png")
                 or p.name.replace("_original.png", "") not in snapped]
        return sorted(set(files))
    out: list[Path] = []
    for t in targets:
        p = Path(t)
        if not p.is_absolute():
            p = ROOT / p
        if p.is_dir():
            out.extend(sorted(p.glob("*.png")))
        elif p.exists():
            out.append(p)
    return out


def _content_ratio(rgba: Image.Image) -> float:
    """非白且不透明的内容像素占比（纯白底是 sprite 形状板的背景）。"""
    buf = rgba.tobytes()
    total = len(buf) // 4
    content = 0
    for i in range(0, len(buf), 4):
        if buf[i + 3] > 0 and not (buf[i] > 246 and buf[i + 1] > 246 and buf[i + 2] > 246):
            content += 1
    return content / total if total else 0.0


def check_sheet(path: Path, grid_override: tuple[int, int] | None = None,
                base: dict | None = None) -> dict:
    grid = sheet_grid(path, grid_override)
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    findings: list[dict] = []

    def add(level: str, fid: str, detail: str) -> None:
        findings.append({"id": fid, "level": level, "detail": detail})

    # 基础像素指标：复用 check_ui_art 的冻结阈值
    b = base or cua.check_one(path, cua.load_palette(), "icon")["metrics"]
    out_ratio = b["outOfPaletteRatio"]
    alpha_ratio = b["semiTransparentRatio"]
    soft_ratio = b["softEdgeRatio"]
    white_ratio = b["pureWhiteRatio"]

    if out_ratio > cua.OUT_FAIL:
        add("FAIL", "out_of_palette", f"越界色 {out_ratio * 100:.2f}%（> 10%）")
    elif out_ratio > cua.OUT_WARN:
        add("WARN", "out_of_palette", f"越界色 {out_ratio * 100:.2f}%（> 2%）")
    if alpha_ratio > cua.ALPHA_FAIL:
        add("FAIL", "semi_transparent", f"半透明 {alpha_ratio * 100:.2f}%（要求 0）")
    elif alpha_ratio > cua.ALPHA_WARN:
        add("WARN", "semi_transparent", f"半透明 {alpha_ratio * 100:.2f}%（要求 0）")
    if soft_ratio > cua.SOFT_WARN:
        add("WARN", "soft_edges", f"边缘过渡色 {soft_ratio * 100:.2f}%（疑似抗锯齿 / 柔边）")

    # 画幅：B / C 组按提示词都是 1:1 方图（参考稿层只记 WARN，不据此拉伸）
    if max(w, h) and abs(w - h) / max(w, h) > 0.02:
        add("WARN", "aspect_ratio", f"{w}x{h} 不是 1:1 方图（提示词要求方图）")

    # 纯白底：sprite 形状板以 #FFFFFF 为底
    if white_ratio < 0.35:
        add("FAIL", "white_background", f"纯白底仅 {white_ratio * 100:.2f}%（预期 >= 50%）")
    elif white_ratio < 0.50:
        add("WARN", "white_background", f"纯白底 {white_ratio * 100:.2f}%（预期 >= 50%）")

    # 1px 纯黑描边
    mapped, total = mapped_counts(im)
    black_ratio = mapped[BLACK] / total if total else 0.0
    if black_ratio < 0.001:
        add("WARN", "black_outline", f"描边黑像素 {black_ratio * 100:.3f}%（提示词要求 1px 黑描边）")

    cells: list[dict] = []
    row_pairs: list[dict] = []
    empty_cells: list[str] = []
    crowded_centers: list[str] = []
    # 「同行两格是同一状态的第 1/2 帧」只对 C2 overlay 成立（docs/20 §4 overlay 提示词）。
    # B 组两格是两个不同 Boss、C1 组每行是两种不同技能，本来就该差异大，不能套脉动规则。
    pair_is_pulse = path.name.startswith("C2-") or grid == (5, 2)
    if grid:
        rows, cols = grid
        margin = 0.04
        for r in range(rows):
            for c in range(cols):
                x0 = int((c + margin) * w / cols)
                x1 = int((c + 1 - margin) * w / cols)
                y0 = int((r + margin) * h / rows)
                y1 = int((r + 1 - margin) * h / rows)
                cell = im.crop((x0, y0, x1, y1))
                cr = _content_ratio(cell)
                # 中央 60% 区域的内容占比
                cw, ch = cell.size
                center = cell.crop((int(cw * 0.2), int(ch * 0.2),
                                    int(cw * 0.8), int(ch * 0.8)))
                center_content = _content_ratio(center)
                cells.append({
                    "row": r, "col": c,
                    "contentRatio": round(cr, 5),
                    "centerContentRatio": round(center_content, 5),
                })
                if cr < 0.01:
                    empty_cells.append(f"{r + 1}-{c + 1}")
                # overlay 形状板要求中心留白 >= 70%
                if path.name.startswith("C2-") or (grid == (5, 2)):
                    if center_content > 0.30:
                        crowded_centers.append(f"{r + 1}-{c + 1}({center_content * 100:.0f}%)")
            if cols >= 2 and rows >= 1:
                a = cells[r * cols]["contentRatio"]
                bb = cells[r * cols + 1]["contentRatio"]
                diff = abs(a - bb) / max(a, bb, 1e-9)
                row_pairs.append({
                    "row": r,
                    "relativeDiff": round(diff, 5),
                    "kind": "pulse" if pair_is_pulse else "distinct",
                })
                if pair_is_pulse:
                    if diff > 0.50:
                        add("FAIL", "pulse_mismatch",
                            f"第 {r + 1} 行两帧内容量差 {diff * 100:.1f}%（只允许 1px 级脉动）")
                    elif diff > 0.25:
                        add("WARN", "pulse_mismatch",
                            f"第 {r + 1} 行两帧内容量差 {diff * 100:.1f}%")
        if empty_cells:
            add("FAIL", "empty_cells",
                f"{len(empty_cells)}/{len(cells)} 格几乎为空：{', '.join(empty_cells)}")
        if crowded_centers:
            add("FAIL", "center_negative_space",
                f"{len(crowded_centers)}/{len(cells)} 格中心留白不足 70%：{', '.join(crowded_centers)}")
    else:
        add("WARN", "grid_unknown",
            "文件名没有 B- / C1- / C2- 前缀，未做网格检查；用 --grid R,C 指定")

    verdict = "FAIL" if any(f["level"] == "FAIL" for f in findings) else (
        "WARN" if any(f["level"] == "WARN" for f in findings) else "PASS")
    return {
        "file": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name,
        "size": [w, h],
        "grid": list(grid) if grid else None,
        "verdict": verdict,
        "metrics": {
            "outOfPaletteRatio": round(out_ratio, 5),
            "semiTransparentRatio": round(alpha_ratio, 5),
            "softEdgeRatio": round(soft_ratio, 5),
            "pureWhiteRatio": round(white_ratio, 5),
            "blackOutlineRatio": round(black_ratio, 5),
        },
        "cells": cells,
        "rowPairs": row_pairs,
        "pairKind": "pulse" if pair_is_pulse else "distinct",
        "findings": findings,
    }

# ---------------------------------------------------------------- 合成图自检
def _scene_good() -> Image.Image:
    """按 docs/20 §4.1 补充句画的分层 16:9 好图：四带浅亮、下部不压暗、前景只在边缘。"""
    mo, paper = PAL["groups"]["mo"], PAL["groups"]["xuanzhi"]
    im = Image.new("RGB", (1600, 900), paper[2])
    d = ImageDraw.Draw(im)
    d.rectangle((0, 225, 1600, 900), fill=paper[1])
    for i in range(8):                       # L1 山影（墨亮阶，占该带约 8%）
        x = i * 200
        d.polygon([(x, 225), (x + 60, 145), (x + 120, 225)], fill=mo[2])
    for i in range(4):                       # L2 立柱（墨中阶，稀疏）
        x = 200 + i * 400
        d.rectangle((x, 300, x + 40, 500), fill=mo[1])
    d.rectangle((0, 860, 150, 900), fill=mo[0])       # L4 左右下缘少量剪影
    d.rectangle((1450, 860, 1600, 900), fill=mo[0])
    return im


def _scene_bad() -> Image.Image:
    """把下部 1/4 整片压成暗色，命中补充句明令禁止项。"""
    im = _scene_good()
    d = ImageDraw.Draw(im)
    d.rectangle((0, 675, 1600, 900), fill=PAL["groups"]["mo"][0])
    return im


def _empty_sheet(size: int = 512) -> Image.Image:
    return Image.new("RGB", (size, size), WHITE)


def _outline_shape(draw: ImageDraw.ImageDraw, box, inset: int = 0) -> None:
    """在 box 内画一个靠边的空心硬边框 + 四角标记，中心自然留白。"""
    x0, y0, x1, y1 = box
    x0, y0, x1, y1 = x0 + inset, y0 + inset, x1 - inset, y1 - inset
    draw.rectangle((x0, y0, x1, y1), outline=BLACK, width=2)
    draw.rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2),
                   outline=PAL["groups"]["qingyu"][1], width=2)
    for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        draw.rectangle((cx - 3, cy - 3, cx + 3, cy + 3), fill=PAL["groups"]["jin"][1])


def _good_b() -> Image.Image:
    im = _empty_sheet()
    d = ImageDraw.Draw(im)
    for c in range(2):
        _outline_shape(d, (int(c * 256) + 18, 18, int((c + 1) * 256) - 18, 494), inset=0)
    return im


def _good_c2(pulse_shift: int = 1) -> Image.Image:
    im = _empty_sheet()
    d = ImageDraw.Draw(im)
    for r in range(5):
        for c in range(2):
            x0, x1 = c * 256 + 14, (c + 1) * 256 - 14
            y0, y1 = r * 102 + 8, (r + 1) * 102 - 8
            sh = pulse_shift if c == 1 else 0
            _outline_shape(d, (x0 + sh, y0, x1 - sh, y1))
    return im


def _distinct_b() -> Image.Image:
    """B 组两格是两个不同 Boss，体量本就该差很多（提示词要求塔主明显更高更宽）。"""
    im = _empty_sheet()
    d = ImageDraw.Draw(im)
    _outline_shape(d, (70, 170, 200, 350))
    _outline_shape(d, (300, 20, 490, 494))
    return im


def _bad_pulse() -> Image.Image:
    """C2 同行右格额外加竖线，制造远超 1px 脉动的帧间差异（不侵占中心留白）。"""
    im = _good_c2()
    d = ImageDraw.Draw(im)
    for r in range(5):
        for k in range(20):
            x = 256 + 18 + k * 3
            d.line((x, r * 102 + 12, x, (r + 1) * 102 - 12), fill=BLACK, width=2)
    return im


def _bad_gradient() -> Image.Image:
    im = _good_b()
    d = ImageDraw.Draw(im)
    for i in range(256):
        # 明显越出 24 色板的霓虹渐变
        d.line((128, 128 + i, 384, 128 + i), fill=(10 + i, 240 - i // 2, 180))
    return im


def _bad_alpha() -> Image.Image:
    im = _good_b().convert("RGBA")
    alpha = im.getchannel("A")
    d = ImageDraw.Draw(alpha)
    d.rectangle((64, 64, 448, 448), fill=128)
    im.putalpha(alpha)
    return im


def _bad_empty_cells() -> Image.Image:
    im = _empty_sheet()
    d = ImageDraw.Draw(im)
    _outline_shape(d, (14, 8, 242, 94))
    return im


def _bad_center_fill() -> Image.Image:
    im = _good_c2()
    d = ImageDraw.Draw(im)
    for r in range(5):
        for c in range(2):
            x0, x1 = c * 256 + 90, (c + 1) * 256 - 90
            y0, y1 = r * 102 + 30, (r + 1) * 102 - 30
            d.rectangle((x0, y0, x1, y1), fill=PAL["groups"]["zhusha"][1])
    return im


def run_selftest(verbose: bool = True) -> dict:
    cases = [
        ("good_b_1x2", "B-good.png", _good_b(), "PASS", None),
        ("good_c2_5x2", "C2-good.png", _good_c2(), "PASS", None),
        # 防回归：两个不同 Boss 体量差很大，不得被误判成「两帧脉动不一致」
        ("distinct_b_1x2", "B-distinct.png", _distinct_b(), "PASS", None),
        ("bad_pulse", "C2-pulse.png", _bad_pulse(), "FAIL", "pulse_mismatch"),
        ("bad_gradient", "B-gradient.png", _bad_gradient(), "FAIL", "out_of_palette"),
        ("bad_alpha", "B-alpha.png", _bad_alpha(), "FAIL", "semi_transparent"),
        ("bad_empty_cells", "C2-empty.png", _bad_empty_cells(), "FAIL", "empty_cells"),
        ("bad_center_fill", "C2-filled.png", _bad_center_fill(), "FAIL", "center_negative_space"),
    ]
    results = []
    with tempfile.TemporaryDirectory(prefix="xianxia-refart-") as td:
        for name, fname, im, expected, expected_fid in cases:
            p = Path(td) / fname
            im.save(p)
            res = check_sheet(p)
            fids = [f["id"] for f in res["findings"]]
            ok = res["verdict"] == expected and (expected_fid is None or expected_fid in fids)
            results.append({
                "case": name,
                "expected": expected,
                "actual": res["verdict"],
                "expectedFinding": expected_fid,
                "findings": fids,
                "ok": ok,
            })
            if verbose:
                print(f"  {'PASS' if ok else 'FAIL'} | {name:<20} "
                      f"期望 {expected} / 实得 {res['verdict']} | {','.join(fids) or '无 findings'}")
        # scene：docs/20 §4.1 补充句硬指标的判定能力
        scene_cases = [
            ("patch_good_16x9", "A2R-scene-good_palette24.png", _scene_good(), "PASS", None),
            ("patch_bad_dark_lower", "A2R-scene-bad_palette24.png", _scene_bad(), "FAIL", "l3_not_dark"),
        ]
        for name, fname, im, expected, expected_fail in scene_cases:
            p = Path(td) / fname
            im.save(p)
            pc = check_scene(p)["patchCompliance"]
            ok = pc["verdict"] == expected and (expected_fail is None or expected_fail in pc["failed"])
            results.append({
                "case": name,
                "expected": expected,
                "actual": pc["verdict"],
                "expectedFinding": expected_fail,
                "findings": pc["failed"],
                "ok": ok,
            })
            if verbose:
                print(f"  {'PASS' if ok else 'FAIL'} | {name:<20} "
                      f"期望 {expected} / 实得 {pc['verdict']} | {','.join(pc['failed']) or '全部达标'}")
    passed = sum(1 for r in results if r["ok"])
    verdict = "PASS" if passed == len(results) else "FAIL"
    return {"verdict": verdict, "passed": passed, "total": len(results), "cases": results}

# ---------------------------------------------------------------- 主流程
def build_report(sheet_targets: list[str], grid_override: tuple[int, int] | None) -> dict:
    scenes = [check_scene(p) for p in collect_scene()]
    sheets = [check_sheet(p, grid_override) for p in collect_sheet(sheet_targets)]
    selftest = run_selftest(verbose=False)
    if not sheets:
        sheet_verdict = "NO_INPUT"
    elif any(s["verdict"] == "FAIL" for s in sheets):
        sheet_verdict = "FAIL"
    elif any(s["verdict"] == "WARN" for s in sheets):
        sheet_verdict = "WARN"
    else:
        sheet_verdict = "PASS"
    return {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tool": "tools/check_reference_art.py",
        "round": 28,
        "paletteSource": "docs/asset-manifest-pixel.json（24 色锁定板）",
        "scope": "A 组塔层背景 + B/C 组 sprite 形状板参考稿",
        "definitions": DEFINITIONS,
        "scene": {"files": scenes, "summary": scene_summary(scenes)},
        "sheet": {
            "verdict": sheet_verdict,
            "files": sheets,
            "note": "B/C 组回稿到达后重跑 all 即会自动纳入；未到达时 verdict=NO_INPUT 是正常状态",
        },
        "selftest": selftest,
        "note": NOTE,
        "verdictMeaning": ("verdict 只表示工具自身健康（合成图自检全绿且 A 组四张齐全），"
                           "不代表回稿合格；回稿结果看 scene / sheet 各自字段"),
        "verdict": "PASS" if (selftest["verdict"] == "PASS" and len(scenes) >= 4) else "FAIL",
    }


def main(argv: list[str]) -> int:
    args = list(argv[1:])
    grid_override = None
    if "--grid" in args:
        i = args.index("--grid")
        if i + 1 >= len(args):
            print("[FAIL] --grid 需要 R,C，如 --grid 5,2", file=sys.stderr)
            return 2
        try:
            r, c = args[i + 1].split(",")
            grid_override = (int(r), int(c))
        except ValueError:
            print("[FAIL] --grid 格式应为 R,C", file=sys.stderr)
            return 2
        del args[i:i + 2]
    mode = "all"
    if args and (not args[0].startswith("-") or args[0] in ("--selftest", "--check")):
        mode = args.pop(0)

    if mode == "--selftest":
        st = run_selftest()
        print(f"REFSELFTEST|{st['verdict']}|{st['passed']}/{st['total']}")
        return 0 if st["verdict"] == "PASS" else 1

    if mode == "sheet":
        paths = collect_sheet(args)
        rows = [check_sheet(p, grid_override) for p in paths]
        for r in rows:
            m = r["metrics"]
            print(f"{r['verdict']:<4} | {r['file']} | {r['size'][0]}x{r['size'][1]}"
                  f" | 网格 {r['grid']} | 纯白 {m['pureWhiteRatio'] * 100:.1f}%"
                  f" | 越界 {m['outOfPaletteRatio'] * 100:.2f}%"
                  f" | 半透明 {m['semiTransparentRatio'] * 100:.2f}%")
            for f in r["findings"]:
                print(f"       └ {f['level']:<4} {f['id']}: {f['detail']}")
        print(f"REFART|sheet={len(rows)}")
        return 1 if any(r["verdict"] == "FAIL" for r in rows) else 0

    report = build_report(args, grid_override)
    if mode == "--check":
        if not REPORT.exists():
            print("REFART|FAIL|报告不存在")
            return 1
        old = json.loads(REPORT.read_text(encoding="utf-8"))
        a = [(r["file"], r["inkGroupRatio"], r["paperGroupRatio"],
              r["combatZoneDarkRatio"]) for r in old["scene"]["files"]]
        b = [(r["file"], r["inkGroupRatio"], r["paperGroupRatio"],
              r["combatZoneDarkRatio"]) for r in report["scene"]["files"]]
        ok = a == b and old["selftest"]["verdict"] == "PASS"
        print(f"REFART|{'PASS' if ok else 'FAIL'}|scene={len(a)}|selftest={old['selftest']['verdict']}")
        return 0 if ok else 1

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    for r in report["scene"]["files"]:
        print(f"SCENE | {r['file'].split('/')[-1]:<44} | {r['size'][0]}x{r['size'][1]}"
              f" | 深墨 {r['inkGroupRatio'] * 100:5.1f}%"
              f" / 浅宣纸 {r['paperGroupRatio'] * 100:5.1f}%"
              f" | 战斗区暗 {r['combatZoneDarkRatio'] * 100:5.1f}%"
              f" | R22代理 {r['r22ProxyLevel']:<6}"
              f" | 补充句 {r['patchCompliance']['verdict']}")
    for r in report["sheet"]["files"]:
        print(f"SHEET | {r['file'].split('/')[-1]:<44} | {r['verdict']:<4}"
              f" | 网格 {r['grid']} | findings={len(r['findings'])}")
    st = report["selftest"]
    print(f"SELFTEST|{st['verdict']}|{st['passed']}/{st['total']}")
    print(f"REFART|{report['verdict']}|scene={len(report['scene']['files'])}"
          f"|sheet={len(report['sheet']['files'])}|selftest={st['passed']}/{st['total']}"
          f"|report=docs/reference-art-report.json")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
