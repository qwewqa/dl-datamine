import json
import os
from dataclasses import dataclass, InitVar
from typing import List, Dict, Any, Callable

from Common import ACTION_CONDITION_TYPES

ABILITY_TYPES: Dict[int, Callable[[List[int], str], str]] = {
    1: lambda *_: 'strength',
    2: lambda ids, _: f'affliction_res {ACTION_CONDITION_TYPES.get(ids[0], ids[0])}',
    14: lambda ids, _: f'action_condition {ids[0]}',
    43: lambda ids, _: f'ability_ref {ids[0]}'
}


@dataclass
class AbilityPart:
    ability_type: int
    ids: List[int]
    id_str: str
    ability_limited_group: int
    target_action: int
    value: float
    description: str = None

    def __post_init__(self):
        if self.description is None:
            if self.ability_type in ABILITY_TYPES:
                self.description = ABILITY_TYPES[self.ability_type](self.ids, self.id_str)
            else:
                self.description = ''


@dataclass
class AbilityData:
    id: int
    event_id: int
    might: int
    name: int
    details: int
    view_ability_group_ids: List[int]
    ability_icon_name: str
    unit_type: str
    element_type: str
    weapon_type: str
    on_skill: int
    condition_type: str
    expire_condition: str
    condition_value: float
    probability: int
    occurrence_num: int
    max_count: int
    cool_time: float
    target_action: int
    shift_group_id: int
    head_text: str
    abilities: List[AbilityPart]


def ability_part(data: Dict[str, Any], suffix: str) -> AbilityPart:
    return AbilityPart(
        ability_type=data[f'_AbilityType{suffix}'],
        ids=[data[f'_VariousId{suffix}a'], data[f'_VariousId{suffix}b'], data[f'_VariousId{suffix}c']],
        id_str=data[f'_VariousId{suffix}str'],
        ability_limited_group=data[f'_AbilityLimitedGroupId{suffix}'],
        target_action=data[f'_TargetAction{suffix}'],
        value=data[f'_AbilityType{suffix}UpValue']
    )


def ability_data(in_dir: str, label: Dict[str, str]) -> Dict[int, AbilityData]:
    with open(os.path.join(in_dir, 'AbilityData.json')) as f:
        data: List[Dict[str, Any]] = json.load(f)
        abilities = {}
        for ability in data:
            abilities[ability['_Id']] = AbilityData(
                id=ability['_Id'],
                event_id=ability['_EventId'],
                might=ability['_PartyPowerWeight'],
                name=label.get(ability['_Name'], ability['_Name']),
                details=label.get(ability['_Details'], ability['_Details']),
                view_ability_group_ids=[ability['_ViewAbilityGroupId1'], ability['_ViewAbilityGroupId2'],
                                        ability['_ViewAbilityGroupId3']],
                ability_icon_name=ability['_AbilityIconName'],
                unit_type=str(ability['_UnitType']),
                element_type=str(ability['_ElementalType']),
                weapon_type=str(ability['_WeaponType']),
                on_skill=ability['_OnSkill'],
                condition_type=str(ability['_ConditionType']),
                expire_condition=str(ability['_ExpireCondition']),
                condition_value=ability['_ConditionValue'],
                probability=ability['_Probability'],
                occurrence_num=ability['_OccurenceNum'],
                max_count=ability['_MaxCount'],
                cool_time=ability['_CoolTime'],
                target_action=ability['_TargetAction'],
                shift_group_id=ability['_ShiftGroupId'],
                head_text=label.get(ability['_HeadText'], ability['_HeadText']),
                abilities=[ability_part(ability, suffix) for suffix in ['1', '2', '3'] if
                           ability[f'_AbilityType{suffix}']]
            )
        return abilities


def get_ability_and_references(ability_id: int, abilities: Dict[int, AbilityData]) -> List[AbilityData]:
    if ability_id not in abilities:
        return []
    queue = [abilities[ability_id]]
    referenced = []
    while queue:
        ab = queue.pop()
        if ab not in referenced:
            referenced.append(ab)
            for part in ab.abilities:
                if part.ability_type == 43:
                    queue.append(abilities[part.ids[0]])
    return referenced
