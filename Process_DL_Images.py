#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image
import os
import re
import copy
from shutil import copyfile, rmtree
import argparse

ALPHA_TYPES = ('A', 'alpha', 'alphaA8')
YCbCr_TYPES = ('Y', 'Cb', 'Cr')
EXT = '.png'
PORTRAIT_SUFFIX = '_portrait'
WYRMPRINT_ALPHA = 'Wyrmprint_Alpha.png'
CATEGORY_REGEX = {
    'Ability_Icons': re.compile(r'^Icon_Ability_\d{7}$'),
    'Skill_Icons': re.compile(r'^Icon_Skill_\d{3}$'),
    'Character_Portrait_Images': re.compile(r'^1\d{5}_\d{2}_r\d{2}_portrait$'),
    'Character_Icon_Images': re.compile(r'^1\d{5}_\d{2}_r\d{2}$'),
    'Crafting_Banner_Images': re.compile(r'^CraftTop_\d{8}$'),
    'Dragon_Images': re.compile(r'^2\d{5}_\d{2}_portrait$'),
    'Dragon_Icons': re.compile(r'^2\d{5}_\d{2}$'),
    'Full-Screen_Art': re.compile(r'^mainstory_\d{6}_(?:\d+_)?base_portrait$'),
    'Weapon_Icons': re.compile(r'^3\d{5}_\d{2}_\d{5}$'),
    'Wyrmprint_Images': re.compile(r'^4\d{5}_\d{2}_portrait$'),
    'Wyrmprint Icons': re.compile(r'^4\d{5}_\d{2}$'),
    'Facility_Images': re.compile(r'^TW\d{2}_\d{6}_IMG_\d{2}_\d{2}$'),
    'Story_Art': re.compile(r'^\d+_\d{2}_base_portrait$'),

    'Summon_Showcase_Banner_Images': re.compile(r'^Summon_(Switch|Top)_Banner$'),
    'Event_Banners': re.compile(r'^EventQuestMenu(List|Top)\d{2}$'),
}
CATEGORY_NAME_FORMATS = {
    'Summon_Showcase_Banner_Images': {
        'Switch': 'Banner_Summon_Showcase_{}',
        'Top': '{}_Summon_Top_Banner'
    },
    'Event_Banners': {
        'List': 'Banner_{}',
        'Top': 'Banner_Top_{}'
    }
}
CATEGORY_EXTRA = ('Misc_Icon', 'Extra')


image_name_pattern_alpha = re.compile(r'^(.*?)(_(A|alpha|alphaA8))?( #(\d+))?$')
image_name_pattern_YCbCr = re.compile(r'^(.*?)_(Y|Cb|Cr)$')
def split_image_name(file_name):
    # format basename_channel(YCbCr)
    matches = image_name_pattern_YCbCr.match(file_name)
    if matches:
        base_name, _ = matches.groups()
        return base_name, 'YCbCr', 0
    # format basename_channel(Alpha) #hash_tag
    matches = image_name_pattern_alpha.match(file_name)
    if matches:
        base_name, _, channel, _, hash_tag = matches.groups()
        channel = 'base' if channel is None else channel
        hash_tag = 0 if hash_tag is None else int(hash_tag)
        return base_name, channel, hash_tag
    else:
        return file_name, 'base', 0

def merge_image_name(base_name, channel, hash_tag):
    image_name = base_name
    if channel != 'base':
        image_name += '_' + channel
    if hash_tag != 0:
        image_name += ' #' + str(hash_tag)
    image_name += EXT
    return image_name

def build_image_dict(current_dir, images={}):
    # TODO: maybe glob?
    if not os.path.exists(current_dir):
        return None
    for f in os.listdir(current_dir):
        fp = '{}/{}'.format(current_dir, f)
        if os.path.isdir(fp):
            build_image_dict(fp, images)
        else:
            file_name, file_ext = os.path.splitext(f)
            if file_ext != EXT:
                continue
            base_name, channel, hash_tag = split_image_name(file_name)
            if current_dir not in images:
                images[current_dir] = {}
            if base_name not in images[current_dir]:
                images[current_dir][base_name] = {}
            if channel not in images[current_dir][base_name]:
                images[current_dir][base_name][channel] = []
            images[current_dir][base_name][channel].append(hash_tag)
    return images

def filter_image_dict(images):
    no_merge = {}
    ref = copy.deepcopy(images)
    for dir_name in ref:
        for base_name in ref[dir_name]:
            if len(ref[dir_name][base_name]) == 1 and 'YCbCr' not in ref[dir_name][base_name]:
                if dir_name not in no_merge:
                    no_merge[dir_name] = {}
                no_merge[dir_name][base_name] = images[dir_name][base_name]
                del images[dir_name][base_name]
    return images, no_merge

def print_image_dict(images, paths=True):
    for d in images:
        print(d)
        for i in images[d]:
            if paths:
                for c in images[d][i]:
                    for h in images[d][i][c]:
                        print('\t', merge_image_name(i, c, h))
            else:
                print(i, '\n\t', images[d][i])

def find_best_alpha(merged):
    best = []
    best_w, best_h = -1, -1
    for key in merged:
        w, h = merged[key].size
        if w > best_w and h >= best_h:
            best_w, best_h = w, h
    for key in merged:
        w, h = merged[key].size
        if w >= best_w and h >= best_h:
            best.append(merged[key])
    return best


def merge_alpha(directory, base_name, alpha_type, base_tags, alpha_tags):
    merged = {}
    nearest_pair = {}
    for bh in base_tags:
        for ah in alpha_tags:
            if bh not in nearest_pair or abs(bh - ah) < abs(bh - nearest_pair[bh]):
                nearest_pair[bh] = ah

    for bh, ah in nearest_pair.items():
        try:
            base_img = Image.open('{}/{}'.format(directory, merge_image_name(base_name, 'base', bh)))
            alph_img = Image.open('{}/{}'.format(directory, merge_image_name(base_name, alpha_type, ah)))
        except Exception:
            print(bh, ah)
            print('ERR: {}/{}'.format(directory, merge_image_name(base_name, alpha_type, ah)))
        if base_img.size != alph_img.size:
            continue
        try:
            r, g, b, _ = base_img.split()
        except:
            r, g, b = base_img.split()
        if alpha_type == 'alphaA8':
            _, _, _, a = alph_img.split()
        else:
            a = alph_img.convert('L')
        merged[(bh, ah)] = Image.merge("RGBA", (r,g,b,a))

    return merged

def merge_YCbCr(directory, base_name, unique_alpha=False):
    Y_img = Image.open('{}/{}'.format(directory, merge_image_name(base_name, 'Y', 0)))
    _, _, _, Y = Y_img.convert('RGBA').split()
    Cb = Image.open('{}/{}'.format(directory, merge_image_name(base_name, 'Cb', 0))).convert('L').resize(Y_img.size, Image.ANTIALIAS)
    Cr = Image.open('{}/{}'.format(directory, merge_image_name(base_name, 'Cr', 0))).convert('L').resize(Y_img.size, Image.ANTIALIAS)
    if unique_alpha:
        a = Image.open('{}/{}'.format(directory, merge_image_name(base_name, 'alpha', 0))).convert('L')
    elif Y_img.size == (1024, 1024):
        a = Image.open(WYRMPRINT_ALPHA).convert('L')
    else:
        a = None
    if a is not None:
        r, g, b = Image.merge("YCbCr", (Y, Cb, Cr)).convert('RGB').split()
        return Image.merge("RGBA", (r, g, b, a))
    else:
        return Image.merge("YCbCr", (Y, Cb, Cr)).convert('RGB')    

def merge_all_images(images):
    merged_images = {}

    for d in images:
        for i in images[d]:
            m = {}
            if 'base' in images[d][i]:
                a_res = {}
                for alpha in ALPHA_TYPES:
                    if alpha in images[d][i]:
                        a_res = {**a_res, **merge_alpha(d, i, alpha, images[d][i]['base'], images[d][i][alpha])}
                if len(a_res) > 0:
                    # m['alpha'] = find_best_alpha(a_res)
                    m['alpha'] = sorted(a_res.values(), key=(lambda x: x.size[0]), reverse=True)
            if 'YCbCr' in images[d][i]:
                m['YCbCr'] = merge_YCbCr(d, i, unique_alpha=('alpha' in images[d][i]))
            if len(m) > 0:
                if d not in merged_images:
                    merged_images[d] = {}
                merged_images[d][i] = m

    return merged_images

def match_category(file_name, file_size=None):
    for category, pattern in CATEGORY_REGEX.items():
        res = pattern.match(file_name)
        if res:
            if len(res.groups()) > 0:
                return category, CATEGORY_NAME_FORMATS[category][res.group(1)]
            return category, None
    # didn't match specific category, but it is likely to be an icon since it's 160x160
    if file_size == (160, 160):
        return 'Misc_Icon', None
    return '', None

def create_out_sub_dir(directory, in_dir, out_dir, make_categories=False):
    if directory == in_dir:
        out_sub_dir = out_dir
    else:
        out_sub_dir = out_dir + '/' + list(filter(bool, directory.replace(in_dir, '').split('/')))[0]
    if not os.path.exists(out_sub_dir):
        os.makedirs(out_sub_dir)
    if make_categories:
        for category in CATEGORY_REGEX:
            if not os.path.exists(out_sub_dir + '/' + category):
                os.makedirs(out_sub_dir + '/' + category)
        if not os.path.exists(out_sub_dir + '/Misc_Icon'):
            os.makedirs(out_sub_dir + '/Misc_Icon')
    return out_sub_dir

def delete_empty_subdirectories(directory):
    if directory:
        for f in os.listdir(directory):
            try:
                os.rmdir(directory + '/' + f)
            except:
                pass

def save_merged_images(merged_images, in_dir, out_dir):
    for d in merged_images:
        # delete empty catagory folders in the previous directory
        out_sub_dir = create_out_sub_dir(d, in_dir, out_dir, make_categories=True)
        for i in merged_images[d]:
            for t in merged_images[d][i]:
                if t == 'YCbCr':
                    img = merged_images[d][i][t]
                    img_name = i + '_portrait'
                    category, _ = match_category(img_name, img.size)
                    save_path = '{}/{}/{}{}'.format(out_sub_dir, category, img_name, EXT)
                    img.save(save_path)
                elif t == 'alpha':
                    max_w, max_h = merged_images[d][i][t][0].size
                    for idx, img in enumerate(merged_images[d][i][t]):
                        category, name_format = match_category(i, img.size)
                        img_name = i
                        if name_format is not None:
                            img_name = name_format.format('#{}#'.format(str(idx)))
                        if max_w > img.size[0] and max_h > img.size[1]:
                            save_path = '{}/{}/{} (Small){}'.format(out_sub_dir, category, img_name, EXT)
                        else:
                            save_path = '{}/{}/{}{}'.format(out_sub_dir, category, img_name, EXT)
                        if os.path.exists(save_path) and os.path.isfile(save_path):
                            save_path = '{}#{}{}'.format(save_path.replace(EXT, ''), idx, EXT)
                        img.save(save_path)
        delete_empty_subdirectories(out_sub_dir)


def copy_Not_Merged_images(Not_Merged, in_dir, out_dir):
    for d in Not_Merged:
        out_sub_dir = create_out_sub_dir(d, in_dir, out_dir, make_categories=True)
        # if not os.path.exists(out_sub_dir + '/Not_Merged'):
        #     os.makedirs(out_sub_dir + '/Not_Merged')
        for i in Not_Merged[d]:
            for c in Not_Merged[d][i]:
                for h in Not_Merged[d][i][c]:
                    category, name_format = match_category(i)
                    if name_format is not None:
                        img_name = name_format.format(h) + EXT
                    else:
                        category = ''
                        img_name = merge_image_name(i, c, h)
                    copyfile(d + '/' + merge_image_name(i, c, h), out_sub_dir + '/' + category + '/' + img_name)
        delete_empty_subdirectories(out_sub_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge alpha and YCbCr images.')
    parser.add_argument('-i', type=str, help='directory of input images', default='./')
    parser.add_argument('-o', type=str, help='directory of output images  (default: ./output-img)', default='./output-img')
    parser.add_argument('--delete_old', help='delete older output files', dest='delete_old', action='store_true')
    parser.add_argument('-wpa', type=str, help='path to Wyrmprint_Alpha.png.', default='Wyrmprint_Alpha.png')

    args = parser.parse_args()
    if args.delete_old:
        if os.path.exists(args.o):
            try:
                rmtree(args.o)
                print('Deleted old {}\n'.format(args.o))
            except Exception:
                print('Could not delete old {}\n'.format(args.o))
    if not os.path.exists(args.o):
        os.makedirs(args.o)

    WYRMPRINT_ALPHA = args.wpa
    images = build_image_dict(args.i)
    images, Not_Merged = filter_image_dict(images)

    merged = merge_all_images(images)
    save_merged_images(merged, args.i, args.o)
    copy_Not_Merged_images(Not_Merged, args.i, args.o)

    print('\nThe following images were copied to {} without merging:'.format(args.o))
    print_image_dict(Not_Merged)
