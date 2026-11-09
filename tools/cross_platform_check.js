/*
 * cross_platform_check.js — Node 侧复算 Godot 黄金样本并逐层比对。
 * 用法：node tools/cross_platform_check.js   （stdout 输出机器可读 JSON）
 * 依赖：tools/card_rules.js（与网页 Demo 内嵌的同一份规则实现）
 *       docs/card-golden-samples.json（由 tools/export_card_golden.gd 经 Godot headless 导出）
 * 边界：证明「网页/Node 规则 == Godot 规则」，不证明画面，也不证明平衡性。
 */
'use strict';
const fs = require('fs');
const path = require('path');
const rules = require('./card_rules.js');

const ROOT = path.resolve(__dirname, '..');
const golden = JSON.parse(fs.readFileSync(path.join(ROOT, 'docs/card-golden-samples.json'), 'utf8'));
const lib = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/buff-card-library.json'), 'utf8'));

const checks = [];
function ok(cond, label, detail) {
    checks.push({ label, ok: !!cond, detail: String(detail === undefined ? '' : detail) });
}
// Godot 的 JSON.stringify 把 Dictionary 键按字典序输出，JS 对象按插入序；
// 值相同即视为一致，故先递归规范化键序再比较（数组顺序保留）。
function canon(v) {
    if (Array.isArray(v)) return v.map(canon);
    if (v && typeof v === 'object') {
        const out = {};
        for (const k of Object.keys(v).sort()) out[k] = canon(v[k]);
        return out;
    }
    return v;
}
function eq(a, b) { return JSON.stringify(canon(a)) === JSON.stringify(canon(b)); }
function near(a, b) { return Math.abs(Number(a) - Number(b)) < 1e-9; }

// ---- 1. RNG 逐位序列 ----
{
    const d = new rules.CardDeck(lib);
    d.rngReset(4264777024);
    const seq = [];
    for (let i = 0; i < golden.rngSequence.length; i++) seq.push(d.rngRandf());
    let allEq = true;
    for (let i = 0; i < seq.length; i++) if (!near(seq[i], golden.rngSequence[i])) allEq = false;
    ok(allEq, 'xorshift32 randf 序列逐位一致', 'n=' + seq.length + ' first=' + seq[0]);
}

// ---- 2. 五个 run 的逐层流程 ----
for (const c of golden.cases) {
    const d = new rules.CardDeck(lib);
    d.newRun(c.runId, c.context);
    let stageOk = true;
    const diffs = [];
    for (const s of c.stages) {
        const offered = d.offer(s.stage);
        const seed = d.runSeed(s.stage);
        const choiceCount = d.choiceCount();
        const eligibleCount = d.eligible(s.stage).length;
        if (!eq(offered, s.offered)) { stageOk = false; diffs.push('s' + s.stage + ':offered ' + JSON.stringify(offered) + ' vs ' + JSON.stringify(s.offered)); }
        if (seed !== s.seed) { stageOk = false; diffs.push('s' + s.stage + ':seed ' + seed + ' vs ' + s.seed); }
        if (choiceCount !== s.choiceCount) { stageOk = false; diffs.push('s' + s.stage + ':choiceCount'); }
        if (eligibleCount !== s.eligibleCount) { stageOk = false; diffs.push('s' + s.stage + ':eligibleCount ' + eligibleCount + ' vs ' + s.eligibleCount); }
        if (s.picked !== undefined) {
            const ev = d.pickEvent(s.stage, s.offered, s.picked);
            const good = d.pick(s.picked, s.stage);
            if (good !== s.pickOk) { stageOk = false; diffs.push('s' + s.stage + ':pickOk'); }
            if (!eq(ev, s.event)) { stageOk = false; diffs.push('s' + s.stage + ':event ' + JSON.stringify(ev) + ' vs ' + JSON.stringify(s.event)); }
        }
        if (!near(d.peakDamage(), s.peakAfter)) { stageOk = false; diffs.push('s' + s.stage + ':peakAfter'); }
        if (d.clampEvents.length !== s.clampEvents) { stageOk = false; diffs.push('s' + s.stage + ':clampEvents ' + d.clampEvents.length + ' vs ' + s.clampEvents); }
        if (d.violations.length !== s.violations) { stageOk = false; diffs.push('s' + s.stage + ':violations'); }
    }
    ok(stageOk, 'run ' + c.runId + ' 逐层 9 步全一致', diffs.length ? diffs.slice(0, 3).join(' | ') : 'stages=' + c.stages.length);
    ok(near(d.peakDamage(), c.peak), 'run ' + c.runId + ' 终局峰值一致', d.peakDamage() + ' vs ' + c.peak);
    ok(eq(Object.keys(d.pickedCounts()).sort().map((k) => [k, d.pickedCounts()[k]]),
           Object.keys(c.pickedCounts).sort().map((k) => [k, c.pickedCounts[k]])),
       'run ' + c.runId + ' 已选卡计数一致', 'unique=' + Object.keys(d.pickedCounts()).length);
    ok(d.clampEvents.length === c.clampEvents && d.violations.length === c.violations && d.isSealed() === c.sealed,
       'run ' + c.runId + ' 守卫/违规/封牌状态一致', 'clamp=' + d.clampEvents.length + ' viol=' + d.violations.length);
}

// ---- 3. 全卡叠加 ----
{
    const mega = new rules.CardDeck(lib);
    mega.newRun('all');
    for (const c of lib.cards) mega.applyParams(c.id);
    ok(near(mega.peakDamage(), golden.mega.peak), '72 卡全叠加峰值一致', mega.peakDamage() + ' vs ' + golden.mega.peak);
    ok(mega.clampEvents.length === golden.mega.clampEvents, '72 卡守卫事件数一致', mega.clampEvents.length + ' vs ' + golden.mega.clampEvents);
    ok(mega.violations.length === golden.mega.violations, '72 卡违规数一致', mega.violations.length + ' vs ' + golden.mega.violations);
    ok(near(mega.offenseState().offense_pool_used, golden.mega.offense.offense_pool_used),
       '共享 offense_pool 用量一致', mega.offenseState().offense_pool_used);
}

const failed = checks.filter((x) => !x.ok);
const report = {
    verdict: failed.length === 0 ? 'PASS' : 'FAIL',
    checks,
    summary: { total: checks.length, passed: checks.length - failed.length, failed: failed.length },
    node: process.version,
    goldenGeneratedAt: golden.generatedAt,
    note: 'Node 复算 Godot 黄金样本；网页 Demo 内嵌同一份 tools/card_rules.js，故结论同样适用于网页。',
};
process.stdout.write(JSON.stringify(report, null, 2) + '\n');
process.exit(failed.length === 0 ? 0 : 1);
