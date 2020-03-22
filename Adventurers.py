import argparse
import json
import os
import re
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from Abilities import get_ability_data, AbilityData, get_ability_and_references
from Common import run_common
from Mappings import ELEMENTS, WEAPON_TYPES
from Actions import Action, parse_action, get_hit_attribute_data, get_text_label, \
    get_action_condition_data
from Skills import Skill, get_skills


@dataclass
class Adventurer:
    id: int
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


def adventurer_data(in_dir: str, label: Dict[str, str], skills: Dict[int, Skill],
                    abilities: Dict[int, AbilityData]) -> Dict[int, Adventurer]:
    with open(os.path.join(in_dir, 'CharaData.json')) as f:
        data: List[Dict[str, Any]] = json.load(f)
        adventurers = {}
        for char in data:
            cid = char['_Id']
            if cid == 0:
                continue
            skill1 = skills.get(char['_Skill1'], None)
            skill2 = skills.get(char['_Skill2'], None)
            adventurers[cid] = Adventurer(
                id=cid,
                name=label.get(char['_SecondName'], label.get(char['_Name'], char['_Name'])),
                weapon_type=WEAPON_TYPES[char['_WeaponType']],
                rarity=char['_Rarity'],
                element=ELEMENTS[char['_ElementalType']],
                abilities={s.replace('_Abilities', ''): get_ability_and_references(char[s], abilities) for s in
                           char.keys() if
                           s.startswith('_Abilities') and char[s]},
                skill1=skill1 if skill1 is None else get_skill_transforms(skill1, skills),
                skill2=skill2 if skill2 is None else get_skill_transforms(skill2, skills),
                playable=bool(char['_IsPlayable']),
                cv_info=label.get(char['_CvInfo'], ''),
                cv_info_en=label.get(char['_CvInfoEn'], ''),
                profile_text=label.get(char['_ProfileText'], '')
            )
        return adventurers


def action_data(in_dir: str, labels: Dict[str, str]) -> Dict[int, Action]:
    file_filter = re.compile('PlayerAction_[0-9]+\\.json')
    hit_attrs = get_hit_attribute_data(in_dir)
    action_conditions = get_action_condition_data(in_dir, labels)
    actions = {}
    for root, _, files in os.walk(in_dir):
        for file_name in [f for f in files if file_filter.match(f) and f.startswith('PlayerAction')]:
            file_path = os.path.join(root, file_name)
            action = parse_action(file_path, hit_attrs, action_conditions)
            actions[action.id] = action
    return actions


def get_valid_filename(s):
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def get_adventurers(in_dir: str) -> Dict[int, Adventurer]:
    labels = get_text_label(in_dir)
    actions = action_data(in_dir, labels)
    abilities = get_ability_data(in_dir, labels)
    skills = get_skills(in_dir, labels, actions, abilities)
    return adventurer_data(in_dir, labels, skills, abilities)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Adventurer Data.')
    parser.add_argument('-i', type=str, help='input dir (from extracting master and actions)', default='./extract')
    parser.add_argument('-o', type=str, help='output dir', default='./adventurers')
    args = parser.parse_args()
    run_common(args.o, [(adv.name, adv) for adv in get_adventurers(args.i).values()])
