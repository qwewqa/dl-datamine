import argparse
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from Asset_Extract import check_target_path
from Parse_Action import Action, parse_action, EnhancedJSONEncoder, hit_attributes

WEAPON_TYPES = {
    1: "Sword",
    2: "Blade",
    3: "Dagger",
    4: "Axe",
    5: "Lance",
    6: "Bow",
    7: "Wand",
    8: "staff"
}

ELEMENTS = {
    1: "Flame",
    2: "Water",
    3: "Wind",
    4: "Light",
    5: "Shadow"
}


@dataclass
class SkillData:
    id: int
    name: str
    description1: str
    description2: str
    description3: str
    description4: str
    sp: int
    sp_lv2: int
    actions: List[Action]
    advanced_action: Optional[Action]
    trans_skill_id: int
    tension: bool


@dataclass
class Adventurer:
    id: int
    name: str
    weapon_type: str
    rarity: int
    element: str
    skill1: Optional[List[SkillData]]
    skill2: Optional[List[SkillData]]
    playable: bool


def text_label(in_dir: str) -> Dict[str, Optional[str]]:
    with open(os.path.join(in_dir, 'TextLabel.json')) as f:
        return defaultdict(lambda: None, {entry['_Id']: entry['_Text'] for entry in json.load(f)})


def get_skill_transforms(skill: SkillData, skills: Dict[int, SkillData]) -> List[SkillData]:
    ids = [skill.id]
    s = skill
    while s.trans_skill_id > 0 and s.trans_skill_id not in ids:
        ids.append(s.trans_skill_id)
        s = skills[s.trans_skill_id]
    return [skills[sid] for sid in ids]


def adventurer_data(in_dir: str, label: Dict[str, str], skills: Dict[int, SkillData]) -> Dict[int, Adventurer]:
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
                name=label[char['_SecondName']] or label[char['_Name']],
                weapon_type=WEAPON_TYPES[char['_WeaponType']],
                rarity=char['_Rarity'],
                element=ELEMENTS[char['_ElementalType']],
                skill1=skill1 if skill1 is None else get_skill_transforms(skill1, skills),
                skill2=skill2 if skill2 is None else get_skill_transforms(skill2, skills),
                playable=bool(char['_IsPlayable'])
            )
        return adventurers


def action_data(in_dir: str) -> Dict[int, Action]:
    file_filter = re.compile("PlayerAction_[0-9]+\\.json")
    hit_attrs = hit_attributes(in_dir)
    actions = {}
    for root, _, files in os.walk(in_dir):
        for file_name in [f for f in files if file_filter.match(f) and f.startswith("PlayerAction")]:
            file_path = os.path.join(root, file_name)
            action = parse_action(file_path, hit_attrs)
            actions[action.id] = action
    return actions


def skill_data(in_dir: str, label: Dict[str, str], actions: Dict[int, Action]) -> Dict[int, SkillData]:
    with open(os.path.join(in_dir, 'SkillData.json')) as f:
        data: List[Dict[str, Any]] = json.load(f)
        skills = {}
        for skill in data:
            action_ids = [aid for aid in
                          [skill['_ActionId1'], skill['_ActionId2'], skill['_ActionId3'], skill['_ActionId4']] if
                          aid > 0]
            advanced_action_id = skill['_AdvancedActionId1']
            skills[skill['_Id']] = SkillData(
                id=skill['_Id'],
                name=label[skill['_Name']] or "",
                description1=label.get(skill['_Description1'], ""),
                description2=label.get(skill['_Description2'], ""),
                description3=label.get(skill['_Description3'], ""),
                description4=label.get(skill['_Description4'], ""),
                sp=skill['_Sp'],
                sp_lv2=skill['_SpLv2'],
                actions=[actions[aid] for aid in action_ids if aid in actions.keys()],
                advanced_action=actions.get(advanced_action_id, None),
                trans_skill_id=skill['_TransSkill'],
                tension=bool(skill['_IsAffectedByTension'])
            )
        return skills


def get_valid_filename(s):
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def get_adventurers(in_dir: str) -> Dict[int, Adventurer]:
    labels = text_label(in_dir)
    actions = action_data(in_dir)
    skills = skill_data(in_dir, labels, actions)
    return adventurer_data(in_dir, labels, skills)


def run(in_dir: str, out_dir: str) -> None:
    adventurers = get_adventurers(in_dir)
    for adventurer in adventurers.values():
        out_path = os.path.join(out_dir, f"{get_valid_filename(adventurer.name)}.json")
        check_target_path(out_path)
        with open(out_path, 'w+', encoding='utf8') as f:
            json.dump(adventurer, f, indent=2, cls=EnhancedJSONEncoder)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract asset files.')
    parser.add_argument('-i', type=str, help='input dir (from extracting master and actions)', default='./extract')
    parser.add_argument('-o', type=str, help='output dir', default='./adv_data')
    args = parser.parse_args()
    run(args.i, args.o)
