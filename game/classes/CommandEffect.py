# -*- coding: utf-8 -*-
"""卡牌效果语言 · 使用手册

========================= 一、文件分工 =========================

    CommandEffect.py   语言与解释器（不含任何具体游戏规则）
    CardsPort.py       桥接层（唯一需要对接你的 Game / Unit 的文件）（废弃）
    Cards.py           卡牌数据（只写“是什么”，不写 if/for）
    game.py            游戏流程（只负责在正确时机派发事件）

========================= 二、三根支柱 =========================

    Effect   = Trigger + Lifespan + Condition + Actions
    Trigger  : 监听哪个事件（EventType）、事件归属哪方（Side）
    Lifespan : 这条效果什么时候存在
                PENDING --(回合边界)--> ACTIVE --(回合边界/触发)--> EXPIRED
    Selection: 目标选择器，所有 Side 都是相对“效果拥有者”而言

解释器只做四件事：
    1. 收到 GameEvent
    2. 找出所有 ACTIVE 且 Trigger 匹配的效果
    3. 用 Selection 把目标解析成实体列表
    4. 执行 Actions，具体改状态的动作全部委托给 GamePort

========================= 三、写一张卡 =========================

    UnitCard(
        4, 4, [Tag(Keyword.Guard)], 3, 1,
        '新兵', 'N', UnitType.infantry, A,
        '守护。部署：抽 1 张牌',
        effects_=(
            Effect(
                trigger=Trigger(EventType.SELF_DEPLOYED),
                lifespan=Lifespan.Once(),
                actions=(DrawCards(Side.FRIENDLY, 1),),
            ),
        ),
    )

三个问题决定整张卡：
    ┌ 什么时候？  Trigger(EventType.XXX, side=...)
    ├ 存在多久？  Lifespan(...)
    └ 做什么？    actions=(Action, ...)

========================= 四、常用速查 =========================

触发器
    SELF_DEPLOYED                     自身部署 / 指令打出
    UNIT_DESTROYED + Self()           亡计
    UNIT_DAMAGED  + Self()            受伤时
    TURN_STARTED / TURN_ENDED         回合开始 / 结束
    CARD_DRAWN / UNIT_DEPLOYED / ...  任意事件

时序
    Lifespan()                        永久（单位被动）
    Lifespan.Once()                   立即执行一次（部署、指令）
    Lifespan.DuringNextEnemyTurn()    下个敌方回合中
    Lifespan.DuringNextOwnerTurn()    下个己方回合中
    Lifespan(START, EndPoint.XXX)     自定义窗口

选择器
    Selection.Self()                  效果宿主自身
    Selection.Subject()               事件主体 / ForEach 当前项
    Selection.Units(Side.ENEMY)       敌方所有单位
    Selection.HQ(Side.FRIENDLY)       友方总部
    Selection(owner=..., unitType=..., keywordsAll=..., maxCost=...)
    pick=Pick.ALL / FIRST / LAST / RANDOM / CHOSEN

动作
    DealDamage / Heal / Destroy / Buff / DrawCards / DiscardCards
    GrantKeyword / RevokeKeyword / Summon / AddKredits
    Seq(a, b)               顺序
    Branch(cond, a, b)      条件分支
    ForEach(sel, body)      对每个目标执行，body 内用 Selection.Subject()
    PlayEffect(effect)      动态挂载新效果（嵌套时序）
    CustomAction(op, sel, args)   走 GamePort.CustomAction 的逃生口

条件
    CondCompare(值, CompareOp.GT, 值)   Value 可以是 int / CountValue / StatValue
    CondExists(sel) / CondHasKeyword(sel, 词条)
    AllOf(...) / AnyOf(...) / NotCond(...)

========================= 五、事件派发点 =========================

解释器只认你发的事件，game.py 里已经接好：
    部署        Deploy()      SELF_DEPLOYED（AttachCard 内）+ UNIT_DEPLOYED
    阵亡        Check()       UNIT_DESTROYED，随后 DetachHost
    回合开始    TurnStart()   TURN_STARTED
    回合结束    TurnEnd()     TURN_ENDED
    使用指令    UseCommand()  SELF_DEPLOYED
    效果伤害    CardsPort     UNIT_DAMAGED / HQ_DAMAGED
    效果抽牌    CardsPort     CARD_DRAWN

还没接的（写了对应效果再补）：
    Attack() 里没有派发 UNIT_ATTACKED；
    攻击仍是直接 t.dfns -= dmg，不经过 Port，所以不会触发“受伤时”。

========================= 六、两种被动 =========================

数值型（改伤害/攻击力）→ 继续用 PassiveTag + ClacDamage/ClacAtk
   必须在结算点同步生效，不要改成事件，否则会晚一个结算点。

事件型（“每当 X 时 Y”）→ 写 Effect(..., lifespan=Lifespan())
   挂到单位效果列表里，随部署挂载、随阵亡 Detach。

========================= 七、扩展点 =========================

新操作   → 在文件末尾加 OP_XXX，在 CardsPort.CustomAction 加分支
新动作   → 继承 Action 实现 Exec
新条件   → 继承 Condition 实现 Test
新触发器 → 在 EventType 加成员，并在 game.py 对应位置 HandleEvent
"""


from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Final, Protocol, TypeAlias


PlayerId: TypeAlias = "str"
EntityId: TypeAlias = "str"


# ============================================================
# 1. 基础枚举
# ============================================================

class Side(Enum):
    FRIENDLY = "友方"
    ENEMY = "敌方"
    ANY = "任意"


class Zone(Enum):
    BOARD = "战场"
    HAND = "手牌"
    DECK = "卡组"
    GRAVEYARD = "墓地"
    HQ = "总部"
    ANY = "任意"


class CardType(Enum):
    UNIT = "单位"
    ORDER = "指令"
    COUNTERMEASURE = "反制"
    ATTACHMENT = "附件"
    HQ = "总部"          # 新增：总部也是一种实体类型


class UnitType(Enum):
    NONE = "无"
    INFANTRY = "步兵"
    TANK = "坦克"
    ARTILLERY = "火炮"
    FIGHTER = "战斗机"
    BOMBER = "轰炸机"
    STARSHIP = "星舰"


class Pick(Enum):
    ALL = "全部"
    FIRST = "第一个"
    LAST = "最后一个"
    RANDOM = "随机"
    CHOSEN = "指定"


class Anchor(Enum):
    SEARCH = "搜索"
    SELF = "自身"
    SUBJECT = "当前目标"


class CompareOp(Enum):
    EQ = "等于"
    NE = "不等于"
    LT = "小于"
    LE = "不大于"
    GT = "大于"
    GE = "不小于"


class StatKind(Enum):
    ATTACK = "攻击"
    HEALTH = "生命"
    COST = "费用"
    ARMOR = "护甲"
    ACTION_COST = "行动花费"     # 新增
    FRONTLINE = "阵线"           # 新增
    TIMELINE = "时间线"          # 新增


class ArithOp(Enum):
    ADD = "加"
    SUB = "减"
    MUL = "乘"
    MAX = "取大"
    MIN = "取小"


class EventType(Enum):
    TURN_STARTED = "回合开始"
    TURN_ENDED = "回合结束"
    UNIT_DEPLOYED = "单位部署"
    UNIT_DESTROYED = "单位阵亡"
    UNIT_ATTACKED = "单位攻击"
    UNIT_DAMAGED = "单位受伤"
    UNIT_HEALED = "单位治疗"
    ATTACK_DECLARED = "宣告攻击"
    CARD_DRAWN = "抽牌"
    CARD_DISCARDED = "弃牌"
    CARD_PLAYED = "使用卡牌"
    ORDER_PLAYED = "使用指令"
    HQ_DAMAGED = "总部受伤"
    KREDIT_GAINED = "获得行动点"
    KEYWORD_GAINED = "获得词条"
    EVENT_CHANGED = "事件变更"
    SELF_DEPLOYED = "自身部署"


class StartPoint(Enum):
    NOW = "立即"
    OWNER_TURN_START = "己方回合开始"
    ENEMY_TURN_START = "敌方回合开始"


class EndPoint(Enum):
    NEVER = "永不"
    AFTER_TRIGGER = "触发后"
    ACTIVE_TURN_END = "激活回合结束"
    OWNER_TURN_START = "己方回合开始"
    ENEMY_TURN_START = "敌方回合开始"
    OWNER_TURN_END = "己方回合结束"
    ENEMY_TURN_END = "敌方回合结束"


class MountState(Enum):
    PENDING = "待激活"
    ACTIVE = "生效中"
    EXPIRED = "已失效"



# 常用词条（纯字符串标记，具体规则由你的战斗系统解释）
KEYWORD_BLITZ: Final[str] = "Blitz"
KEYWORD_GUARD: Final[str] = "Guard"
KEYWORD_AMBUSH: Final[str] = "Ambush"
KEYWORD_SMOKESCREEN: Final[str] = "Smokescreen"
KEYWORD_FURY: Final[str] = "Fury"
KEYWORD_PINCER: Final[str] = "Pincer"
KEYWORD_ARMOR: Final[str] = "Armor"
KEYWORD_MOBILIZE: Final[str] = "Mobilize"
KEYWORD_INTEL: Final[str] = "Intel"
KEYWORD_ALPINE: Final[str] = "Alpine"


# ============================================================
# 2. 运行上下文
# ============================================================

@dataclass(frozen=True)
class GameEvent:
    """一条游戏事件。actor 是事件发起者，subject 是事件主体实体。"""
    kind: EventType
    actor: PlayerId | None = None
    subject: EntityId | None = None
    data: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class EvalContext:
    """求值上下文：谁的效果、宿主是谁、在响应什么事件。"""
    interp: "Interpreter" = field(compare=False, repr=False)
    owner: PlayerId
    selfCard: EntityId | None = None
    event: GameEvent | None = None
    subject: EntityId | None = None
    effect: "Effect | None" = None


# ============================================================
# 3. 目标选择器
# ============================================================

@dataclass(frozen=True)
class Selection:
    owner: Side = Side.ANY
    zone: Zone = Zone.BOARD
    anchor: Anchor = Anchor.SEARCH
    cardType: CardType | None = None
    unitType: UnitType | None = None
    keywordsAll: tuple[str, ...] = ()
    keywordsNone: tuple[str, ...] = ()
    maxCost: int | None = None
    minAttack: int | None = None
    maxActionCost: int | None = None      # 新增
    minHealth: int | None = None          # 新增
    maxHealth: int | None = None          # 新增
    frontline: int | None = None          # 新增：0 A后方 / 1 前线 / 2 B后
    timeline: int | None = None           # 新增：0/1/2 时间线
    includeDead: bool = False
    pick: Pick = Pick.ALL
    count: int = 1

    @staticmethod
    def Self() -> "Selection":
        return Selection(anchor=Anchor.SELF, zone=Zone.ANY)

    @staticmethod
    def Subject() -> "Selection":
        return Selection(anchor=Anchor.SUBJECT, zone=Zone.ANY)

    @staticmethod
    def Units(side: Side = Side.ANY, unitType: UnitType | None = None) -> "Selection":
        return Selection(owner=side, zone=Zone.BOARD, unitType=unitType)

    @staticmethod
    def Hand(side: Side) -> "Selection":
        return Selection(owner=side, zone=Zone.HAND)

    @staticmethod
    def HQ(side: Side) -> "Selection":
        return Selection(owner=side, zone=Zone.HQ)



# ============================================================
# 4. 数值表达式
# ============================================================

@dataclass(frozen=True)
class StatValue:
    """取选中目标的某项属性。若解析出多个，取第一个。"""
    selection: Selection
    stat: StatKind


@dataclass(frozen=True)
class CountValue:
    """选中目标的数量。"""
    selection: Selection


@dataclass(frozen=True)
class EventValue:
    """从当前事件 payload 里取整数值。"""
    key: str


@dataclass(frozen=True)
class ArithValue:
    op: ArithOp
    left: "Value"
    right: "Value"


Value: TypeAlias = "int | StatValue | CountValue | EventValue | ArithValue"


def EvalValue(value: Value, ctx: EvalContext) -> int:
    """求值一个数值表达式。"""
    if isinstance(value, int):
        return value
    if isinstance(value, StatValue):
        targets = ctx.interp.Resolve(value.selection, ctx)
        if not targets:
            return 0
        return ctx.interp.port.GetStat(targets[0], value.stat)
    if isinstance(value, CountValue):
        return len(ctx.interp.Resolve(value.selection, ctx))
    if isinstance(value, EventValue):
        if ctx.event is None:
            return 0
        return ctx.event.data.get(value.key, 0)
    if isinstance(value, ArithValue): # type: ignore
        left = EvalValue(value.left, ctx)
        right = EvalValue(value.right, ctx)
        if value.op is ArithOp.ADD:
            return left + right
        if value.op is ArithOp.SUB:
            return left - right
        if value.op is ArithOp.MUL:
            return left * right
        if value.op is ArithOp.MAX:
            return max(left, right)
        return min(left, right)
    raise TypeError(f"未知的 Value 节点: {type(value)!r}")


def Num(n: int) -> Value:
    return n


# ============================================================
# 5. 条件
# ============================================================

class Condition(ABC):
    """条件节点基类。继承它并实现 Test 即可扩充新条件。"""

    @abstractmethod
    def Test(self, ctx: EvalContext) -> bool:
        """返回条件是否成立。"""


@dataclass(frozen=True)
class CondAll(Condition):
    items: tuple[Condition, ...]

    def Test(self, ctx: EvalContext) -> bool:
        return all(item.Test(ctx) for item in self.items)


@dataclass(frozen=True)
class CondAny(Condition):
    items: tuple[Condition, ...]

    def Test(self, ctx: EvalContext) -> bool:
        return any(item.Test(ctx) for item in self.items)


@dataclass(frozen=True)
class CondNot(Condition):
    item: Condition

    def Test(self, ctx: EvalContext) -> bool:
        return not self.item.Test(ctx)


@dataclass(frozen=True)
class CondCompare(Condition):
    left: "Value"
    op: CompareOp
    right: "Value"
    _OPS: Any = field(default=None, compare=False, repr=False)

    def Test(self, ctx: EvalContext) -> bool:
        left = EvalValue(self.left, ctx)
        right = EvalValue(self.right, ctx)
        if self.op is CompareOp.EQ:
            return left == right
        if self.op is CompareOp.NE:
            return left != right
        if self.op is CompareOp.LT:
            return left < right
        if self.op is CompareOp.LE:
            return left <= right
        if self.op is CompareOp.GT:
            return left > right
        return left >= right


@dataclass(frozen=True)
class CondExists(Condition):
    """选中的目标是否非空（至少一个）。"""
    selection: Selection

    def Test(self, ctx: EvalContext) -> bool:
        return len(ctx.interp.Resolve(self.selection, ctx)) > 0


@dataclass(frozen=True)
class CondHasKeyword(Condition):
    """选中目标是否全部（或任一）拥有某关键词。"""
    selection: Selection
    keyword: str
    requireAll: bool = False

    def Test(self, ctx: EvalContext) -> bool:
        targets = ctx.interp.Resolve(self.selection, ctx)
        if not targets:
            return False
        checks = [self.keyword in ctx.interp.port.GetKeywords(t) for t in targets]
        return all(checks) if self.requireAll else any(checks)


def AllOf(*items: Condition) -> Condition:
    return CondAll(items)


def AnyOf(*items: Condition) -> Condition:
    return CondAny(items)


def NotCond(item: Condition) -> Condition:
    return CondNot(item)


# ============================================================
# 6. 动作
# ============================================================

class Action(ABC):
    """动作节点基类。继承它并实现 Exec 即可扩充新动作。"""

    @abstractmethod
    def Exec(self, ctx: EvalContext) -> None:
        """执行该动作。"""


@dataclass(frozen=True)
class SeqAction(Action):
    items: tuple[Action, ...]

    def Exec(self, ctx: EvalContext) -> None:
        for item in self.items:
            item.Exec(ctx)


@dataclass(frozen=True)
class BranchAction(Action):
    condition: Condition
    thenAction: Action
    elseAction: Action | None = None

    def Exec(self, ctx: EvalContext) -> None:
        if self.condition.Test(ctx):
            self.thenAction.Exec(ctx)
        elif self.elseAction is not None:
            self.elseAction.Exec(ctx)


@dataclass(frozen=True)
class ForEachAction(Action):
    """对选中目标逐个执行 body，body 内用 Selection.Subject() 引用当前项。"""
    selection: Selection
    body: Action

    def Exec(self, ctx: EvalContext) -> None:
        for entity in ctx.interp.Resolve(self.selection, ctx):
            self.body.Exec(replace(ctx, subject=entity))


@dataclass(frozen=True)
class DamageAction(Action):
    selection: Selection
    amount: "Value"

    def Exec(self, ctx: EvalContext) -> None:
        amount = EvalValue(self.amount, ctx)
        for target in ctx.interp.Resolve(self.selection, ctx):
            ctx.interp.port.DealDamage(ctx.selfCard, target, amount, ctx)


@dataclass(frozen=True)
class HealAction(Action):
    selection: Selection
    amount: "Value"

    def Exec(self, ctx: EvalContext) -> None:
        amount = EvalValue(self.amount, ctx)
        for target in ctx.interp.Resolve(self.selection, ctx):
            ctx.interp.port.Heal(target, amount, ctx)


@dataclass(frozen=True)
class DestroyAction(Action):
    selection: Selection

    def Exec(self, ctx: EvalContext) -> None:
        for target in ctx.interp.Resolve(self.selection, ctx):
            ctx.interp.port.Destroy(target, ctx)


@dataclass(frozen=True)
class DrawAction(Action):
    player: Side
    amount: "Value" = 1

    def Exec(self, ctx: EvalContext) -> None:
        who = ctx.interp.PlayerFor(self.player, ctx.owner)
        ctx.interp.port.DrawCards(who, EvalValue(self.amount, ctx), ctx)


@dataclass(frozen=True)
class DiscardAction(Action):
    selection: Selection

    def Exec(self, ctx: EvalContext) -> None:
        for target in ctx.interp.Resolve(self.selection, ctx):
            ctx.interp.port.Discard(target, ctx)


@dataclass(frozen=True)
class ModifyStatsAction(Action):
    selection: Selection
    attack: "Value" = 0
    health: "Value" = 0

    def Exec(self, ctx: EvalContext) -> None:
        atk = EvalValue(self.attack, ctx)
        hp = EvalValue(self.health, ctx)
        for target in ctx.interp.Resolve(self.selection, ctx):
            ctx.interp.port.ModifyStats(target, atk, hp, ctx)


@dataclass(frozen=True)
class KeywordAction(Action):
    selection: Selection
    keyword: str
    remove: bool = False

    def Exec(self, ctx: EvalContext) -> None:
        for target in ctx.interp.Resolve(self.selection, ctx):
            if self.remove:
                ctx.interp.port.RevokeKeyword(target, self.keyword, ctx)
            else:
                ctx.interp.port.GrantKeyword(target, self.keyword, ctx)


@dataclass(frozen=True)
class SummonAction(Action):
    player: Side
    cardId: str
    count: "Value" = 1

    def Exec(self, ctx: EvalContext) -> None:
        who = ctx.interp.PlayerFor(self.player, ctx.owner)
        for _ in range(EvalValue(self.count, ctx)):
            ctx.interp.port.Summon(who, self.cardId, ctx)


@dataclass(frozen=True)
class KreditAction(Action):
    player: Side
    amount: "Value"

    def Exec(self, ctx: EvalContext) -> None:
        who = ctx.interp.PlayerFor(self.player, ctx.owner)
        ctx.interp.port.AddKredits(who, EvalValue(self.amount, ctx), ctx)


@dataclass(frozen=True)
class PlayEffectAction(Action):
    effect: "Effect"

    def Exec(self, ctx: EvalContext) -> None:
        host = ctx.subject if ctx.subject is not None else ctx.selfCard
        ctx.interp.Attach(self.effect, ctx.owner, host)


@dataclass(frozen=True)
class CustomAction(Action):
    """逃生口：交给 GamePort.CustomAction 处理。"""
    op: str
    selection: Selection | None = None
    args: dict[str, int | str] = field(default_factory=dict)

    def Exec(self, ctx: EvalContext) -> None:
        if self.selection is None:
            ctx.interp.port.CustomAction(self.op, self.args, ctx, None)
            return
        for target in ctx.interp.Resolve(self.selection, ctx):
            ctx.interp.port.CustomAction(self.op, self.args, ctx, target)


# ---- 顺手可读的工厂函数 ----

def Seq(*items: Action) -> Action:
    return SeqAction(items)


def Branch(condition: Condition, thenAction: Action, elseAction: Action | None = None) -> Action:
    return BranchAction(condition, thenAction, elseAction)


def ForEach(selection: Selection, body: Action) -> Action:
    return ForEachAction(selection, body)


def DealDamage(selection: Selection, amount: "Value") -> Action:
    return DamageAction(selection, amount)


def Heal(selection: Selection, amount: "Value") -> Action:
    return HealAction(selection, amount)


def Destroy(selection: Selection) -> Action:
    return DestroyAction(selection)


def DrawCards(player: Side, amount: "Value" = 1) -> Action:
    return DrawAction(player, amount)


def DiscardCards(selection: Selection) -> Action:
    return DiscardAction(selection)


def Buff(selection: Selection, attack: "Value" = 0, health: "Value" = 0) -> Action:
    return ModifyStatsAction(selection, attack, health)


def GrantKeyword(selection: Selection, keyword: str) -> Action:
    return KeywordAction(selection, keyword, remove=False)


def RevokeKeyword(selection: Selection, keyword: str) -> Action:
    return KeywordAction(selection, keyword, remove=True)


def Summon(player: Side, cardId: str, count: "Value" = 1) -> Action:
    return SummonAction(player, cardId, count)


def AddKredits(player: Side, amount: "Value") -> Action:
    return KreditAction(player, amount)


def PlayEffect(effect: "Effect") -> Action:
    return PlayEffectAction(effect)


# ============================================================
# 7. 触发器 / 生命周期 / 效果
# ============================================================

@dataclass(frozen=True)
class Trigger:
    """监听什么事件。

    on             : 事件类型
    side           : 事件发起者相对“效果拥有者”的阵营（ANY 表示不检查）
    subjectMatches : 事件主体必须落在该选择器解析结果中
    oncePerTurn    : 同一回合只触发一次
    """
    on: EventType
    side: Side = Side.ANY
    subjectMatches: Selection | None = None
    oncePerTurn: bool = False


@dataclass(frozen=True)
class Lifespan:
    """效果的时间窗口，实现“下个敌方回合中……”“下个友方回合开始时……”等。

    常用组合：
      - 永久能力          : Lifespan()
      - 部署效果          : Lifespan.Once()
      - 下个敌方回合期间  : Lifespan(ENEMY_TURN_START, ACTIVE_TURN_END)
      - 下个友方回合开始  : Lifespan(OWNER_TURN_START, AFTER_TRIGGER)
      - 持续到己方下回合  : Lifespan(NOW, OWNER_TURN_START)
    """
    start: StartPoint = StartPoint.NOW
    end: EndPoint = EndPoint.NEVER

    @staticmethod
    def Once() -> "Lifespan":
        """立即生效，触发一次后消失（部署效果用）。"""
        return Lifespan(StartPoint.NOW, EndPoint.AFTER_TRIGGER)

    @staticmethod
    def DuringNextEnemyTurn() -> "Lifespan":
        return Lifespan(StartPoint.ENEMY_TURN_START, EndPoint.ACTIVE_TURN_END)

    @staticmethod
    def DuringNextOwnerTurn() -> "Lifespan":
        return Lifespan(StartPoint.OWNER_TURN_START, EndPoint.ACTIVE_TURN_END)


@dataclass(frozen=True)
class Effect:
    """一条完整效果：在某窗口内，当事件发生时，若条件成立则执行动作序列。"""
    trigger: Trigger
    actions: tuple[Action, ...]
    condition: Condition | None = None
    lifespan: Lifespan = field(default_factory=Lifespan)
    name: str = ""


class CardLike(Protocol):
    """任何“带效果列表的卡牌定义”。

    UnitCard / CommandCard 都满足；场上的 Unit 实例不满足，因此
    AttachCard 的第一个参数永远是卡牌定义，第二个参数才是场上实体。
    """
    effects: tuple[Effect, ...]



# ============================================================
# 8. GamePort —— 你需要实现的“空函数”
# ============================================================

class GamePort(ABC):
    """游戏世界接口。所有方法体都留给你实现。

    查询类方法应返回解释器所需的最小信息；操作类方法负责真正改变游戏状态。
    若你希望操作产生的连锁（例如死亡触发）也走解释器，可以在操作实现里
    回调 interpreter.HandleEvent(...)。
    """

    # ---------- 查询 ----------

    @abstractmethod
    def GetHQ(self, player: PlayerId) -> EntityId: ...

    @abstractmethod
    def ListEntities(self, player: PlayerId, zone: Zone) -> Sequence[EntityId]: ...

    @abstractmethod
    def GetStat(self, entity: EntityId, stat: StatKind) -> int: ...

    @abstractmethod
    def GetKeywords(self, entity: EntityId) -> frozenset[str]: ...

    @abstractmethod
    def GetCardType(self, entity: EntityId) -> CardType: ...

    @abstractmethod
    def GetUnitType(self, entity: EntityId) -> UnitType: ...

    @abstractmethod
    def IsAlive(self, entity: EntityId) -> bool: ...

    @abstractmethod
    def OpponentOf(self, player: PlayerId) -> PlayerId: ...

    @abstractmethod
    def Choose(self, candidates: Sequence[EntityId], ctx: EvalContext) -> EntityId | None: ...

    # ---------- 操作 ----------

    @abstractmethod
    def DealDamage(self, source: EntityId | None, target: EntityId, amount: int, ctx: EvalContext) -> None: ...

    @abstractmethod
    def Heal(self, target: EntityId, amount: int, ctx: EvalContext) -> None: ...

    @abstractmethod
    def Destroy(self, target: EntityId, ctx: EvalContext) -> None: ...

    @abstractmethod
    def DrawCards(self, player: PlayerId, amount: int, ctx: EvalContext) -> None: ...

    @abstractmethod
    def Discard(self, entity: EntityId, ctx: EvalContext) -> None: ...

    @abstractmethod
    def ModifyStats(self, entity: EntityId, attack: int, health: int, ctx: EvalContext) -> None: ...

    @abstractmethod
    def GrantKeyword(self, entity: EntityId, keyword: str, ctx: EvalContext) -> None: ...

    @abstractmethod
    def RevokeKeyword(self, entity: EntityId, keyword: str, ctx: EvalContext) -> None: ...

    @abstractmethod
    def Summon(self, player: PlayerId, cardId: str, ctx: EvalContext) -> None: ...

    @abstractmethod
    def AddKredits(self, player: PlayerId, amount: int, ctx: EvalContext) -> None: ...

    @abstractmethod
    def CustomAction(self, op: str, args: Mapping[str, int | str],
                    ctx: EvalContext, target: EntityId | None) -> None: ...

# ============================================================
# 9. 解释器
# ============================================================

MAX_EVENT_DEPTH: Final[int] = 32


@dataclass
class MountedEffect:
    """挂在解释器上的效果实例（携带状态）。"""
    effect: Effect
    owner: PlayerId
    selfCard: EntityId | None
    state: MountState = MountState.PENDING
    mountedTurn: int = 0
    activatedTurn: int = -1
    lastFiredTurn: int = -1


class Interpreter:
    """效果解释器：事件分发 + 生命周期状态机 + 目标解析 + 执行。"""

    def __init__(self, port: GamePort, rng: random.Random | None = None) -> None:
        self.port = port
        self.rng = rng if rng is not None else random.Random()
        self.mounted: list[MountedEffect] = []
        self.turnNumber: int = 0
        self.activePlayer: PlayerId | None = None
        self.eventDepth: int = 0

    # ---------- 挂载 ----------

    def Attach(self, effect: Effect, owner: PlayerId, selfCard: EntityId | None = None) -> MountedEffect:
        """把一条效果挂到解释器上。start=NOW 的直接激活，其余等待回合边界。"""
        mounted = MountedEffect(
            effect=effect,
            owner=owner,
            selfCard=selfCard,
            mountedTurn=self.turnNumber,
        )
        if effect.lifespan.start is StartPoint.NOW:
            mounted.state = MountState.ACTIVE
            mounted.activatedTurn = self.turnNumber
        self.mounted.append(mounted)
        return mounted

    def AttachCard(self, card: CardLike, owner: PlayerId,
                  entity: EntityId | None = None) -> None:
      """部署/打出卡牌：挂上它所有效果，并派发 SELF_DEPLOYED 事件。"""
      for effect in card.effects:
          self.Attach(effect, owner, entity)
      hasDeploy = any(e.trigger.on is EventType.SELF_DEPLOYED for e in card.effects)
      if hasDeploy:
          self.HandleEvent(GameEvent(EventType.SELF_DEPLOYED, actor=owner, subject=entity))


    # ---------- 事件入口 ----------

    def HandleEvent(self, event: GameEvent) -> None:
        """所有游戏事件都从这里进入。"""
        if self.eventDepth >= MAX_EVENT_DEPTH:
            return
        self.eventDepth += 1
        try:
            self.ProcessBoundaries(event)
            for mounted in tuple(self.mounted):
                if mounted.state is not MountState.ACTIVE:
                    continue
                if not self.MatchesTrigger(mounted, event):
                    continue
                ctx = EvalContext(
                    interp=self,
                    owner=mounted.owner,
                    selfCard=mounted.selfCard,
                    event=event,
                    subject=event.subject,
                    effect=mounted.effect,
                )
                if mounted.effect.condition is not None and not mounted.effect.condition.Test(ctx):
                    continue
                mounted.lastFiredTurn = self.turnNumber
                for action in mounted.effect.actions:
                    action.Exec(ctx)
                if mounted.effect.lifespan.end is EndPoint.AFTER_TRIGGER:
                    mounted.state = MountState.EXPIRED
            self.mounted = [m for m in self.mounted if m.state is not MountState.EXPIRED]
        finally:
            self.eventDepth -= 1

    # ---------- 生命周期 ----------

    def ProcessBoundaries(self, event: GameEvent) -> None:
        if event.kind is EventType.TURN_STARTED:
            self.turnNumber += 1
            self.activePlayer = event.actor
            # 先激活（保证本回合可监听），再过期（避免刚激活就被清掉）
            for mounted in self.mounted:
                if mounted.state is MountState.PENDING and self.StartReached(mounted, event):
                    mounted.state = MountState.ACTIVE
                    mounted.activatedTurn = self.turnNumber
            for mounted in self.mounted:
                if mounted.state is MountState.ACTIVE and self.EndReached(mounted, event):
                    mounted.state = MountState.EXPIRED
        elif event.kind is EventType.TURN_ENDED:
            for mounted in self.mounted:
                if mounted.state is MountState.ACTIVE and self.EndReached(mounted, event):
                    mounted.state = MountState.EXPIRED

    def StartReached(self, mounted: MountedEffect, event: GameEvent) -> bool:
        start = mounted.effect.lifespan.start
        if start is StartPoint.NOW:
            return True
        if event.kind is not EventType.TURN_STARTED:
            return False
        if self.turnNumber <= mounted.mountedTurn:
            return False
        return self.MatchTurnPoint(start.name, mounted, event.actor)

    def EndReached(self, mounted: MountedEffect, event: GameEvent) -> bool:
        end = mounted.effect.lifespan.end
        if end is EndPoint.NEVER or end is EndPoint.AFTER_TRIGGER:
            return False
        if end is EndPoint.ACTIVE_TURN_END:
            return event.kind is EventType.TURN_ENDED and self.turnNumber == mounted.activatedTurn
        if event.kind is EventType.TURN_STARTED:
            if self.turnNumber <= mounted.mountedTurn:
                return False
            return self.MatchTurnPoint(end.name, mounted, event.actor)
        if event.kind is EventType.TURN_ENDED:
            return self.MatchTurnPoint(end.name, mounted, event.actor)
        return False

    def MatchTurnPoint(self, pointName: str, mounted: MountedEffect, actor: PlayerId | None) -> bool:
        if actor is None:
            return False
        if pointName == StartPoint.OWNER_TURN_START.name or pointName == EndPoint.OWNER_TURN_START.name:
            return actor == mounted.owner
        if pointName == StartPoint.ENEMY_TURN_START.name or pointName == EndPoint.ENEMY_TURN_START.name:
            return actor == self.port.OpponentOf(mounted.owner)
        if pointName == EndPoint.OWNER_TURN_END.name:
            return actor == mounted.owner
        if pointName == EndPoint.ENEMY_TURN_END.name:
            return actor == self.port.OpponentOf(mounted.owner)
        return False

    # ---------- 触发器匹配 ----------

    def MatchesTrigger(self, mounted: MountedEffect, event: GameEvent) -> bool:
        trigger = mounted.effect.trigger
        if trigger.on is not event.kind:
            return False
        if trigger.oncePerTurn and mounted.lastFiredTurn == self.turnNumber:
            return False
        if trigger.side is not Side.ANY:
            if event.actor is None:
                return False
            if self.SideOf(event.actor, mounted.owner) is not trigger.side:
                return False
        if trigger.subjectMatches is not None:
            if event.subject is None:
                return False
            ctx = EvalContext(
                interp=self,
                owner=mounted.owner,
                selfCard=mounted.selfCard,
                event=event,
                subject=event.subject,
            )
            if event.subject not in self.Resolve(trigger.subjectMatches, ctx):
                return False
        return True

    # ---------- 目标解析 ----------

    def SideOf(self, player: PlayerId, owner: PlayerId) -> Side:
        return Side.FRIENDLY if player == owner else Side.ENEMY

    def PlayerFor(self, side: Side, owner: PlayerId) -> PlayerId:
        if side is Side.FRIENDLY:
            return owner
        if side is Side.ENEMY:
            return self.port.OpponentOf(owner)
        raise ValueError("PlayerFor 不接受 Side.ANY")

    def Resolve(self, selection: Selection, ctx: EvalContext) -> list[EntityId]:
        """把选择器解析成实体列表。"""
        if selection.anchor is Anchor.SELF:
            return [ctx.selfCard] if ctx.selfCard is not None else []
        if selection.anchor is Anchor.SUBJECT:
            return [ctx.subject] if ctx.subject is not None else []

        players = self.PlayersFor(selection.owner, ctx.owner)
        found: list[EntityId] = []
        for player in players:
            found.extend(self.SearchZone(player, selection))
        filtered = [e for e in found if self.MatchesFilters(e, selection)]
        return self.PickEntities(filtered, selection, ctx)

    def PlayersFor(self, side: Side, owner: PlayerId) -> tuple[PlayerId, ...]:
        if side is Side.FRIENDLY:
            return (owner,)
        if side is Side.ENEMY:
            return (self.port.OpponentOf(owner),)
        return (owner, self.port.OpponentOf(owner))

    def SearchZone(self, player: PlayerId, selection: Selection) -> list[EntityId]:
        zone = selection.zone
        if zone is Zone.HQ:
            return [self.port.GetHQ(player)]
        if zone is Zone.ANY:
            out: list[EntityId] = []
            for sub in (Zone.BOARD, Zone.HAND, Zone.DECK, Zone.GRAVEYARD):
                out.extend(self.port.ListEntities(player, sub))
            return out
        return list(self.port.ListEntities(player, zone))
    


    def MatchesFilters(self, entity: EntityId, selection: Selection) -> bool:
        port = self.port
        if selection.cardType is not None and port.GetCardType(entity) is not selection.cardType:
            return False
        if selection.unitType is not None and port.GetUnitType(entity) is not selection.unitType:
            return False
        if selection.keywordsAll:
            have = port.GetKeywords(entity)
            if not all(k in have for k in selection.keywordsAll):
                return False
        if selection.keywordsNone:
            have = port.GetKeywords(entity)
            if any(k in have for k in selection.keywordsNone):
                return False
        if selection.maxCost is not None and port.GetStat(entity, StatKind.COST) > selection.maxCost:
            return False
        if selection.minAttack is not None and port.GetStat(entity, StatKind.ATTACK) < selection.minAttack:
            return False
        # —— 新增 ——
        if selection.maxActionCost is not None \
                and port.GetStat(entity, StatKind.ACTION_COST) > selection.maxActionCost:
            return False
        if selection.minHealth is not None and port.GetStat(entity, StatKind.HEALTH) < selection.minHealth:
            return False
        if selection.maxHealth is not None and port.GetStat(entity, StatKind.HEALTH) > selection.maxHealth:
            return False
        if selection.frontline is not None and port.GetStat(entity, StatKind.FRONTLINE) != selection.frontline:
            return False
        if selection.timeline is not None and port.GetStat(entity, StatKind.TIMELINE) != selection.timeline:
            return False
        if not selection.includeDead and selection.zone is Zone.BOARD and not port.IsAlive(entity):
            return False
        return True
    
    def MakeContext(self, owner: PlayerId,
                  selfCard: EntityId | None = None) -> EvalContext:
      """给游戏流程（非效果）调用 GamePort 时用的上下文。"""
      return EvalContext(interp=self, owner=owner, selfCard=selfCard)



    def PickEntities(self, candidates: list[EntityId], selection: Selection, ctx: EvalContext) -> list[EntityId]:
        if not candidates:
            return []
        if selection.pick is Pick.ALL:
            return candidates
        if selection.pick is Pick.FIRST:
            return candidates[: selection.count]
        if selection.pick is Pick.LAST:
            return candidates[-selection.count:]
        if selection.pick is Pick.RANDOM:
            n = min(selection.count, len(candidates))
            return self.rng.sample(candidates, n)
        # Pick.CHOSEN
        chosen: list[EntityId] = []
        pool = list(candidates)
        while pool and len(chosen) < selection.count:
            picked = self.port.Choose(tuple(pool), ctx)
            if picked is None or picked not in pool:
                break
            chosen.append(picked)
            pool.remove(picked)
        return chosen
    
    def DetachHost(self, host: EntityId | None) -> None:
      """移除挂在某实体上的全部效果（单位阵亡 / 指令结算完毕）。"""
      self.mounted = [m for m in self.mounted if m.selfCard != host]

# ============================================================
# 10. CustomAction 操作名
# ============================================================

OP_ACTION_COST: Final[str] = "行动花费"
OP_SET_ATTACK: Final[str] = "设置攻击"
OP_SET_HEALTH: Final[str] = "设置生命"
OP_SET_ACTION_COST: Final[str] = "设置行动花费"
OP_AP: Final[str] = "行动点"
OP_AP_SLOT: Final[str] = "行动点槽"
OP_SET_AP: Final[str] = "设置行动点"
OP_SET_AP_SLOT: Final[str] = "设置行动点槽"
OP_ADD_TO_HAND: Final[str] = "加入手牌"
OP_TO_TOP: Final[str] = "置于卡组顶"
OP_TO_BOTTOM: Final[str] = "置于卡组底"
OP_SHUFFLE: Final[str] = "洗入卡组"
OP_CHANGE_EVENT: Final[str] = "更改事件"
