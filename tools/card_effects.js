/*
 * card_effects.js — 冻结卡库 → 网页战斗「可观测效果」的编译器（浏览器 / Node 同源）
 *
 * 第 21 轮：用户上轮反馈「demo 只能看到选卡，战斗效果也看不到」。第 20 轮只把
 * 数值型卡的共享池接进战斗，机制型卡选中后只有一个「hook 未实现」的提示。
 * 本模块把卡库里**已经冻结写明**的 params 映射成 battle_sim.js 可消费的 EffectSet，
 * 让「选一张机制卡 → 回战斗」真的看得见多段命中 / 吸血 / 破防 / 护盾 / 复活等变化。
 *
 * 严格边界（docs/18 与网页面板如实标注，不得省略）：
 *   - 只读 lib.cards[].params / hook / type，**不修改卡库、不改冻结数值、不改五上界**。
 *   - 五上界变量（base_damage / extra_pool / combo_multiplier / crit_multiplier /
 *     defense_rate 的攻击侧 / realm_ratio）归 card_rules.js / CardDeck.gd，本模块不重复实现。
 *   - 只映射**语义明确**的键；语义需设计确认、归局外系统、或网页验证层没有对应
 *     系统的键，一律进 unbound 并给出理由，**不猜数值、不伪造效果**。
 *   - 本模块产出的是「网页验证层的可视化口径」，不是 docs/01 冻结规格，不是平衡结论，
 *     全部待设计确认（PROPOSAL）。Godot 侧没有战斗逻辑，本结果不可迁移到实机。
 */
(function (global) {
    'use strict';

    // ---------- 网页验证层的安全上界（防止飘字/回血/护盾数值失控；不是游戏平衡值） ----------
    const CAPS = Object.freeze({
        segments: 4,            // 单次技能最多拆分段数
        pierceDefense: 0.30,    // 削减目标 defense 上限
        shieldMax: 160,
        cdScaleMin: 0.50,       // CD 最短不低于原值 50%
        spiritCostMin: 0.30,
        spiritOnKill: 20,
        spiritOnHit: 6,
        spiritOnHurt: 8,
        hpMaxDelta: 120,
        spiritMaxDelta: 60,
        moveSpeedBonus: 0.50,
        hurtInvuln: 0.60,       // 受击后无敌窗口（避水：0.2 → 0.5）
        critRateBonus: 0.30,
        damageTakenMin: 0.50,
        flatReduce: 20,
        freeCastUses: 3,
        reviveHp: 0.30,
    });

    // ---------- 归抽卡规则层 / 局外系统（card_rules.js / CardDeck.gd 负责，不在此重复） ----------
    const DECK_KEYS = Object.freeze({
        base_damage: '五上界变量，由 CardDeck.applyParams / clampOffense 守卫',
        extra_pool: '五上界变量，由 CardDeck 共享池路径处理',
        combo_multiplier: '五上界变量，由 CardDeck 守卫',
        crit_multiplier: '五上界变量，由 CardDeck 守卫',
        realm_ratio: '五上界变量（境界属局外轴 M2）',
        pool: '数值池声明，归 CardDeck 的 offense_pool 口径',
        cap: '上界声明，归 CardDeck 的 clampOffense 口径',
        stop_draw: '封牌，CardDeck.pick 已实现',
        skip_draw: '舍牌，CardDeck.skipDraw 已实现',
        choice_count: '三选一数量，CardDeck.choiceCount 已实现',
        affix_cap: '词缀上限，属局外 Roguelite 系统',
        reward_clamp: '奖励钳制，属局外结算系统',
        stone: '灵石经济，属局外 economy 系统',
        free_forge: '局外重铸，网页验证层无对应系统',
        goals: '局外目标，网页验证层无对应系统',
        legacy_choices: '传承灵韵，属 MetaSave 局外存档',
        legacy_count: '传承灵韵，属 MetaSave 局外存档',
        recompute_B: '需重算 B 公式（R35 未处置），不得在此近似',
        seal_every: '抽卡节奏，属 CardDeck 候选规则',
        redraw: '重抽，属 CardDeck 候选规则',
        visible: '候选可见张数，属 CardDeck 候选规则',
        fresh_category: '候选类别刷新，属 CardDeck 候选规则',
        amplify: '局外传承倍率，属 MetaSave',
        seal: '封牌标记，归 CardDeck',
    });

    // ---------- 语义需设计确认 / 网页无对应系统：明确不模拟，绝不猜数值 ----------
    const NONE_REASON = Object.freeze({
        damage: '「damage」在卡库里兼作代价/条件/倍率，语义需设计确认，不猜测',
        taken: '受伤代价的条件语义需设计确认',
        heal: '治疗比例的作用对象（伤害/HP 上限/每次命中）未定，需设计确认',
        per_stage: '按层结算的回复量基准未给值，需设计确认',
        convert: '卡面是「治疗量/已吸收量 → 下一次技能伤害」，不是吸血；网页验证层没有该转化链，不伪造',
        regen: '卡面均为「脱战后」或「连续 3 次命中」才生效，战斗中不该触发；脱战判定未定义',
        on_hit: '同一 hook 下「截取」指玩家受击回灵、「逆转回灵」指命中回灵，按卡 ID 精确映射（见 BATTLE_MAP）',
        per_hit: '破云式里是分段倍率（由 split 处理），逆转回灵里是命中回灵量；按卡 ID 区分',
        shield_cap: '反涌是「灵力溢出转护盾」，网页验证层没有溢出结算，不固定发盾',
        pierce: '剑意凝形需「剑修标签 ≥2」条件 + 贯穿路径判定，标签系统未建',
        affix: '敌人词缀系统未建（五行逆克只对带「铁壁」词缀的敌人生效）',
        school: '门派标签系统未建',
        tags: '门派标签系统未建',
        split_total: '由 hits 一并处理（落点均分，网页无落点系统，用同一目标分段近似）',
        per_hit_ratio: '由 split 一并处理',
        dot_stack: 'DoT 每跳伤害策划案未给值，不凭空造数',
        stack: '叠层每跳伤害策划案未给值，不凭空造数',
        no_new_peak: '「不刷新峰值」属统计口径，不影响战斗逐帧行为',
        per_puppet: '召唤物 / 假人系统网页验证层没有，不模拟',
        threshold: '条件阈值触发口径需设计确认',
        threshold_delta: '技能槽阈值口径需设计确认',
        swap_per_stage: '技能槽换位的键位映射需设计确认（Q17 未拍板）',
        remap: '技能槽重映射需键位设计稿（Q17 未拍板）',
        school_tags: '门派标签系统未建',
        skill_slots: '技能槽扩容需 UI 设计稿（Q17 未拍板）',
        idle: '潜行帧表现需素材 / UI 设计稿',
        stealth: '潜行机制未设计',
        proxy: '假人替身系统未建',
        reset_cd: '复活附带重置 CD 的口径需设计确认',
        cast_lock: '施法硬直归 PROPOSAL 占位，改它等于改演示节奏，不做',
        out_combat: '脱战判定未定义（聚息明确写「战斗中不生效」）',
        streak: '「连续 3 次命中」计数触发口径需设计确认',
        cd: '该 cd 属触发间隔而非技能 CD，语义需确认',
        dao_xing: '道行倍率属局外轴，网页验证层无对应系统',
        all_stats: '全属性词条需属性表设计确认',
        layers: '叠层机制需设计确认',
        self_damage: '自伤代价的结算时机需设计确认',
        no_heal: '禁疗禁的是哪个来源需设计确认',
        uses: '触发次数需与 auto_cast 条件一并设计确认',
        mode: '「击杀回灵改为命中回灵」的替换口径由按卡 ID 映射处理',
        skill: '技能 ID 声明，表示该卡只作用于指定技能；本验证层 4 技能槽无法一一对应，已逐条标注近似',
        auto_: 'auto_cast 条件触发需设计确认，本轮只在面板显示标记',
        shield_max_note: '',
    });

    const LAYER_BATTLE = 'battle';
    const LAYER_DECK = 'deck';
    const LAYER_NONE = 'none';

    function clampf(v, lo, hi) { return Math.min(Math.max(Number(v) || 0, lo), hi); }
    function num(v) { return Number(v) || 0; }

    /** battle_sim.js 消费的 EffectSet 默认值：全 0 / 全 false 时与第 20 轮行为逐字段一致。 */
    function defaultMods() {
        return {
            segmentRatios: [1.0],   // 一次命中拆成几段、每段伤害比例
            pierceDefense: 0,       // 削减目标 defense（破域，无条件 5%）
            shieldMax: 0,
            cdScale: 1,             // 技能 CD 系数
            spiritCostScale: 1,     // 灵力消耗系数
            freeCastOnFull: false,  // 灵力满时下一技能不耗灵（灵潮）
            spiritOnKill: 0,
            spiritOnHit: 0,         // 逆转回灵：每次命中回灵
            spiritOnHurt: 0,        // 截取：玩家受击回灵
            hpMaxFlat: 0,           // 绝对增量（凝丹 +24 / 寿元 +60）
            hpMaxRatio: 0,          // 比例增量（舍身 −15%）
            spiritMaxFlat: 0,
            spiritMaxRatio: 0,
            moveSpeedBonus: 0,
            hurtInvuln: 0,          // 受击后的无敌窗口（避水 0.5 s）
            critRateBonus: 0,
            damageTakenScale: 1,    // 玩家承伤系数（铁皮 / 混元 / 守拙）
            flatReduce: 0,          // 铁骨：固定减伤
            reviveHp: 0,            // 舍利 / 转生：首次阵亡复活比例
            reveal: false,          // 天人感应：面板显示敌人 HP
        };
    }

    function replaceRatios(m, arr) {
        // 多张同类卡叠加时截断，避免一次技能飘出十几段字
        m.segmentRatios = arr.slice(0, CAPS.segments);
    }

    // ---------- 语义明确的键 → 战斗效果（每张卡可命中多条） ----------
    // handler(m, p, c) 直接改 mods；返回给 UI 的 label / detail 单独声明。
    // apply(m, p, c) 返回 false 表示「这张卡的这个键本轮不映射」→ 自动归 none，
    // 避免按参数名猜测语义（第 21 轮逐张核对卡面 text 后收敛）。
    const BATTLE_MAP = Object.freeze({
        split: {
            label: '多段命中',
            detail: () => '飞剑分裂 2 道，总伤不变 → 0.5 / 0.5 均分',
            note: '⚠️ R54：卡面「总伤不变」与 params split:2 × per_hit:0.6 = 1.2 不自洽；本验证层以冻结卡面 text 为准，待设计确认',
            apply: (m, p) => {
                const n = clampf(Math.round(num(p.split)), 1, CAPS.segments);
                replaceRatios(m, Array(n).fill(1.0 / n));
                return true;
            },
        },
        hits: {
            label: '落点均分',
            detail: p => '引雷符落点 +1，总伤在 2 个落点间均分（0.5 / 0.5）',
            note: '网页验证层没有「落点」坐标系统，用同一目标分段近似；不改总伤',
            apply: (m, p) => {
                if (!p.split_total) return false;
                const n = clampf(Math.round(num(p.hits)), 1, CAPS.segments);
                replaceRatios(m, Array(n).fill(1.0 / n));
                return true;
            },
        },
        extra_hit: {
            label: '追加一段',
            detail: p => '追加 1 段 ' + (num(p.extra_hit) * 100).toFixed(0) + '% 伤害（单次峰值不变）',
            apply: (m, p) => {
                if (m.segmentRatios.length < CAPS.segments) {
                    m.segmentRatios.push(clampf(num(p.extra_hit), 0.05, 1.0));
                }
                return true;
            },
        },
        pierce_defense: {
            label: '破防',
            detail: p => '无视目标 ' + (num(p.pierce_defense) * 100).toFixed(0) + '% 减伤',
            apply: (m, p) => {
                if (p.affix) return false;    // 五行逆克只对「铁壁」词缀生效，词缀系统未建
                m.pierceDefense = clampf(m.pierceDefense + num(p.pierce_defense), 0, CAPS.pierceDefense);
                return true;
            },
        },
        shield_max: {
            label: '护盾',
            detail: p => '每层开局护盾 +' + p.shield_max,
            apply: (m, p) => { m.shieldMax = clampf(m.shieldMax + num(p.shield_max), 0, CAPS.shieldMax); return true; },
        },
        skill_cd: {
            label: '技能冷却',
            detail: p => '全技能 CD ' + (num(p.skill_cd) * 100).toFixed(0) + '%',
            apply: (m, p) => { m.cdScale = clampf(m.cdScale + num(p.skill_cd), CAPS.cdScaleMin, 1.5); return true; },
        },
        spirit_cost: {
            label: '灵力消耗',
            detail: p => '技能灵力消耗 ' + (num(p.spirit_cost) * 100).toFixed(0) + '%',
            apply: (m, p, c) => {
                // 丹香卡面限定「回春诀灵耗减半」，网页 4 技能槽不按技能区分，不全局套用
                if (c.id === 'card_danxiang') return false;
                m.spiritCostScale = clampf(m.spiritCostScale + num(p.spirit_cost), CAPS.spiritCostMin, 1.5);
                return true;
            },
        },
        free_cast: {
            label: '免费施法',
            detail: () => '灵力满时下一技能不耗灵',
            apply: (m, p) => { if (p.free_cast === true) m.freeCastOnFull = true; return !!p.free_cast; },
        },
        on_kill: {
            label: '击杀回灵',
            detail: p => '击杀回灵 +' + p.on_kill,
            apply: (m, p) => { m.spiritOnKill = clampf(m.spiritOnKill + num(p.on_kill), 0, CAPS.spiritOnKill); return true; },
        },
        per_hit: {
            label: '命中回灵',
            detail: p => '击杀回灵改为每次命中回灵 +' + p.per_hit,
            apply: (m, p, c) => {
                if (c.id !== 'card_nianzhuan') return false;   // 破云式里是分段倍率，由 split 处理
                m.spiritOnHit = clampf(m.spiritOnHit + num(p.per_hit), 0, CAPS.spiritOnHit);
                return true;
            },
        },
        on_hit: {
            label: '受击回灵',
            detail: p => '玩家受击回灵 +' + p.on_hit,
            apply: (m, p, c) => {
                if (c.id !== 'card_jieqi') return false;
                m.spiritOnHurt = clampf(m.spiritOnHurt + num(p.on_hit), 0, CAPS.spiritOnHurt);
                return true;
            },
        },
        hp_max: {
            label: '生命上限',
            detail: p => (Math.abs(num(p.hp_max)) < 1
                ? 'HP 上限 ' + (num(p.hp_max) * 100).toFixed(0) + '%'
                : 'HP 上限 ' + (num(p.hp_max) > 0 ? '+' : '') + p.hp_max),
            apply: (m, p) => {
                const v = num(p.hp_max);
                // 卡库里绝对值（+24 / +60）与比例（−0.15）混用，按 |v|<1 区分
                if (Math.abs(v) < 1) m.hpMaxRatio = clampf(m.hpMaxRatio + v, -0.6, 0.6);
                else m.hpMaxFlat = clampf(m.hpMaxFlat + v, -CAPS.hpMaxDelta, CAPS.hpMaxDelta);
                return true;
            },
        },
        spirit_max: {
            label: '灵力上限',
            detail: p => (Math.abs(num(p.spirit_max)) < 1
                ? '灵力上限 ' + (num(p.spirit_max) * 100).toFixed(0) + '%'
                : '灵力上限 ' + (num(p.spirit_max) > 0 ? '+' : '') + p.spirit_max),
            apply: (m, p) => {
                const v = num(p.spirit_max);
                if (Math.abs(v) < 1) m.spiritMaxRatio = clampf(m.spiritMaxRatio + v, -0.6, 0.6);
                else m.spiritMaxFlat = clampf(m.spiritMaxFlat + v, -CAPS.spiritMaxDelta, CAPS.spiritMaxDelta);
                return true;
            },
        },
        move_speed: {
            label: '移动速度',
            detail: p => '移速 ' + (num(p.move_speed) * 100).toFixed(0) + '%',
            apply: (m, p) => { m.moveSpeedBonus = clampf(m.moveSpeedBonus + num(p.move_speed), -0.5, CAPS.moveSpeedBonus); return true; },
        },
        invuln: {
            label: '受击无敌',
            detail: p => '受击后无敌窗口 0.2 s → ' + p.invuln + ' s',
            apply: (m, p) => { m.hurtInvuln = clampf(Math.max(m.hurtInvuln, num(p.invuln)), 0, CAPS.hurtInvuln); return true; },
        },
        crit_rate: {
            label: '暴击率',
            detail: p => '暴击率 +' + (num(p.crit_rate) * 100).toFixed(0) + '%',
            apply: (m, p) => { m.critRateBonus = clampf(m.critRateBonus + num(p.crit_rate), 0, CAPS.critRateBonus); return true; },
        },
        defense_rate: {
            label: '玩家减伤',
            detail: p => '承伤 -' + (num(p.defense_rate) * 100).toFixed(0) + '%',
            note: '卡面 0.75 钳制指攻击侧 defense_rate；这里按玩家承伤近似，待设计确认',
            apply: (m, p) => { m.damageTakenScale = clampf(m.damageTakenScale - num(p.defense_rate), CAPS.damageTakenMin, 1.0); return true; },
        },
        flat_reduce: {
            label: '固定减伤',
            detail: p => '每次承伤 -' + p.flat_reduce,
            apply: (m, p) => { m.flatReduce = clampf(m.flatReduce + num(p.flat_reduce), 0, CAPS.flatReduce); return true; },
        },
        revive_hp: {
            label: '复活',
            detail: p => '本局首次阵亡以 ' + (num(p.revive_hp) * 100).toFixed(0) + '% HP 复活',
            apply: (m, p) => { m.reviveHp = clampf(Math.max(m.reviveHp, num(p.revive_hp)), 0, CAPS.reviveHp); return true; },
        },
        reveal: {
            label: '敌人情报',
            detail: () => '面板显示敌人 HP 数值（信息层，不改判定）',
            apply: (m, p) => { if (p.reveal === true) m.reveal = true; return !!p.reveal; },
        },
    });

    /** 按顺序稳定遍历 params，保证 (卡库, 已选序列) 可复现。 */
    function compileCardEffects(lib, cardIds) {
        const byId = Object.create(null);
        const allCards = (lib && lib.cards) || [];
        for (const c of allCards) byId[c.id] = c;

        const mods = defaultMods();
        const cards = [];
        const layers = { battle: [], deck: [], none: [] };
        const unboundKeys = Object.create(null);
        const notes = [];                  // 卡面 / 参数不自洽、近似实现等如实记录
        const seen = Object.create(null);   // 同一张卡可堆叠，但 UI 明细按 ID 合并计数

        for (const id of (cardIds || [])) {
            const c = byId[id];
            if (!c) continue;
            const p = c.params || {};
            const entry = seen[id];
            const row = entry || { id: c.id, name: c.name, type: c.type, hook: c.hook,
                                   stacks: 0, effects: [] };
            if (!entry) { seen[id] = row; cards.push(row); }
            row.stacks += 1;

            for (const key of Object.keys(p)) {
                let layer, label, detail, reason = '';
                const r = Object.prototype.hasOwnProperty.call(BATTLE_MAP, key) ? BATTLE_MAP[key] : null;
                if (r) {
                    if (r.apply(mods, p, c) === false) {
                        // 键有映射但本卡语义不满足 → 如实归 none，不猜测
                        layer = LAYER_NONE;
                        label = key;
                        reason = NONE_REASON[key] || ('「' + c.name + '」的 ' + key + ' 条件未满足，本验证层不模拟');
                        detail = reason;
                    } else {
                        layer = LAYER_BATTLE;
                        label = r.label;
                        detail = r.detail(p, c);
                        if (r.note) notes.push({ card: c.id, name: c.name, key: key, note: r.note });
                    }
                } else if (Object.prototype.hasOwnProperty.call(DECK_KEYS, key)) {
                    layer = LAYER_DECK;
                    label = key;
                    detail = DECK_KEYS[key];
                    reason = DECK_KEYS[key];
                } else {
                    layer = LAYER_NONE;
                    label = key;
                    reason = NONE_REASON[key] ||
                        ('卡库参数「' + key + '」在本验证层没有对应系统，待正式工程确认');
                    detail = reason;
                }
                const item = { key: key, layer: layer, label: label, detail: detail,
                               card: c.id, value: p[key] };
                row.effects.push(item);
                layers[layer].push(item);
                if (layer !== LAYER_BATTLE) {
                    if (!unboundKeys[key]) unboundKeys[key] = { key: key, reason: reason, cards: [] };
                    if (!unboundKeys[key].cards.includes(c.id)) unboundKeys[key].cards.push(c.id);
                }
            }
        }
        return {
            cards: cards,
            mods: mods,
            layers: layers,
            unboundKeys: Object.keys(unboundKeys).sort().map(k => unboundKeys[k]),
            notes: notes,
            counts: {
                battle: layers.battle.length,
                deck: layers.deck.length,
                none: layers.none.length,
                cards: cards.length,
            },
            caps: CAPS,
            scope: 'web-validation-only',   // 明确不是冻结规格 / 不是 Godot 实机口径
        };
    }

    const api = { compileCardEffects, defaultMods, CAPS, BATTLE_MAP, DECK_KEYS, NONE_REASON };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (global) global.CardEffects = api;
})(typeof window !== 'undefined' ? window : globalThis);
