#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第 29 轮素材的浏览器目检画板（单文件 / 零依赖 / 零网络请求，可复现）

用途：把 B3 Boss 帧表、B4 技能特效 / 命中 / 状态层、背景四深度层
      做成可交互的静态目检页，让「待人工目检」的项目真的能被人看见。

口径：
  - 这是【验证层】画板，不是游戏本体，也不是 UI 设计稿（Q17 未拍板）。
  - 所有图片内嵌 base64 data URI，file:// 双击即可打开，无外部请求。
  - 页面里的数字全部来自 docs/ 下已落盘的报告，不新造结论；
    帧率 / 贴图内存 / 实机对比度一律标「待实测」。
  - 产物不含机器绝对路径（final_selfcheck 的 absolute_paths 断言会扫）。

用法：
  python3 tools/build_asset_overview.py
  python3 tools/build_asset_overview.py --check   # 生成到内存比对，不写盘

产出：previews/asset-overview.html
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOSS = ROOT / "assets/boss"
VFX = ROOT / "assets/vfx/frames"
OVL = ROOT / "assets/vfx/overlay"
BG = ROOT / "assets/bg"
OUT = ROOT / "previews/asset-overview.html"

SCENES = [
    ("bg_normal", "常规塔层 1–3 层", "A1"),
    ("bg_rest", "喘息层 3/6/8", "A2R"),
    ("bg_high", "高层复合敌群 7", "A3"),
    ("bg_boss", "Boss 层 5/9", "A4"),
]
LEVELS = ["L1", "L2", "L3", "L4"]
SKILLS = [
    ("vfx_sword_qi", "剑气斩", "横向青玉弯月弧"),
    ("vfx_flying_sword", "御剑诀", "斜向三道飞剑"),
    ("vfx_thunder_talisman", "引雷符", "纵向落雷"),
    ("vfx_paper_puppet", "纸傀术", "方符展成傀儡"),
    ("vfx_dan_fire", "三昧丹火", "圆形火团"),
    ("vfx_rejuvenation", "回春诀", "环形青玉光晕"),
    ("vfx_fist_force", "破山拳罡", "贴地扇形波"),
    ("vfx_vajra_body", "金刚不坏", "六边形金罩"),
    ("vfx_hit", "通用命中", "四向星芒"),
]
OVERLAYS = [
    ("ovl_shield", "护盾", "六边青玉罩"),
    ("ovl_elite", "霸体 / 精英", "金框角标"),
    ("ovl_burn", "灼烧", "三火苗"),
    ("ovl_chill", "迟缓", "三冰晶"),
    ("ovl_affix", "词缀印文", "朱砂印"),
]
BOSSES = [
    ("boss_judge", "锁血判官（第 5 层）", 18, "横向梯形 + 乌纱帽 + 朱砂印文"),
    ("boss_tower_lord", "天梯之主（第 9 层）", 24, "高耸纵向 + 外扩肩甲 + 半环背光"),
]


def b64(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def collect_images() -> dict:
    imgs: dict[str, str] = {}
    for p in sorted(BOSS.glob("boss_*_r_*.png")):
        imgs[p.stem] = b64(p)
    for p in sorted(VFX.glob("vfx_*_[0-9][0-9].png")):
        imgs[p.stem] = b64(p)
    for p in sorted(OVL.glob("ovl_*_[0-9][0-9].png")):
        imgs[p.stem] = b64(p)
    for scene, _, _ in SCENES:
        folder = BG / scene
        for lv in LEVELS:
            p = folder / f"{scene}_{lv}.png"
            imgs[f"{scene}_{lv}"] = b64(p)
        imgs[f"{scene}_composite"] = b64(folder / f"{scene}_composite.png")
    return imgs


def collect_meta() -> dict:
    b = json.loads((ROOT / "docs/b3b4-build-report.json").read_text(encoding="utf-8"))
    g = json.loads((ROOT / "docs/bg-layers-report.json").read_text(encoding="utf-8"))
    q = json.loads((ROOT / "docs/qc-report.json").read_text(encoding="utf-8"))
    return {
        "b3b4": b["totals"],
        "bg": g["totals"],
        "qc": q["summary"],
        "bgScenes": [
            {"id": s["scene"], "floors": s["floors"], "ref": s["reference"],
             "l1Dark": s["layers"]["L1"]["darkRatio"],
             "combatDark": s["combatZone"]["darkPixelRatio"],
             "r22": s["combatZone"]["r22Proxy"],
             "l4": s["l4AreaRatio"],
             "layers": {k: {"coverage": s["layers"][k]["coverage"],
                            "outOfPalette": s["layers"][k]["outOfPalette"],
                            "semiAlpha": s["layers"][k]["semiAlphaLevels"]}
                        for k in LEVELS}}
            for s in g["scenes"]
        ],
        "groups": [{"id": x["id"], "frames": x["frameCount"],
                    "palette": x["outOfPaletteTotal"],
                    "semiAlpha": x["semiAlphaTotal"]} for x in b["groups"]],
    }


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>九重天梯 · 第 29 轮素材目检画板</title>
<style>
  :root{--ink:#12161F;--ink2:#2A3140;--paper:#E8DFC8;--paper2:#C9BFA3;
        --card:#F7F3E8;--jade:#2F6E6A;--red:#7A2420;--gold:#8A6520;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--paper);color:var(--ink);
       font:14px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}
  .wrap{max-width:1160px;margin:0 auto;padding:24px 20px 60px}
  h1{font-size:24px;margin:0 0 4px;letter-spacing:2px}
  h2{font-size:17px;margin:0 0 12px;padding-bottom:6px;border-bottom:2px solid var(--ink)}
  .sub{color:var(--ink2);font-size:13px;margin-bottom:16px}
  .notice{background:#FFF6DC;border:1px solid var(--gold);padding:10px 14px;margin:12px 0 22px;
          font-size:13px;border-radius:2px}
  .notice b{color:var(--red)}
  section{background:var(--card);border:1px solid var(--ink);padding:16px 18px;margin:0 0 20px}
  .row{display:flex;gap:14px;flex-wrap:wrap;align-items:flex-start}
  button{font:inherit;background:var(--paper2);color:var(--ink);border:1px solid var(--ink);
         padding:5px 12px;cursor:pointer}
  button.on{background:var(--jade);color:#fff}
  button:hover{filter:brightness(1.08)}
  label.chk{display:inline-flex;align-items:center;gap:5px;margin-right:12px;font-size:13px}
  .stage{position:relative;width:480px;height:270px;border:1px solid var(--ink);
         background:var(--paper);overflow:hidden;flex:0 0 auto}
  .stage img{position:absolute;top:0;left:0;width:480px;height:270px;
             image-rendering:pixelated;image-rendering:crisp-edges}
  .stage.zoom img{width:960px;height:540px}
  .stage.zoom{width:960px;height:540px}
  table{border-collapse:collapse;width:100%;font-size:12.5px;margin-top:10px}
  th,td{border:1px solid var(--ink2);padding:4px 7px;text-align:left}
  th{background:var(--paper2)}
  .ok{color:var(--jade);font-weight:600}
  .todo{color:var(--red);font-weight:600}
  .thumb{width:64px;height:64px;image-rendering:pixelated;border:1px solid var(--ink2);
         background:#1b2130;cursor:pointer}
  .thumb.sel{outline:3px solid var(--red)}
  .big{width:256px;height:256px;image-rendering:pixelated;border:1px solid var(--ink);
       background:#1b2130;flex:0 0 auto}
  .group{margin:0 0 16px}
  .group h3{font-size:14px;margin:0 0 6px}
  .strip{display:flex;gap:4px;flex-wrap:wrap}
  .tag{display:inline-block;background:var(--paper2);border:1px solid var(--ink2);
       padding:1px 6px;font-size:11px;margin-right:5px}
  .foot{font-size:12px;color:var(--ink2);margin-top:24px}
  code{background:#E3DCC6;padding:1px 4px;font-size:12px}
</style>
</head>
<body>
<div class="wrap">
  <h1>九重天梯 · 素材目检画板</h1>
  <div class="sub">第 31 轮（更正第 29 轮） · B3 两个 Boss / B4 剩余特效与状态层 / 背景四深度层 ·
    单文件零依赖，图片全部内嵌</div>

  <div class="notice">
    <b>口径提醒：</b>这是验证层画板，不是游戏本体，也不是 UI 设计稿。本批素材已改为
    <b>gpt-image2 回稿转录</b>：B / C1 / C2 / A 组回稿经裁格、去白底、分带切层、
    24 色复核后作为真实像素源，取代第 29 轮的几何重绘；用户原稿未改动，A2R 与
    08-icons 的平台水印已在转录时修补。默认入库为原稿保真、不调色，
    战斗区暗像素比超 30% 的三个场景已在报告中如实登记。
    每组 <code>status = 待目检与合规确认；不得直接入库</code>；
    <b>Q17 未拍板、GUI F5 未跑、未接任何 Godot 场景</b>；
    特效 / overlay 运行时仍按 Q24 走程序化 shader，PNG 仅形状样板；
    视差系数 0.15/0.45/1.0/1.30 是 PROPOSAL 待实测。
  </div>

  <section>
    <h2>① 背景四深度层（可逐层开关叠加）</h2>
    <div class="row" id="sceneBtns"></div>
    <div style="margin:12px 0 8px">
      <label class="chk"><input type="checkbox" id="c1" checked> L1 远景</label>
      <label class="chk"><input type="checkbox" id="c2" checked> L2 中景</label>
      <label class="chk"><input type="checkbox" id="c3" checked> L3 地面</label>
      <label class="chk"><input type="checkbox" id="c4" checked> L4 前景</label>
      <button id="zoomBtn">2× 放大</button>
      <button id="compositeBtn">只看合成图</button>
    </div>
    <div class="row">
      <div class="stage" id="stage">
        <img id="L1"><img id="L2"><img id="L3"><img id="L4">
      </div>
      <div style="flex:1;min-width:260px">
        <div id="sceneInfo"></div>
        <table id="layerTable"></table>
      </div>
    </div>
  </section>

  <section>
    <h2>② B3 · 两个 Boss 正式帧表（128×128）</h2>
    <div id="bossArea"></div>
  </section>

  <section>
    <h2>③ B4 · 8 技能 + 通用命中（64×64 × 4 帧）</h2>
    <div id="vfxArea"></div>
  </section>

  <section>
    <h2>④ B4 · 5 组状态 overlay（64×64 × 2 帧，同形状换亮阶）</h2>
    <div id="ovlArea"></div>
  </section>

  <section>
    <h2>⑤ 机器体检结论（来自已落盘报告）</h2>
    <div id="qcSummary"></div>
    <table id="groupTable"></table>
    <div style="margin-top:16px">
      <h3>仍需人工目检 / 待实测（机器不判，不得伪造 PASS）</h3>
      <ul>
        <li class="todo">Godot 按 F5 看像素硬边 / 480×270×4 整数缩放 / 朝右镜像（10 项目检表，docs/13 §9）</li>
        <li class="todo">R22 阴兵对比度、实机中央战斗区可读性；darkSet 只是亮度代理</li>
        <li class="todo">四层能否沿水平线独立切图、有无跨层连续深色块、有无文字水印</li>
        <li class="todo">贴图内存、帧率、hitboxOffsetX=16px、4× 实机排版</li>
        <li class="todo">动作幅度 / 造型精细度是参数化占位，不等于美术终稿</li>
        <li class="todo">Q17 拍板后才谈导入 Godot / 建正式战斗工程</li>
      </ul>
    </div>
  </section>

  <div class="foot">
    数据来源：<code>docs/b3b4-build-report.json</code> ·
    <code>docs/bg-layers-report.json</code> · <code>docs/qc-report.json</code>；
    生成器 <code>tools/build_asset_overview.py</code>。
    复跑：<code>python3 tools/build_asset_overview.py --check</code>、
    <code>python3 tools/qc_sprites.py</code>、<code>python3 tools/final_selfcheck.py</code>。
    完整口径见 <code>docs/22</code> 与 <code>docs/23</code>。
  </div>
</div>
<script>
const IMG = __IMG_JSON__;
const META = __META_JSON__;
const SCENES = __SCENES_JSON__;
const LEVELS = __LEVELS_JSON__;
const SKILLS = __SKILLS_JSON__;
const OVERLAYS = __OVERLAYS_JSON__;
const BOSSES = __BOSSES_JSON__;

function esc(s){return String(s).replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function imgData(k){return IMG[k] || '';}

/* ---- 背景四层 ---- */
let curScene = SCENES[0][0], compositeOnly = false;
function renderSceneBtns(){
  document.getElementById('sceneBtns').innerHTML = SCENES.map(s =>
    `<button data-s="${s[0]}" class="${s[0]===curScene?'on':''}">${esc(s[1])} · ${esc(s[2])}</button>`
  ).join('');
  document.querySelectorAll('#sceneBtns button').forEach(b => b.onclick = () => {
    curScene = b.dataset.s; compositeOnly = false;
    renderSceneBtns(); updateScene();
  });
}
function updateScene(){
  LEVELS.forEach((lv,i) => {
    const el = document.getElementById(lv);
    el.src = imgData(curScene + '_' + lv);
    el.style.display = (compositeOnly && lv !== 'L3') ? 'none'
      : (document.getElementById('c'+(i+1)).checked ? 'block' : 'none');
    if (compositeOnly && lv === 'L3') el.src = imgData(curScene + '_composite');
  });
  const info = META.bgScenes.find(s => s.id === curScene);
  document.getElementById('sceneInfo').innerHTML =
    `<b>${esc(curScene)}</b> <span class="tag">层 ${esc(info.floors)}</span>` +
    `<span class="tag">参考 ${esc(info.ref)}</span><br>` +
    `L1 暗像素 <b>${info.l1Dark}</b> / 战斗区暗像素 <b>${info.combatDark}</b> ` +
    `(<span class="${info.r22==='LOW'?'ok':'todo'}">${info.r22}</span>) / ` +
    `L4 占比 <b>${info.l4}</b>`;
  document.getElementById('layerTable').innerHTML =
    '<tr><th>层</th><th>coverage</th><th>越界色</th><th>半透明</th></tr>' +
    LEVELS.map(lv => {const d = info.layers[lv];
      return `<tr><td>${lv}</td><td>${d.coverage}</td>` +
             `<td class="${d.outOfPalette?'todo':'ok'}">${d.outOfPalette}</td>` +
             `<td class="${d.semiAlpha?'todo':'ok'}">${d.semiAlpha}</td></tr>`;}).join('');
}
LEVELS.forEach((lv,i) => document.getElementById('c'+(i+1)).onchange = updateScene);
document.getElementById('zoomBtn').onclick = e => {
  const st = document.getElementById('stage');
  st.classList.toggle('zoom');
  e.target.textContent = st.classList.contains('zoom') ? '1× 还原' : '2× 放大';
};
document.getElementById('compositeBtn').onclick = () => {
  compositeOnly = !compositeOnly; updateScene();
};

/* ---- 序列帧组（Boss / 技能 / overlay） ---- */
function frameKeys(prefix, n, boss){
  const out = [];
  const names = Object.keys(IMG);
  const re = boss ? new RegExp('^' + prefix + '_(idle|run|atk|skill|hit|death)_r_[0-9]{2}$')
                  : new RegExp('^' + prefix + '_[0-9]{2}$');
  names.filter(k => re.test(k)).sort().forEach(k => out.push(k));
  return out;
}
function makeGroup(host, prefix, title, subtitle, boss){
  const keys = frameKeys(prefix, 0, boss);
  const div = document.createElement('div');
  div.className = 'group';
  div.innerHTML = `<h3>${esc(title)} <span class="tag">${keys.length} 帧</span>` +
                  `<span class="tag">${esc(subtitle)}</span></h3>` +
                  `<div class="row"><img class="big" id="big_${prefix}" src="${imgData(keys[0])}">` +
                  `<div><div class="strip" id="strip_${prefix}">` +
                  keys.map((k,i)=>`<img class="thumb ${i===0?'sel':''}" data-k="${k}" ` +
                           `src="${imgData(k)}" title="${esc(k)}">`).join('') +
                  `</div><div style="margin-top:8px"><button data-a="play">▶ 播放</button> ` +
                  `<button data-a="prev">◀ 上一帧</button> <button data-a="next">下一帧 ▶</button> ` +
                  `<span id="lab_${prefix}"></span></div></div></div>`;
  host.appendChild(div);
  let idx = 0, timer = null;
  const big = div.querySelector('.big');
  const thumbs = Array.from(div.querySelectorAll('.thumb'));
  const lab = div.querySelector('#lab_' + prefix);
  function show(i){
    idx = (i + keys.length) % keys.length;
    big.src = imgData(keys[idx]);
    thumbs.forEach((t,j)=>t.classList.toggle('sel', j===idx));
    lab.textContent = keys[idx];
  }
  thumbs.forEach((t,j)=>t.onclick=()=>show(j));
  div.querySelector('[data-a="prev"]').onclick=()=>show(idx-1);
  div.querySelector('[data-a="next"]').onclick=()=>show(idx+1);
  div.querySelector('[data-a="play"]').onclick=e=>{
    if(timer){clearInterval(timer);timer=null;e.target.textContent='▶ 播放';}
    else{timer=setInterval(()=>show(idx+1), boss?170:120);e.target.textContent='⏸ 暂停';}
  };
  show(0);
}

const bossArea = document.getElementById('bossArea');
BOSSES.forEach(b => makeGroup(bossArea, b[0], b[1] + ' · ' + b[2] + ' 帧', b[3], true));
const vfxArea = document.getElementById('vfxArea');
SKILLS.forEach(s => makeGroup(vfxArea, s[0], s[1], s[2], false));
const ovlArea = document.getElementById('ovlArea');
OVERLAYS.forEach(s => makeGroup(ovlArea, s[0], s[1], s[2], false));

/* ---- 体检汇总 ---- */
const t = META.qc, b = META.b3b4, g = META.bg;
document.getElementById('qcSummary').innerHTML =
  `<div class="row"><div><b>全项目质检</b>：${t.groups} 组 / ${t.frames} 帧，` +
  `<span class="ok">${JSON.stringify(t.verdicts)}</span>；` +
  `越界色 ${t.outOfPaletteTotal} / 半透明帧 ${t.semiAlphaFrames} / 尺寸不符 ${t.sizeMismatchFrames}</div>` +
  `<div><b>第 29 轮新增</b>：Boss ${b.bossFrames} 帧 · 技能+命中 ${b.vfxFrames} 帧 · ` +
  `overlay ${b.overlayFrames} 帧 · 背景 ${g.layers} 层（${g.scenes} 场景）</div></div>`;
document.getElementById('groupTable').innerHTML =
  '<tr><th>组 ID</th><th>帧数</th><th>越界色</th><th>半透明</th></tr>' +
  META.groups.map(x => `<tr><td>${esc(x.id)}</td><td>${x.frames}</td>` +
    `<td class="${x.palette?'todo':'ok'}">${x.palette}</td>` +
    `<td class="${x.semiAlpha?'todo':'ok'}">${x.semiAlpha}</td></tr>`).join('');

renderSceneBtns(); updateScene();
</script>
</body>
</html>
"""


def build() -> str:
    images = collect_images()
    meta = collect_meta()
    repl = {
        "__IMG_JSON__": json.dumps(images, ensure_ascii=False, separators=(",", ":")),
        "__META_JSON__": json.dumps(meta, ensure_ascii=False, separators=(",", ":")),
        "__SCENES_JSON__": json.dumps(SCENES, ensure_ascii=False),
        "__LEVELS_JSON__": json.dumps(LEVELS, ensure_ascii=False),
        "__SKILLS_JSON__": json.dumps(SKILLS, ensure_ascii=False),
        "__OVERLAYS_JSON__": json.dumps(OVERLAYS, ensure_ascii=False),
        "__BOSSES_JSON__": json.dumps(BOSSES, ensure_ascii=False),
    }
    html = TEMPLATE
    for key, val in repl.items():
        html = html.replace(key, val)
    left = re.findall(r"__[A-Z_]+__", html)
    if left:
        raise RuntimeError(f"模板占位符未替换：{left}")
    return html


def main() -> None:
    check_only = "--check" in sys.argv
    html = build()
    sha = hashlib.sha256(html.encode("utf-8")).hexdigest()[:16]
    if check_only:
        if not OUT.is_file():
            print("ASSETOVERVIEW|FAIL|产物不存在")
            sys.exit(1)
        disk = OUT.read_text(encoding="utf-8")
        if disk != html:
            print(f"ASSETOVERVIEW|FAIL|产物与生成器不一致 | sha={sha}")
            sys.exit(1)
        print(f"ASSETOVERVIEW|PASS|--check 产物一致 | bytes={len(html.encode('utf-8'))} | sha={sha}")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"ASSETOVERVIEW|PASS|{OUT.relative_to(ROOT)} | "
          f"bytes={len(html.encode('utf-8'))} | sha={sha} | 内嵌图 {html.count('data:image/png;base64,')} 张")


if __name__ == "__main__":
    main()
