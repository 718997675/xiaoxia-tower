#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UI 回稿色板吸附：把外部模型出的图量化到 24 色锁定板，输出 PNG。

用途（第 24 轮）：GPT-Image-2.0 等模型出的像素稿本身是硬边色块，但 JPEG 压缩或
截图会在硬边处产生振铃中间色（实测 77208 种颜色、柔边率 72.94%）。吸附到冻结
色板后越界 0% / 柔边 0%，且不损失画面结构。豆包那类平滑矢量图不适用本脚本
（量化会把曲线打成碎块），判断依据见 docs/19 与工作日志。

用法：
    python3 tools/snap_ui_palette.py previews/ui/00-anchor-gpt-image2-original.png
    python3 tools/snap_ui_palette.py previews/ui/                 # 批量处理目录
    python3 tools/snap_ui_palette.py src.png -o out.png           # 指定输出路径
    python3 tools/snap_ui_palette.py previews/ui/ --then-check    # 吸附后接着跑体检

规则：
  - 色值一律从 docs/asset-manifest-pixel.json 读取，不写死。
  - 全透明像素 (a=0) 保持 (0,0,0,0)，不参与吸附（② HUD 透明背景需要）。
  - 半透明像素 (1..254) 保留 alpha 并计数（像素风要求 0，需另行处理）。
  - 输出恒为 PNG；几何尺寸不变、不缩放不裁切。尺寸问题靠出图时选 16:9 画幅解决。
  - 目录模式跳过 *_palette24.png 与 *_original.png，避免重复处理。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    print("需要 Pillow：pip3 install pillow", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "asset-manifest-pixel.json"
SUFFIX = "_palette24"
SKIP_SUFFIXES = (SUFFIX, "_original")
EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
SIGNIFICANT_DIST = 40.0  # 与 check_ui_art.OUT_OF_PALETTE_DIST 保持一致


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def load_palette() -> list[tuple[int, int, int]]:
    """从冻结清单取 24 色（6 组 × 3 阶 + 描边 + 闪白）。"""
    pal = json.loads(MANIFEST.read_text(encoding="utf-8"))["palette"]
    colors = [
        _hex_to_rgb(grp[key])
        for grp in pal["groups"].values()
        for key in ("dark", "main", "light")
    ]
    colors += [_hex_to_rgb(pal["functional"][key]) for key in ("outline", "flash")]
    return colors


def snap_one(src: Path, dst: Path, palette: list[tuple[int, int, int]]) -> dict:
    img = Image.open(src)
    had_alpha = "A" in img.getbands() or "transparency" in img.info
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()

    # 与 check_ui_art.OUT_OF_PALETTE_DIST 同阈值：只有超过它才算「实质越界」，
    # JPEG 造成的极轻微色偏只算「微调」，两者分开报，避免把 99% 的微调误读成改动画面。
    memo: dict[tuple[int, int, int], tuple[tuple[int, int, int], float]] = {}

    def nearest(r: int, g: int, b: int) -> tuple[tuple[int, int, int], float]:
        key = (r, g, b)
        hit = memo.get(key)
        if hit is None:
            best, d2 = min(
                ((c, (r - c[0]) ** 2 + (g - c[1]) ** 2 + (b - c[2]) ** 2)
                 for c in palette),
                key=lambda t: t[1],
            )
            hit = (best, d2 ** 0.5)
            memo[key] = hit
        return hit

    opaque = changed = significant = semi = transparent = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                transparent += 1
                continue
            if a < 255:
                semi += 1
            opaque += 1
            best, dist = nearest(r, g, b)
            if dist > SIGNIFICANT_DIST:
                significant += 1
            if (r, g, b) != best:
                changed += 1
                px[x, y] = (best[0], best[1], best[2], a)

    out = rgba if had_alpha else rgba.convert("RGB")
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, "PNG", optimize=True)
    return {
        "src": str(src.relative_to(ROOT)) if src.is_relative_to(ROOT) else str(src),
        "dst": str(dst.relative_to(ROOT)) if dst.is_relative_to(ROOT) else str(dst),
        "size": [w, h],
        "distinctBefore": len(memo),
        "distinctAfter": len(set(px[x, y][:3] for y in range(h) for x in range(w)
                                 if px[x, y][3] != 0)),
        "changedPixels": changed,
        "changedRatio": round(changed / max(1, opaque), 5),
        "significantChanged": significant,
        "significantRatio": round(significant / max(1, opaque), 5),
        "semiTransparent": semi,
        "transparent": transparent,
        "keptAlpha": had_alpha,
    }


def collect(target: Path) -> list[Path]:
    if target.is_dir():
        return sorted(
            p for p in target.iterdir()
            if p.is_file() and p.suffix.lower() in EXTS
            and not any(p.stem.endswith(s) for s in SKIP_SUFFIXES)
        )
    return [target] if target.exists() else []


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="UI 回稿吸附到 24 色锁定板")
    ap.add_argument("target", help="图片文件或目录")
    ap.add_argument("-o", "--output", help="单文件模式下指定输出 PNG 路径")
    ap.add_argument("--then-check", action="store_true",
                    help="吸附完成后对目标目录跑 tools/check_ui_art.py")
    args = ap.parse_args(argv)

    target = Path(args.target)
    if not target.is_absolute():
        target = ROOT / target
    files = collect(target)
    if not files:
        print(f"[FAIL] 没有可处理的图片：{target}", file=sys.stderr)
        return 1

    palette = load_palette()
    print(f"色板来源：docs/asset-manifest-pixel.json（{len(palette)} 色）")
    results = []
    for f in files:
        dst = Path(args.output) if args.output and len(files) == 1 \
            else f.with_name(f.stem + SUFFIX + ".png")
        if not dst.is_absolute():
            dst = ROOT / dst if args.output else dst
        r = snap_one(f, dst, palette)
        results.append(r)
        print(f"OK | {r['src']} -> {r['dst']} | {r['size'][0]}x{r['size'][1]}"
              f" | 颜色 {r['distinctBefore']} -> {r['distinctAfter']}"
              f" | 实质越界 {r['significantRatio'] * 100:.2f}%"
              f" | 压缩微调 {r['changedRatio'] * 100:.2f}%"
              f" | 半透明 {r['semiTransparent']}")
        if r["semiTransparent"]:
            print(f"    └ 注意：含 {r['semiTransparent']} 个半透明像素，像素风要求 0")

    print(f"SNAP|files={len(results)}|palette={len(palette)}")
    if args.then_check:
        check_dir = target if target.is_dir() else target.parent
        rel = check_dir.relative_to(ROOT) if check_dir.is_relative_to(ROOT) else check_dir
        print(f"\n--- 接着跑体检：{rel} ---")
        proc = subprocess.run([sys.executable, str(ROOT / "tools" / "check_ui_art.py"),
                               str(rel)], cwd=ROOT, text=True,
                              capture_output=True)
        print(proc.stdout.strip())
        if proc.stderr.strip():
            print(proc.stderr.strip(), file=sys.stderr)
        return proc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
