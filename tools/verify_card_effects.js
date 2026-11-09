/*
 * verify_card_effects.js — card_effects.js / battle_sim.js 联动的 Node headless 断言（第 21 轮）
 *
 * 只验「只读冻结卡库 → 编译效果集 → 战斗内核真的按它变化」，不验画面、不验手感、
 * 不验平衡性、不碰 Godot。输出纯 JSON 到 stdout，由 tools/verify_card_effects.py
 * 固化为 docs/card-effects-report.json。
 *
 * 口径来源：data/buff-card-library.json（冻结卡库运行时副本）、docs/18。
 */
'use strict';
const fs = require('fs');
const path = require('path');
const B = require('./battle_sim.js');
const E = require('./card_effects.js');

const ROOT = path.resolve(__dirname, '..');
const lib = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'buff-card-library.json'), 'utf8'));
const checks = [];
function ok(label, pass, detail) {
    checks.push({ label: label, ok: !!pass, detail: String(detail === undefined ? '' : detail) });
}
function fx(ids) { return E.compileCardEffects(lib, ids); }
function layerOf(ids, key) {
    const r = fx(ids);
    const item = r.layers.battle.concat(r.layers.deck, r.layers.none).find(x => x.key === key && x.card === ids[0]);
    return item ? item.layer : 'missing';
}
function simWith(ids, stage, runId) {
    const s = new B.BattleSim({ runId: runId || 'fx-verify', stage: stage || 1 });
    s.applyCardEffects(fx(ids));
    return s;
}
function firstHitDamage(ids) {
    const s = simWith(ids, 1, 'fx-pd');
    s.enemies[0].x = s.x + 40;         // 放进剑气斩 reach 104 内
    s.drainEvents();
    s.tryCast(0);
    return s.drainEvents().find(e => e.type === 'damage_applied').damage;
}

// ---- ① 卡库与编译器的基本契约 ----
ok('冻结运行时卡库恰 72 张', lib.cards.length === 72, 'cards=' + lib.cards.length);
const all = fx(lib.cards.map(c => c.id));
const paramTotal = lib.cards.reduce((a, c) => a + Object.keys(c.params || {}).length, 0);
ok('72 卡全量编译不抛异常且三层计数自洽',
   all.counts.cards === 72 &&
   all.counts.battle + all.counts.deck + all.counts.none === paramTotal,
   'battle=' + all.counts.battle + ' / deck=' + all.counts.deck +
   ' / none=' + all.counts.none + ' / params=' + paramTotal);
ok('每个未映射键都有非空理由（不静默丢弃）',
   all.unboundKeys.length > 0 && all.unboundKeys.every(k => k.reason && k.reason.length > 6),
   'unboundKeys=' + all.unboundKeys.length);
ok('R54「破云式卡面 / params 不自洽」被显式记录',
   all.notes.some(n => n.card === 'card_poyun' && n.note.includes('总伤不变')),
   'notes=' + all.notes.length);
const withFx = lib.cards.filter(c => fx([c.id]).counts.battle > 0);
ok('如实统计有战斗层效果的卡（26/72，不凑数）',
   withFx.length === 26, withFx.length + '/72');
ok('scope 明确标注为网页验证层（不是冻结规格 / 不是 Godot）',
   all.scope === 'web-validation-only', all.scope);

// ---- ② 空效果不扰动第 20 轮基线 ----
const empty = fx([]);
ok('空效果集 == defaultMods()',
   JSON.stringify(empty.mods) === JSON.stringify(E.defaultMods()), 'mods 全默认');
ok('两端 mods 字段集合一致（card_effects ↔ battle_sim）',
   JSON.stringify(Object.keys(E.defaultMods()).sort()) ===
   JSON.stringify(Object.keys(B.emptyCardMods()).sort()), 'schema 同源');
const base = new B.BattleSim({ runId: 'fx-empty', stage: 1 });
const blank = new B.BattleSim({ runId: 'fx-empty', stage: 1 });
blank.applyCardEffects(empty);
for (let t = 0; t < 120; t++) {
    const inp = { axis: t % 30 < 15 ? 1 : -1,
                  skills: [t % 15 === 0, false, false, false], dodge: false };
    base.step(B.TICK, inp);
    blank.step(B.TICK, inp);
}
ok('空效果与未接效果 120 tick 快照逐字段一致',
   JSON.stringify(base.snapshot()) === JSON.stringify(blank.snapshot()), '120 tick / 4 s');
ok('空效果不标记「已生效卡」',
   blank.snapshot().cardEffects.active === false &&
   blank.snapshot().cardEffects.bound === 0, 'active=false / bound=0');

// ---- ③ 五上界绝不被卡牌效果突破 ----
ok('五上界常量未被第 21 轮改动',
   B.CAP_BASE === 180 && B.CAP_REALM_RATIO === 1.60 && B.CAP_EXTRA_POOL === 600 &&
   B.CAP_COMBO === 2.5 && B.CAP_CRIT === 1.8 && B.CAP_DEFENSE === 0.75,
   '180 / 1.60 / 600 / 2.5 / 1.8 / 0.75');
ok('全 72 卡效果叠加后 damageFormula 峰值仍 3996',
   B.damageFormula(180, 1.60, 600, 2.5, 1.8, 0, null) === 3996 &&
   B.maxHit() === 3996, 'peak=3996 < Boss 4400');
const caps = E.CAPS;
ok('全 72 卡 mods 全部在网页验证层安全上界内',
   all.mods.segmentRatios.length <= caps.segments &&
   all.mods.pierceDefense <= caps.pierceDefense &&
   all.mods.shieldMax <= caps.shieldMax &&
   all.mods.cdScale >= caps.cdScaleMin &&
   all.mods.spiritCostScale >= caps.spiritCostMin &&
   all.mods.damageTakenScale >= caps.damageTakenMin &&
   all.mods.reviveHp <= caps.reviveHp,
   'segments=' + all.mods.segmentRatios.length + ' / cdScale=' + all.mods.cdScale.toFixed(2));

// ---- ④ 逐卡核对卡面 text：该生效的生效、不该生效的如实不生效 ----
const poyun = fx(['card_poyun']).mods;
ok('破云式 → 2 段且总伤不变（卡面「总伤不变」优先于 params 0.6×2）',
   poyun.segmentRatios.length === 2 &&
   Math.abs(poyun.segmentRatios.reduce((a, b) => a + b, 0) - 1) < 1e-9,
   poyun.segmentRatios.join(' + '));
const leizhuan = fx(['card_leizhuan']).mods;
ok('雷篆重描 → 落点均分 0.5 / 0.5（不改总伤）',
   leizhuan.segmentRatios.length === 2 &&
   Math.abs(leizhuan.segmentRatios.reduce((a, b) => a + b, 0) - 1) < 1e-9,
   leizhuan.segmentRatios.join(' + '));
ok('拳风连震 → 追加 1 段 30%（单次峰值不变）',
   Math.abs(fx(['card_quanfeng']).mods.segmentRatios[1] - 0.3) < 1e-9, '1.0 + 0.3');
ok('破域 → 破防 5%（无条件）',
   Math.abs(fx(['card_poyu']).mods.pierceDefense - 0.05) < 1e-9, '0.05');
ok('五行逆克 → 需「铁壁」词缀，词缀系统未建故不生效（不伪造）',
   fx(['card_wuxing']).mods.pierceDefense === 0 &&
   layerOf(['card_wuxing'], 'pierce_defense') === 'none', '归 none');
ok('回春化刃 / 金刚怒目的 convert 不映射成吸血（卡面是治疗量转伤害）',
   layerOf(['card_huiling'], 'convert') === 'none' &&
   layerOf(['card_jingang'], 'convert') === 'none' &&
   fx(['card_huiling']).mods.lifesteal === undefined, '归 none / 不新增吸血字段');
ok('聚息 / 珠链 / 清露的 regen 不映射（卡面均为脱战或连击条件）',
   layerOf(['card_juxi'], 'regen') === 'none' &&
   layerOf(['card_zhulian'], 'regen') === 'none' &&
   layerOf(['card_qinglu'], 'regen') === 'none', '战斗中不伪造回血');
ok('截取 on_hit → 玩家「受击」回灵（不是命中回灵）',
   fx(['card_jieqi']).mods.spiritOnHurt === 4 &&
   fx(['card_jieqi']).mods.spiritOnHit === 0, 'spiritOnHurt=4');
ok('逆转回灵 per_hit → 每次命中回灵 +2（按卡 ID 区分，不按参数名猜）',
   fx(['card_nianzhuan']).mods.spiritOnHit === 2 &&
   fx(['card_nianzhuan']).mods.spiritOnHurt === 0, 'spiritOnHit=2');
ok('破云式 per_hit 是分段倍率，不再被误当回灵',
   fx(['card_poyun']).mods.spiritOnHit === 0, '归 none / 由 split 处理');
ok('剑意凝形 pierce 需剑修标签 ≥2，标签系统未建故不生效',
   layerOf(['card_jianyi'], 'pierce') === 'none', '归 none');
ok('灵潮 free_cast → 灵力满时下一技能不耗灵',
   fx(['card_lingchao']).mods.freeCastOnFull === true, 'freeCastOnFull=true');
ok('丹香 spirit_cost 限定回春诀，本验证层不全局套用',
   layerOf(['card_danxiang'], 'spirit_cost') === 'none' &&
   fx(['card_danxiang']).mods.spiritCostScale === 1, '归 none');
ok('凝丹 hp_max +24 是绝对值，舍身 −0.15 是比例（不混用）',
   fx(['card_ningdan']).mods.hpMaxFlat === 24 &&
   Math.abs(fx(['card_sheshi']).mods.hpMaxRatio + 0.15) < 1e-9, 'flat=24 / ratio=-0.15');
ok('灵脉拓宽 +16 绝对值 / 无根 −20% 比例',
   fx(['card_lingmai']).mods.spiritMaxFlat === 16 &&
   Math.abs(fx(['card_wugen']).mods.spiritMaxRatio + 0.2) < 1e-9, 'flat=16 / ratio=-0.20');
ok('护体 shield_max +20 生效 / 反涌「灵力溢出转护盾」不固定发盾',
   fx(['card_huti']).mods.shieldMax === 20 &&
   fx(['card_fanyong']).mods.shieldMax === 0, '20 / 0');
ok('避水 invuln → 受击后无敌窗口 0.5 s（不是闪避无敌）',
   Math.abs(fx(['card_bishui']).mods.hurtInvuln - 0.5) < 1e-9, 'hurtInvuln=0.5');
ok('舍利 30% / 转生 20% → 首次阵亡复活',
   Math.abs(fx(['card_sheli']).mods.reviveHp - 0.3) < 1e-9 &&
   Math.abs(fx(['card_zhuansheng']).mods.reviveHp - 0.2) < 1e-9, '0.30 / 0.20');
ok('天人感应 reveal 只标信息层，不改判定',
   fx(['card_tianren']).mods.reveal === true, 'reveal=true');
ok('五上界变量（base_damage / extra_pool / cap 等）归抽卡层，不在此重复',
   layerOf(['card_jianfeng'], 'base_damage') === 'deck' &&
   layerOf(['card_jianfeng'], 'pool') === 'deck' &&
   layerOf(['card_jianfeng'], 'cap') === 'deck', '归 deck');

// ---- ⑤ 效果真的进了战斗内核（不是只写了文档） ----
const multi = simWith(['card_poyun'], 1, 'fx-multi');
multi.enemies[0].x = multi.x + 40;
multi.drainEvents();
multi.tryCast(0);
const multiHits = multi.drainEvents().filter(e => e.type === 'damage_applied');
ok('破云式 → 一次剑气斩发出 2 个 damage_applied（第 1/2、2/2 段）',
   multiHits.length === 2 && multiHits[0].segment === 1 && multiHits[1].segment === 2,
   '段数=' + multiHits.length + ' / 伤害 ' + multiHits.map(e => e.damage).join('+'));
const hpUp = simWith(['card_ningdan'], 1);
ok('凝丹 → 战斗快照 HP 上限 300 → 324',
   hpUp.maxHp === 324 && hpUp.hp === 324, 'maxHp=' + hpUp.maxHp);
const cdDown = simWith(['card_qingling'], 1);
cdDown.enemies[0].x = cdDown.x + 40;
cdDown.tryCast(0);
ok('轻灵 → 技能 CD 0.8 s × 0.96 = 0.768 s',
   Math.abs(cdDown.cd[0] - 0.768) < 1e-9, 'cd=' + cdDown.cd[0]);
ok('破域 → 对 30% 减伤敌人的实战伤害变大',
   firstHitDamage(['card_poyu']) > firstHitDamage([]),
   firstHitDamage([]) + ' → ' + firstHitDamage(['card_poyu']));
const shield = simWith(['card_huti'], 4, 'fx-shield');
shield.enemies[0].x = shield.x + 20;
shield.enemies[0].attackTimer = 0;
shield.drainEvents();
shield.tick(B.TICK, { axis: 0, skills: [false, false, false, false], dodge: false });
const shieldEv = shield.drainEvents();
ok('护体 → 受击先扣护盾并发出 shield_absorb 事件',
   shieldEv.some(e => e.type === 'shield_absorb') && shield.shield < 20,
   'shield 20 → ' + shield.shield);
const revive = simWith(['card_sheli'], 9, 'fx-revive');
revive.hp = 1;
revive.enemies[0].x = revive.x + 20;
revive.enemies[0].attackTimer = 0;
revive.drainEvents();
revive.tick(B.TICK, { axis: 0, skills: [false, false, false, false], dodge: false });
const reviveEv = revive.drainEvents();
ok('舍利 → 首次阵亡复活且本局不结束',
   reviveEv.some(e => e.type === 'revive') && revive.hp > 0 && !revive.finished,
   'hp=' + revive.hp + ' / finished=' + revive.finished);
const preset = ['card_poyun', 'card_huti', 'card_sheli', 'card_tiepi', 'card_qingling'];
const compiled = fx(preset);
const battleWithFx = simWith(preset, 1);
ok('预置机制卡组 → snapshot 标记已生效卡与命中分段',
   battleWithFx.snapshot().cardEffects.active === true &&
   battleWithFx.snapshot().cardEffects.bound === compiled.counts.battle &&
   battleWithFx.snapshot().cardEffects.segments === 2,
   'bound=' + compiled.counts.battle + ' / segments=2');

const passed = checks.filter(c => c.ok).length;
const failed = checks.length - passed;
const report = {
    verdict: failed === 0 ? 'PASS' : 'FAIL',
    summary: {
        total: checks.length, passed: passed, failed: failed,
        battleBoundCards: withFx.length,
        boundEntries: all.counts.battle,
        deckBound: all.counts.deck,
        unbound: all.counts.none,
        unboundKeys: all.unboundKeys.length,
        specConflicts: all.notes.filter(n => n.note.includes('R54')).length,
    },
    checks: checks,
    notes: all.notes,
    unboundKeys: all.unboundKeys.map(k => k.key),
};
process.stdout.write(JSON.stringify(report, null, 2) + '\n');
process.exit(failed === 0 ? 0 : 1);
