/*
 * card_rules.js — 层间三选一卡牌规则层「跨端同一实现」
 *
 * 第 19 轮（R47）：把 scripts/CardDeck.gd 的规则逐行移植为 JS，供
 *   ① previews/web-demo.html（浏览器，file:// 直接可用）
 *   ② tools/cross_platform_check.js（Node，与 Godot 黄金样本比对）
 * 共用同一份代码，避免「网页一套、Godot 一套」导致网页验证失去意义。
 *
 * 与 GDScript 的对应点（改动任一处都必须两端同步并重跑黄金样本）：
 *   - FNV-1a 32 位，输入为 UTF-8 字节
 *   - xorshift32（非引擎 PCG32），randf = 高 24 位 / 2^24
 *   - offer() 每次以 run_seed(stage) 重置 RNG，保证 (run_id, stage) 确定性
 *   - 五上界钳制与 clamp_events 事件口径完全一致
 *
 * 规格依据：docs/11 §4/§6、docs/12、docs/buff-card-library.json、docs/15。
 * 边界：权重 / 概率 / 层数曲线均为 PROPOSAL、待实测；本文件只复刻规则，不做平衡结论。
 */
(function (global) {
    'use strict';

    const CAP_BASE = 180.0;
    const CAP_REALM_RATIO = 1.60;
    const CAP_EXTRA_POOL = 600.0;
    const CAP_COMBO = 2.5;
    const CAP_CRIT = 1.8;
    const CAP_DEFENSE = 0.75;
    const BOSS_HP_REFERENCE = 4400.0;
    const DEFAULT_CHOICES = 3;
    const WUXIANG_CHOICES = 2;
    const LAST_DRAW_STAGE = 8;
    const UPPER_KEYS = [
        'base_damage', 'realm_ratio', 'extra_pool',
        'combo_multiplier', 'crit_multiplier', 'defense_rate',
    ];
    const LIMITS = [
        ['base_damage', CAP_BASE],
        ['realm_ratio', CAP_REALM_RATIO],
        ['extra_pool', CAP_EXTRA_POOL],
        ['combo_multiplier', CAP_COMBO],
        ['crit_multiplier', CAP_CRIT],
        ['defense_rate', CAP_DEFENSE],
    ];
    const FNV_OFFSET = 0x811c9dc5;
    const FNV_PRIME = 0x01000193;
    const MASK32 = 0xffffffff;

    function fnv1a(s) {
        let h = FNV_OFFSET >>> 0;
        const bytes = new TextEncoder().encode(s);
        for (let i = 0; i < bytes.length; i++) {
            h = (h ^ bytes[i]) >>> 0;
            h = Math.imul(h, FNV_PRIME) >>> 0;
        }
        return h >>> 0;
    }

    function clampf(v, lo, hi) {
        return Math.min(Math.max(v, lo), hi);
    }

    class CardDeck {
        constructor(lib) {
            this.lib = lib;
            this.cards = (lib && lib.cards) || [];
            this.byId = Object.create(null);
            for (const c of this.cards) this.byId[c.id] = c;
            this.lastError = this.cards.length === 72 ? '' : '卡库不是 72 张';
            this.reset();
        }

        reset() {
            this.picked = Object.create(null);
            this.context = {};
            this.offense = Object.create(null);
            for (const k of UPPER_KEYS) this.offense[k] = 0.0;
            this.poolUsed = 0.0;
            this.clampEvents = [];
            this.violations = [];
            this.sealed = false;
            this.skipped = [];
            this.runId = '';
            this.rngState = 0;
        }

        isLoaded() { return this.cards.length === 72 && this.lastError === ''; }
        cardCount() { return this.cards.length; }

        newRun(runId, context) {
            this.reset();
            this.runId = String(runId);
            this.context = {
                school: 'jian', skills: [], gear: [], affix: [], realm: 1, slots: 3,
            };
            if (context) for (const k of Object.keys(context)) this.context[k] = context[k];
        }

        setContext(key, value) { this.context[key] = value; }
        isSealed() { return this.sealed; }
        pickedCounts() { return Object.assign({}, this.picked); }
        skippedStages() { return this.skipped.slice(); }
        clampEventsCopy() { return this.clampEvents.slice(); }
        violationsCopy() { return this.violations.slice(); }

        offenseState() {
            const out = Object.assign({}, this.offense);
            out.offense_pool_used = this.poolUsed;
            return out;
        }

        // ---- 确定性种子 / xorshift32（与 CardDeck.gd 逐位一致）----
        runSeed(stage) { return fnv1a(this.runId + ':' + String(stage)); }

        rngReset(seed) {
            this.rngState = seed >>> 0;
            if (this.rngState === 0) this.rngState = 0x6d2b79f5;
        }

        rngNext() {
            let x = this.rngState >>> 0;
            x = (x ^ ((x << 13) >>> 0)) >>> 0;
            x = (x ^ (x >>> 17)) >>> 0;
            x = (x ^ ((x << 5) >>> 0)) >>> 0;
            this.rngState = x >>> 0;
            return x >>> 0;
        }

        rngRandf() { return ((this.rngNext() >>> 8) & 0xffffff) / 16777216.0; }

        // ---- 候选池过滤 ----
        reqOk(c, stage) {
            for (const raw of (c.req || [])) {
                const r = String(raw);
                if (r.startsWith('stage>=')) {
                    if (stage < parseInt(r.slice(7), 10)) return false;
                    continue;
                }
                const idx = r.indexOf(':');
                const key = idx < 0 ? r : r.slice(0, idx);
                const val = idx < 0 ? '' : r.slice(idx + 1);
                if (key === 'school') {
                    if (String(this.context.school || '') !== val) return false;
                } else if (key === 'skill') {
                    if (!(this.context.skills || []).includes(val)) return false;
                } else if (key === 'gear') {
                    if (val === 'any') {
                        if ((this.context.gear || []).length === 0) return false;
                    } else if (val === '3slots') {
                        if (Number(this.context.slots || 3) < 3) return false;
                    }
                } else if (key === 'affix') {
                    if (!(this.context.affix || []).includes(val)) return false;
                } else {
                    return false; // 未知前置一律不放行
                }
            }
            return true;
        }

        unlockOk(c) {
            const u = String(c.unlock || 'none');
            if (u === 'none') return true;
            if (u.startsWith('realm:')) {
                return Number(this.context.realm || 1) >= parseInt(u.slice(6), 10);
            }
            return false;
        }

        excluded(cardId) {
            for (const pickedId of Object.keys(this.picked)) {
                if (Number(this.picked[pickedId]) <= 0) continue;
                const pc = this.byId[pickedId];
                if (pc && (pc.excl || []).includes(cardId)) return true;
            }
            const c = this.byId[cardId];
            if (!c) return false;
            for (const other of (c.excl || [])) {
                if (Number(this.picked[other] || 0) > 0) return true;
            }
            return false;
        }

        eligible(stage) {
            const out = [];
            for (const c of this.cards) {
                const cid = c.id;
                if (Number(this.picked[cid] || 0) >= Number(c.stack || 1)) continue;
                if (!this.reqOk(c, stage)) continue;
                if (!this.unlockOk(c)) continue;
                if (this.excluded(cid)) continue;
                out.push(cid);
            }
            return out;
        }

        // ---- 加权抽取 ----
        weight(c, stage) {
            let w = Number(c.weight === undefined ? 10 : c.weight);
            if (c.rarity === 'legend') w *= 1.0 + 0.1 * stage;
            return Math.max(w, 0.0);
        }

        weightedPick(candidates, weights) {
            let total = 0.0;
            for (const w of weights) total += Number(w);
            if (total <= 0.0) return '';
            const r = this.rngRandf() * total;
            let acc = 0.0;
            for (let i = 0; i < candidates.length; i++) {
                acc += Number(weights[i]);
                if (r <= acc) return String(candidates[i]);
            }
            return String(candidates[candidates.length - 1]);
        }

        choiceCount() {
            if (Number(this.picked['card_wuxiangpo'] || 0) > 0) return DEFAULT_CHOICES;
            if ((this.context.affix || []).includes('affix_wuxiang')) return WUXIANG_CHOICES;
            return DEFAULT_CHOICES;
        }

        offer(stage) {
            if (this.sealed || stage > LAST_DRAW_STAGE || stage < 1) return [];
            const pool = this.eligible(stage);
            this.rngReset(this.runSeed(stage));
            const usedCat = new Set();
            const offered = [];
            for (let n = 0; n < this.choiceCount(); n++) {
                const candidates = [];
                const weights = [];
                for (const cid of pool) {
                    const c = this.byId[cid];
                    if (usedCat.has(c.cat) || offered.includes(cid)) continue;
                    candidates.push(cid);
                    weights.push(this.weight(c, stage));
                }
                if (candidates.length === 0) break;
                const chosen = this.weightedPick(candidates, weights);
                if (chosen === '') break;
                offered.push(chosen);
                usedCat.add(this.byId[chosen].cat);
            }
            return offered;
        }

        pick(cardId, stage) {
            if (this.sealed || !this.byId[cardId]) return false;
            if (!this.offer(stage).includes(cardId)) return false;
            this.picked[cardId] = Number(this.picked[cardId] || 0) + 1;
            this.applyParams(cardId);
            const p = this.byId[cardId].params || {};
            if (p.stop_draw === true) this.sealed = true;
            if (p.skip_draw === true) this.skipped.push(stage);
            return true;
        }

        skipDraw(stage) {
            if (Number(this.picked['card_shouzhuo'] || 0) <= 0 || this.skipped.includes(stage)) return false;
            this.skipped.push(stage);
            return true;
        }

        // ---- 五上界守卫（DF-21 / R32）----
        applyParams(cardId) {
            const c = this.byId[cardId];
            if (!c) return { ok: false };
            const p = c.params || {};
            const touchesUpper = UPPER_KEYS.some((k) => Object.prototype.hasOwnProperty.call(p, k));
            if (touchesUpper && !(Object.prototype.hasOwnProperty.call(p, 'pool') ||
                                  Object.prototype.hasOwnProperty.call(p, 'cap'))) {
                this.violations.push({ card: cardId, why: '触碰上界变量但未声明 pool/cap（R32 机器规则）' });
            }
            if (p.pool === 'offense_pool') {
                this.poolUsed += Number(p.base_damage || 0);
            }
            for (const key of UPPER_KEYS) {
                if (!Object.prototype.hasOwnProperty.call(p, key)) continue;
                if (key === 'base_damage' && p.pool === 'offense_pool') continue;
                this.offense[key] = Number(this.offense[key] || 0) + Number(p[key]);
            }
            this.clampOffense();
            return { ok: true, offense: this.offenseState(), peak: this.peakDamage() };
        }

        clampOffense() {
            for (const [key, limit] of LIMITS) {
                const before = Number(this.offense[key] || 0);
                const after = clampf(before, 0.0, limit);
                this.offense[key] = after;
                if (Math.abs(after - before) > 0.000001) {
                    this.clampEvents.push({ var: key, before, after, kind: 'numeric_clamp' });
                } else if (before > 0.000001 && key !== 'defense_rate') {
                    this.clampEvents.push({ var: key, delta: before, kind: 'upper_bound_guard' });
                }
            }
            const poolBefore = this.poolUsed;
            this.poolUsed = clampf(poolBefore, 0.0, CAP_EXTRA_POOL);
            if (Math.abs(this.poolUsed - poolBefore) > 0.000001) {
                this.clampEvents.push({ var: 'offense_pool', before: poolBefore, after: this.poolUsed });
            }
        }

        peakDamage() {
            const base = clampf(CAP_BASE + Number(this.offense.base_damage || 0), 0.0, CAP_BASE);
            const realm = clampf(CAP_REALM_RATIO + Number(this.offense.realm_ratio || 0), 0.0, CAP_REALM_RATIO);
            const pool = clampf(CAP_EXTRA_POOL + Number(this.offense.extra_pool || 0) + this.poolUsed,
                                0.0, CAP_EXTRA_POOL);
            const combo = clampf(CAP_COMBO + Number(this.offense.combo_multiplier || 0), 0.0, CAP_COMBO);
            const crit = clampf(CAP_CRIT + Number(this.offense.crit_multiplier || 0), 0.0, CAP_CRIT);
            // 最坏口径：目标不减伤（玩家 defense_rate 属生存维度，不进攻击峰值）
            return Math.round((base * realm + pool) * combo * crit);
        }

        damageCeilingOk() {
            return this.peakDamage() < BOSS_HP_REFERENCE && this.violations.length === 0;
        }

        pickEvent(stage, offered, picked) {
            const c = this.byId[picked] || {};
            return {
                stage,
                offered: offered.slice(),
                picked,
                card_id: picked,
                card_rarity: String(c.rarity || ''),
                card_category: String(c.cat || ''),
                seen_before: Number(this.picked[picked] || 0) > 1,
                run_id: this.runId,
                seed: this.runSeed(stage),
            };
        }
    }

    const api = {
        CardDeck, fnv1a, CAP_BASE, CAP_REALM_RATIO, CAP_EXTRA_POOL,
        CAP_COMBO, CAP_CRIT, CAP_DEFENSE, BOSS_HP_REFERENCE,
        DEFAULT_CHOICES, WUXIANG_CHOICES, LAST_DRAW_STAGE, UPPER_KEYS,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (global) global.CardRules = api;
})(typeof window !== 'undefined' ? window : globalThis);
