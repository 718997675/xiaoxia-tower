#!/usr/bin/env node
/*
 * cross_platform_battle_check.js — 战斗「公式层」跨端口径复算（第 22 轮）
 *
 * 输入：docs/battle-golden-samples.json（由 Godot headless 的 tools/export_battle_golden.gd 导出）
 * 复算：tools/battle_sim.js（浏览器 / Node 共用的网页战斗内核）
 *
 * 覆盖：docs/01 §8.1 伤害公式 + 五上界 + 9 层难度波形 + 4 技能冻结字段
 * 不覆盖：逐 tick 状态机、技能 CD / 灵力 / 玩家 HP 等 PROPOSAL 占位（刻意不镜像）
 *
 * 输出：stdout 打印 JSON（verdict / summary / checks），由 tools/verify_battle_cross.py 固化报告。
 * 退出码：0 = 一致；1 = 有差异。
 */
'use strict';

const fs = require('fs');
const path = require('path');
const B = require('./battle_sim.js');

const ROOT = path.resolve(__dirname, '..');
const GOLDEN = path.join(ROOT, 'docs', 'battle-golden-samples.json');

/*
 * 五上界在此处**独立转写**一遍（来源：docs/01 §8.1 冻结表格）。
 * 之所以不从 battle_sim.js 读：跨端校验的价值就在于两侧口径是两次独立转写，
 * 若这里直接引用被校验方的常量，等于自己验自己。
 */
const SPEC = {
    base: 180.0,
    realmRatio: 1.60,
    extraPool: 600.0,
    comboMult: 2.5,
    critMult: 1.8,
    defenseRate: 0.75,
    bossHpReference: 4400.0,
    dmgMin: 1,
    dmgMax: 9999,
};

const checks = [];
function ok(label, cond, detail) {
    checks.push({ ok: !!cond, label: label, detail: String(detail) });
}

function clampf(v, lo, hi) { return Math.min(Math.max(v, lo), hi); }

function localDamage(base, realm, pool, combo, crit, defense) {
    const b = clampf(base, 0, SPEC.base);
    const r = clampf(realm, 0, SPEC.realmRatio);
    const p = clampf(pool, 0, SPEC.extraPool);
    const c = clampf(combo, 0, SPEC.comboMult);
    const cr = clampf(crit, 0, SPEC.critMult);
    const d = clampf(defense, 0, SPEC.defenseRate);
    const raw = (b * r + p) * c * cr * (1 - d);
    return Math.max(SPEC.dmgMin, Math.min(SPEC.dmgMax, Math.round(raw)));
}

function main() {
    if (!fs.existsSync(GOLDEN)) {
        console.log(JSON.stringify({
            verdict: 'FAIL', summary: { total: 1, passed: 0, failed: 1 },
            checks: [{ ok: false, label: 'golden_missing', detail: '缺 docs/battle-golden-samples.json' }],
        }, null, 2));
        process.exit(1);
    }
    const golden = JSON.parse(fs.readFileSync(GOLDEN, 'utf8'));

    // ① 伤害公式：逐条复算
    let matched = 0;
    const mismatches = [];
    for (const c of golden.cases || []) {
        const i = c.input;
        const expect = localDamage(i.base, i.realm, i.pool, i.combo, i.crit, i.defense);
        const actual = B.damageFormula(i.base, i.realm, i.pool, i.combo, i.crit, i.defense, []);
        if (expect === c.damage && actual === c.damage) {
            matched++;
        } else {
            if (mismatches.length < 8) {
                mismatches.push(`${c.id}: 期望 ${c.damage} / 本地 ${expect} / battle_sim ${actual}`);
            }
        }
    }
    const total = (golden.cases || []).length;
    ok(`伤害公式逐条复算一致（${total} 条）`, matched === total,
        matched === total ? '全部一致' : `仅 ${matched}/${total} 一致；${mismatches.join(' | ')}`);

    // ② 钳制与负值标记
    const clampMismatch = [];
    for (const c of golden.cases || []) {
        const i = c.input;
        const clamped = (clampf(i.base, 0, SPEC.base) !== i.base)
            || (clampf(i.realm, 0, SPEC.realmRatio) !== i.realm)
            || (clampf(i.pool, 0, SPEC.extraPool) !== i.pool)
            || (clampf(i.combo, 0, SPEC.comboMult) !== i.combo)
            || (clampf(i.crit, 0, SPEC.critMult) !== i.crit)
            || (clampf(i.defense, 0, SPEC.defenseRate) !== i.defense);
        const negative = (i.base < 0 || i.realm < 0 || i.pool < 0 || i.combo < 0 || i.defense < 0);
        if (clamped !== c.clamped || negative !== c.negative) {
            if (clampMismatch.length < 8) {
                clampMismatch.push(`${c.id}: clamped 期望 ${c.clamped} 得 ${clamped} / negative 期望 ${c.negative} 得 ${negative}`);
            }
        }
    }
    ok('钳制标记与负值标记一致', clampMismatch.length === 0,
        clampMismatch.length === 0 ? '全部一致' : clampMismatch.join(' | '));

    // ③ 五上界最坏伤害（目标不减伤）
    const localMax = localDamage(SPEC.base, SPEC.realmRatio, SPEC.extraPool,
        SPEC.comboMult, SPEC.critMult, 0);
    ok('五上界最坏伤害一致', localMax === golden.maxHit && B.maxHit() === golden.maxHit,
        `本地 ${localMax} / battle_sim ${B.maxHit()} / 黄金样本 ${golden.maxHit}`);

    // ④ 最坏伤害 < Boss 4400
    ok('最坏伤害 < Boss 血量参考 4400', localMax < SPEC.bossHpReference,
        `${localMax} < ${SPEC.bossHpReference}（即最坏口径需 2 次命中）`);

    // ⑤ 9 层难度波形镜像一致
    const gs = golden.stages || [];
    const bs = B.STAGES || [];
    let stageBad = [];
    for (let i = 0; i < Math.max(gs.length, bs.length); i++) {
        const g = gs[i], s = bs[i];
        if (!g || !s) { stageBad.push(`第 ${i + 1} 层缺失`); continue; }
        if (g.n !== s.n || g.hp !== s.hp || g.dps !== s.dps || g.t !== s.t
            || Math.abs(g.d - s.d) > 1e-9 || g.type !== s.type
            || JSON.stringify(g.mobs) !== JSON.stringify(s.mobs)) {
            stageBad.push(`第 ${i + 1} 层不一致`);
        }
    }
    ok('9 层难度波形（HP/dps/T(n)/D(n)/类型/怪表）镜像一致', stageBad.length === 0,
        stageBad.length === 0 ? `${gs.length} 层全部一致` : stageBad.join(' | '));

    // ⑥ 4 技能冻结字段镜像一致（只比冻结字段，PROPOSAL 占位不比）
    const gskills = golden.skillsFrozen || [];
    const bskills = B.SKILLS || [];
    const skillBad = [];
    const FROZEN = ['id', 'name', 'key', 'kind', 'vfx'];
    for (let i = 0; i < Math.max(gskills.length, bskills.length); i++) {
        const g = gskills[i], s = bskills[i];
        if (!g || !s) { skillBad.push(`第 ${i + 1} 个技能缺失`); continue; }
        for (const f of FROZEN) {
            if (g[f] !== s[f]) skillBad.push(`${g.id}.${f} 期望 ${g[f]} 得 ${s[f]}`);
        }
    }
    ok('4 技能冻结字段（id/名称/键位/类型/VFX）镜像一致', skillBad.length === 0,
        skillBad.length === 0 ? `${gskills.length} 项全部一致` : skillBad.join(' | '));

    // ⑦ 钳制路径必须被覆盖：黄金样本里要同时存在「未越界」与「越界」两类输入
    const overCap = (golden.cases || []).filter(c => {
        const i = c.input;
        return i.base > SPEC.base || i.realm > SPEC.realmRatio || i.pool > SPEC.extraPool
            || i.combo > SPEC.comboMult || i.crit > SPEC.critMult || i.defense > SPEC.defenseRate;
    });
    const inCap = (golden.cases || []).length - overCap.length;
    ok('钳制路径被覆盖（同时存在越界与未越界输入）', overCap.length > 0 && inCap > 0,
        `越界 ${overCap.length} 条 / 未越界 ${inCap} 条`);

    // ⑧ 越界子集复核：每条越界输入的伤害都必须等于「按五上界钳制后」的独立复算值
    const overBad = [];
    for (const c of overCap) {
        const i = c.input;
        const expect = localDamage(i.base, i.realm, i.pool, i.combo, i.crit, i.defense);
        if (expect !== c.damage || c.clamped !== true) {
            if (overBad.length < 8) {
                overBad.push(`${c.id}: 期望 ${expect} 得 ${c.damage}（clamped=${c.clamped}）`);
            }
        }
    }
    ok('越界输入伤害 == 钳制后独立复算值（且均标记 clamped）', overBad.length === 0,
        overBad.length === 0 ? `${overCap.length} 条全部一致` : overBad.join(' | '));

    const passed = checks.filter(c => c.ok).length;
    const failed = checks.length - passed;
    const out = {
        verdict: failed === 0 ? 'PASS' : 'FAIL',
        summary: { total: checks.length, passed: passed, failed: failed },
        scope: '战斗公式层跨端复算（公式 + 五上界 + 9 层波形 + 4 技能冻结字段）；不含逐 tick 状态机',
        goldenGeneratedAt: golden.generatedAt || '',
        goldenEngine: golden.engine || '',
        checks: checks,
    };
    console.log(JSON.stringify(out, null, 2));
    process.exit(failed === 0 ? 0 : 1);
}

main();
