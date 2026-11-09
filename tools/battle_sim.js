/*
 * battle_sim.js — 横版战斗「确定性规则内核」（浏览器 / Node 共用同一份实现）
 *
 * 第 20 轮（用户要求）：「先做主菜单和战斗横版界面，不然 demo 只能看到选卡」。
 * 本文件是网页 Demo 战斗画面的**规则层**，不是游戏本体、不是 Godot 场景。
 *
 * 规格依据（只读引用，不修改任何冻结数值）：
 *   - docs/01-策划案.md §6 M1 状态表 / 输入映射表 / 反馈清单 / M5 朝向镜像
 *   - docs/01-策划案.md §8.1 统一伤害公式 + 五上界铁律（clamp 1..9999）
 *   - docs/01-策划案.md §8.3 九层难度波形 HP_total / P_dps / T(n) / D(n)
 *   - docs/06-素材生产清单.md §4 技能清单、§5 怪物行为、§7 塔层→素材映射
 *   - docs/09 表现规格：480×270 逻辑分辨率、24 色、只出朝右一套
 *
 * 边界（必须在 docs/17 与网页上如实标注）：
 *   - 技能 CD / 灵力消耗 / 玩家 HP / 敌人伤害 / 暴击率 / 回复速率等**策划案未给值**，
 *     一律为 PROPOSAL 占位，供网页演示节奏使用，**不得当作冻结数值或平衡结论**。
 *   - 第 5 / 9 层 Boss 在**规则层**仍由 BOSS_PLACEHOLDER 映射到 mob_jian_hun（冻结规则不改）。
 *     第 32 轮更正：assets/boss/ 已有 gpt-image2 回稿转录的 42 帧真素材，网页展示层默认
 *     按 snapshot.type 取真帧；占位模式仅作对照。Godot 正式战斗工程仍未接入，
 *     不得把网页画面当作实机结论（Q17 / GUI F5 未过）。
 *   - 时间以固定 tick（1/30 s）推进，与浏览器帧率无关，保证 (seed, 输入序列) 可复现。
 *   - 与 CardDeck 的联动只取 offenseState() 的 extra_pool / offense_pool_used / combo，
 *     并再次钳到五上界；本文件不新开数值池。
 *   - 第 21 轮：新增 applyCardEffects()，消费 tools/card_effects.js 编译出的 EffectSet，
 *     让机制型卡在网页战斗里可观测。**空效果时与第 20 轮逐字段一致**（44/44 断言回归）。
 *     这些效果属「网页验证层可视化口径」，不是冻结规格，不迁移到 Godot 实机。
 */
(function (global) {
    'use strict';

    // ---------- 冻结口径（docs/01 §8.1，不得改） ----------
    const CAP_BASE = 180.0;
    const CAP_REALM_RATIO = 1.60;
    const CAP_EXTRA_POOL = 600.0;
    const CAP_COMBO = 2.5;
    const CAP_CRIT = 1.8;
    const CAP_DEFENSE = 0.75;
    const BOSS_HP_REFERENCE = 4400.0;
    const DMG_MIN = 1;
    const DMG_MAX = 9999;

    // ---------- 表现口径（docs/01 §9 / §8.3） ----------
    const LOGICAL_W = 480;
    const LOGICAL_H = 270;
    const GROUND_Y = 216;          // 与 previews 像素跑动页一致
    const FRAME_SIZE = 64;
    const TICK = 1.0 / 30.0;

    // ---------- PROPOSAL 占位（策划案未给值，待设计确认，标「待实测」） ----------
    const PROPOSAL = Object.freeze({
        playerMaxHp: 300,
        playerMaxSpirit: 100,
        playerMaxStamina: 100,
        spiritRegen: 9.0,           // 点/秒
        staminaRegen: 12.0,         // 点/秒
        dodgeCost: 25,
        dodgeInvuln: 0.42,         // 秒
        dodgeSpeed: 190,
        moveSpeed: 96,
        critChance: 0.10,
        castLock: 0.18,             // 秒，CASTING 硬直
        comboGainPerHit: 0.08,
        comboDecay: 0.12,           // 点/秒
        enemyAttackBase: 9,
        enemyAttackPerStage: 3.2,
        enemyAttackInterval: 1.9,   // 秒
        enemyMoveSpeed: 42,
        enemyRangedSpeed: 62,
    });

    // 9 层难度波形：HP_total / P_dps / T(n) / D(n) 逐行照抄 docs/01 §8.3
    const STAGES = Object.freeze([
        { n: 1, hp: 300, dps: 10, t: 39, d: 1.00, type: '教学', mobs: ['mob_shanxiao'] },
        { n: 2, hp: 480, dps: 14, t: 45, d: 1.15, type: '常规', mobs: ['mob_shanxiao', 'mob_zhi_kui'] },
        { n: 3, hp: 440, dps: 16, t: 36, d: 0.92, type: '喘息', mobs: ['mob_shanxiao', 'mob_zhi_kui'] },
        { n: 4, hp: 700, dps: 20, t: 46, d: 1.18, type: '常规', mobs: ['mob_yin_bing'] },
        { n: 5, hp: 920, dps: 24, t: 50, d: 1.28, type: '挑战', mobs: ['boss_judge', 'mob_shanxiao'] },
        { n: 6, hp: 780, dps: 28, t: 36, d: 0.92, type: '喘息', mobs: ['mob_shanxiao', 'mob_yin_bing'] },
        { n: 7, hp: 1150, dps: 34, t: 44, d: 1.13, type: '常规', mobs: ['mob_shanxiao', 'mob_zhi_kui', 'mob_yin_bing', 'mob_jian_hun'] },
        { n: 8, hp: 1160, dps: 42, t: 36, d: 0.92, type: '喘息', mobs: ['mob_zhi_kui', 'mob_jian_hun'] },
        { n: 9, hp: 4400, dps: 55, t: 104, d: 2.67, type: '塔主 Boss', mobs: ['boss_tower_lord'] },
    ]);

    // 4 技能槽：只挑已有 VFX 样板的 4 项（docs/06 §4），键位来自 docs/01 §6 输入映射表
    // cd / spirit / base / heal 全部是 PROPOSAL，供演示节奏使用，不是冻结值。
    const SKILLS = Object.freeze([
        { id: 'sword_qi', name: '剑气斩', key: 'J', kind: 'attack', vfx: 'vfx_sword_qi',
          cd: 0.8, spirit: 6, base: 20, reach: 104, hits: 1, proposal: true },
        { id: 'thunder_talisman', name: '引雷符', key: 'K', kind: 'attack', vfx: 'vfx_thunder_talisman',
          cd: 2.4, spirit: 16, base: 46, reach: 168, hits: 2, proposal: true },
        { id: 'dan_fire', name: '三昧丹火', key: 'L', kind: 'attack', vfx: 'vfx_dan_fire',
          cd: 1.6, spirit: 12, base: 34, reach: 132, hits: 2, proposal: true },
        { id: 'rejuvenation', name: '回春诀', key: 'I', kind: 'heal', vfx: 'vfx_rejuvenation',
          cd: 6.0, spirit: 20, heal: 60, reach: 0, hits: 0, proposal: true },
    ]);

    // 怪物行为（docs/06 §5）：近战扑击 / 远程投符 / 持戈近战 / 高速突进
    const MOBS = Object.freeze({
        mob_shanxiao: { name: '山魈', behavior: 'melee', speed: 0.85, defense: 0.10 },
        mob_zhi_kui: { name: '纸傀', behavior: 'ranged', speed: 0.75, defense: 0.05 },
        mob_yin_bing: { name: '阴兵', behavior: 'melee', speed: 0.95, defense: 0.20 },
        mob_jian_hun: { name: '剑魂', behavior: 'rush', speed: 1.45, defense: 0.15 },
        boss_judge: { name: '锁血判官', behavior: 'melee', speed: 0.80, defense: 0.30, boss: true },
        boss_tower_lord: { name: '天梯之主', behavior: 'rush', speed: 1.00, defense: 0.30, boss: true },
    });

    const BOSS_PLACEHOLDER = Object.freeze({
        boss_judge: 'mob_jian_hun',
        boss_tower_lord: 'mob_jian_hun',
    });

    // ---------- 工具 ----------
    function clampf(v, lo, hi) { return Math.min(Math.max(v, lo), hi); }
    function fnv1a(s) {
        let h = 0x811c9dc5 >>> 0;
        const bytes = new TextEncoder().encode(String(s));
        for (let i = 0; i < bytes.length; i++) {
            h = (h ^ bytes[i]) >>> 0;
            h = Math.imul(h, 0x01000193) >>> 0;
        }
        return h >>> 0;
    }
    function xorshift32(state) {
        let x = state >>> 0;
        x = (x ^ ((x << 13) >>> 0)) >>> 0;
        x = (x ^ (x >>> 17)) >>> 0;
        x = (x ^ ((x << 5) >>> 0)) >>> 0;
        return x >>> 0;
    }

    /** docs/01 §8.1 统一伤害公式。负输入显式报错，不静默吞掉（§6 边界情况表）。 */
    function damageFormula(base, realm, pool, combo, crit, defense, errors) {
        const err = errors || [];
        if (base < 0 || realm < 0 || pool < 0 || combo < 0 || defense < 0) {
            err.push('伤害公式收到负值输入，已按下界钳制');
        }
        const b = clampf(base, 0, CAP_BASE);
        const r = clampf(realm, 0, CAP_REALM_RATIO);
        const p = clampf(pool, 0, CAP_EXTRA_POOL);
        const c = clampf(combo, 0, CAP_COMBO);
        const cr = clampf(crit, 0, CAP_CRIT);
        const d = clampf(defense, 0, CAP_DEFENSE);
        const raw = (b * r + p) * c * cr * (1 - d);
        return Math.max(DMG_MIN, Math.min(DMG_MAX, Math.round(raw)));
    }

    /** 五上界最坏口径（与 CardDeck.peakDamage 一致）：Boss 4400 需 2 次命中。 */
    function maxHit() {
        return damageFormula(CAP_BASE, CAP_REALM_RATIO, CAP_EXTRA_POOL,
                             CAP_COMBO, CAP_CRIT, 0.0, null);
    }

    /**
     * 卡牌效果默认值（字段必须与 card_effects.js 的 defaultMods() 一致，
     * 由 verify_card_effects.js 断言键集合，防止两端漂移）。
     * 全 0 / 全 false 时下面每个分支都不改变第 20 轮的行为。
     */
    function emptyCardMods() {
        return {
            segmentRatios: [1.0],
            pierceDefense: 0,
            shieldMax: 0,
            cdScale: 1,
            spiritCostScale: 1,
            freeCastOnFull: false,
            spiritOnKill: 0,
            spiritOnHit: 0,
            spiritOnHurt: 0,
            hpMaxFlat: 0,
            hpMaxRatio: 0,
            spiritMaxFlat: 0,
            spiritMaxRatio: 0,
            moveSpeedBonus: 0,
            hurtInvuln: 0,
            critRateBonus: 0,
            damageTakenScale: 1,
            flatReduce: 0,
            reviveHp: 0,
            reveal: false,
        };
    }

    class BattleSim {
        /** opts: { runId, stage, deckState } —— deckState 来自 CardDeck.offenseState() */
        constructor(opts) {
            this.opts = opts || {};
            this.runId = String(this.opts.runId || 'battle-demo');
            this.events = [];
            this.errors = [];
            this.tickCount = 0;
            this.timeAcc = 0;
            this.fx = emptyCardMods();      // 默认空效果 → 与第 20 轮行为一致
            this.cardFx = null;
            this.startStage(Number(this.opts.stage || 1), this.opts.deckState || {});
            if (this.opts.cardEffects) this.applyCardEffects(this.opts.cardEffects);
        }

        /**
         * 第 21 轮：接 tools/card_effects.js 的 EffectSet。只影响表现 / 生存 / 节奏，
         * 绝不改 CAP_* 五上界、damageFormula、STAGES、SKILLS、PROPOSAL。
         * 可在 startStage 之后调用：重算上限与护盾，但不重置已携带的 hp。
         */
        applyCardEffects(effectSet) {
            // 空效果集 ≡ 没接效果：连「已接效果」标记都不能变，否则 snapshot 会与基线不一致。
            this.cardFx = (effectSet && effectSet.counts && effectSet.counts.cards > 0) ? effectSet : null;
            const incoming = (effectSet && effectSet.mods) || {};
            this.fx = Object.assign(emptyCardMods(), incoming);
            if (!Array.isArray(this.fx.segmentRatios) || this.fx.segmentRatios.length === 0) {
                this.fx.segmentRatios = [1.0];
            }
            const hp = this.hp;
            const oldMaxHp = this.maxHp;
            const wasFull = hp >= oldMaxHp;          // 开局满血：卡牌提上限应同步满血
            this.maxHp = Math.max(1, Math.round((PROPOSAL.playerMaxHp + this.fx.hpMaxFlat) *
                                                (1 + this.fx.hpMaxRatio)));
            this.maxSpirit = Math.max(1, Math.round((PROPOSAL.playerMaxSpirit + this.fx.spiritMaxFlat) *
                                                    (1 + this.fx.spiritMaxRatio)));
            this.hp = wasFull ? this.maxHp : Math.min(hp, this.maxHp);
            this.spirit = Math.min(this.spirit, this.maxSpirit);
            this.shield = this.fx.shieldMax;   // 护盾按「每层开局」结算（护体 / 反涌口径）
            this.reviveLeft = this.fx.reviveHp > 0 ? 1 : 0;
            this.freeCastReady = !!this.fx.freeCastOnFull;
            return this;
        }

        // ---- 卡牌联动：只取共享池与 combo 路径，一律再钳到上界 ----
        syncDeck(deckState) {
            const extra = Number((deckState && deckState.extra_pool) || 0);
            const used = Number((deckState && deckState.offense_pool_used) || 0);
            const combo = Number((deckState && deckState.combo_multiplier) || 0);
            this.pool = clampf(extra + used, 0, CAP_EXTRA_POOL);
            this.comboBonus = clampf(combo, 0, CAP_COMBO - 1.0);
        }

        startStage(stage, deckState) {
            const n = clampf(Math.round(stage), 1, 9);
            this.stageDef = STAGES[n - 1];
            this.stage = n;
            this.syncDeck(deckState || this.opts.deckState || {});
            this.rngState = fnv1a(this.runId + ':battle:' + String(n));
            if (this.rngState === 0) this.rngState = 0x6d2b79f5;
            this.time = 0;
            this.tickCount = 0;
            this.timeAcc = 0;
            this.state = 'IDLE';           // docs/01 §6 M1 状态表
            this.facing = 1;              // M5：只能 ±1，0 视为 +1
            this.x = 96;
            this.maxHp = Math.max(1, Math.round((PROPOSAL.playerMaxHp + this.fx.hpMaxFlat) *
                                                (1 + this.fx.hpMaxRatio)));
            this.maxSpirit = Math.max(1, Math.round((PROPOSAL.playerMaxSpirit + this.fx.spiritMaxFlat) *
                                                    (1 + this.fx.spiritMaxRatio)));
            this.hp = this.maxHp;
            this.spirit = this.maxSpirit;
            this.stamina = PROPOSAL.playerMaxStamina;
            this.shield = this.fx.shieldMax;
            this.reviveLeft = this.fx.reviveHp > 0 ? 1 : 0;
            this.freeCastReady = !!this.fx.freeCastOnFull;
            this.cd = SKILLS.map(() => 0);
            this.castLock = 0;
            this.invuln = 0;
            this.comboChain = 0;
            this.kills = 0;
            this.hits = 0;
            this.damageDealt = 0;
            this.damageTaken = 0;
            this.lastDamage = 0;
            this.finished = false;
            this.win = false;
            this.activeVfx = [];
            this.enemies = this.spawnEnemies();
            this.events = [];
            this.errors = [];
            this.emit('stage_start', { stage: n, type: this.stageDef.type, hpTotal: this.stageDef.hp });
            return this;
        }

        spawnEnemies() {
            const def = this.stageDef;
            const ids = def.mobs.slice();
            const total = def.hp;
            const share = Math.max(1, Math.floor(total / ids.length));
            return ids.map((id, i) => {
                const meta = MOBS[id] || MOBS.mob_shanxiao;
                const isBoss = !!meta.boss;
                const hp = (i === ids.length - 1) ? (total - share * (ids.length - 1)) : share;
                return {
                    id: id + ':' + i,
                    type: id,
                    sprite: BOSS_PLACEHOLDER[id] || id,
                    name: meta.name,
                    behavior: meta.behavior,
                    defense: meta.defense,
                    boss: isBoss,
                    placeholder: !!BOSS_PLACEHOLDER[id],
                    scale: isBoss ? 1.5 : 1.0,
                    phase: isBoss ? 1 : 0,
                    x: clampf(300 + i * 52, 200, 430),
                    hp: hp,
                    maxHp: hp,
                    anim: 'idle',
                    animTime: 0,
                    attackTimer: 0.9 + i * 0.35,
                    hurtFlash: 0,
                    dead: false,
                    deathTime: 0,
                };
            });
        }

        emit(type, data) {
            this.events.push(Object.assign({ type: type, t: Number(this.time.toFixed(3)) }, data || {}));
        }
        drainEvents() { const e = this.events; this.events = []; return e; }

        randf() {
            this.rngState = xorshift32(this.rngState);
            return ((this.rngState >>> 8) & 0xffffff) / 16777216.0;
        }

        /** 当前伤害口径（读给 UI 展示用，不产生副作用） */
        damagePreview(skillIndex, crit) {
            const s = SKILLS[skillIndex];
            if (!s || s.kind !== 'attack') return 0;
            return this.computeDamage(s.base, crit, 0);
        }

        computeDamage(base, crit, defense) {
            const realm = 1.00;                       // 局外境界第 1 境；上限 1.60 留给破境（M2）
            const combo = clampf(1.0 + this.comboBonus + this.comboChain, 0, CAP_COMBO);
            return damageFormula(base, realm, this.pool, combo,
                                 crit ? CAP_CRIT : 1.0, defense, this.errors);
        }

        /** docs/01 §6：同帧多次输入按 dodge > skill > move 取一次 */
        step(dt, input) {
            if (this.finished) return this.drainEvents();
            this.timeAcc += Math.max(0, Math.min(Number(dt) || 0, 0.25));
            let guard = 0;
            while (this.timeAcc >= TICK && guard < 32 && !this.finished) {
                this.timeAcc -= TICK;
                this.tick(TICK, input || {});
                guard++;
            }
            return this.drainEvents();
        }

        tick(dt, input) {
            this.time += dt;
            this.tickCount++;
            for (let i = 0; i < this.cd.length; i++) this.cd[i] = Math.max(0, this.cd[i] - dt);
            this.castLock = Math.max(0, this.castLock - dt);
            this.invuln = Math.max(0, this.invuln - dt);
            this.spirit = clampf(this.spirit + PROPOSAL.spiritRegen * dt, 0, this.maxSpirit);
            // 灵潮：灵力回满后重新获得一次免费施法机会
            if (this.fx.freeCastOnFull && this.spirit >= this.maxSpirit - 0.001) {
                this.freeCastReady = true;
            }
            this.stamina = clampf(this.stamina + PROPOSAL.staminaRegen * dt, 0, PROPOSAL.playerMaxStamina);
            this.comboChain = Math.max(0, this.comboChain - PROPOSAL.comboDecay * dt);

            if (this.state === 'DEAD') return;
            if (this.state === 'CASTING' && this.castLock <= 0) {
                this.state = 'IDLE';
                this.emit('cast_finished', {});
            }
            if (this.state === 'DODGING' && this.invuln <= 0) {
                this.state = 'IDLE';
                this.emit('dodge_finished', {});
            }

            // 输入优先级：dodge > skill > move（docs/01 §6）
            // 注意：skills 数组「存在」不等于「有技能被按下」；全 false 时必须落到 move，
            // 否则玩家永远走不动（第 20 轮无头浏览器实测抓到的真实缺陷）。
            const busy = (this.state === 'CASTING' || this.state === 'DODGING');
            const skillIdx = Array.isArray(input.skills) ? input.skills.findIndex(Boolean) : -1;
            if (input.dodge && !busy && this.stamina >= PROPOSAL.dodgeCost) {
                this.stamina -= PROPOSAL.dodgeCost;
                this.invuln = PROPOSAL.dodgeInvuln;
                this.state = 'DODGING';
                this.x = clampf(this.x + this.facing * PROPOSAL.dodgeSpeed * dt, 20, LOGICAL_W - 20);
                this.emit('dodge', { x: this.x, facing: this.facing });
            } else if (skillIdx >= 0 && skillIdx < SKILLS.length && !busy) {
                this.tryCast(skillIdx);
            } else if (!busy) {
                const axis = Number(input.axis || 0);
                if (axis !== 0) {
                    this.facing = axis > 0 ? 1 : -1;
                    const speed = PROPOSAL.moveSpeed * (1 + this.fx.moveSpeedBonus);
                    this.x = clampf(this.x + this.facing * speed * dt, 20, LOGICAL_W - 20);
                }
            }

            this.updateEnemies(dt);
            this.updateVfx(dt);
            this.checkEnd();
        }

        tryCast(idx) {
            const s = SKILLS[idx];
            if (!s) return;
            const fx = this.fx;
            // 灵潮：灵力满时下一技能不耗灵；默认 fx 下 cost === s.spirit，与第 20 轮一致
            const cost = (fx.freeCastOnFull && this.freeCastReady &&
                          this.spirit >= this.maxSpirit - 0.001) ? 0 : s.spirit * fx.spiritCostScale;
            if (this.cd[idx] > 0 || this.spirit < cost) {
                this.emit('cast_unavailable', { skill: s.id, reason: this.cd[idx] > 0 ? 'CD' : '灵力不足' });
                return;                                  // §6：字段不变，输入直接忽略
            }
            if (cost === 0 && s.spirit > 0) {
                this.freeCastReady = false;
                this.emit('card_effect', { kind: 'free_cast', skill: s.id,
                                           text: '灵潮：灵力满，本次施法不耗灵' });
            }
            this.spirit -= cost;
            this.cd[idx] = s.cd * fx.cdScale;
            this.state = 'CASTING';
            this.castLock = PROPOSAL.castLock;
            this.emit('cast_started', { skill: s.id, x: this.x, facing: this.facing });
            this.emit('vfx_requested', {                  // DF-03：特效只由信号驱动，不参与判定
                vfx: s.vfx, x: this.x + this.facing * 48, y: GROUND_Y - 32,
                facing: this.facing, skill: s.id, ttl: 0.42,
            });
            if (s.kind === 'heal') {
                const healed = Math.min(s.heal, this.maxHp - this.hp);
                this.hp += healed;
                this.emit('heal', { amount: healed, x: this.x, y: GROUND_Y - 64 });
                return;
            }
            // 命中判定：矩形身前 reach px（§6），不镜像整个场景，只按 facing 翻判定框
            const targets = this.enemies.filter(e => !e.dead &&
                (e.x - this.x) * this.facing >= -12 && (e.x - this.x) * this.facing <= s.reach);
            const hitTargets = targets.slice(0, Math.max(1, s.hits));
            if (hitTargets.length === 0) {
                this.emit('cast_miss', { skill: s.id });
                return;
            }
            const ratios = fx.segmentRatios;             // 默认 [1.0] → 与原路径等价
            if (ratios.length > 1) {
                this.emit('card_effect', { kind: 'multi_hit', skill: s.id, segments: ratios.length,
                    text: '多段命中：' + ratios.map(r => (r * 100).toFixed(0) + '%').join(' + ') });
            }
            for (const e of hitTargets) {
                const crit = this.randf() < (PROPOSAL.critChance + fx.critRateBonus);
                const defense = clampf(e.defense - fx.pierceDefense, 0, CAP_DEFENSE);
                const baseDmg = this.computeDamage(s.base, crit, defense);
                if (fx.pierceDefense > 0) {
                    this.emit('card_effect', { kind: 'pierce_defense', skill: s.id,
                        text: '破防：目标减伤 ' + e.defense.toFixed(2) + ' → ' + defense.toFixed(2) });
                }
                for (let si = 0; si < ratios.length; si++) {
                    if (e.dead) break;                   // 目标已倒下，不追加分段
                    const dmg = Math.max(DMG_MIN, Math.round(baseDmg * ratios[si]));
                    e.hp = Math.max(0, e.hp - dmg);
                    e.hurtFlash = 0.18;
                    e.anim = 'hit';
                    e.animTime = 0;
                    this.hits++;
                    this.damageDealt += dmg;
                    this.lastDamage = dmg;
                    this.comboChain = clampf(this.comboChain + PROPOSAL.comboGainPerHit, 0, CAP_COMBO - 1.0);
                    const ev = {
                        target: e.id, damage: dmg, crit: crit, x: e.x, y: GROUND_Y - 64,
                        skill: s.id, pool: this.pool,
                        combo: clampf(1.0 + this.comboBonus + this.comboChain, 0, CAP_COMBO),
                    };
                    if (ratios.length > 1) { ev.segment = si + 1; ev.segments = ratios.length; }
                    this.emit('damage_applied', ev);
                    if (fx.spiritOnHit > 0) {
                        this.spirit = clampf(this.spirit + fx.spiritOnHit, 0, this.maxSpirit);
                    }
                }
                if (crit) this.emit('shake', { power: 2 });
                if (e.boss) {
                    const ratio = e.hp / e.maxHp;
                    const newPhase = ratio > 0.66 ? 1 : (ratio > 0.33 ? 2 : 3);
                    if (newPhase !== e.phase) {
                        e.phase = newPhase;
                        this.emit('boss_phase', { target: e.id, phase: newPhase });
                    }
                }
                if (e.hp <= 0) {
                    e.dead = true;
                    e.anim = 'death';
                    e.animTime = 0;
                    this.kills++;
                    this.emit('enemy_death', { target: e.id, name: e.name, x: e.x });
                    if (fx.spiritOnKill > 0) {
                        this.spirit = clampf(this.spirit + fx.spiritOnKill, 0, this.maxSpirit);
                        this.emit('card_effect', { kind: 'spirit_on_kill',
                            text: '击杀回灵 +' + fx.spiritOnKill });
                    }
                }
            }
        }

        updateEnemies(dt) {
            const atk = PROPOSAL.enemyAttackBase + (this.stage - 1) * PROPOSAL.enemyAttackPerStage;
            for (const e of this.enemies) {
                e.hurtFlash = Math.max(0, e.hurtFlash - dt);
                e.animTime += dt;
                if (e.dead) { e.deathTime += dt; continue; }
                const dist = this.x - e.x;
                const adist = Math.abs(dist);
                const meta = MOBS[e.type] || MOBS.mob_shanxiao;
                const speed = PROPOSAL.enemyMoveSpeed * (meta.speed || 1);
                let moving = false;
                if (meta.behavior === 'ranged') {
                    // 06 §5：远程投符，保持距离
                    if (adist < 110) { e.x -= Math.sign(dist) * speed * 0.7 * dt; moving = true; }
                    else if (adist > 190) { e.x += Math.sign(dist) * speed * 0.7 * dt; moving = true; }
                } else if (adist > (e.boss ? 62 : 46)) {
                    const mult = meta.behavior === 'rush' ? 1.6 : 1.0;
                    e.x += Math.sign(dist) * speed * mult * dt;
                    moving = true;
                }
                e.x = clampf(e.x, 24, LOGICAL_W - 24);
                if (e.hurtFlash <= 0) e.anim = moving ? 'run' : 'idle';
                e.attackTimer -= dt;
                const inRange = adist < (meta.behavior === 'ranged' ? 220 : 72);
                if (e.attackTimer <= 0 && inRange) {
                    e.attackTimer = PROPOSAL.enemyAttackInterval;
                    e.anim = 'atk';
                    e.animTime = 0;
                    this.emit('enemy_attack', { target: e.id, name: e.name, x: e.x });
                    if (this.invuln > 0) {
                        this.emit('dodge_ignore', { target: e.id });
                    } else {
                        // 第 21 轮：玩家承伤系数 / 固定减伤 / 护盾；空效果时等价于原来的 Math.round(atk)
                        const dmg = Math.max(1, Math.round(atk * this.fx.damageTakenScale) - this.fx.flatReduce);
                        let left = dmg;
                        if (this.shield > 0) {
                            const absorbed = Math.min(this.shield, left);
                            this.shield -= absorbed;
                            left -= absorbed;
                            this.emit('shield_absorb', { amount: absorbed, shieldLeft: this.shield });
                        }
                        this.hp = Math.max(0, this.hp - left);
                        this.damageTaken += dmg;
                        this.emit('player_hurt', { damage: left, x: this.x, y: GROUND_Y - 64 });
                        this.emit('edge_tint', {});        // §6 反馈清单：屏幕边缘朱砂晕
                        if (this.fx.spiritOnHurt > 0) {
                            this.spirit = clampf(this.spirit + this.fx.spiritOnHurt, 0, this.maxSpirit);
                            this.emit('card_effect', { kind: 'spirit_on_hurt',
                                text: '截取：受击回灵 +' + this.fx.spiritOnHurt });
                        }
                        if (this.fx.hurtInvuln > 0 && this.hp > 0) {
                            this.invuln = Math.max(this.invuln, this.fx.hurtInvuln);
                            this.emit('card_effect', { kind: 'hurt_invuln',
                                text: '避水：受击后无敌 ' + this.fx.hurtInvuln + ' s' });
                        }
                        if (this.hp <= 0) {
                            if (this.reviveLeft > 0 && this.fx.reviveHp > 0) {
                                this.reviveLeft = 0;
                                this.hp = Math.max(1, Math.round(this.maxHp * this.fx.reviveHp));
                                this.invuln = Math.max(this.invuln, 0.6);
                                this.emit('revive', { hp: this.hp, stage: this.stage });
                                this.emit('card_effect', { kind: 'revive',
                                    text: '舍利 / 转生：首次阵亡以 ' + (this.fx.reviveHp * 100).toFixed(0) + '% HP 复活' });
                            } else {
                                this.state = 'DEAD';
                                this.finished = true;
                                this.win = false;
                                this.emit('run_ended', { win: false, stage: this.stage });
                            }
                        }
                    }
                }
            }
        }

        updateVfx(dt) {
            this.activeVfx = this.activeVfx.filter(v => (v.ttl -= dt) > 0);
        }

        checkEnd() {
            if (this.finished) return;
            if (this.enemies.every(e => e.dead)) {
                this.finished = true;
                this.win = this.stage >= 9;
                this.emit('stage_cleared', {
                    stage: this.stage, kills: this.kills, damage: this.damageDealt,
                    next: this.stage < 9 ? this.stage + 1 : null,
                });
                if (this.stage >= 9) this.emit('run_ended', { win: true, stage: 9 });
            }
        }

        nextStage(deckState) {
            if (this.stage >= 9) return false;
            this.startStage(this.stage + 1, deckState || this.opts.deckState || {});
            return true;
        }

        snapshot() {
            return {
                stage: this.stage, stageType: this.stageDef.type, hpTotal: this.stageDef.hp,
                state: this.state, facing: this.facing, x: Number(this.x.toFixed(2)),
                hp: this.hp, maxHp: this.maxHp, spirit: Number(this.spirit.toFixed(1)),
                maxSpirit: this.maxSpirit, shield: Number(this.shield.toFixed(1)),
                stamina: Number(this.stamina.toFixed(1)), cd: this.cd.map(v => Number(v.toFixed(2))),
                invuln: Number(this.invuln.toFixed(2)), pool: Number(this.pool.toFixed(1)),
                combo: Number(clampf(1.0 + this.comboBonus + this.comboChain, 0, CAP_COMBO).toFixed(3)),
                hits: this.hits, kills: this.kills, lastDamage: this.lastDamage,
                damageDealt: this.damageDealt, damageTaken: this.damageTaken,
                time: Number(this.time.toFixed(2)), tick: this.tickCount,
                finished: this.finished, win: this.win, errors: this.errors.slice(),
                cardEffects: {
                    active: !!this.cardFx,
                    bound: (this.cardFx && this.cardFx.counts && this.cardFx.counts.battle) || 0,
                    segments: this.fx.segmentRatios.length,
                    reviveLeft: this.reviveLeft,
                    freeCastReady: this.freeCastReady,
                    reveal: !!this.fx.reveal,
                },
                enemies: this.enemies.map(e => ({
                    id: e.id, type: e.type, sprite: e.sprite, name: e.name,
                    x: Number(e.x.toFixed(1)), hp: e.hp, maxHp: e.maxHp,
                    anim: e.anim, animTime: Number(e.animTime.toFixed(2)),
                    flash: Number(e.hurtFlash.toFixed(2)), dead: e.dead,
                    boss: e.boss, placeholder: e.placeholder, scale: e.scale, phase: e.phase,
                })),
            };
        }
    }

    const api = {
        BattleSim, STAGES, SKILLS, MOBS, PROPOSAL, damageFormula, maxHit,
        emptyCardMods, fnv1a, xorshift32, clampf,
        CAP_BASE, CAP_REALM_RATIO, CAP_EXTRA_POOL, CAP_COMBO, CAP_CRIT,
        CAP_DEFENSE, BOSS_HP_REFERENCE, LOGICAL_W, LOGICAL_H, GROUND_Y,
        FRAME_SIZE, TICK, DMG_MIN, DMG_MAX,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (global) global.BattleSim = api;
})(typeof window !== 'undefined' ? window : globalThis);
