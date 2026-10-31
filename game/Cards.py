# -*- coding: utf-8 -*-
from .classes.Target import *
from .Constants import *
from .classes.Card import PassiveTag, PassiveType, ClacType, Tag, Keyword
from .classes.CommandEffect import (
    Buff, CountValue, CustomAction, DealDamage, DrawCards, Effect, EndPoint,
    EventType, ForEach, GrantKeyword, Heal, Lifespan, PlayEffect, Selection,
    Side, StartPoint, Trigger, Pick, Zone, UnitType as EffectUnitType,
)

from .classes.CommandEffect import (
    OP_ACTION_COST as _OP_ACTION_COST,
    OP_ADD_TO_HAND as _OP_ADD_TO_HAND,
    OP_AP_SLOT as _OP_AP_SLOT,
    OP_CHANGE_EVENT as _OP_CHANGE_EVENT,
    OP_SET_ATTACK as _OP_SET_ATTACK,
    OP_SET_HEALTH as _OP_SET_HEALTH,
    OP_SHUFFLE as _OP_SHUFFLE,
    OP_TO_TOP as _OP_TO_TOP,
)


from dataclasses import dataclass
import random

A = 0
B = 1
C = 2

allCards: list[UnitCard | CommandCard] = [
  # ================= 0 =================
  UnitCard(6, 7, [Tag(Keyword.Guard), Tag(Keyword.Prepared)], 7, 2,
          'ZTZ99A主战坦克', 'N', UnitType.tank, B, '守护,预备'),

  # ================= 1 =================
  UnitCard(4, 2, [Tag(Keyword.Blitz)], 3, 1,
          '2S38"偏流"', 'N', UnitType.tank, B, '闪击'),

  # ================= 2 指令 =================
  CommandCard(7, [], '破釜沉舟', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        Buff(Selection.Units(Side.FRIENDLY), 4, -1),
        DealDamage(Selection.HQ(Side.FRIENDLY), 7),
        # 快照每个被加过 buff 的单位，本友方回合结束时单独复原
        ForEach(
          Selection.Units(Side.FRIENDLY),
          PlayEffect(Effect(
            trigger=Trigger(EventType.TURN_ENDED, side=Side.FRIENDLY),
            lifespan=Lifespan(StartPoint.NOW, EndPoint.AFTER_TRIGGER),
            actions=(Buff(Selection.Self(), -4, 1),),   # ← 加圆括号和逗号
          )),
        ),
      ),
    ),
  ), dect_='使所有友方单位获得 +4-1，本回合结束时复原；对友方总部造成 7 点伤害', tl=A),

  # ================= 3 指令 =================
  CommandCard(3, [], '全频带阻塞干扰', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        CustomAction(_OP_ACTION_COST, Selection.Units(Side.ANY), {'值': 4}),
      ),
    ),
  ), dect_='使所有单位获得 +4 行动花费', tl=B),

  # ================= 4 指令 =================
  CommandCard(7, [], '死线扩散', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        CustomAction(_OP_SET_ATTACK, Selection.Units(Side.ENEMY), {'值': 0}),
        CustomAction(_OP_AP_SLOT, None, {'值': -2}),
      ),
    ),
  ), dect_='使所有敌方单位攻击力变为 0；友方失去 2 个行动点槽', tl=C),

  # ================= 5 单位：闪击 + 亡计 =================
  UnitCard(5, 4, [Tag(Keyword.Blitz), Tag(Keyword.Deathrattle)], 6, 2,
          '强-5 强击机', 'N', UnitType.bomber, B,
          '闪击。亡计：对敌方总部造成 3 点伤害',
          effects_=(
            Effect(
              trigger=Trigger(EventType.UNIT_DESTROYED,
                              subjectMatches=Selection.Self()),
              lifespan=Lifespan(),
              actions=(DealDamage(Selection.HQ(Side.ENEMY), 3),),
            ),
          )),

  # ================= 6 指令 =================
  CommandCard(5, [], '陈庆之北伐', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(Buff(Selection.Units(Side.ENEMY), -1, -2),
              CustomAction(_OP_TO_TOP, None, {'值': 8}),),
  ),), dect_='使所有敌方单位获得 -1-2，将两张"白袍军"置于友方卡组顶', tl=A),

  # ================= 7 =================
  UnitCard(7, 5, [Tag(Keyword.Blitz)], 7, 1,
          'BMPT-"终结者"', 'N', UnitType.tank, B, '闪击'),

  # ================= 8 =================
  UnitCard(5, 4, [Tag(Keyword.Blitz)], 3, 0,
          '白袍军', 'N', UnitType.infantry, A, '闪击'),

  # ================= 9 指令 =================
  CommandCard(4, [Tag(Keyword.TimeWarp)], '王莽', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(DrawCards(Side.FRIENDLY, 2),),
    ),
  ), dect_='穿梭，抽 2 张牌', tl=A),

  # ================= 10 指令 =================
  CommandCard(5, [], '改革开放', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(DrawCards(Side.FRIENDLY, 3),),
    ),
  ), dect_='抽 3 张牌', tl=B),

  # ================= 11 单位：被动 =================
  UnitCard(6, 3,
          [PassiveTag(PT=PassiveType.TakeDamage, CT=ClacType.MLimit, value=1)],
          5, 1, '德械师', 'N', UnitType.infantry, A,
          '本单位受到的伤害至多为 1'),

  # ================= 12 =================
  UnitCard(5, 6, [], 5, 2,
          'T-34 85D/5T', 'N', UnitType.tank, A, ''),

  # ================= 13 =================
  UnitCard(5, 5, [Tag(Keyword.Blitz)], 5, 1,
          'T-72', 'N', UnitType.tank, [A, B], '闪击'),

  # ================= 14 指令 =================
  CommandCard(6, [], '军备竞赛', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        CustomAction(_OP_SHUFFLE, None, {'值': 13}),
        CustomAction(_OP_TO_TOP, None, {'值': 13}),
      ),
    ),
  ), dect_='将 2 张"T-72"分别置于友方卡组顶与洗入卡组', tl=B),

  # ================= 15 指令 =================
  CommandCard(3, [], '经济危机', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        DealDamage(Selection.HQ(Side.FRIENDLY), 3),
        DrawCards(Side.FRIENDLY, 1),
        CustomAction(_OP_SHUFFLE, None, {'值': 16})
      ),
    ),
  ), dect_='抽 1 张牌，对友方总部造成 3 点伤害，将 1 张"市场经济"洗入卡组', tl=B),

  # ================= 16 指令 =================
  CommandCard(3, [], '市场经济', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        DrawCards(Side.FRIENDLY, 4),
        CustomAction(_OP_SHUFFLE, None, {'值': 15}),
        # CustomAction(_OP_SHUFFLE, None, {'值': 16}),
      ),
    ),
  ), dect_='抽 4 张牌，将 1 张"经济危机"洗入卡组', tl=B),

  # ================= 17 调试：A 时间段穿梭 =================
  CommandCard(2, [Tag(Keyword.TimeWarp)], '四维碎块', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(DrawCards(Side.FRIENDLY, 1),),
    ),
  ), dect_='穿梭，抽 1 张牌', tl=A),

  # ================= 18 调试：B 时间段穿梭 =================
  CommandCard(2, [Tag(Keyword.TimeWarp)], '增援未来', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(DrawCards(Side.FRIENDLY, 1),),
    ),
  ), dect_='穿梭，抽 1 张牌', tl=B),

  # ================= 19 调试：C 时间段穿梭 =================
  UnitCard(1,2, [Tag(Keyword.TimeWarp),Tag(Keyword.Blitz)], 2, 1, '"星环"号', '', 
          UnitType.fighter, C, dect_='穿梭，抽 1 张牌'),

  # ================= 20 调试：大航海开关 =================
  CommandCard(1, [], '篡改大航海', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(CustomAction(_OP_CHANGE_EVENT, None, {'值': 0}),),
    ),
  ), dect_='切换“大航海”的开启/关闭状态', tl=A),

  # ================= 21 调试：二战开关 =================
  CommandCard(1, [], '二次修订凡尔赛', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(CustomAction(_OP_CHANGE_EVENT, None, {'值': 1}),),
    ),
  ), dect_='切换“第二次世界大战”的开启/关闭状态', tl=A),

  # ================= 22 调试：冷战开关 =================
  CommandCard(1, [], '外交调和', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(CustomAction(_OP_CHANGE_EVENT, None, {'值': 2}),),
    ),
  ), dect_='切换“美苏冷战”的开启/关闭状态', tl=A),

  # ================= 23 调试：三战开关 =================
  CommandCard(1, [], '导火索', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(CustomAction(_OP_CHANGE_EVENT, None, {'值': 3}),),
    ),
  ), dect_='切换“第三次世界大战”的开启/关闭状态', tl=B),

  # ================= 24 调试：多时间线 + 部署效果 =================
  UnitCard(2, 2, [], 2, 1, '线列步兵', 'N', UnitType.infantry, [A, B],
          '部署：抽 1 张牌',
          effects_=(
            Effect(
              trigger=Trigger(EventType.SELF_DEPLOYED),
              lifespan=Lifespan.Once(),
              actions=(DrawCards(Side.FRIENDLY, 1),),
            ),
          )),

  # ================= 25 调试：守护 + 亡计 =================
  UnitCard(2, 6, [Tag(Keyword.Guard), Tag(Keyword.Deathrattle)], 3, 2,
          '现代步兵', 'N', UnitType.infantry, B,
          '守护。亡计：抽 1 张牌',
          effects_=(
            Effect(
              trigger=Trigger(EventType.UNIT_DESTROYED,
                              subjectMatches=Selection.Self()),
              lifespan=Lifespan(),
              actions=(DrawCards(Side.FRIENDLY, 1),),
            ),
          )),

  # ================= 26 调试：被动减伤 =================
  UnitCard(5, 5,
          [PassiveTag(PT=PassiveType.TakeDamage, CT=ClacType.MLimit, value=2)],
          4, 2, '天罚2500', 'N', UnitType.tank, C,
          '本单位受到的伤害至多为 2'),

  # ================= 27 调试：指向性指令 =================
  CommandCard(3, [], '精确打击', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        DealDamage(
          Selection(owner=Side.ENEMY, zone=Zone.BOARD,
                    pick=Pick.CHOSEN, count=1),
          4,
        ),
      ),
    ),
  ), dect_='对一个敌方单位造成 4 点伤害', tl=B),

  # ================= 28 A：志愿军第38军 =================
  UnitCard(5, 4, [], 4, 1, '志愿军第38军"万岁军"', 'N', UnitType.infantry, A,
          '部署：所有友方步兵获得 +1+1',
          effects_=(
            Effect(
              trigger=Trigger(EventType.SELF_DEPLOYED),
              lifespan=Lifespan.Once(),
              actions=(
                Buff(Selection.Units(Side.FRIENDLY,
                                    EffectUnitType.INFANTRY), 1, 1),
              ),
            ),
          )),

  # ================= 29 A：第101空降师 =================
  UnitCard(4, 4, [Tag(Keyword.Blitz)], 4, 1, '第101空降师', 'N',
          UnitType.infantry, A,
          '闪击。部署：抽 1 张牌',
          effects_=(
            Effect(
              trigger=Trigger(EventType.SELF_DEPLOYED),
              lifespan=Lifespan.Once(),
              actions=(DrawCards(Side.FRIENDLY, 1),),
            ),
          )),

  # ================= 30 A：近卫第13步兵师 =================
  UnitCard(2, 7,
          [Tag(Keyword.Guard),
          PassiveTag(PT=PassiveType.TakeDamage, CT=ClacType.MLimit, value=1)],
          5, 1, '近卫第13步兵师', 'N', UnitType.infantry, A,
          '守护。本单位受到的伤害至多为 1'),

  # ================= 31 B：第75游骑兵团 =================
  UnitCard(3, 4, [Tag(Keyword.Agile, 1)], 3, 1, '第75游骑兵团', 'N',
          UnitType.infantry, B, 'Rangers lead the way! \n灵活 1'),

  # ================= 32 B：第22特别空勤团 =================
  UnitCard(3, 3, [Tag(Keyword.Blitz)], 3, 1, '第22特别空勤团', 'N',
          UnitType.infantry, B,
          'Who Dares Wins.\n闪击。部署：使一个随机敌方单位获得 -2 攻击力',
          effects_=(
            Effect(
              trigger=Trigger(EventType.SELF_DEPLOYED),
              lifespan=Lifespan.Once(),
              actions=(
                Buff(Selection(owner=Side.ENEMY, zone=Zone.BOARD,
                              pick=Pick.RANDOM, count=1),
                    -2, 0),
              ),
            ),
          )),

  # ================= 33 B：雪豹突击队 =================
  UnitCard(2, 4, [Tag(Keyword.Guard)], 4, 1, '雪豹突击队', 'N',
          UnitType.infantry, B,
          '守护。部署：所有敌方单位攻击力 -1',
          effects_=(
            Effect(
              trigger=Trigger(EventType.SELF_DEPLOYED),
              lifespan=Lifespan.Once(),
              actions=(Buff(Selection.Units(Side.ENEMY), -1, 0),),
            ),
          )),

  # ================= 34 C：第82空降师·外骨骼营 =================
  UnitCard(5, 6, [Tag(Keyword.Prepared)], 5, 2, '第82空降师·外骨骼营',
          'N', UnitType.infantry, C,
          '预备。部署：抽 1 张牌',
          effects_=(
            Effect(
              trigger=Trigger(EventType.SELF_DEPLOYED),
              lifespan=Lifespan.Once(),
              actions=(DrawCards(Side.FRIENDLY, 1),),
            ),
          )),

  # ================= 35 A：敦刻尔克大撤退 =================
  CommandCard(2, [], '敦刻尔克大撤退', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        DrawCards(Side.FRIENDLY, 2),
        DealDamage(Selection.HQ(Side.FRIENDLY), 2),
      ),
    ),
  ), dect_='抽 2 张牌。友方总部受到 2 点伤害', tl=A),

  # ================= 36 B：沙漠风暴 =================
  CommandCard(5, [], '沙漠风暴', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        DealDamage(Selection.Units(Side.ENEMY), 2),
      ),
    ),
  ), dect_='对所有敌方单位造成 2 点伤害', tl=B),

  # ================= 37 指令 =================
  CommandCard(4, [], '计划经济', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        DrawCards(Side.FRIENDLY, 5),
        DealDamage(Selection.HQ(Side.FRIENDLY), 5),
        # CustomAction(_OP_SHUFFLE, None, {'值': 16}),
      ),
    ),
  ), dect_='抽 5 张牌，对友方总部造成 5 点伤害', tl=B),

  # ================= 38 A：志愿军第15军 =================
  UnitCard(4, 6, [Tag(Keyword.Guard)], 4, 1, '志愿军第15军', 'N',
          UnitType.infantry, A,
          '上甘岭的坑道部队。守护。部署：所有友方步兵获得 +0+1',
          effects_=(
            Effect(
              trigger=Trigger(EventType.SELF_DEPLOYED),
              lifespan=Lifespan.Once(),
              actions=(
                Buff(Selection.Units(Side.FRIENDLY,
                                    EffectUnitType.INFANTRY), 0, 1),
              ),
            ),
          )),

  # ================= 39 A：上甘岭战役 =================
  CommandCard(4, [], '上甘岭战役', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        Buff(Selection.Units(Side.FRIENDLY, EffectUnitType.INFANTRY), 1, 1),
        DrawCards(Side.FRIENDLY, 1),
      ),
    ),
  ), dect_='所有友方步兵获得 +1+1，抽 1 张牌', tl=A),

  # ================= 40 全时间线穿梭 =================
  CommandCard(3, [Tag(Keyword.TimeWarp)], '时序裂隙', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(DrawCards(Side.FRIENDLY, 1),),
    ),
  ), dect_='全时间线可用。穿梭，抽 1 张牌', tl=[A, B, C]),

  # ================= 41 全时间线穿梭 =================
  CommandCard(4, [Tag(Keyword.TimeWarp)], '漂流者协议', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(DrawCards(Side.FRIENDLY, 2),),
    ),
  ), dect_='全时间线可用。穿梭，抽 2 张牌', tl=[A, B, C]),

  # ================= 42 C：回环信标 =================
  CommandCard(2, [Tag(Keyword.TimeWarp)], '回环信标', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(DrawCards(Side.FRIENDLY, 1),),
    ),
  ), dect_='穿梭，抽 1 张牌', tl=C),

  # ================= 43 C：时间折叠 =================
  CommandCard(3, [Tag(Keyword.TimeWarp)], '时间折叠', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(DrawCards(Side.FRIENDLY, 2),),
    ),
  ), dect_='穿梭，抽 2 张牌', tl=C),

  # ================= 44 C：轨道空降第501团 =================
  UnitCard(4, 4, [Tag(Keyword.Prepared)], 3, 1, '轨道空降第501团', 'N',
          UnitType.infantry, C,
          '预备。部署：抽 1 张牌',
          effects_=(
            Effect(
              trigger=Trigger(EventType.SELF_DEPLOYED),
              lifespan=Lifespan.Once(),
              actions=(DrawCards(Side.FRIENDLY, 1),),
            ),
          )),

  # ================= 45 C：第15机动步兵营 =================
  UnitCard(3, 7, [Tag(Keyword.Guard)], 4, 1, '第15机动步兵营', 'N',
          UnitType.infantry, C,
          '守护',
          effects_=(
            # Effect(
            #   trigger=Trigger(EventType.SELF_DEPLOYED),
            #   lifespan=Lifespan.Once(),
            #   actions=(
            #     Buff(Selection(owner=Side.ENEMY, zone=Zone.BOARD,
            #                   pick=Pick.RANDOM, count=1),
            #         -2, 0),
            #   ),
            # ),
          )),

  # ================= 46 C：第120穿梭特遣队 =================
  UnitCard(3, 3, [Tag(Keyword.TimeWarp)], 2, 1, '第120穿梭特遣队', 'N',
          UnitType.infantry, C,
          '穿梭。部署：抽 1 张牌',
          effects_=(
            Effect(
              trigger=Trigger(EventType.SELF_DEPLOYED),
              lifespan=Lifespan.Once(),
              actions=(DrawCards(Side.FRIENDLY, 1),),
            ),
          )),

  # ================= 47 C：强相互作用力装甲 =================
  UnitCard(6, 3,
          [PassiveTag(PT=PassiveType.TakeDamage, CT=ClacType.MLimit, value=2)],
          6, 2, '强相互作用力装甲', 'N', UnitType.tank, C,
          '本单位受到的伤害至多为 2'),

  # ================= 48 C：第9轨道突击营 =================
  UnitCard(6, 5, [Tag(Keyword.Blitz)], 5, 1, '第9轨道突击营', 'N',
          UnitType.infantry, C, '闪击'),

  # ================= 49 C：曲率侦察舰 =================
  UnitCard(4, 4, [Tag(Keyword.Blitz)], 4, 1, '曲率侦察舰', 'N',
          UnitType.fighter, C, '闪击'),

  # ================= 50 C：技术泄露 =================
  CommandCard(3, [Tag(Keyword.TimeWarp)], '技术泄露', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(DealDamage(Selection.Units(Side.ENEMY), 2),),
    ),
  ), dect_='穿梭。对所有敌方单位造成 2 点伤害', tl=C),

  # ================= 51 C：戴森环工程 =================
  CommandCard(6, [], '戴森环工程', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        CustomAction(_OP_AP_SLOT, None, {'值': 2}),
        DrawCards(Side.FRIENDLY, 1),
      ),
    ),
  ), dect_='获得 2 个行动点槽，抽 1 张牌', tl=C),

  # ================= 52 C：纳米修复云 =================
  CommandCard(3, [], '纳米修复云', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        Heal(Selection.Units(Side.FRIENDLY), 2),
      ),
    ),
  ), dect_='所有友方单位恢复 2 点生命', tl=C),

  # ================= 53 C：水滴 =================
  CommandCard(7, [], '水滴', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        DealDamage(Selection.HQ(Side.ENEMY), 7),
      ),
    ),
  ), dect_='对敌方总部造成 7 点伤害', tl=C),

  # ================= 54 C：时间锚点 =================
  CommandCard(2, [], '时间锚点', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(CustomAction(_OP_CHANGE_EVENT, None, {'值': 3}),),
    ),
  ), dect_='切换“第三次世界大战”的开启/关闭状态', tl=C),

  # ================= 55 C：轨道轰炸 =================
  CommandCard(4, [], '轨道轰炸', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        DealDamage(Selection(owner=Side.ENEMY, zone=Zone.BOARD,
                            frontline=1), 3),
      ),
    ),
  ), dect_='对所有前线敌方单位造成 3 点伤害', tl=C),
  # ================= 56 A: IS-3
  UnitCard(
    7,7,[Tag(Keyword.TimeWarp)],7,3,"IS-3",'',UnitType.tank,A,'穿梭',()
  ),
  # 57 C 647号宇宙
  CommandCard(4, [Tag(Keyword.TimeWarp)], '647号宇宙', '', effects_=(
    
  ), dect_='穿梭', tl=C),
  # 58 B 古筝行动
  CommandCard(
    6, [], '古筝行动', '',
    effects_=(
      Effect(
        trigger=Trigger(EventType.SELF_DEPLOYED),
        lifespan=Lifespan.Once(),
        actions=(
          CustomAction(_OP_SET_HEALTH, Selection.Units(Side.ENEMY), {'值': 1}),
        ),
      ),
    ),
    dect_='使所有敌方单位防御力变为 1',
    tl=B,
  ) ,
  # ================= 59 A 战时动员
  CommandCard(
    2, [], '战时动员', '',
    effects_=(
      Effect(
        Trigger(EventType.SELF_DEPLOYED),
        actions=(
          Heal(Selection.HQ(Side.FRIENDLY), 3),
          CustomAction(_OP_AP_SLOT, None, {'值': 1}),
        ),
        lifespan=Lifespan.Once()
      ),
    ),
    dect_='友方总部获得 +3 防御力，获得 1 个行动点槽',
    tl=[A,B,C]
  ),
  # ================= 60 ABC 战时生产
  CommandCard(
    3, [], '战时生产', '',
    effects_=(
      Effect(
        Trigger(EventType.SELF_DEPLOYED),
        actions=(
          CustomAction(_OP_AP_SLOT, None, {'值': 2}),
        ),
        lifespan=Lifespan.Once()
      ),
    ),
    dect_='获得 2 个行动点槽',
    tl=[A, B, C]
  ),
  # ================= 61 B 第92机械化旅
  UnitCard(
    4, 4, [], 4, 1, '第92机械化旅', 'N', UnitType.infantry, B,
    '部署：所有友方坦克获得 +1+2',
    effects_=(
      Effect(
        Trigger(EventType.SELF_DEPLOYED),
        actions=(
          Buff(Selection.Units(Side.FRIENDLY, EffectUnitType.TANK), 1, 2),
        ),
        lifespan=Lifespan.Once()
      ),
    )
  ),
  # ================= 62 B 豹2A4
  UnitCard(6, 6, [], 5, 1, '豹2A4', 'N', UnitType.tank, B, ''),
  # ================= 63 B 自杀无人机
  UnitCard(
    7, 1,
    [
      Tag(Keyword.Blitz),
      PassiveTag(PT=PassiveType.HqAttack, CT=ClacType.Sub, value=3),
    ],
    3, 2, '自杀无人机', 'N', UnitType.fighter, B,
    '闪击。攻击敌方总部时伤害 -3'
  ),
  # ================= 64 AB 预备役部队
  UnitCard(
    1, 1, [Tag(Keyword.Blitz)], 1, 0, '预备役部队', 'N',
    UnitType.infantry, [A, B],
    '闪击。友方回合开始时获得 +1+1',
    effects_=(
      Effect(
        Trigger(EventType.TURN_STARTED, side=Side.FRIENDLY, oncePerTurn=True),
        actions=(
          Buff(Selection.Self(), 1, 1),
        ),
        lifespan=Lifespan()
      ),
    )
  ),
  # ================= 65 B 征兵动员
  CommandCard(
    2, [], '征兵动员', '',
    effects_=(
      Effect(
        Trigger(EventType.SELF_DEPLOYED),
        actions=(
          CustomAction(_OP_ADD_TO_HAND, None, {'值': 64}),
          CustomAction(_OP_ADD_TO_HAND, None, {'值': 64}),
        ),
        lifespan=Lifespan.Once()
      ),
    ),
    dect_='将 2 张"预备役部队"加入手牌',
    tl=B
  ),
  # ================= 66 B 滚木突击队
  UnitCard(
    2, 2, [Tag(Keyword.Blitz), Tag(Keyword.Deathrattle)], 3, 1,
    '滚木突击队', 'N', UnitType.infantry, B,
    '闪击。亡计：将 2 张"滚木"洗入敌方卡组',
    effects_=(
      Effect(
        Trigger(EventType.UNIT_DESTROYED, subjectMatches=Selection.Self()),
        actions=(
          CustomAction(_OP_SHUFFLE, Selection.HQ(Side.ENEMY), {'值': 67}),
          CustomAction(_OP_SHUFFLE, Selection.HQ(Side.ENEMY), {'值': 67}),
        ),
        lifespan=Lifespan()
      ),
    )
  ),
  # ================= 67 B 滚木（衍生牌）
  CommandCard(4, [], '滚木', '', effects_=(), dect_='', tl=B),
  # ================= 68 A 圣诞停火
  CommandCard(
    10, [], '圣诞停火', '',
    effects_=(
      Effect(
        Trigger(EventType.SELF_DEPLOYED),
        actions=(
          CustomAction(_OP_SET_ATTACK, Selection.Units(Side.ANY), {'值': 0}),
          DrawCards(Side.FRIENDLY, 10),
          DrawCards(Side.ENEMY, 10),
          Heal(Selection.HQ(Side.FRIENDLY), 15),
          Heal(Selection.HQ(Side.ENEMY), 15),
        ),
        lifespan=Lifespan.Once()
      ),
    ),
    dect_='将所有单位的攻击力变为 0。双方各抽 10 张牌，双方总部恢复 15 点生命',
    tl=A
  ),
  # ================= 69 A 凛冬将至
  CommandCard(
    7, [], '凛冬将至', '',
    effects_=(
      Effect(
        Trigger(EventType.SELF_DEPLOYED),
        actions=(
          Buff(Selection.Units(Side.ENEMY), -2, -1),
          Buff(Selection.Units(Side.FRIENDLY), 2, 2),
        ),
        lifespan=Lifespan.Once()
      ),
    ),
    dect_='所有敌方单位获得 -2-1，所有友方单位获得 +2+2',
    tl=A
  ),
  # ================= 70 A 邓艾部队
  UnitCard(3, 3, [], 2, 1, '邓艾部队', 'N', UnitType.infantry, A, ''),
  # ================= 71 A 陆逊
  CommandCard(
    5, [], '陆逊', '',
    effects_=(
      Effect(
        Trigger(EventType.SELF_DEPLOYED),
        actions=(
          DealDamage(
            Selection.Units(Side.ENEMY),
            CountValue(Selection.Units(Side.ENEMY))
          ),
        ),
        lifespan=Lifespan.Once()
      ),
    ),
    dect_='对所有敌方单位造成等同于敌方单位数量的伤害',
    tl=A
  ),
  # ================= 72 A 虎式坦克H1型
  UnitCard(8, 8, [], 6, 3, '虎式坦克H1型', 'N', UnitType.tank, A, ''),
  # ================= 73 A 第1装甲集团军群
  UnitCard(
    9, 10, [], 12, 3, '第1装甲集团军群', 'N', UnitType.infantry, A,
    '友方回合开始时，将 1 张"虎式坦克H1型"加入手牌',
    effects_=(
      Effect(
        Trigger(EventType.TURN_STARTED, side=Side.FRIENDLY, oncePerTurn=True),
        actions=(
          CustomAction(_OP_ADD_TO_HAND, None, {'值': 72}),
        ),
        lifespan=Lifespan()
      ),
    )
  ),
  # ================= 74 AB 闪电战
  CommandCard(
    2, [], '闪电战', '',
    effects_=(
      Effect(
        Trigger(EventType.SELF_DEPLOYED),
        actions=(
          GrantKeyword(Selection.Units(Side.FRIENDLY), Keyword.Blitz.value),
        ),
        lifespan=Lifespan.Once()
      ),
    ),
    dect_='所有友方单位获得闪击',
    tl=[A, B]
  )
  
]
def RemoveCard(cardIdx : int):
  cardIds.remove(cardIdx)


# 原来 +1 会让最后一张牌索引越界，去掉
cardIds = list(range(len(allCards)))


RemoveCard(15)# 经济危机为衍生牌
RemoveCard(67)# 滚木为衍生牌

if not DEBUG:
  RemoveCard(68)
if DEBUG:
  cardIds *= 2

random.shuffle(cardIds)

@dataclass
class HandCard():
  id : int
  cost : int
  extraTags : list[Tag]


def CardToHand(cid : int):
  return HandCard(cid, allCards[cid].cost, [])


def Shuffle():
  random.shuffle(cardIds)
