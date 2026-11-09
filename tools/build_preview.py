#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_preview.py —— 生成自包含的像素素材动画预览页。

用途：把 assets/char 与 assets/vfx/frames 的序列帧、assets/_preview 的 GIF
      全部以 base64 内嵌进单个 HTML，换账号 / 换机器只需带走这一个文件。

用法（在项目根目录执行）：
    python3 tools/build_preview.py
    # 输出：assets/_preview/vfx-preview.html

只依赖 Python 标准库，不需要 Pillow。源素材不变时可反复重跑，不消耗积分。
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAR = ROOT / "assets" / "char"
VFX = ROOT / "assets" / "vfx" / "frames"
PREVIEW = ROOT / "assets" / "_preview"
OUT = PREVIEW / "vfx-preview.html"

CHAR_FILES = [
    "char_player_idle_r_00.png",
    "char_player_idle_r_01.png",
    "char_player_idle_r_02.png",
    "char_player_cast_r_00.png",
]
VFX_FILES = [f"vfx_sword_qi_{i:02d}.png" for i in range(4)]
GIF_FILES = {"gif_vfx": "vfx_sword_qi.gif", "gif_char": "char_player.gif"}


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def build_payload():
    """返回 (内嵌资源表, 自动发现的素材组, GIF 列表)。

    自动发现部分扫描各资源目录的【引擎 JSON】（排除 *_report.json）：
    规整脚本每产出一组帧就写一份引擎 JSON，所以这里无需手工登记新批次，
    换账号重跑本脚本即自动包含所有已产素材。
    """
    data: dict[str, str] = {}
    for name in CHAR_FILES:
        data[f"char:{name}"] = "data:image/png;base64," + b64(CHAR / name)
    for name in VFX_FILES:
        data[f"vfx:{name}"] = "data:image/png;base64," + b64(VFX / name)
    for key, name in GIF_FILES.items():
        data[key] = "data:image/gif;base64," + b64(PREVIEW / name)

    groups = []
    for rel in ("char", "enemy", "boss", "vfx/frames", "vfx/overlay"):
        folder = ROOT / "assets" / rel
        if not folder.exists():
            continue
        for jf in sorted(folder.glob("*.json")):
            if jf.name.endswith("_report.json"):
                continue
            meta = json.loads(jf.read_text(encoding="utf-8"))
            frames = [n for n in meta.get("frames", []) if (jf.parent / n).exists()]
            if not frames:
                continue
            gid = meta.get("id", jf.stem)
            for n in frames:
                data[f"g:{gid}:{n}"] = "data:image/png;base64," + b64(jf.parent / n)
            groups.append({"id": gid, "kind": meta.get("kind", "?"),
                           "dir": f"assets/{rel}", "frames": frames,
                           "fps": float(meta.get("fps", 8))})

    gifs = []
    for gf in sorted(PREVIEW.glob("*.gif")):
        key = f"gif:{gf.stem}"
        data[key] = "data:image/gif;base64," + b64(gf)
        gifs.append({"key": key, "name": gf.name})
    return data, groups, gifs


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>九重天梯 · 像素特效动画预览</title>
<style>
  :root{
    --ink:#12161F; --ink2:#2A3140; --ink3:#4A5568;
    --paper:#E8DFC8; --paper2:#C9BFA3; --paper3:#8A8268;
    --jade:#5FA8A0; --jadeD:#2F6E6A; --jadeL:#9BD4CC;
    --cinnabar:#C8453B; --gold:#D9A441;
  }
  *{box-sizing:border-box}
  body{
    margin:0; background:var(--ink); color:var(--paper);
    font:13px/1.6 "SF Mono",Menlo,Consolas,"PingFang SC","Microsoft YaHei",monospace;
    -webkit-font-smoothing:none;
  }
  .wrap{max-width:1180px;margin:0 auto;padding:28px 22px 60px}
  header{border-bottom:1px solid var(--ink3);padding-bottom:18px;margin-bottom:22px}
  h1{font-size:20px;margin:0 0 6px;letter-spacing:1px;color:var(--paper)}
  h1 span{color:var(--gold)}
  .sub{color:var(--paper3);font-size:12px}
  .badge{display:inline-block;border:1px solid var(--jadeD);color:var(--jadeL);
         padding:1px 7px;margin-right:6px;font-size:11px}
  .badge.warn{border-color:var(--cinnabar);color:#E8806F}

  .bar{
    position:sticky;top:0;z-index:20;background:var(--ink2);
    border:1px solid var(--ink3);padding:10px 10px;margin-bottom:20px;
    display:flex;flex-wrap:wrap;gap:9px;align-items:center;
  }
  .grp{display:flex;align-items:center;gap:4px}
  .grp>label{color:var(--paper3);font-size:11px;margin-right:2px}
  button{
    font:inherit;font-size:12px;color:var(--paper);background:var(--ink);
    border:1px solid var(--ink3);padding:4px 8px;cursor:pointer;
  }
  button:hover{border-color:var(--jade);color:var(--jadeL)}
  button.on{background:var(--jadeD);border-color:var(--jade);color:#fff}
  button.primary{border-color:var(--gold);color:var(--gold);min-width:82px}
  .sep{width:1px;height:20px;background:var(--ink3)}

  section{margin-bottom:34px}
  h2{font-size:14px;margin:0 0 5px;color:var(--gold);letter-spacing:.5px}
  h2 em{font-style:normal;color:var(--paper3);font-size:11px;font-weight:400;margin-left:8px}
  .note{color:var(--paper3);font-size:11px;margin:0 0 12px}
  .stage{
    display:inline-block;padding:14px;border:1px solid var(--ink3);
    overflow:auto;max-width:100%;
  }
  .stage.bg-ink{background:var(--ink)}
  .stage.bg-paper{background:var(--paper)}
  .stage.bg-checker{
    background:repeating-conic-gradient(var(--paper2) 0% 25%,var(--paper) 0% 50%) 0 0/16px 16px;
  }
  canvas{display:block;image-rendering:pixelated;image-rendering:crisp-edges}
  .row{display:flex;gap:20px;flex-wrap:wrap;align-items:flex-start}
  .cell{min-width:0}
  .cell h3{font-size:12px;margin:0 0 8px;color:var(--jadeL);font-weight:400}
  .meta{margin-top:8px;font-size:11px;color:var(--paper3)}
  .meta b{color:var(--gold);font-weight:400}

  .frames{display:flex;gap:10px;flex-wrap:wrap}
  .frames figure{margin:0;text-align:center}
  .frames img{
    image-rendering:pixelated;image-rendering:crisp-edges;
    background:var(--ink);border:1px solid var(--ink3);display:block;
  }
  .frames figcaption{font-size:10px;color:var(--paper3);margin-top:4px}

  .callout{
    border-left:3px solid var(--cinnabar);background:#241a1c;
    padding:10px 14px;margin:14px 0 0;font-size:12px;color:var(--paper2);
  }
  .callout b{color:#E8806F;font-weight:400}
  .palette{display:flex;gap:0;margin-top:10px;flex-wrap:wrap}
  .palette i{width:22px;height:22px;display:block;border:1px solid rgba(255,255,255,.08)}
  a.dl{color:var(--jadeL);text-decoration:none;border-bottom:1px dotted var(--jadeD)}
  a.dl:hover{color:var(--gold);border-color:var(--gold)}
  footer{border-top:1px solid var(--ink3);padding-top:16px;color:var(--paper3);font-size:11px}
  .gifrow{display:flex;gap:20px;flex-wrap:wrap;margin-top:12px}
  .gifrow img{image-rendering:pixelated;border:1px solid var(--ink3);width:256px;height:256px}
  .lib{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px;margin-top:12px}
  .libcard{background:var(--ink2);border:1px solid var(--ink3);padding:10px;text-align:center}
  .libh{font-size:11px;color:var(--jadeL);margin-bottom:8px;word-break:break-all}
  .libimg{width:180px;height:180px;image-rendering:pixelated;image-rendering:crisp-edges;
          background:var(--ink);border:1px solid var(--ink3);display:block;margin:0 auto}
  .libcap{font-size:10px;color:var(--gold);margin-top:7px;word-break:break-all}
  .libsub{font-size:10px;color:var(--paper3);margin-top:3px}
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>九重天梯 · <span>像素特效动画预览</span></h1>
  <div class="sub">
    <span class="badge">64×64 RGBA</span>
    <span class="badge">24 色板 · 越界色 0</span>
    <span class="badge">NEAREST 硬边</span>
    <span class="badge warn">样板批次 · 未入引擎实测</span>
  </div>
  <div class="sub" style="margin-top:6px">主角 idle 3 帧 / 施法 1 帧 · 剑气特效 4 帧 · 单文件自包含（图片已内嵌，可单独带走）</div>
</header>

<div class="bar">
  <div class="grp">
    <button id="btnPlay" class="primary">⏸ 暂停</button>
    <button id="btnPrev">◀ 上一帧</button>
    <button id="btnNext">下一帧 ▶</button>
  </div>
  <div class="sep"></div>
  <div class="grp"><label>速度</label>
    <button data-speed="0.5">0.5×</button>
    <button data-speed="1" class="on">1×</button>
    <button data-speed="2">2×</button>
  </div>
  <div class="sep"></div>
  <div class="grp"><label>放大</label>
    <button data-scale="4">4×</button>
    <button data-scale="6" class="on">6×</button>
    <button data-scale="8">8×</button>
  </div>
  <div class="sep"></div>
  <div class="grp"><label>背景</label>
    <button data-bg="ink" class="on">墨底</button>
    <button data-bg="paper">宣纸</button>
    <button data-bg="checker">棋盘</button>
  </div>
  <div class="sep"></div>
  <div class="grp"><label>发射点</label>
    <button data-offset="16" class="on">16px 现规格</button>
    <button data-offset="40">40px 建议</button>
  </div>
  <div class="sep"></div>
  <div class="grp"><button id="btnGuides" class="on">判定框 / 锚点 ✓</button></div>
</div>

<section>
  <h2>① 技能释放合成 <em>角色施法帧 + 剑气特效，按 SkillCaster.gd 的 vfx_requested 同帧出光</em></h2>
  <p class="note">逻辑坐标 176×72 · 角色脚底锚点对齐 · 时间轴 12 步 @12fps（待机 3 → 施法+特效 4 → 消散 2 → 回到待机）<br>切「宣纸」背景可检查亮核是否与底色相融；默认墨底为建议观感。空格播放 / ←→ 逐帧；URL 加 <code>?step=6</code> 可直达某步（1–12，暂停态）。</p>
  <div class="row">
    <div class="cell">
      <div class="stage bg-ink" id="stageCombo"><canvas id="cCombo"></canvas></div>
      <div class="meta">当前 <b id="stepLabel">—</b> · 时序 <b id="timeLabel">0.00s</b> · 合成仅为规格示意，<b>非 Godot 实测</b></div>
    </div>
    <div class="cell" style="max-width:430px">
      <div class="callout" id="callout">
        <b>⚠ 现规格有个重叠问题</b><br>
        <code>hitboxOffsetX = 16</code>，而特效帧半宽 32px —— 特效中心距角色中心仅 16px，
        能量弧会盖住角色主体。点右上「40px 建议」可直观看对比。
        这是<b>预览示意</b>，真实观感需在 Godot 里按锚点实测后定，别直接改数值。
      </div>
    </div>
  </div>
</section>

<section>
  <h2>② 分段播放 <em>特效 12fps / 待机 6fps，各自独立循环</em></h2>
  <p class="note">三个画布共享同一时间轴与播放控制，可暂停后逐帧检查</p>
  <div class="row">
    <div class="cell">
      <h3>剑气特效 · vfx_sword_qi</h3>
      <div class="stage bg-ink"><canvas id="cVfx"></canvas></div>
      <div class="meta">帧 <b id="vfxFrame">0</b>/4 · <b>12fps</b> · 生长→消散</div>
    </div>
    <div class="cell">
      <h3>主角待机 · char_player_idle_r</h3>
      <div class="stage bg-ink"><canvas id="cChar"></canvas></div>
      <div class="meta">帧 <b id="charFrame">0</b>/3 · <b>6fps</b> · 脚底对齐</div>
    </div>
    <div class="cell">
      <h3>施法定格 · cast_r_00</h3>
      <div class="stage bg-ink"><canvas id="cCast"></canvas></div>
      <div class="meta">单帧 · 与特效首帧同帧触发</div>
    </div>
  </div>
</section>

<section>
  <h2>③ 逐帧对照 <em>剑气 4 帧，放大后检查硬边与色板</em></h2>
  <div class="frames" id="frameStrip"></div>
  <div class="palette" id="palette"></div>
  <div class="meta">24 色锁定调色板（20 核心 + 4 预留位）· 本批越界色 <b>0</b></div>
</section>

<section>
  <h2>④ GIF 原片 <em>即使脚本被禁用也能直接看动画</em></h2>
  <div class="gifrow">
    <a class="dl" id="dlVfx" download="vfx_sword_qi.gif"><img id="imgGifVfx" alt="剑气特效 GIF"><br>↓ 下载剑气特效 GIF</a>
    <a class="dl" id="dlChar" download="char_player.gif"><img id="imgGifChar" alt="主角动画 GIF"><br>↓ 下载主角动画 GIF</a>
  </div>
  <p class="note" style="margin-top:12px">也可直接取项目内文件：<code>assets/_preview/vfx_sword_qi.gif</code>、<code>assets/_preview/char_player.gif</code></p>
</section>

<section>
  <h2>⑤ 素材库 <em>自动发现 <b id="libCount">0</b> 组；换账号重跑 <code>tools/build_preview.py</code> 即自动包含新批次</em></h2>
  <p class="note">每组按引擎 JSON 里的 fps 独立循环，与上方播放控制同步暂停 / 变速；新批次不需要改这个页面</p>
  <div class="lib" id="library"></div>
  <p class="note" style="margin-top:14px">全部 GIF 下载：<span id="gifLinks"></span></p>
</section>

<footer>
  生成脚本：<code>tools/build_preview.py</code>（标准库即可重跑，不消耗积分） ·
  资源规格：<code>docs/asset-manifest-pixel.json</code> ·
  生产报告：<code>docs/05-首批素材生产报告.md</code> ·
  交接入口：<code>docs/00-项目交接与进度.md</code><br>
  状态：样板批次。全量仍缺 71 人物帧 / 24 特效帧（或改程序化）/ 40–60 图标；
  角色偏正面非纯朝右、特效首帧与判定框对齐、字体授权、合规确认均<b>待实测 / 待查证</b>。
</footer>

</div>
<script>
/*__DATA__*/

const PALETTE = ["#12161F","#2A3140","#4A5568","#8A8268","#C9BFA3","#E8DFC8",
  "#2F6E6A","#5FA8A0","#9BD4CC","#7A2420","#C8453B","#E8806F",
  "#8A6520","#D9A441","#F2D089","#4A3A6B","#8A6FC4","#C0A8E0",
  "#000000","#FFFFFF","#333333","#555555","#777777","#999999"];

const CHAR_KEYS = ["char:char_player_idle_r_00.png","char:char_player_idle_r_01.png",
                   "char:char_player_idle_r_02.png","char:char_player_cast_r_00.png"];
const VFX_KEYS  = ["vfx:vfx_sword_qi_00.png","vfx:vfx_sword_qi_01.png",
                   "vfx:vfx_sword_qi_02.png","vfx:vfx_sword_qi_03.png"];

const IMG = {};
function loadImages(){
  const keys = Object.keys(DATA);
  return Promise.all(keys.map(k => new Promise(res => {
    const im = new Image();
    im.onload = () => { IMG[k] = im; res(); };
    im.onerror = () => res();
    im.src = DATA[k];
  })));
}

let playing = true, speed = 1, scale = 6, bg = "ink", guides = true, offset = 16;
let t = 0, last = 0;
const VFX_MS = 1000/12, CHAR_MS = 1000/6;
const COMBO_STEPS = 12;
// step: [角色帧(0-2 idle / 3 cast), 特效帧(0-3) 或 -1, 标签]
const TIMELINE = [
  [0,-1,"待机 1"],[1,-1,"待机 2"],[2,-1,"待机 3"],
  [3, 0,"施法 · 起手火花"],[3, 1,"施法 · 弯月初成"],
  [3, 2,"施法 · 大扫斩"],[3, 3,"施法 · 碎裂消散"],
  [3,-1,"特效结束"],[0,-1,"回到待机"],[1,-1,"待机 2"],
  [2,-1,"待机 3"],[0,-1,"待机 1"]
];

function ctxOf(id, w, h){
  const c = document.getElementById(id);
  if(c.width !== w || c.height !== h){ c.width = w; c.height = h; }
  c.style.width = (w*scale) + "px";
  c.style.height = (h*scale) + "px";
  const x = c.getContext("2d");
  x.imageSmoothingEnabled = false;
  x.clearRect(0,0,w,h);
  return x;
}
function cross(x, cx, cy, color){
  x.strokeStyle = color; x.lineWidth = 1;
  x.beginPath();
  x.moveTo(cx-3.5,cy+0.5); x.lineTo(cx+3.5,cy+0.5);
  x.moveTo(cx+0.5,cy-3.5); x.lineTo(cx+0.5,cy+3.5);
  x.stroke();
}
function dashRect(x, left, top, w, h, color){
  x.save(); x.strokeStyle = color; x.lineWidth = 1; x.setLineDash([3,2]);
  x.strokeRect(left+0.5, top+0.5, w-1, h-1); x.restore();
}

function draw(){
  const charStep = Math.floor(t/CHAR_MS) % 3;
  const stepIdx  = Math.floor(t/VFX_MS) % COMBO_STEPS;
  const [ci, vi, label] = TIMELINE[stepIdx];
  // 施法阶段与合成时间轴对齐，避免"合成是大扫斩、独立画布却是弯月"；待机时独立 4 帧循环
  const vfxStep  = (vi >= 0) ? vi : Math.floor(t/VFX_MS) % 4;

  // ① 合成 176x72：脚底 y=70 → 图顶 8（角色 bbox 底 62）；角色中心 (56,40)
  const W=176, H=72, CHAR_X=24, CHAR_Y=8, FOOT_Y=70;
  const cx = CHAR_X+32, cy = CHAR_Y+32;
  const vx = cx+offset-32, vy = cy-32;
  const g = ctxOf("cCombo", W, H);
  g.drawImage(IMG[CHAR_KEYS[ci]], CHAR_X, CHAR_Y);
  if(vi >= 0) g.drawImage(IMG[VFX_KEYS[vi]], vx, vy);
  if(guides){
    cross(g, cx, FOOT_Y, "#D9A441");                               // 脚底锚点
    cross(g, cx+offset, cy, "#9BD4CC");                            // 特效中心
    dashRect(g, cx+offset-12, cy-16, 24, 32, "#C8453B");           // hitbox 24x32
    g.strokeStyle="rgba(201,191,163,.28)"; g.lineWidth=1;
    g.beginPath(); g.moveTo(0,FOOT_Y+0.5); g.lineTo(W,FOOT_Y+0.5); g.stroke(); // 地面参考线
  }

  // ② 三个独立画布
  const a = ctxOf("cVfx", 64, 64);  a.drawImage(IMG[VFX_KEYS[vfxStep]], 0, 0);
  const b = ctxOf("cChar", 64, 64); b.drawImage(IMG[CHAR_KEYS[charStep]], 0, 0);
  const c = ctxOf("cCast", 64, 64); c.drawImage(IMG[CHAR_KEYS[3]], 0, 0);
  if(guides){ cross(a,32,32,"rgba(155,212,204,.7)"); }

  document.getElementById("stepLabel").textContent = `步 ${stepIdx+1}/12 · ${label}`;
  document.getElementById("timeLabel").textContent = (t/1000).toFixed(2)+"s";
  document.getElementById("vfxFrame").textContent = vfxStep;
  document.getElementById("charFrame").textContent = charStep;

  // 素材库：每组按自身 fps 独立循环（GROUPS 由 Python 自动发现注入）
  for(const g of GROUPS){
    const el = document.querySelector(`.libimg[data-group="${g.id}"]`);
    if(!el) continue;
    const i = Math.floor(t / (1000/g.fps)) % g.frames.length;
    const src = DATA[`g:${g.id}:${g.frames[i]}`];
    if(src && el.getAttribute("src") !== src) el.setAttribute("src", src);
    const cap = el.parentElement.querySelector(".libcap");
    if(cap) cap.textContent = `帧 ${i+1}/${g.frames.length} · ${g.frames[i]}`;
  }
}

function loop(now){
  if(!last) last = now;
  const dt = Math.min(now-last, 100);
  last = now;
  if(playing) t += dt*speed;
  draw();
  requestAnimationFrame(loop);
}

function setOn(sel, attr, val){
  document.querySelectorAll(sel).forEach(b => b.classList.toggle("on", b.dataset[attr] === String(val)));
}
function bind(){
  document.getElementById("btnPlay").onclick = e => {
    playing = !playing;
    e.target.textContent = playing ? "⏸ 暂停" : "▶ 播放";
  };
  const stepBy = dir => { t = Math.max(0, t + dir*VFX_MS); playing = false;
    document.getElementById("btnPlay").textContent = "▶ 播放"; draw(); };
  document.getElementById("btnPrev").onclick = () => stepBy(-1);
  document.getElementById("btnNext").onclick = () => stepBy(1);
  document.querySelectorAll("[data-speed]").forEach(b => b.onclick = () => {
    speed = parseFloat(b.dataset.speed); setOn("[data-speed]","speed",speed); });
  document.querySelectorAll("[data-scale]").forEach(b => b.onclick = () => {
    scale = parseInt(b.dataset.scale); setOn("[data-scale]","scale",scale); draw(); });
  document.querySelectorAll("[data-bg]").forEach(b => b.onclick = () => {
    bg = b.dataset.bg; setOn("[data-bg]","bg",bg);
    document.querySelectorAll(".stage").forEach(s => {
      s.classList.remove("bg-ink","bg-paper","bg-checker"); s.classList.add("bg-"+bg); });
  });
  const callout = document.getElementById("callout");
  const c16 = callout.innerHTML;
  const c40 = `<b>✓ 建议口径：发射点 40px</b><br>
    特效中心前移到角色中心 +40px，能量弧主体与角色轮廓基本错开（仍保留约 9px 交叠，读起来像"从身前斩出"）。
    这只是<b>预览示意</b>：真正要不要改 <code>hitboxOffsetX</code>，
    必须在 Godot 里按锚点与判定框实测后定，别直接把 16 改成 40。`;
  document.querySelectorAll("[data-offset]").forEach(b => b.onclick = () => {
    offset = parseInt(b.dataset.offset); setOn("[data-offset]","offset",offset);
    callout.innerHTML = (offset===16) ? c16 : c40;
    draw(); });
  document.getElementById("btnGuides").onclick = e => {
    guides = !guides; e.target.classList.toggle("on",guides);
    e.target.textContent = "判定框 / 锚点 " + (guides?"✓":"✗"); draw(); };
  document.addEventListener("keydown", e => {
    if(e.code==="Space"){ e.preventDefault(); document.getElementById("btnPlay").click(); }
    if(e.code==="ArrowRight") stepBy(1);
    if(e.code==="ArrowLeft") stepBy(-1);
  });
}

function buildStatic(){
  const strip = document.getElementById("frameStrip");
  VFX_KEYS.forEach((k,i) => {
    const f = document.createElement("figure");
    const im = document.createElement("img");
    im.src = DATA[k]; im.width = 64*scale; im.height = 64*scale;
    im.dataset.frame = i; im.style.background = "var(--ink)";
    const cap = document.createElement("figcaption");
    cap.textContent = `帧 0${i} · ${["火花","弯月","扫斩","碎裂"][i]}`;
    f.appendChild(im); f.appendChild(cap); strip.appendChild(f);
  });
  const pal = document.getElementById("palette");
  PALETTE.forEach(c => { const i=document.createElement("i"); i.style.background=c;
    i.title=c; pal.appendChild(i); });
  const gv = document.getElementById("imgGifVfx"); gv.src = DATA.gif_vfx;
  const gc = document.getElementById("imgGifChar"); gc.src = DATA.gif_char;
  document.getElementById("dlVfx").href = DATA.gif_vfx;
  document.getElementById("dlChar").href = DATA.gif_char;
  document.querySelectorAll("[data-scale]").forEach(b => b.addEventListener("click", () => {
    document.querySelectorAll(".frames img").forEach(im => {
      im.width = 64*scale; im.height = 64*scale; });
  }));
  buildLibrary(); buildGifLinks();
}

function buildLibrary(){
  const lib = document.getElementById("library");
  GROUPS.forEach(g => {
    const card = document.createElement("div"); card.className = "libcard";
    const h = document.createElement("div"); h.className = "libh";
    h.textContent = `${g.id} · ${g.kind} · ${g.frames.length} 帧 @${g.fps}fps`;
    const im = document.createElement("img"); im.className = "libimg";
    im.dataset.group = g.id; im.alt = g.id;
    const cap = document.createElement("div"); cap.className = "libcap"; cap.textContent = "帧 1";
    const sub = document.createElement("div"); sub.className = "libsub"; sub.textContent = g.dir;
    card.append(h, im, cap, sub); lib.appendChild(card);
  });
  document.getElementById("libCount").textContent = GROUPS.length;
}

function buildGifLinks(){
  const box = document.getElementById("gifLinks");
  GIFS.forEach(g => {
    const a = document.createElement("a");
    a.className = "dl"; a.href = DATA[g.key]; a.download = g.name;
    a.textContent = `↓ ${g.name}`; a.style.marginRight = "14px";
    box.appendChild(a);
  });
}

loadImages().then(() => {
  buildStatic(); bind();
  const startStep = parseInt(new URLSearchParams(location.search).get("step") || "", 10);
  if(!isNaN(startStep) && startStep >= 1 && startStep <= COMBO_STEPS){
    t = (startStep-1)*VFX_MS; playing = false;
    document.getElementById("btnPlay").textContent = "▶ 播放";
  }
  draw();                       // 首帧立即出图，不依赖 rAF 是否被调度
  requestAnimationFrame(loop);
});
</script>
</body>
</html>
"""


def main() -> None:
    missing = [str(p) for p in [*(CHAR / n for n in CHAR_FILES),
                                *(VFX / n for n in VFX_FILES),
                                *(PREVIEW / n for n in GIF_FILES.values())]
               if not p.exists()]
    if missing:
        raise SystemExit("缺少素材，请先跑 tools/regularize_sprites.py：\n  " + "\n  ".join(missing))

    payload, groups, gifs = build_payload()
    inject = ("const DATA = " + json.dumps(payload, separators=(",", ":")) + ";\n"
              + "const GROUPS = " + json.dumps(groups, ensure_ascii=False, separators=(",", ":")) + ";\n"
              + "const GIFS = " + json.dumps(gifs, ensure_ascii=False, separators=(",", ":")) + ";")
    html = TEMPLATE.replace("/*__DATA__*/", inject)
    OUT.write_text(html, encoding="utf-8")
    print(f"生成 {OUT.relative_to(ROOT)} | {len(html):,} 字符 | 内嵌 {len(payload)} 个资源 "
          f"| 自动发现 {len(groups)} 组 / {len(gifs)} 个 GIF")
    print("自包含单文件，可单独复制 / 换账号带走；重跑不消耗积分。")


if __name__ == "__main__":
    main()
