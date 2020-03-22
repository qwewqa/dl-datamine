import argparse
import json
import os
import re
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from Abilities import get_ability_data, AbilityData, get_ability_and_references
from Actions import get_text_label, \
    get_actions
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
    skill1: Optional[List[Skill]]
    skill2: Optional[List[Skill]]
    playable: bool
    cv_info: str
    cv_info_en: str
    profile_text: str


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


def gather_adventurer(adventurer_data: AdventurerData, skills: Dict[int, Skill],
                      abilities: Dict[int, AbilityData]) -> Adventurer:
    skill1 = skills.get(adventurer_data.skill1, None)
    skill2 = skills.get(adventurer_data.skill2, None)
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
        abilities={k: get_ability_and_references(aid, abilities) for k, aid in adventurer_data.ability_ids.items()},
        skill1=skill1 if skill1 is None else get_skill_transforms(skill1, skills),
        skill2=skill2 if skill2 is None else get_skill_transforms(skill2, skills),
        playable=adventurer_data.playable,
        cv_info=adventurer_data.cv_info,
        cv_info_en=adventurer_data.cv_info_en,
        profile_text=adventurer_data.profile_text
    )


def gather_adventurers(in_dir: str, label: Dict[str, str], skills: Dict[int, Skill],
                       abilities: Dict[int, AbilityData]) -> Dict[int, Adventurer]:
    return {adv_id: gather_adventurer(adv, skills, abilities) for adv_id, adv in
            get_adventurer_data(in_dir, label).items()}


def run(in_dir: str) -> Dict[int, Adventurer]:
    label = get_text_label(in_dir)
    actions = get_actions(in_dir, label)
    abilities = get_ability_data(in_dir, label)
    skills = get_skills(in_dir, label, actions, abilities)
    return gather_adventurers(in_dir, label, skills, abilities)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Adventurer Data.')
    parser.add_argument('-i', type=str, help='input dir (from extracting master and actions)', default='./extract')
    parser.add_argument('-o', type=str, help='output dir', default='./adventurers')
    args = parser.parse_args()
    run_common(args.o, [(adv.name, adv) for adv in run(args.i).values()])
