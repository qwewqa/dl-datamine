import dataclasses
import json
import os
import re
from typing import Tuple, List, Any

from Asset_Download import check_target_path


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def get_valid_filename(s):
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def run_common(out_dir: str, output: List[Tuple[str, Any]]) -> None:
    for o in output:
        out_path = os.path.join(out_dir, f"{get_valid_filename(o[0])}.json")
        check_target_path(out_path)
        with open(out_path, 'w+', encoding='utf8') as f:
            json.dump(o[1], f, indent=2, cls=EnhancedJSONEncoder)
