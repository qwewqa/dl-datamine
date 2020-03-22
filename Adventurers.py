import argparse
import json
import os
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Union

from Abilities import get_ability_data, AbilityData, get_ability_and_references
from ActionConditions import ActionConditionData, get_action_condition_data
from Actions import get_text_label, \
    get_actions, Action
from Common import run_common
from Mappings import ELEMENTS, WEAPON_TYPES
from Skills import Skill, get_skills


@dataclass
class AdventurerData:
    id: int
    base_id: int
    variation_id: int
    name: str
    atk: int
    hp: int
    weapon_type: str
    rarity: int
    element: str
    ability_ids: Dict[str, int]
    skill1: int
    skill2: int
    playable: bool
    cv_info: str
    cv_info_en: str
    profile_text: str

    def __hash__(self):
        return (self.id, self.name).__hash__()


@dataclass
class Adventurer:
    id: int
    base_id: int
    variation_id: int
    atk: int
    hp: int
    name: str
    weapon_type: str
    rarity: int
    element: str
    abilities: Dict[str, AbilityData]
    skill1: List[Skill]
    skill2: List[Skill]
    enhanced: Dict
    playable: bool
    cv_info: str
    cv_info_en: str
    profile_text: str

    def __hash__(self):
        return (self.id, self.name).__hash__()


def get_skill_transforms(skill: Skill, skills: Dict[int, Skill]) -> List[Skill]:
    ids = [skill.id]
    s = skill
    while s.trans_skill_id > 0 and s.trans_skill_id not in ids:
        ids.append(s.trans_skill_id)
        s = skills[s.trans_skill_id]
    return [skills[sid] for sid in ids]


def get_adventurer_data(in_dir: str, label: Dict[str, str]) -> Dict[int, AdventurerData]:
    with open(os.path.join(in_dir, 'CharaData.json')) as f:
        data: List[Dict[str, Any]] = json.load(f)
        adventurers = {}
        for char in data:
            cid = char['_Id']
            if cid == 0:
                continue
            adventurers[cid] = AdventurerData(
                id=cid,
                base_id=char['_BaseId'],
                variation_id=char['_VariationId'],
                name=label.get(char['_SecondName'], label.get(char['_Name'], char['_Name'])),
                atk=sum([char[s] for s in char.keys() if s.startswith('_PlusAtk')]) + char['_McFullBonusAtk5'] + char[
                    '_AddMaxAtk1'],
                hp=sum([char[s] for s in char.keys() if s.startswith('_PlusHp')]) + char['_McFullBonusHp5'] + char[
                    '_AddMaxHp1'],
                weapon_type=WEAPON_TYPES[char['_WeaponType']],
                rarity=char['_Rarity'],
                element=ELEMENTS[char['_ElementalType']],
                ability_ids={s.replace('_Abilities', ''): char[s] for s in
                             char.keys() if s.startswith('_Abilities') and char[s]},
                skill1=char['_Skill1'],
                skill2=char['_Skill2'],
                playable=bool(char['_IsPlayable']),
                cv_info=label.get(char['_CvInfo'], ''),
                cv_info_en=label.get(char['_CvInfoEn'], ''),
                profile_text=label.get(char['_ProfileText'], '')
            )
        return adventurers


def get_enhanced(subjects: List[Union[AbilityData, Skill, Action, ActionConditionData]], skills: Dict[int, Skill],
                 actions: Dict[int, Action], action_conditions: Dict[int, ActionConditionData], abilities: Dict[int, AbilityData]) -> Dict:
    queue = subjects
    passed = set()
    s1 = set()
    s2 = set()
    fs = set()

    while queue:
        s = queue.pop()
        if s in passed:
            continue
        passed.add(s)
        if isinstance(s, AbilityData):
            for a in s.abilities:
                if a.ability_type == 14:
                    queue.append(action_conditions[a.ids[0]])
                if a.ability_type == 43:
                    queue.append(abilities[a.ids[0]])
        elif isinstance(s, Skill):
            queue.extend([i for j in s.abilities for i in j])
            queue.extend(s.actions)
            if isinstance(s.advanced_action, Action):
                queue.append(s.advanced_action)
        elif isinstance(s, Action):
            queue.extend(s.action_conditions.values())
        elif isinstance(s, ActionConditionData):
            if s.enhanced_skill1:
                n = skills[s.enhanced_skill1]
                s1.add(n)
                queue.append(n)
            if s.enhanced_skill2:
                n = skills[s.enhanced_skill2]
                s2.add(n)
                queue.append(n)
            if s.enhanced_fs:
                n = actions[s.enhanced_fs]
                fs.add(n)
                queue.append(n)
    return {'skill1': list(s1), 'skill2': list(s2), 'fs': list(fs)}


def gather_adventurer(adventurer_data: AdventurerData, skills: Dict[int, Skill], actions: Dict[int, Action],
                      action_conditions: Dict[int, ActionConditionData],
                      abilities: Dict[int, AbilityData]) -> Adventurer:
    s1 = skills.get(adventurer_data.skill1, None)
    s2 = skills.get(adventurer_data.skill2, None)
    s1 = [] if s1 is None else get_skill_transforms(s1, skills)
    s2 = [] if s2 is None else get_skill_transforms(s2, skills)
    ab = {k: get_ability_and_references(aid, abilities) for k, aid in adventurer_data.ability_ids.items()}
    flat_skills_abilities = [s for s in s1] + [s for s in s2] + [a for al in ab.values() for a in al]
    return Adventurer(
        id=adventurer_data.id,
        base_id=adventurer_data.base_id,
        variation_id=adventurer_data.variation_id,
        name=adventurer_data.name,
        atk=adventurer_data.atk,
        hp=adventurer_data.hp,
        weapon_type=adventurer_data.weapon_type,
        rarity=adventurer_data.rarity,
        element=adventurer_data.element,
        abilities=ab,
        skill1=s1,
        skill2=s2,
        enhanced=get_enhanced(flat_skills_abilities, skills, actions, action_conditions, abilities),
        playable=adventurer_data.playable,
        cv_info=adventurer_data.cv_info,
        cv_info_en=adventurer_data.cv_info_en,
        profile_text=adventurer_data.profile_text
    )


def gather_adventurers(in_dir: str, label: Dict[str, str], skills: Dict[int, Skill], actions: Dict[int, Action],
                       action_conditions: Dict[int, ActionConditionData],
                       abilities: Dict[int, AbilityData]) -> Dict[int, Adventurer]:
    return {adv_id: gather_adventurer(adv, skills, actions, action_conditions, abilities) for adv_id, adv in
            get_adventurer_data(in_dir, label).items()}


def run(in_dir: str) -> Dict[int, Adventurer]:
    label = get_text_label(in_dir)
    actions = get_actions(in_dir, label)
    action_conditions = get_action_condition_data(in_dir, label)
    abilities = get_ability_data(in_dir, label)
    skills = get_skills(in_dir, label, actions, abilities)
    return gather_adventurers(in_dir, label, skills, actions, action_conditions, abilities)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Adventurer Data.')
    parser.add_argument('-i', type=str, help='input dir (from extracting master and actions)', default='./extract')
    parser.add_argument('-o', type=str, help='output dir', default='./adventurers')
    args = parser.parse_args()
    run_common(args.o, [(f'{adv.id}_{adv.name}', adv) for adv in run(args.i).values()])
