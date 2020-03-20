import argparse
import dataclasses
import errno
import json
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Callable

from Asset_Extract import check_target_path


def to_frames(duration: float) -> int:
    return round(duration * 60)


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
    label: str = ''
    hit_delete: bool = False
    name: str = 'Hit'

    def __str__(self):
        return f'[{Event.__str__(self)}] Hit: label {self.label}, ' \
               f'duration {self.duration:.3f} : {to_frames(self.duration)}f, ' \
               f'interval {self.interval:.3f} : {to_frames(self.interval)}f'


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
    CommandType.FIRE_STOCK_BULLET_DATA: fire_stock_bullet_data
}


def parse_action(path: str) -> Action:
    with open(path) as f:
        raw = json.load(f)
        action = [gameObject['_data'] for gameObject in raw if '_data' in gameObject.keys()]
        data: List[Event] = []
        for command in action:
            command_type = CommandType(command['commandType'])
            if command_type in PROCESSORS.keys():
                data.extend(PROCESSORS[command_type](command))
        return Action(
            id=int(Path(path).stem.split('_')[1]),
            timeline=sorted(data)
        )


def process_action(in_path: str, out_path: str, mode: str):
    action = parse_action(in_path)
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
        for root, _, files in os.walk(in_path):
            for file_name in [f for f in files if file_filter.match(f) and f.startswith('PlayerAction')]:
                file_in_path = os.path.join(root, file_name)
                file_out_path = os.path.join(out_path, Path(file_name).with_suffix(extension))
                process_action(file_in_path, file_out_path, mode)
    else:
        if os.path.isdir(out_path):
            out_path = os.path.join(out_path, Path(in_path).with_suffix(extension).name)
        process_action(in_path, out_path, mode)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract asset files.')
    parser.add_argument('-i', type=str, help='input file or dir', default='./extract')
    parser.add_argument('-o', type=str, help='output file dir', default='./actions')
    parser.add_argument('-m', type=str, help='mode: default "json", "simple")', default='json')
    args = parser.parse_args()
    process_actions(args.i, args.o, args.m)
