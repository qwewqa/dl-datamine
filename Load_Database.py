import os
import argparse

from loader.AssetExtractor import Extractor
from loader.Database import DBManager

from loader.Master import load_master, load_json
from loader.Actions import load_actions
from loader.Motion import load_character_motion, load_dragon_motion

EN = 'en'
JP = 'jp'

MANIFEST_EN = 'enmanifest_with_asset_labels.txt'
MANIFEST_JP = 'jpmanifest_with_asset_labels.txt'

MASTER = 'master'
ACTIONS = 'actions'
CHARACTERS_MOTION = 'characters/motion'
DRAGON_MOTION = 'dragon_motion'

TEXT_LABEL = 'TextLabel.json'
LABEL_PATTERNS_EN = {
    r'^master$': 'master'
}
LABEL_PATTERNS_JP = {
    r'^master$': 'master',
    r'^actions$': 'actions',
    r'^characters/motion': 'characters_motion',
    r'characters/motion/animationclips$': 'characters_motion',
    r'^dragon/motion': 'dragon_motion',
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import data to database.')
    parser.add_argument('--do_prep', help='Do downloading and extracting of assets', action='store_true')
    parser.add_argument('-o', type=str, help='output file', default='dl.sqlite')
    args = parser.parse_args()

    if args.do_prep:
        ex = Extractor(MANIFEST_JP, MANIFEST_EN, stdout_log=True)
        ex.download_and_extract_all(LABEL_PATTERNS_JP, region='jp')
        ex.download_and_extract_all(LABEL_PATTERNS_EN, region='en')
    in_dir = '_extract'

    db = DBManager(args.o)
    load_master(db, os.path.join(in_dir, EN, MASTER))
    load_json(db, os.path.join(in_dir, JP, MASTER, TEXT_LABEL), 'TextLabelJP')
    load_actions(db, os.path.join(in_dir, JP, ACTIONS))
    load_character_motion(db, os.path.join(in_dir, JP, CHARACTERS_MOTION))
    load_dragon_motion(db, os.path.join(in_dir, JP, DRAGON_MOTION))