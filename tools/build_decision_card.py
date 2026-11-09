#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一页式决策卡生成器（可复现，0 积分）

用法：
  /opt/homebrew/bin/python3 tools/build_decision_card.py

读 docs/decision-card.json → 生成 assets/_preview/decision-card.html（自包含、无外部依赖、
无机器绝对路径）。页面逐项勾选后可复制 key=value 回执，交给 tools/apply_decisions.py 校验。

设计约束：
  - 默认预选推荐值只为降低拍板成本，不代表用户已确认；
  - 页面不写任何项目文件，回执只是要复制给助手的文本；
  - 数据内嵌，单独把 HTML 带走也能用。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs/decision-card.json"
OUT = ROOT / "assets/_preview/decision-card.html"

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>决策卡 · 仙侠爬塔 Roguelite</title>
<style>
:root{
  --ink:#12161F; --ink2:#2A3140; --ink3:#4A5568;
  --paper:#E8DFC8; --paper2:#C9BFA3; --paper3:#8A8268;
  --jade:#5FA8A0; --jadeL:#9BD4CC; --red:#C8453B; --redL:#E8806F;
  --gold:#D9A441; --goldL:#F2D089; --violet:#8A6FC4;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ink);color:var(--paper);
  font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",system-ui,sans-serif;
  font-size:14px;line-height:1.65}
.wrap{max-width:1080px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:24px;margin:0 0 6px;letter-spacing:1px}
.sub{color:var(--paper3);font-size:13px;margin-bottom:18px}
.badge{display:inline-block;padding:2px 9px;border:1px solid var(--gold);color:var(--gold);
  font-size:12px;border-radius:2px;margin-left:8px;vertical-align:2px}
.bar{background:var(--ink2);border:1px solid var(--ink3);padding:12px 14px;margin-bottom:18px}
.bar strong{color:var(--goldL)}
.warn{color:var(--redL);margin-top:7px;font-size:13px}
.tools{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px}
button{background:var(--ink2);color:var(--paper);border:1px solid var(--ink3);
  padding:8px 14px;font:inherit;font-size:13px;cursor:pointer;transition:.12s}
button:hover{border-color:var(--gold);color:var(--goldL)}
button.primary{background:var(--gold);color:var(--ink);border-color:var(--gold);font-weight:700}
button.primary:hover{background:var(--goldL);color:var(--ink)}
h2{font-size:16px;margin:30px 0 4px;color:var(--jadeL);border-bottom:1px solid var(--ink3);padding-bottom:7px}
.gdesc{color:var(--paper3);font-size:12px;margin:0 0 14px}
.card{background:var(--ink2);border:1px solid var(--ink3);padding:14px 16px;margin-bottom:12px}
.card.hard{border-left:3px solid var(--red)}
.card.conflict{border-left:3px solid var(--violet)}
.head{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:8px}
.id{font-family:ui-monospace,Menlo,Consolas,monospace;color:var(--goldL);font-size:14px;font-weight:700}
.need{font-size:14px;font-weight:600}
.meta{color:var(--paper3);font-size:12px;margin:3px 0 10px}
.meta b{color:var(--paper2);font-weight:600}
.opts{display:grid;gap:7px}
.opt{display:flex;gap:9px;align-items:flex-start;padding:8px 10px;border:1px solid var(--ink3);
  cursor:pointer;background:rgba(0,0,0,.16)}
.opt:hover{border-color:var(--jade)}
.opt.sel{border-color:var(--gold);background:rgba(217,164,65,.09)}
.opt input{margin-top:4px;accent-color:var(--gold);flex:none}
.opt .lbl{font-weight:600}
.opt.rec .lbl::after{content:" ★ 推荐";color:var(--gold);font-size:11px;font-weight:600}
.opt .note{color:var(--paper3);font-size:12px;margin-top:2px}
.opt.bad .lbl{color:var(--redL)}
textarea,input[type=text]{width:100%;background:var(--ink);color:var(--jadeL);
  border:1px solid var(--ink3);padding:9px 11px;font-family:ui-monospace,Menlo,Consolas,monospace;
  font-size:12.5px;line-height:1.6}
input[type=text]{max-width:340px}
textarea{resize:vertical}
.tip{color:var(--paper3);font-size:12px;margin:8px 0}
#receipt{height:230px}
.ok{color:var(--jadeL)}
.foot{margin-top:26px;color:var(--paper3);font-size:12px;border-top:1px solid var(--ink3);padding-top:14px}
code{color:var(--goldL);font-family:ui-monospace,Menlo,Consolas,monospace}
</style>
</head>
<body>
<div class="wrap">
  <h1>决策卡 · 仙侠爬塔 Roguelite<span class="badge" id="statusBadge">未提交</span></h1>
  <div class="sub">把「还差什么」从问答题变成选择题 · 提案详见 <code>docs/09-内容命名提案.md</code> · 欠债台账 <code>docs/08-…</code></div>

  <div class="bar">
    <div>已选择 <strong id="picked">0</strong> / <span id="total">0</span> 项 ·
      硬门禁解除 <strong id="gates">0</strong> / 4 ·
      <span id="credits">剩余积分档：随 Q24 联动</span></div>
    <div class="warn" id="warn"></div>
    <div class="tip">★ 为推荐值，页面已默认预选 —— <b>预选不等于你已确认</b>。逐项核对后复制底部回执发给助手，回执校验默认 dry-run，不会自动建工程或冻结设计。</div>
  </div>

  <div class="tools">
    <button class="primary" id="btnCopy">复制回执</button>
    <button id="btnRec">全部采用推荐</button>
    <button id="btnClear">清空选择</button>
    <button id="btnJson">下载答复 JSON</button>
  </div>

  <div id="groups"></div>

  <h2>回执（复制下面这段发给助手）</h2>
  <div class="tip">格式 <code>key=value</code>；<code>#</code> 开头为注释，会被忽略。留空表示该项暂不解除。</div>
  <textarea id="receipt" readonly spellcheck="false"></textarea>
  <div class="tip" id="copyMsg"></div>

  <div class="foot">
    自包含页面，无外部依赖、无机器绝对路径，可单独带走。数据来自 <code>docs/decision-card.json</code>，
    由 <code>tools/build_decision_card.py</code> 可复现生成。用户未提交回执前，
    <code>design-freeze-draft.json</code> 保持 <code>frozen=false</code>。
  </div>
</div>

<script>
const DATA = __DATA__;
const STORE = "xianxia-decision-card-v1";
const state = {};

function initialState(){
  DATA.items.forEach(it => { state[it.id] = (it.type === "text") ? "" : (it.recommended || ""); });
  try{
    const saved = JSON.parse(localStorage.getItem(STORE) || "{}");
    Object.keys(saved).forEach(k => { if (k in state) state[k] = saved[k]; });
  }catch(e){}
}
function save(){
  try{ localStorage.setItem(STORE, JSON.stringify(state)); }catch(e){}
}
function setValue(id, v){ state[id] = v; save(); render(); }
function allRecommended(){
  DATA.items.forEach(it => { state[it.id] = (it.type === "text") ? "" : (it.recommended || ""); });
  save(); render();
}
function clearAll(){
  DATA.items.forEach(it => { state[it.id] = ""; });
  save(); render();
}

function render(){
  const host = document.getElementById("groups");
  host.innerHTML = "";
  DATA.groups.forEach(g => {
    const items = DATA.items.filter(i => i.group === g.id);
    if(!items.length) return;
    const h = document.createElement("h2"); h.textContent = g.title; host.appendChild(h);
    const p = document.createElement("div"); p.className = "gdesc"; p.textContent = g.desc; host.appendChild(p);
    items.forEach(it => {
      const card = document.createElement("div");
      card.className = "card" + (it.group === "hardGate" ? " hard" : "") + (it.group === "conflict" ? " conflict" : "");
      let html = '<div class="head"><span class="id">' + it.id + '</span><span class="need">' + it.need + '</span></div>';
      html += '<div class="meta"><b>卡住：</b>' + it.blocks + '　·　<b>拿到后改：</b>' + it.onResolve + '</div>';
      if(it.type === "text"){
        html += '<input type="text" data-id="' + it.id + '" placeholder="' + (it.placeholder || "") + '" value="' + (state[it.id] || "").replace(/"/g, "&quot;") + '">';
        html += '<div class="tip">' + it.note + '</div>';
      }else{
        html += '<div class="opts">';
        (it.options || []).forEach(op => {
          const sel = state[it.id] === op.value;
          const bad = /不推荐|冲突|作废|返工代价最高/.test(op.note || "");
          html += '<label class="opt' + (sel ? " sel" : "") + (op.value === it.recommended ? " rec" : "") + (bad && op.value !== it.recommended ? " bad" : "") + '">'
            + '<input type="radio" name="' + it.id + '" value="' + op.value + '"' + (sel ? " checked" : "") + '>'
            + '<span><span class="lbl">' + op.label + '</span><div class="note">' + op.note + '</div></span></label>';
        });
        html += '</div>';
      }
      card.innerHTML = html;
      host.appendChild(card);
    });
  });

  host.querySelectorAll('input[type=radio]').forEach(el => {
    el.addEventListener("change", () => setValue(el.name, el.value));
  });
  host.querySelectorAll('input[type=text]').forEach(el => {
    el.addEventListener("input", () => { state[el.dataset.id] = el.value; save(); updateStats(); buildReceipt(); });
  });

  updateStats(); buildReceipt();
}

function updateStats(){
  const picked = DATA.items.filter(it => (state[it.id] || "").trim() !== "").length;
  document.getElementById("picked").textContent = picked;
  document.getElementById("total").textContent = DATA.items.length;
  const gates = ["Q1","Q3","Q5","Q8"].filter(k => (state[k] || "").trim() !== "").length;
  document.getElementById("gates").textContent = gates;
  const w = document.getElementById("warn");
  w.textContent = gates < 4
    ? "⚠ 硬门禁仍有 " + (4 - gates) + " 项未解除 —— 按 08 §5，不解除不能进阶段二建工程。"
    : "✓ 四个硬门禁均已填写（仍需助手核对回执后才能视为解除）。";
  const q24 = state["Q24"] || "";
  document.getElementById("credits").textContent = "剩余积分档：" +
    (q24 === "all_sprite_sheets" ? "A 190–450" : q24 === "procedural_plus_pixelfx" ? "B 85–200（推荐）" : "随 Q24 联动");
  document.getElementById("statusBadge").textContent = picked === DATA.items.length ? "全部已选" : "未提交";
}

function buildReceipt(){
  const lines = [
    "# 决策卡回执 · 由 assets/_preview/decision-card.html 生成",
    "# 复制以下 key=value 发给助手；# 开头为注释，会被忽略；留空表示暂不解除"
  ];
  DATA.items.forEach(it => { lines.push(it.id + "=" + (state[it.id] || "").trim()); });
  document.getElementById("receipt").value = lines.join("\n");
}

document.getElementById("btnRec").addEventListener("click", allRecommended);
document.getElementById("btnClear").addEventListener("click", clearAll);
document.getElementById("btnCopy").addEventListener("click", () => {
  const t = document.getElementById("receipt");
  const msg = document.getElementById("copyMsg");
  const done = () => { msg.className = "tip ok"; msg.textContent = "✓ 已复制，粘贴到对话里发给助手即可。"; };
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(t.value).then(done, () => { t.select(); document.execCommand("copy"); done(); });
  }else{ t.select(); document.execCommand("copy"); done(); }
});
document.getElementById("btnJson").addEventListener("click", () => {
  const blob = new Blob([JSON.stringify({generatedBy:"decision-card.html", answers:state}, null, 2)], {type:"application/json"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
  a.download = "decision-answers.json"; a.click(); URL.revokeObjectURL(a.href);
});

initialState();
render();
</script>
</body>
</html>
"""


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    items = data["items"]
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids)), "决策项 ID 重复"
    groups = {g["id"] for g in data["groups"]}
    for it in items:
        assert it["group"] in groups, "未知分组: " + it["group"]
        assert it["need"] and it["blocks"] and it["onResolve"], "字段不全: " + it["id"]
        if it.get("type") == "text":
            assert not it.get("options"), "text 项不应有 options: " + it["id"]
        else:
            vals = [o["value"] for o in it["options"]]
            assert len(vals) == len(set(vals)), "选项重复: " + it["id"]
            assert it["recommended"] in vals, "推荐值不在选项里: " + it["id"]

    html = HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False, indent=1))
    assert "__DATA__" not in html, "数据占位符未替换"
    assert "/Users/" not in html and "C:\\" not in html, "机器绝对路径泄漏"
    for i in items:
        assert i["id"] in html, "决策项未写入页面: " + i["id"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"决策卡生成：{OUT.relative_to(ROOT)}")
    print(f"  {len(data['groups'])} 组 / {len(items)} 项 / {len(html)} 字符")
    print(f"  硬门禁：{sum(1 for i in items if i['group'] == 'hardGate')} 项")
    print("  自包含 / 无外部依赖 / 无绝对路径：OK")


if __name__ == "__main__":
    main()
