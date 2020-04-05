#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from collections import OrderedDict, defaultdict
import argparse
import csv
import os
import re

BOOK_ID_NAME_OVERRIDES = {
    '320000801': (lambda data: '{} ({})'.format(data['Name'], data['ElementalType']))
}
DATA_ID_NAME_OVERRIDES = {
    '400010002': 'Head',
    '100360006': 'Imperial Defender (Jeanne)',
    '500010007': 'Imperial Soldier (Jeanne)',
    '500030007': 'Imperial Lancer (Jeanne)',
    '500050013': 'Imperial Mage (Jeanne)',
    '500140001': 'Imperial Phantom (Flame)',
    '500150002': 'Imperial Phantom (Water)',
    '500150003': 'Imperial Phantom (Wind)',
    '500150004': 'Imperial Phantom (Light)',
    '500150015': 'Imperial Phantom (Shadow)',
    '900160001': 'Reaper',
    '900180001': 'Magma Lump',
    '900190001': 'Drawbridge',
    '900220001': 'Large Bubble',
    '900230001': 'Small Bubble',
    '900240001': 'Whirlpool',
    '900110001': 'Sphere of Salvation',
    '900250001': 'Sphere of Salvation',
    '900260001': 'Dominion Lance',
    '900270001': 'Octopus Bomb',
    '900290501': 'Purgatorial Prison',
    '900320301': 'Wily Machine 2 Cockpit Armor',
    '900330301': 'Underdog\'s Mine',
    '900350001': 'Floating Spirit Summoning Circle',
    '900400001': '???????',
    '900410401': 'Unbreakable Satellite',
}
QUEST_NAME_REGEX = {
    re.compile(r'TUTORIAL_'): (lambda: 'Prologue'),
    re.compile(r'MAIN_(\d+)_(\d+)_E_'):
            (lambda x, y: 'Chapter {}: {}'.format(int(x), MAIN_DIFFICULTY.get(y, y))),
    re.compile(r'WALL_\d+_(\d+)_(\d+)_E_'):
            (lambda x, y: 'The Mercurial Gauntlet ({}): Lv. {}'.format(
                ELEMENTAL_TYPES.get(x.lstrip('0'), x), int(y))),
    re.compile(r'RARE_\d+_(\d+)_E(\d+)'):
            (lambda x, y: get_rare_enemy_quest_name(x,y)),

    # Simple TextLabel lookup.
    re.compile(r'EXP_\d+_(\d+)_E'):
            (lambda x: get_label('QUEST_NAME_2010101{}'.format(x))),
    re.compile(r'WEEKLY_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_202{}01{}'.format(x, y))),
    re.compile(r'DRAGONBATTLE_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_203{}01{}'.format(x, y))),
    re.compile(r'DRAGONBATTLE_ULT_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_210{}01{}'.format(
                    x, QUEST_DIFFICULTY_OVERRIDES['DRAGONBATTLE_ULT'].get(y, y)))),
    re.compile(r'EMPIRE_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_211{}01{}'.format(x, y))),
    re.compile(r'ASTRAL_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_217{}01{}'.format(x, y))),
    re.compile(r'AGITO_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_219{}01{}'.format(x, y))),
    re.compile(r'VOIDBATTLE_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_300{}01{}'.format(
                    QUEST_NAME_OVERRIDES['VOIDBATTLE'].get(x, x), y))),
}
QUEST_NAME_OVERRIDES = {
    'VOIDBATTLE': {
        '10': '11',
        '11': '10',
    },
}
QUEST_DIFFICULTY_OVERRIDES = {
    'DRAGONBATTLE_ULT': {
        '01': '02',
        '04': '01',
        '05': '03',
        '06': '04',
    },
}
MAIN_DIFFICULTY = {
    '01': 'Normal',
    '02': 'Hard',
    '03': 'Very Hard',
}
RARE_ENEMY_QUESTS = {
    '01': 'Light Campaign / Avenue / Ruins Quests: Level ',
    '02': 'Water Campaign / Ruins Quests: Level ',
    '03': 'Wind Campaign / Ruins Quests: Level ',
    '04': 'Shadow Campaign / Avenue / Ruins Quests: Level ',
    '05': 'Flame Campaign / Ruins Quests: Level ',
}
TRIBES = {
    '0': 'None',
    '1': 'Thaumian',
    '2': 'Physian',
    '3': 'Demihuman',
    '4': 'Therion',
    '5': 'Undead',
    '6': 'Demon',
    '7': 'Human',
    '8': 'Dragon',
}
ELEMENTAL_TYPES = {
    '1': 'Flame',
    '2': 'Water',
    '3': 'Wind',
    '4': 'Light',
    '5': 'Shadow',
    '99': '', # None
}

class Enemy:
    def __init__(self, enemy_param, enemy_data, enemy_list, weapon_data):
        ep = enemy_param
        ed = enemy_data[ep['_DataId']]
        el = enemy_list[ed['_BookId']]

        data = OrderedDict()
        data['Id'] = ep['_Id']
        data['DataId'] = ep['_DataId']
        data['Name'] = get_label(el['_Name']) or DATA_ID_NAME_OVERRIDES.get(data['DataId'], '')
        data['RareStayTime'] = ep['_RareStayTime']
        data['HP'] = ep['_HP']
        data['Atk'] = ep['_Atk']
        data['Def'] = ep['_Def']
        data['Overwhelm'] = ep['_Overwhelm']
        data['BaseOD'] = ep['_BaseOD']
        data['BaseBreak'] = ep['_BaseBreak']
        data['CounterRate'] = ep['_CounterRate']
        data['BarrierRate'] = ep['_BarrierRate']
        data['GetupActionRate'] = ep['_GetupActionRate']
        data['Poison'] = ep['_RegistAbnormalRate01']
        data['Burn'] = ep['_RegistAbnormalRate02']
        data['Freeze'] = ep['_RegistAbnormalRate03']
        data['Paralysis'] = ep['_RegistAbnormalRate04']
        data['Blind'] = ep['_RegistAbnormalRate05']
        data['Stun'] = ep['_RegistAbnormalRate06']
        data['Bog'] = ep['_RegistAbnormalRate07']
        data['Sleep'] = ep['_RegistAbnormalRate08']
        data['Curse'] = ep['_RegistAbnormalRate09']
        data['Frostbite'] = ep['_RegistAbnormalRate10']
        data['PartsA'] = ep['_PartsA']
        data['PartsB'] = ep['_PartsB']
        data['PartsC'] = ep['_PartsC']
        data['PartsD'] = ep['_PartsD']
        data['PartsNode'] = ep['_PartsNode']
        # data['CrashedHPRate'] = ep['_CrashedHPRate'] # Currently unused
        data['MissionType'] = get_enemy_quest_name(ep['_ParamGroupName'])
        data['MissionDifficulty'] = ''    # Currently unused
        data['Tribe'] = TRIBES.get(el['_TribeType'], el['_TribeType'])
        data['Weapon'] = get_label(weapon_data.get(ed['_WeaponId'], ''))
        data['ElementalType'] = ELEMENTAL_TYPES.get(ed['_ElementalType'])
        data['BreakDuration'] = ed['_BreakDuration']
        data['MoveSpeed'] = ed['_MoveSpeed']
        data['TurnSpeed'] = ed['_TurnSpeed']
        data['SuperArmor'] = ed['_SuperArmor']
        data['BreakAtkRate'] = ed['_BreakAtkRate']
        data['BreakDefRate'] = ed['_BreakDefRate']
        data['ODAtkRate'] = ed['_ObAtkRate']
        data['ODDefRate'] = ed['_ObDefRate']
        data['Ability01'] = ep['_Ability01']
        data['Ability02'] = ep['_Ability02']
        data['Ability03'] = ep['_Ability03']
        data['Ability04'] = ep['_Ability04']
        self.data = data

        # Name overrides that take precedence over a known name
        if ed['_BookId'] in BOOK_ID_NAME_OVERRIDES:
            data['Name'] = BOOK_ID_NAME_OVERRIDES[ed['_BookId']](data)

    def __repr__(self):
        return ''.join([
                '{{EnemyData|',
                '|'.join('='.join(item) for item in self.data.items()),
                '}}',
            ])

def get_label(label, default=''):
    return TEXT_LABEL.get(label, default) or default

def get_enemy_quest_name(group_name):
    for pattern in QUEST_NAME_REGEX:
        match = pattern.match(group_name)
        if match:
            return QUEST_NAME_REGEX[pattern](*match.groups())
    return MANUAL_QUEST_MAP.get(group_name, '')

def get_rare_enemy_quest_name(x, y):
    x = int(x)
    if x == 0:
        return 'Campaign / Avenue / Ruins Quests'
    else:
        return RARE_ENEMY_QUESTS[y] + str(x)

def csv_to_dict(path, index=None, value_key=None, tabs=False):
    with open(path, 'r', newline='', encoding='utf-8') as csvfile:
        if tabs:
            reader = csv.DictReader(csvfile, dialect='excel-tab')
        else:
            reader = csv.DictReader(csvfile)
        keys = reader.fieldnames

        if not index:
            index = keys[0] # get first key as index
        if not value_key and len(keys) == 2:
            # If not otherwise specified, load 2 column files as dict[string] = string
            value_key = keys[1] # get second key
        if value_key:
            return {row[index]: row[value_key] for row in reader if row[index] != '0'}
        else:
            # load >2 column files as a dict[string] = OrderedDict
            return {row[index]: row for row in reader if row[index] != '0'}

def parse(input_dir, output_dir='EnemyData',
          manual_map_file_path='./ManualMapRelations.txt', text_label_dict=None):
    global MANUAL_QUEST_MAP, TEXT_LABEL 
    enemy_param = csv_to_dict(os.path.join(input_dir, 'EnemyParam.txt'), index='_Id')
    enemy_data = csv_to_dict(os.path.join(input_dir, 'EnemyData.txt'), index='_Id')
    enemy_list = csv_to_dict(os.path.join(input_dir, 'EnemyList.txt'), index='_Id')
    weapon_data = csv_to_dict(os.path.join(input_dir, 'WeaponData.txt'), index='_Id', value_key='_Name')
    MANUAL_QUEST_MAP = csv_to_dict(manual_map_file_path, tabs=True)
    if text_label_dict:
        TEXT_LABEL = text_label_dict
    else:
        TEXT_LABEL = csv_to_dict(os.path.join(input_dir, 'TextLabel.txt'), tabs=True)

    tribes = defaultdict(list)
    nameless = []
    questless = []
    for enemy_param in enemy_param.values():
        enemy = Enemy(enemy_param, enemy_data, enemy_list, weapon_data)
        add = True
        if not enemy.data['Name']:
            nameless.append(enemy)
            add = False
        if not enemy.data['MissionType']:
            questless.append('{}: {}'.format(enemy_param['_ParamGroupName'], enemy))
            add = False
        if add:
            tribes[enemy.data['Tribe']].append(enemy)

    os.makedirs(output_dir, exist_ok=True)

    for tribe, enemies in tribes.items():
        output_path = os.path.join(output_dir, tribe + '.txt')
        print(output_path)
        # Sort the enemies alphabetically by name
        enemies.sort(key=lambda x: x.data.get('Name', ''))
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write('\n'.join((str(e) for e in enemies)))

    if nameless or questless:
        with open(os.path.join(output_dir, 'MISSING_NAMES.txt'), 'w', encoding='utf-8') as outfile:
            if nameless:
                outfile.write('Missing Enemy Names\n')
                outfile.write('===================\n')
                outfile.write('\n'.join((str(e) for e in nameless)))
                outfile.write('\n\n')
            if questless:
                outfile.write('Missing Quest Name Mapping\n')
                outfile.write('==========================\n')
                outfile.write('\n'.join((str(e) for e in questless)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Enemy CSV data into Wikitext.')
    parser.add_argument('-i', type=str, help='directory of input text files  (default: ./)', default='./')
    parser.add_argument('-o', type=str, help='directory of output text files  (default: ./EnemyData)', default='./EnemyData')
    parser.add_argument('-map', type=str, help='path to ManualMapRelations.txt  (default: ./)', default='./')

    args = parser.parse_args()
    input_dir = args.i
    output_dir = args.o
    map_file = os.path.join(args.map, 'ManualMapRelations.txt')
    parse(input_dir, output_dir, map_file)