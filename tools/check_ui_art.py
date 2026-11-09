#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UI 回稿体检：外部模型出的界面图是否守住工程规格。

用法：
    python3 tools/check_ui_art.py previews/ui/main-menu.png
    python3 tools/check_ui_art.py previews/ui/                 # 整个目录
    python3 tools/check_ui_art.py --type icon assets/ui/icons  # 图标 / 图标样式表
    python3 tools/check_ui_art.py --type auto previews/ui/     # 自动按尺寸判类型

检查项（依据 docs/04 §4 / docs/07 §4 / docs/12 §4 / docs/asset-manifest-pixel.json）：
    1. 尺寸：界面稿必须是 480x270 的整数倍；图标必须是 2 的幂且 <= 128
    2. 调色板越界像素占比（24 色锁定板）
    3. 半透明像素占比（alpha 介于 1..254）
    4. 边缘过渡色占比（抗锯齿/柔边痕迹的代理指标）
    5. 纯白像素占比（#FFFFFF 只用于闪白）

退出码：0 = 全部 PASS 或仅 WARN；1 = 存在 FAIL。
报告固定写到 docs/ui-art-check-report.json。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    print("需要 Pillow：pip3 install pillow", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "asset-manifest-pixel.json"
REPORT = ROOT / "docs" / "ui-art-check-report.json"

LOGICAL = (480, 270)
OUT_OF_PALETTE_DIST = 40.0      # 像素到最近调色板色的欧氏距离阈值
OUT_WARN, OUT_FAIL = 0.02, 0.10
ALPHA_WARN, ALPHA_FAIL = 0.002, 0.005
WHITE_WARN = 0.25
SOFT_WARN = 0.03
MAX_EDGE_SAMPLES = 200_000       # 柔边检测最多采样这么多像素


def load_palette() -> list[tuple[int, int, int]]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pal = data["palette"]
    colors: list[tuple[int, int, int]] = []
    for grp in pal["groups"].values():
        for key in ("dark", "main", "light"):
            colors.append(_hex_to_rgb(grp[key]))
    for key in ("outline", "flash"):
        colors.append(_hex_to_rgb(pal["functional"][key]))
    return colors


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _is_pow2(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def classify_size(w: int, h: int, mode: str) -> tuple[bool, str]:
    """返回 (是否合规, 说明)。"""
    if mode == "icon":
        ok = _is_pow2(w) and _is_pow2(h) and w <= 128 and h <= 128
        return ok, f"{w}x{h} 应为 2 的幂且 <=128"
    if mode == "screen":
        ok = w % LOGICAL[0] == 0 and h % LOGICAL[1] == 0
        return ok, f"{w}x{h} 应为 480x270 的整数倍"
    # auto
    if w % LOGICAL[0] == 0 and h % LOGICAL[1] == 0:
        return True, f"{w}x{h} = 480x270 的整数倍"
    if _is_pow2(w) and _is_pow2(h) and w <= 128 and h <= 128:
        return True, f"{w}x{h} 为 2 的幂图标尺寸"
    return False, f"{w}x{h} 既不是 480x270 整数倍，也不是 2 的幂图标尺寸"


def check_one(path: Path, palette: list[tuple[int, int, int]], mode: str) -> dict:
    img = Image.open(path)
    rgba = img.convert("RGBA")
    w, h = rgba.size
    buf = rgba.tobytes()

    # 记忆化：同色像素只算一次最近调色板色
    memo: dict[tuple[int, int, int], tuple[str, float]] = {}

    def nearest(r: int, g: int, b: int) -> tuple[str, float]:
        key = (r, g, b)
        hit = memo.get(key)
        if hit is not None:
            return hit
        best, best_d = palette[0], 1e18
        for c in palette:
            d = (r - c[0]) ** 2 + (g - c[1]) ** 2 + (b - c[2]) ** 2
            if d < best_d:
                best_d, best = d, c
        res = ("#%02X%02X%02X" % best, best_d ** 0.5)
        memo[key] = res
        return res

    total = 0
    transparent = 0
    alpha_partial = 0
    white = 0
    out_of_palette = 0
    hist: dict[str, int] = {}
    nearest_index: list[tuple[str, float]] = []

    for i in range(0, len(buf), 4):
        r, g, b, a = buf[i], buf[i + 1], buf[i + 2], buf[i + 3]
        total += 1
        if a == 0:
            transparent += 1
            nearest_index.append(("", 0.0))
            continue
        if a < 255:
            alpha_partial += 1
        if r == 255 and g == 255 and b == 255:
            white += 1
        col, dist = nearest(r, g, b)
        if dist > OUT_OF_PALETTE_DIST:
            out_of_palette += 1
        else:
            hist[col] = hist.get(col, 0) + 1
        nearest_index.append((col, dist))

    # 边缘过渡色：越界像素，且邻域中存在「最近调色板色不同」的邻居
    # -> 说明它骑在两个调色板色块的交界上，典型是抗锯齿 / 柔边 / 渐变
    edge_soft = 0
    edge_sampled = 0
    if w > 2 and h > 2:
        step = max(1, int((w * h / MAX_EDGE_SAMPLES) ** 0.5))
        for y in range(1, h - 1, step):
            row = y * w
            for x in range(1, w - 1, step):
                idx = row + x
                own = nearest_index[idx][0]
                if nearest_index[idx][1] <= OUT_OF_PALETTE_DIST:
                    continue
                edge_sampled += 1
                for dy in (-1, 0, 1):
                    base = (y + dy) * w
                    hit = False
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        if nearest_index[base + (x + dx)][0] != own:
                            hit = True
                            break
                    if hit:
                        edge_soft += 1
                        break

    opaque_total = max(1, total - transparent)
    out_ratio = out_of_palette / opaque_total
    alpha_ratio = alpha_partial / total
    white_ratio = white / opaque_total
    soft_ratio = (edge_soft / edge_sampled) if edge_sampled else 0.0

    findings: list[dict] = []
    verdict = "PASS"

    size_ok, size_msg = classify_size(w, h, mode)
    if not size_ok:
        verdict = "FAIL"
        findings.append({"id": "size_rule", "level": "FAIL", "detail": size_msg})

    if out_ratio > OUT_FAIL:
        verdict = "FAIL"
    elif out_ratio > OUT_WARN:
        verdict = "WARN"
    if out_ratio > OUT_WARN:
        findings.append({
            "id": "out_of_palette",
            "level": "FAIL" if out_ratio > OUT_FAIL else "WARN",
            "detail": f"调色板越界像素 {out_ratio * 100:.2f}%"
                      f"（WARN > {OUT_WARN * 100:.0f}% / FAIL > {OUT_FAIL * 100:.0f}%）",
        })
    if alpha_ratio > ALPHA_WARN:
        if alpha_ratio > ALPHA_FAIL:
            verdict = "FAIL"
        findings.append({
            "id": "semi_transparent",
            "level": "FAIL" if alpha_ratio > ALPHA_FAIL else "WARN",
            "detail": f"半透明像素 {alpha_ratio * 100:.2f}%（像素风要求 0）",
        })
    if soft_ratio > SOFT_WARN:
        findings.append({
            "id": "soft_edges",
            "level": "WARN",
            "detail": f"边缘过渡色 {soft_ratio * 100:.2f}%（抽样 {edge_sampled} 像素），疑似抗锯齿/柔边，要求硬边",
        })
    if white_ratio > WHITE_WARN:
        findings.append({
            "id": "too_much_white",
            "level": "WARN",
            "detail": f"纯白像素 {white_ratio * 100:.2f}%（#FFFFFF 只用于闪白）",
        })

    # verdict 统一按 findings 的最高等级重算：
    # 避免前面 size_rule 判出的 FAIL 被后面 out_of_palette 的 WARN 分支覆盖。
    if any(f["level"] == "FAIL" for f in findings):
        verdict = "FAIL"
    elif any(f["level"] == "WARN" for f in findings):
        verdict = "WARN"
    else:
        verdict = "PASS"

    top = sorted(hist.items(), key=lambda kv: -kv[1])[:8]
    return {
        "file": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "size": [w, h],
        "sizeRule": mode,
        "sizeNote": size_msg,
        "verdict": verdict,
        "metrics": {
            "outOfPaletteRatio": round(out_ratio, 5),
            "semiTransparentRatio": round(alpha_ratio, 5),
            "softEdgeRatio": round(soft_ratio, 5),
            "softEdgeSampled": edge_sampled,
            "pureWhiteRatio": round(white_ratio, 5),
            "transparentRatio": round(transparent / total, 5),
            "distinctColors": len(memo),
        },
        "topPaletteHits": [{"color": c, "pixels": n} for c, n in top],
        "findings": findings,
    }


def collect(targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for t in targets:
        p = Path(t)
        if not p.is_absolute():
            p = ROOT / p
        if p.is_dir():
            files.extend(sorted(p.glob("*.png")))
        elif p.exists():
            files.append(p)
        else:
            print(f"[SKIP] 不存在：{t}", file=sys.stderr)
    return files


def main(argv: list[str]) -> int:
    mode = "auto"
    targets: list[str] = []
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--type" and i + 1 < len(argv):
            mode = argv[i + 1]
            i += 2
            continue
        if a.startswith("--"):
            i += 1
            continue
        targets.append(a)
        i += 1
    if not targets:
        targets = ["previews/ui"]
    files = collect(targets)
    if not files:
        print("[FAIL] 没有可检查的 PNG")
        return 1
    palette = load_palette()
    results = [check_one(f, palette, mode) for f in files]
    overall = "PASS"
    if any(r["verdict"] == "FAIL" for r in results):
        overall = "FAIL"
    elif any(r["verdict"] == "WARN" for r in results):
        overall = "WARN"

    report = {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tool": "tools/check_ui_art.py",
        "paletteSource": "docs/asset-manifest-pixel.json (24 色锁定板)",
        "sizeRuleMode": mode,
        "thresholds": {
            "outOfPaletteWarn": OUT_WARN,
            "outOfPaletteFail": OUT_FAIL,
            "semiTransparentWarn": ALPHA_WARN,
            "semiTransparentFail": ALPHA_FAIL,
            "softEdgeWarn": SOFT_WARN,
            "pureWhiteWarn": WHITE_WARN,
            "paletteDistance": OUT_OF_PALETTE_DIST,
        },
        "verdict": overall,
        "files": results,
        "note": "AI 生成图按 03 §4 只算参考稿，本报告是返工依据而非入库闸门；入库走程序化像素链路。",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    for r in results:
        m = r["metrics"]
        print(f"{r['verdict']:<4} | {r['file']} | {r['size'][0]}x{r['size'][1]}"
              f" | 越界 {m['outOfPaletteRatio'] * 100:.2f}%"
              f" | 半透明 {m['semiTransparentRatio'] * 100:.2f}%"
              f" | 柔边 {m['softEdgeRatio'] * 100:.2f}%"
              f" | 纯白 {m['pureWhiteRatio'] * 100:.2f}%")
        for f in r["findings"]:
            print(f"       └ {f['level']:<4} {f['id']}: {f['detail']}")
    print(f"UIART|{overall}|files={len(results)}|report=docs/ui-art-check-report.json")
    return 1 if overall == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
