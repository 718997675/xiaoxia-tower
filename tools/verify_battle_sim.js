/*
 * verify_battle_sim.js — battle_sim.js 的 Node headless 断言（第 20 轮）
 *
 * 只验规则内核，不碰浏览器 DOM、不读 Godot。输出纯 JSON 到 stdout，
 * 由 tools/verify_battle_sim.py 捕获并固化为 docs/battle-sim-report.json。
 *
 * 口径来源：docs/01 §6 / §8.1 / §8.3、docs/06 §4/§5/§7、docs/17。
 */
'use strict';
const B = require('./battle_sim.js');

const checks = [];
function ok(label, pass, detail) {
    checks.push({ label, ok: !!pass, detail: String(detail === undefined ? '' : detail) });
}

// ---- ① docs/01 §8.1 统一伤害公式五组样例 ----
const f = B.damageFormula;
const cases = [
    ['全最小值', f(20, 1.00, 0, 1.0, 1.0, 0.75, null), 5],
    ['期望中期', f(60, 1.60, 120, 1.0, 1.0, 0.30, null), 151],
    ['全最大值 v0.2', f(180, 1.60, 600, 2.5, 1.8, 0.0, null), 3996],
    ['塔内满传承', f(180, 1.60, 300, 2.5, 1.8, 0.0, null), 2646],
    ['v0.1 废弃口径（不得再出现）', f(180, 4.00, 600, 2.5, 1.8, 0.0, null), 3996],
];
for (const [name, got, want] of cases) {
    ok('伤害公式 · ' + name + ' = ' + want, got === want, 'got=' + got);
}
const errs = [];
const neg = f(-1, -1, -1, 1.0, 1.0, -1, errs);
ok('负输入钳到下限并显式上报', neg === 1 && errs.length > 0, 'dmg=' + neg + ' / errs=' + errs.length);
// 公式里的 clamp(1,9999) 只是兜底：五上界先钳住变量，raw 永远 ≤3996，9999 不可达。
ok('极值输入下 9999 兜底不可达（五上界先钳变量）',
   f(99999, 9, 99999, 9, 9, 0, null) === 3996, 'dmg=3996 / clamp(1,9999) 为公式兜底');

// ---- ② 五上界铁律 ----
ok('五上界常量与 01 §8.1 一致',
   B.CAP_BASE === 180 && B.CAP_REALM_RATIO === 1.60 && B.CAP_EXTRA_POOL === 600 &&
   B.CAP_COMBO === 2.5 && B.CAP_CRIT === 1.8 && B.CAP_DEFENSE === 0.75,
   '180 / 1.60 / 600 / 2.5 / 1.8 / 0.75');
ok('共享池越 600 被钳（不另开池）', f(180, 1.60, 9999, 2.5, 1.8, 0, null) === 3996, 'dmg=3996');
ok('combo_mult 越 2.5 被钳', f(180, 1.60, 600, 99, 1.8, 0, null) === 3996, 'dmg=3996');
ok('defense_rate 越 0.75 被钳', f(20, 1.0, 0, 1.0, 1.0, 99, null) === 5, 'dmg=5');
ok('maxHit() 峰值 3996 < Boss 4400', B.maxHit() === 3996 && B.maxHit() < B.BOSS_HP_REFERENCE,
   '3996 < 4400');
ok('全最大值 2 次命中清 Boss（余量 404）', 2 * B.maxHit() >= 4400,
   '2×3996=7992 / 余量 ' + (2 * 3996 - 4400));

// ---- ③ 9 层难度波形（docs/01 §8.3） ----
ok('恰 9 层且第 9 层是 Boss 4400', B.STAGES.length === 9 &&
   B.STAGES[8].hp === 4400 && B.STAGES[8].type === '塔主 Boss', 'n=9 / hp=4400');
const hpSum = B.STAGES.reduce((a, s) => a + s.hp, 0);
ok('HP_total 合计 10330', hpSum === 10330, 'sum=' + hpSum);
ok('喘息层为 3 / 6 / 8', [3, 6, 8].every(n => B.STAGES[n - 1].type === '喘息'), '3/6/8');
let waveOk = true, waveDetail = [];
for (const s of B.STAGES) {
    const t = Math.round(s.hp / s.dps * 1.3);
    const d = Math.round(t / 39 * 100) / 100;
    if (t !== s.t || d !== s.d) { waveOk = false; waveDetail.push('n=' + s.n + ' ' + t + '/' + d); }
}
ok('T(n)=HP/dps×1.3、D(n)=T(n)/T(1) 逐层复算一致', waveOk,
   waveOk ? '9 层全一致（D2=1.15 / D5=1.28 / D9=2.67）' : waveDetail.join(' '));
// docs/01 §8.3 校验口径：「最长连续上升 2 层」「无连续 3 关以上单调上升」
// = 连续上升的「次数」最多 2（1→2、3→4→5），不允许 3 次连升。
let run = 0, maxRun = 0;
for (let i = 1; i < B.STAGES.length; i++) {
    if (B.STAGES[i].d > B.STAGES[i - 1].d) { run++; maxRun = Math.max(maxRun, run); }
    else run = 0;
}
ok('最长连续上升 2 层 / 无连续 3 关以上单调上升', maxRun <= 2, 'maxRun=' + maxRun);

// ---- ④ 技能与输入映射（docs/01 §6 / docs/06 §4） ----
ok('4 技能槽键位 J / K / L / I 与输入映射表一致',
   B.SKILLS.length === 4 && B.SKILLS.map(s => s.key).join('') === 'JKLI', 'J/K/L/I');
ok('4 技能全部有已产 VFX 样板',
   B.SKILLS.every(s => /^vfx_(sword_qi|thunder_talisman|dan_fire|rejuvenation)$/.test(s.vfx)),
   B.SKILLS.map(s => s.vfx).join(', '));
ok('技能 CD / cost / base 全部标 PROPOSAL（非冻结值）',
   B.SKILLS.every(s => s.proposal === true), '4/4 proposal=true');
ok('回春诀为治疗（06 §4 无攻击性）',
   B.SKILLS.find(s => s.id === 'rejuvenation').kind === 'heal', 'kind=heal');
ok('塔层怪物映射均在 MOBS 行为表内',
   B.STAGES.every(s => s.mobs.every(m => !!B.MOBS[m])), '9 层映射全覆盖');
ok('Boss 素材缺失 → 占位标记（不伪造素材）',
   B.MOBS.boss_judge.boss && B.MOBS.boss_tower_lord.boss &&
   new B.BattleSim({ runId: 'probe', stage: 9 }).enemies[0].placeholder === true,
   '第 9 层 placeholder=true');

// ---- ⑤ M1 状态机 ----
{
    const s = new B.BattleSim({ runId: 'state-check', stage: 1 });
    s.step(B.TICK, { skills: [true, false, false, false] });
    const afterFirst = s.snapshot();
    ok('施法进入 CASTING 且扣灵力 / 置 CD',
       afterFirst.state === 'CASTING' && afterFirst.cd[0] > 0 && afterFirst.spirit < 100,
       'state=' + afterFirst.state + ' cd0=' + afterFirst.cd[0]);
    let seenUnavailable = false;
    for (let i = 0; i < 10; i++) {
        const ev = s.step(B.TICK, { skills: [true, false, false, false] });
        if (ev.some(e => e.type === 'cast_unavailable' && e.reason === 'CD')) seenUnavailable = true;
    }
    ok('CD 内重复技能输入直接忽略', seenUnavailable, 'cast_unavailable / reason=CD');
}
{
    const s = new B.BattleSim({ runId: 'spirit-check', stage: 1 });
    s.spirit = 0;
    const ev = s.step(B.TICK, { skills: [false, true, false, false] });
    ok('灵力不足不施法且字段不变',
       ev.some(e => e.type === 'cast_unavailable' && e.reason === '灵力不足') && s.spirit < 10,
       '引雷符 cost=16 / spirit≈0');
}
{
    const s = new B.BattleSim({ runId: 'dodge-check', stage: 1 });
    s.enemies[0].x = s.x + 30;
    s.enemies[0].attackTimer = 0;
    const ev = s.step(B.TICK, { dodge: true });
    ok('闪避消耗体力并给无敌帧', ev.some(e => e.type === 'dodge') && s.invuln > 0,
       'stamina=' + s.stamina + ' invuln=' + s.invuln);
    const hpBefore = s.hp;
    s.enemies[0].attackTimer = 0;
    const ev2 = s.step(B.TICK, {});
    ok('无敌帧内忽略敌人伤害',
       s.hp === hpBefore && ev2.some(e => e.type === 'dodge_ignore'), 'hp 未变');
}
{
    const s = new B.BattleSim({ runId: 'dead-check', stage: 1 });
    s.state = 'DEAD'; s.finished = true; s.hp = 0;
    const before = JSON.stringify(s.snapshot());
    s.step(B.TICK, { axis: 1, skills: [true, true, true, true], dodge: true });
    ok('DEAD 状态忽略全部输入', JSON.stringify(s.snapshot()) === before, '快照不变');
}
{
    const s = new B.BattleSim({ runId: 'facing-check', stage: 1 });
    s.step(B.TICK, { axis: -1 });
    const left = s.snapshot().facing;
    s.step(B.TICK, { axis: 1 });
    ok('M5 朝向只能 ±1（0 视为 +1）', left === -1 && s.snapshot().facing === 1, '-1 → +1');
}
{
    // 第 20 轮实测缺陷：skills 数组存在但全 false 时曾吞掉 move，令玩家永远走不动。
    const s = new B.BattleSim({ runId: 'move-check', stage: 1 });
    const x0 = s.x;
    for (let i = 0; i < 30; i++) s.step(B.TICK, { axis: 1, skills: [false, false, false, false] });
    ok('skills 全 false 时仍执行 move（不吞输入）', s.x > x0 + 80,
       'x ' + x0.toFixed(1) + ' → ' + s.x.toFixed(1) + ' / 30 tick');
}

// ---- ⑥ 确定性 / 固定 tick ----
function drive(id) {
    const s = new B.BattleSim({ runId: id, stage: 1 });
    for (let i = 0; i < 240; i++) {
        const axis = (i % 60 < 30) ? 1 : -1;
        const skills = [i % 24 === 0, i % 71 === 0, i % 43 === 0, false];
        s.step(B.TICK, { axis: axis, skills: skills });
    }
    return s.snapshot();
}
const a = JSON.stringify(drive('determinism-A'));
const b = JSON.stringify(drive('determinism-A'));
ok('同 (runId, stage, 输入序列) 快照逐字段一致', a === b, '240 tick / 8 s');
const c = JSON.stringify(drive('determinism-B'));
ok('不同 runId 产生不同战斗轨迹', a !== c, '暴击与敌人行为由 seed 驱动');
{
    const s1 = new B.BattleSim({ runId: 'tick-A', stage: 1 });
    const s2 = new B.BattleSim({ runId: 'tick-A', stage: 1 });
    const input = { axis: 1, skills: [true, false, false, false] };
    s1.step(B.TICK * 6, input);
    for (let i = 0; i < 6; i++) s2.step(B.TICK, input);
    ok('固定 tick 与浏览器帧率无关', JSON.stringify(s1.snapshot()) === JSON.stringify(s2.snapshot()),
       '一次 step(6 tick) == 六次 step(1 tick)');
}

// ---- ⑦ 与 CardDeck 共享池联动 ----
{
    const empty = new B.BattleSim({ runId: 'deck-link', stage: 1 });
    const dmgEmpty = empty.computeDamage(60, false, 0);
    empty.syncDeck({ extra_pool: 200, offense_pool_used: 50, combo_multiplier: 0.4 });
    const dmgLinked = empty.computeDamage(60, false, 0);
    ok('选卡后共享池提高实战伤害', dmgLinked > dmgEmpty && empty.pool === 250,
       dmgEmpty + ' → ' + dmgLinked + ' / pool=250');
    empty.syncDeck({ extra_pool: 99999, offense_pool_used: 99999, combo_multiplier: 99 });
    ok('联动后仍受五上界钳制（pool≤600 / combo≤2.5）',
       empty.pool === 600 && empty.comboBonus === 1.5 &&
       empty.computeDamage(180, true, 0) <= B.maxHit(),
       'pool=600 / comboBonus=1.5 / dmg=' + empty.computeDamage(180, true, 0));
    ok('联动不产生数值违规', empty.errors.length === 0, 'errors=0');
}

// ---- ⑧ 清层 / 9 层推进 / 事件队列 ----
{
    const s = new B.BattleSim({ runId: 'clear-check', stage: 1 });
    for (const e of s.enemies) { e.dead = true; e.hp = 0; }
    const ev = s.step(B.TICK, {});
    ok('敌人清空发 stage_cleared 且给下一层',
       ev.some(e => e.type === 'stage_cleared' && e.next === 2), 'stage 1→2');
    let n = s.stage;
    while (s.stage < 9) { s.nextStage({}); n = s.stage; }
    ok('可推进到第 9 层塔主（HP_total 4400）',
       n === 9 && s.stageDef.hp === 4400 && s.enemies[0].boss, 'stage=9 / hp=4400');
}
{
    const s = new B.BattleSim({ runId: 'event-check', stage: 1 });
    s.enemies[0].x = s.x + 40;
    const ev = s.step(B.TICK, { skills: [true, false, false, false] });
    const types = ev.map(e => e.type);
    ok('判定同帧同时发 cast_started / vfx_requested / damage_applied',
       types.includes('cast_started') && types.includes('vfx_requested') && types.includes('damage_applied'),
       types.join(', '));
    ok('特效只由 vfx_requested 驱动（DF-03）',
       ev.filter(e => e.type === 'vfx_requested').length === 1, 'count=1');
}
{
    const s = new B.BattleSim({ runId: 'bounds-check', stage: 7 });
    for (let i = 0; i < 300; i++) s.step(B.TICK, { axis: i < 150 ? 1 : -1 });
    const snap = s.snapshot();
    ok('角色与敌人始终在 480 逻辑宽度内',
       snap.x >= 20 && snap.x <= 460 && snap.enemies.every(e => e.x >= 24 && e.x <= 456),
       'player.x=' + snap.x);
    ok('逻辑分辨率 480×270 / 地面 y=216 与 01 §9 一致',
       B.LOGICAL_W === 480 && B.LOGICAL_H === 270 && B.GROUND_Y === 216, '480×270 / y=216');
}

const passed = checks.filter(c => c.ok).length;
const report = {
    verdict: passed === checks.length ? 'PASS' : 'FAIL',
    summary: { total: checks.length, passed: passed, failed: checks.length - passed },
    algorithm: '固定 tick 1/30s + xorshift32 + FNV-1a；伤害公式照抄 docs/01 §8.1；PROPOSAL 占位值不参与冻结数值',
    checks: checks,
};
process.stdout.write(JSON.stringify(report, null, 2) + '\n');
process.exit(passed === checks.length ? 0 : 1);
