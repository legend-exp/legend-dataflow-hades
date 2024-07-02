import json
from pathlib import Path

from scripts.util import (
    FileKey,
    subst_vars,
    unix_time,
)
from scripts.util.patterns import get_pattern_tier_dsp
from scripts.util.utils import (
    tier_dsp_path,
    tier_path,
)

testprod = Path(__file__).parent / "dummy_cycle"

with open(str(testprod / "config.json")) as r:
    setup = json.load(r)
subst_vars(setup, var_values={"_": str(testprod)})
setup = setup["setups"]["test"]


def test_util():
    assert tier_path(setup) == str(testprod / "generated/tier")
    assert unix_time("20230101T123456Z") == 1672572896.0


def test_filekey():
    key = FileKey("l200", "p00", "r000", "cal", "20230101T123456Z")
    assert key.name == "l200-p00-r000-cal-20230101T123456Z"
    assert key._list() == ["l200", "p00", "r000", "cal", "20230101T123456Z"]
    keypart = "-l200-p00-r000-cal"
    key = FileKey.parse_keypart(keypart)
    assert key.name == "l200-p00-r000-cal-*"
    key = FileKey.from_string("l200-p00-r000-cal-20230101T123456Z")
    assert key.name == "l200-p00-r000-cal-20230101T123456Z"
    key = FileKey.get_filekey_from_filename("l200-p00-r000-cal-20230101T123456Z-tier_dsp.lh5")
    assert key.name == "l200-p00-r000-cal-20230101T123456Z"
    assert (
        key.get_path_from_filekey(get_pattern_tier_dsp(setup))[0]
        == f"{tier_dsp_path(setup)}/cal/p00/r000/l200-p00-r000-cal-20230101T123456Z-tier_dsp.lh5"
    )
    assert (
        FileKey.get_filekey_from_pattern(
            key.get_path_from_filekey(get_pattern_tier_dsp(setup))[0],
            get_pattern_tier_dsp(setup),
        ).name
        == key.name
    )
