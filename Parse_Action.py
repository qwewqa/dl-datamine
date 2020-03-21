import argparse
import dataclasses
import json
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Callable, Any, Optional

from Asset_Extract import check_target_path
from Common import ACTION_CONDITION_TYPES


def to_frames(duration: float) -> int:
    return round(duration * 60)


def load_by_id(path: str) -> Dict[Any, Any]:
    with open(path) as f:
        return {entry['_Id']: entry for entry in json.load(f)}


def get_text_labels(in_dir: str) -> Dict[str, str]:
    with open(os.path.join(in_dir, 'TextLabel.json')) as f:
        return {entry['_Id']: entry['_Text'] for entry in json.load(f)}


@dataclass
class HitAttributes:
    id: str
    hit_exec: int
    target_group: int
    mod: float
    od_rate: float
    break_rate: float
    self_damage: int
    set_hp: float
    consume_hp_rate: float
    recovery_value: int
    sp: int
    recovery_sp_ratio: float
    recovery_sp_skill: int
    recovery_dp_percentage: float
    recovery_dragon_time: float
    recovery_dp: int
    recovery_ep: int
    gauge: int
    fixed_damage: int
    current_hp_damage_rate: int
    hp_drain_rate: float
    hp_drain_rate2: float
    hp_drain_limit_rate: float
    hp_drain_attribute: str
    counter_coef: float
    crisis_rate: float
    action_condition: int
    action_grant: int
    killer_states: List[int]
    killer_rate: int
    buff_boost: float


def parse_hit_attributes(data: dict):
    return HitAttributes(
        id=data['_Id'],
        hit_exec=data['_HitExecType'],
        target_group=data['_TargetGroup'],
        mod=data['_DamageAdjustment'],
        od_rate=data['_ToOdDmgRate'],
        break_rate=data['_ToBreakDmgRate'],
        self_damage=data['_IsDamageMyself'],
        set_hp=data['_SetCurrentHpRate'],
        consume_hp_rate=data['_ConsumeHpRate'],
        recovery_value=data['_RecoveryValue'],
        sp=data['_AdditionRecoverySp'],
        recovery_sp_ratio=data['_RecoverySpRatio'],
        recovery_sp_skill=data['_RecoverySpSkillIndex'],
        recovery_dp_percentage=data['_AdditionRecoveryDpPercentage'],
        recovery_dragon_time=data['_RecoveryDragonTime'],
        recovery_dp=data['_AdditionRecoveryDpLv1'],
        recovery_ep=data['_RecoveryEp'],
        gauge=data['_AdditionActiveGaugeValue'],
        fixed_damage=data['_FixedDamage'],
        current_hp_damage_rate=data['_CurrentHpRateDamage'],
        hp_drain_rate=data['_HpDrainRate'],
        hp_drain_rate2=data['_HpDrainRate2'],
        hp_drain_limit_rate=data['_HpDrainLimitRate'],
        hp_drain_attribute=data['_HpDrainAttribute'],
        counter_coef=data['_DamageCounterCoef'],
        crisis_rate=data['_CrisisLimitRate'],
        action_condition=data['_ActionCondition1'],
        action_grant=data['_ActionGrant'],
        killer_states=[cond for cond in [data['_KillerState1'], data['_KillerState2'], data['_KillerState3']] if
                       cond > 0],
        killer_rate=data['_KillerStateDamageRate'],
        buff_boost=data['_DamageUpRateByBuffCount']
    )


@dataclass
class ActionCondition:
    id: int
    type: str
    text: str
    text_ex: str
    unique_icon: int
    resist_buff_reset: int
    unified_management: int
    overwrite: int
    overwrite_identical_owner: int
    overwrite_group_id: int
    user_power_up_effect: int
    lost_on_dragon: int
    restore_on_reborn: int
    rate: int
    efficacy_type: int
    remove_condition_id: int
    duration: float
    duration_num: int
    min_duration: float
    remove_action: int
    slip_damage_interval: float
    slip_damage_fixed: int
    slip_damage_ratio: float
    slip_damage_max: int
    slip_damage_power: float
    regen_power: float
    event_probability: int
    event_coefficient: float
    damage_coefficient: float
    target_action: int
    target_elemental: int
    condition_abs: int
    condition_debuff: int
    hp: float
    attack: float
    defense: float
    defense_b: float
    critical: float
    skill: float
    fs: float
    recovery: float
    sp: float
    attack_speed: float
    charge_speed: float
    # rate_poison: float
    # rate_burn: float
    # rate_freeze: float
    # rate_paralysis: float
    # rate_blind: float
    # rate_stun: float
    # rate_curse: float
    # rate_bog: float
    # rate_sleep: float
    # rate_frostbite: float
    # rate_fire: float
    # rate_water: float
    # rate_wind: float
    # rate_light: float
    # rate_dark: float
    # rate_thaumian: float
    # rate_physian: float
    # rate_demihuman: float
    # rate_therion: float
    # rate_undead: float
    # rate_demon: float
    # rate_human: float
    # rate_dragon: float
    damage_cut: float
    damage_cut_2: float
    weak_invalid: float
    heal_invalid: int
    valid_regen_hp: float
    valid_regen_sp: float
    valid_regen_dp: float
    valid_slip_hp: float
    unique_regen_sp: float
    auto_regen_s1: float
    auto_regen_s2: float
    rate_reraise: float
    rate_armored: float
    shield1: float
    shield2: float
    shield3: float
    # malaise1: int  # vnidd
    # malaise2: int
    # malaise3: int
    # rate_nicked: float  # dull
    transform_skill: float
    grant_skill: int
    disable_action: int
    disable_move: int
    invincible_lv: int
    combo_shift: int
    enhanced_fs: int
    enhanced_skill1: int
    enhanced_skill2: int
    enhanced_weapon_skill: int
    enhanced_critical: float
    tension: int
    inspiration: int
    sparking: int
    rate_hp_drain: float
    hp_drain_limit_rate: float
    self_damage_rate: float
    hp_consumption_rate: float
    hp_consumption_coef: float
    remove_trigger: int
    damage_link: str
    extra_buff_type: int


def parse_action_condition(data: dict, labels: Dict[str, str]) -> ActionCondition:
    return ActionCondition(
        id=data['_Id'],
        type=ACTION_CONDITION_TYPES.get(data['_Type'], str(data['_Type'])),
        text=labels.get(data['_Text'], data['_Text']),
        text_ex=labels.get(data['_TextEx'], data['_TextEx']),
        unique_icon=data['_UniqueIcon'],
        resist_buff_reset=data['_ResistBuffReset'],
        unified_management=data['_UnifiedManagement'],
        overwrite=data['_Overwrite'],
        overwrite_identical_owner=data['_OverwriteIdenticalOwner'],
        overwrite_group_id=data['_OverwriteGroupId'],
        user_power_up_effect=data['_UsePowerUpEffect'],
        lost_on_dragon=data['_LostOnDragon'],
        restore_on_reborn=data['_RestoreOnReborn'],
        rate=data['_Rate'],
        efficacy_type=data['_EfficacyType'],
        remove_condition_id=data['_RemoveConditionId'],
        duration=data['_DurationSec'],
        duration_num=data['_DurationNum'],
        min_duration=data['_MinDurationSec'],
        remove_action=data['_RemoveAciton'],
        slip_damage_interval=data['_SlipDamageIntervalSec'],
        slip_damage_fixed=data['_SlipDamageFixed'],
        slip_damage_ratio=data['_SlipDamageRatio'],
        slip_damage_max=data['_SlipDamageMax'],
        slip_damage_power=data['_SlipDamagePower'],
        regen_power=data['_RegenePower'],
        event_probability=data['_EventProbability'],
        event_coefficient=data['_EventCoefficient'],
        damage_coefficient=data['_DamageCoefficient'],
        target_action=data['_TargetAction'],
        target_elemental=data['_TargetElemental'],
        condition_abs=data['_ConditionAbs'],
        condition_debuff=data['_ConditionDebuff'],
        hp=data['_RateHP'],
        attack=data['_RateAttack'],
        defense=data['_RateDefense'],
        defense_b=data['_RateDefenseB'],
        critical=data['_RateCritical'],
        skill=data['_RateSkill'],
        fs=data['_RateBurst'],
        recovery=data['_RateRecovery'],
        sp=data['_RateRecoverySp'],
        attack_speed=data['_RateAttackSpeed'],
        charge_speed=data['_RateChargeSpeed'],
        damage_cut=data['_RateDamageCut'],
        damage_cut_2=data['_RateDamageCut2'],
        weak_invalid=data['_RateWeakInvalid'],
        heal_invalid=data['_HealInvalid'],
        valid_regen_hp=data['_ValidRegeneHP'],
        valid_regen_sp=data['_ValidRegeneSP'],
        valid_regen_dp=data['_ValidRegeneDP'],
        valid_slip_hp=data['_ValidSlipHp'],
        unique_regen_sp=data['_UniqueRegeneSp01'],
        auto_regen_s1=data['_AutoRegeneS1'],
        auto_regen_s2=data['_AutoRegeneSW'],
        rate_reraise=data['_RateReraise'],
        rate_armored=data['_RateArmored'],
        shield1=data['_RateDamageShield'],
        shield2=data['_RateDamageShield2'],
        shield3=data['_RateDamageShield3'],
        transform_skill=data['_TransSkill'],
        grant_skill=data['_GrantSkill'],
        disable_action=data['_DisableAction'],
        disable_move=data['_DisableMove'],
        invincible_lv=data['_InvincibleLv'],
        combo_shift=data['_ComboShift'],
        enhanced_fs=data['_EnhancedBurstAttack'],
        enhanced_skill1=data['_EnhancedSkill1'],
        enhanced_skill2=data['_EnhancedSkill2'],
        enhanced_weapon_skill=data['_EnhancedSkillWeapon'],
        enhanced_critical=data['_EnhancedCritical'],
        tension=data['_Tension'],
        inspiration=data['_Inspiration'],
        sparking=data['_Sparking'],
        rate_hp_drain=data['_RateHpDrain'],
        hp_drain_limit_rate=data['_HpDrainLimitRate'],
        self_damage_rate=data['_SelfDamageRate'],
        hp_consumption_rate=data['_HpConsumptionRate'],
        hp_consumption_coef=data['_HpConsumptionCoef'],
        remove_trigger=data['_RemoveTrigger'],
        damage_link=data['_DamageLink'],
        extra_buff_type=data['_ExtraBuffType']
    )


def get_hit_attributes(in_dir: str) -> Dict[str, HitAttributes]:
    return {data[0]: parse_hit_attributes(data[1]) for data in
            load_by_id(os.path.join(in_dir, 'PlayerActionHitAttribute.json')).items()}


def get_action_conditions(in_dir: str, labels: Dict[str, str]) -> Dict[int, ActionCondition]:
    return {data[0]: parse_action_condition(data[1], labels) for data in
            load_by_id(os.path.join(in_dir, 'ActionCondition.json')).items()}


@dataclass
class Event:
    name: str = ''
    seconds: float = 0.0
    delay: float = 0.0
    speed: float = 1.0
    duration: float = 0.0

    @property
    def default_start(self) -> float:
        return self.seconds / self.speed + self.delay

    def __lt__(self, other):
        return self.default_start < other.default_start

    def __str__(self):
        if self.delay > 0:
            if self.speed != 1.0:
                return f'{self.default_start:.3f} ({self.seconds:.3f}/{self.speed:.3f} + {self.delay:.3f}) : ' \
                       f'{to_frames(self.default_start)}f ({to_frames(self.seconds)}f/{self.speed:.3f} + {to_frames(self.delay)}f)'
            else:
                return f'{self.default_start:.3f} ({self.seconds:.3f} + {self.delay:.3f}) : ' \
                       f'{to_frames(self.default_start)}f ({to_frames(self.seconds)}f + {to_frames(self.delay)}f)'
        else:
            if self.speed != 1.0:
                return f'{self.default_start:.3f} ({self.seconds:.3f}/{self.speed:.3f}) : ' \
                       f'{to_frames(self.default_start)}f ({to_frames(self.seconds)}f/{self.speed:.3f})'
            else:
                return f'{self.default_start:.3f} : ' \
                       f'{to_frames(self.default_start)}f'


@dataclass
class PartsMotion(Event):
    activate_id: int = 0
    motion_state: str = ''
    motion_frame: int = 0
    blend_duration: float = 0
    name: str = 'PartsMotion'

    def __str__(self):
        return f'[{Event.__str__(self)}] Parts Motion: motion_state {self.motion_state}, ' \
               f'duration {self.duration:.3f} : {to_frames(self.duration)}f, ' \
               f'blend_duration {self.blend_duration:.3f} : {to_frames(self.blend_duration)}f'

    def __repr__(self):
        return f'[{Event.__str__(self)}] Parts Motion: activate_id {self.activate_id}, ' \
               f'motion_state {self.motion_state}, ' \
               f'motion_frame {self.motion_frame}, ' \
               f'duration {self.duration:.3f} : {to_frames(self.duration)}f, ' \
               f'blend_duration {self.blend_duration:.3f} : {to_frames(self.blend_duration)}f'


@dataclass
class Hit(Event):
    interval: float = 50.0
    lifetime: Optional[float] = None
    label: str = ''
    hit_delete: bool = False
    name: str = 'Hit'

    def __str__(self):
        return f'[{Event.__str__(self)}] Hit: label {self.label}, ' \
               f'duration {self.duration:.3f} : {to_frames(self.duration)}f, ' \
               f'interval {self.interval:.3f} : {to_frames(self.interval)}f' + \
               (f', lifetime {self.lifetime:.3f} : {to_frames(self.lifetime)}f' if self.lifetime else '')


@dataclass
class ActiveCancel(Event):
    activate_id: int = 0
    action_id: int = 0
    action_type: int = 0
    motion_end: bool = False
    name: str = 'ActiveCancel'

    def __str__(self):
        return f'[{Event.__str__(self)}] Active Cancel: action_id {self.action_id}, ' \
               f'duration {self.duration:.3f} : {to_frames(self.duration)}f'

    def __repr__(self):
        return f'[{Event.__str__(self)}] Active Cancel: action_id {self.action_id}, ' \
               f'action_type {self.action_type}, ' \
               f'activate_id {self.activate_id}, ' \
               f'motion_end {self.motion_end}, ' \
               f'duration {self.duration:.3f} : {to_frames(self.duration)}f'


SIGNAL_TYPES = {
}


@dataclass
class Signal(Event):
    activate_id: int = 0
    signal_type: int = 0
    motion_end: bool = False
    action_id: int = 0
    deco_id: int = 0
    name: str = 'Signal'

    def __str__(self):
        return f'[{Event.__str__(self)}] Signal: ' \
               f'signal_type {SIGNAL_TYPES[self.signal_type] if self.signal_type in SIGNAL_TYPES.keys() else self.signal_type}, ' \
               f'action_id {self.action_id}, ' \
               f'duration {self.duration:.3f} : {to_frames(self.duration)}f'

    def __repr__(self):
        return f'[{Event.__str__(self)}] Signal: ' \
               f'signal_type {SIGNAL_TYPES[self.signal_type] if self.signal_type in SIGNAL_TYPES.keys() else self.signal_type}, ' \
               f'activate_id {self.activate_id}, ' \
               f'action_id {self.action_id}, ' \
               f'motion_end {self.motion_end}, ' \
               f'deco_id {self.deco_id}, ' \
               f'duration {self.duration:.3f} : {to_frames(self.duration)}f'


@dataclass
class Action:
    id: int
    timeline: List[Event]
    hit_attributes: Dict[str, HitAttributes]
    action_conditions: Dict[int, ActionCondition]


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def parts_motion_data(data: dict):
    return [PartsMotion(seconds=data['_seconds'],
                        speed=data['_speed'],
                        duration=data['_duration'],
                        activate_id=data['_activateId'],
                        motion_state=data['_motionState'],
                        motion_frame=data['_motionFrame'],
                        blend_duration=data['_blendDuration']
                        )]


def bullet_data(data: dict):
    primary = Hit(seconds=data['_seconds'],
                  speed=data['_speed'],
                  duration=data['_duration'],
                  delay=data['_delayTime'] if data['_delayVisible'] else 0.0,
                  interval=data['_collisionHitInterval'],
                  hit_delete=data['_isHitDelete'],
                  label=data['_hitAttrLabel'])
    bullets = [primary]
    ab_label = data['_arrangeBullet']['_abHitAttrLabel']
    if ab_label != '':
        bullets.append(dataclasses.replace(primary, label=ab_label))
    return bullets


def other_bullet_data(data: dict):
    primary = Hit(seconds=data['_seconds'],
                  speed=data['_speed'],
                  duration=data['_duration'],
                  interval=data['_collisionHitInterval'],
                  hit_delete=data['_isHitDelete'],
                  label=data['_hitAttrLabel'])
    bullets = [primary]
    ab_label = data['_arrangeBullet']['_abHitAttrLabel']
    if ab_label != '':
        bullets.append(dataclasses.replace(primary, label=ab_label))
    return bullets


def hit_data(data: dict):
    return [Hit(seconds=data['_seconds'],
                speed=data['_speed'],
                duration=data['_duration'],
                interval=data['_collisionHitInterval'],
                label=data['_hitLabel'])]


def setting_hit_data(data: dict):
    return [Hit(seconds=data['_seconds'],
                speed=data['_speed'],
                duration=data['_duration'],
                lifetime=data['_lifetime'],
                delay=data['_delayTime'],
                interval=data['_collisionHitInterval'],
                label=data['_hitAttrLabel'])]


def active_cancel(data: dict):
    return [ActiveCancel(seconds=data['_seconds'],
                         speed=data['_speed'],
                         duration=data['_duration'],
                         activate_id=data['_activateId'],
                         action_id=data['_actionId'],
                         action_type=data['_actionType'],
                         motion_end=bool(data['_motionEnd']))]


def signal_data(data: dict):
    return [Signal(seconds=data['_seconds'],
                   speed=data['_speed'],
                   duration=data['_duration'],
                   activate_id=data['_activateId'],
                   signal_type=data['_signalType'],
                   motion_end=bool(data['_motionEnd']),
                   action_id=data['_actionId'],
                   deco_id=data['_decoId'])]


def multi_bullet_data(data: dict):
    num = data['_generateNum']
    interval = data['_generateDelay']
    base_bullets = bullet_data(data)
    bullets = []
    for i in range(num):
        bullets.extend([dataclasses.replace(bullet, seconds=bullet.seconds + interval * i) for bullet in base_bullets])
    return bullets


def fire_stock_bullet_data(data: dict):
    num = data['_bulletNum']
    base = bullet_data(data)
    return base * num


class CommandType(Enum):
    UNKNOWN = -1
    PARTS_MOTION_DATA = 2
    BULLET_DATA = 9
    HIT_DATA = 10
    EFFECT_DATA = 11
    SOUND_DATA = 12
    CAMERA_MOTION_DATA = 13
    SEND_SIGNAL_DATA = 14
    ACTIVE_CANCEL_DATA = 15
    MULTI_BULLET_DATA = 24
    PARABOLA_BULLET_DATA = 41
    PIVOT_BULLET_DATA = 53
    FIRE_STOCK_BULLET_DATA = 59
    SETTING_HIT_DATA = 66

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN


PROCESSORS: Dict[CommandType, Callable[[Dict], List[Event]]] = {
    CommandType.HIT_DATA: hit_data,
    CommandType.ACTIVE_CANCEL_DATA: active_cancel,
    CommandType.BULLET_DATA: bullet_data,
    CommandType.PARABOLA_BULLET_DATA: other_bullet_data,
    CommandType.PIVOT_BULLET_DATA: other_bullet_data,
    CommandType.SEND_SIGNAL_DATA: signal_data,
    CommandType.PARTS_MOTION_DATA: parts_motion_data,
    CommandType.MULTI_BULLET_DATA: multi_bullet_data,
    CommandType.FIRE_STOCK_BULLET_DATA: fire_stock_bullet_data,
    CommandType.SETTING_HIT_DATA: setting_hit_data
}


def attributes_for_label(label: str, attributes: Dict[str, HitAttributes]) -> List[HitAttributes]:
    if re.compile('.*LV0[1-4]').match(label):
        suffixes = ['LV01', 'LV02', 'LV03', 'LV04']
        base_name = label[0:-4]
        return [attributes[base_name + suffix] for suffix in suffixes if base_name + suffix in attributes.keys()]
    else:
        return [attributes[label]] if label in attributes.keys() else []


def parse_action(path: str, attributes: Dict[str, HitAttributes],
                 action_conditions: Dict[int, ActionCondition]) -> Action:
    with open(path) as f:
        raw = json.load(f)
        action = [gameObject['_data'] for gameObject in raw if '_data' in gameObject.keys()]
        data: List[Event] = []
        for command in action:
            command_type = CommandType(command['commandType'])
            if command_type in PROCESSORS.keys():
                data.extend(PROCESSORS[command_type](command))
        hit_labels = set()
        for event in data:
            if hasattr(event, 'label'):
                hit_labels.add(event.label)
        hit_attrs: Dict[str, HitAttributes] = {attribute.id: attribute for label in
                                               hit_labels for attribute in
                                               attributes_for_label(label, attributes)}
        return Action(
            id=int(Path(path).stem.split('_')[1]),
            timeline=sorted(data),
            hit_attributes=hit_attrs,
            action_conditions={ac.id: ac for ac in
                               [action_conditions[attr.action_condition] for attr in hit_attrs.values() if
                                attr.action_condition > 0]}
        )


def process_action(in_path: str, out_path: str, mode: str, attributes: Dict[str, HitAttributes],
                   action_conditions: Dict[int, ActionCondition]):
    action = parse_action(in_path, attributes, action_conditions)
    check_target_path(out_path)
    with open(out_path, 'w+', encoding='utf8') as f:
        if mode == 'json':
            json.dump(action, f, indent=2, cls=EnhancedJSONEncoder)
        elif mode == 'simple':
            f.write(f'Action {action.id}\n')
            for event in action.timeline:
                f.write(f'{event}\n')


def process_actions(in_path: str, out_path: str, mode: str):
    extension = {
        'json': '.json',
        'simple': '.txt'
    }[mode]
    file_filter = re.compile('PlayerAction_[0-9]+\\.json')
    if os.path.isdir(in_path):
        labels = get_text_labels(in_path)
        attributes = get_hit_attributes(in_path)
        action_conditions = get_action_conditions(in_path, labels)
        for root, _, files in os.walk(in_path):
            for file_name in [f for f in files if file_filter.match(f) and f.startswith('PlayerAction')]:
                file_in_path = os.path.join(root, file_name)
                file_out_path = os.path.join(out_path, Path(file_name).with_suffix(extension))
                process_action(file_in_path, file_out_path, mode, attributes, action_conditions)
    else:
        if os.path.isdir(out_path):
            out_path = os.path.join(out_path, Path(in_path).with_suffix(extension).name)
        in_dir = Path(in_path).parent
        labels = get_text_labels(in_dir)
        attributes = get_hit_attributes(in_dir)
        action_conditions = get_action_conditions(in_dir, labels)
        process_action(in_path, out_path, mode, attributes, action_conditions)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract asset files.')
    parser.add_argument('-i', type=str, help='input file or dir', default='./extract')
    parser.add_argument('-o', type=str, help='output file dir', default='./actions')
    parser.add_argument('-m', type=str, help='mode: default "json", "simple")', default='json')
    args = parser.parse_args()
    process_actions(args.i, args.o, args.m)
