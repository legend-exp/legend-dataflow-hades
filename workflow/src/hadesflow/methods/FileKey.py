"""
This module contains classes to convert between keys and files using the patterns defined in patterns.py
"""

import re
from collections import namedtuple
from pathlib import Path

import snakemake as smk

from .patterns import (
    get_pattern_tier,
    key_pattern,
    processing_pattern,
)
from dbetto.time import unix_time
from .utils import convert_to_legend_timestamp, convert_to_legend_run

# key_pattern -> key


def regex_from_filepattern(filepattern):
    f = []
    wildcards = []
    last = 0
    for match in re.compile(r"\{(?P<name>[\w]+)\}").finditer(filepattern):
        f.append(re.escape(filepattern[last : match.start()]))
        wildcard = match.group("name")
        if wildcard in wildcards:
            f.append(f"(?P={wildcard})")
        else:
            wildcards.append(wildcard)
            if wildcard == "ext":
                f.append(
                    f"(?P<{wildcard}>.*)"
                )  # this means ext will capture everything after 1st dot
            else:
                f.append(f"(?P<{wildcard}>" + r"[^\.\/]+)")
        last = match.end()
    f.append(re.escape(filepattern[last:]))
    f.append("$")
    return "".join(f)


class FileKey(
    namedtuple("FileKey", ["experiment", "detector", "measurement", "run", "timestamp"])
):
    __slots__ = ()

    re_pattern = "(-(?P<experiment>[^-]+)(\\-(?P<detector>[^-]+)(\\-(?P<measurement>[^-]+)(\\-(?P<run>[^-]+)(\\-(?P<timestamp>[^-]+))?)?)?)?)?$"
    key_pattern = key_pattern()

    @property
    def name(self):
        return f"{self.experiment}-{self.detector}-{self.measurement}-{self.run}-{self.timestamp}"

    @property
    def key(self):
        return f"-{self.name}"

    def _list(self):
        return list(self)

    def items(self):
        return self._asdict().items()

    @property
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    @classmethod
    def from_string(cls, key_string):
        return cls.get_filekey_from_pattern(key_string)

    @classmethod
    def get_filekey_from_filename(cls, filename):
        return cls.get_filekey_from_pattern(filename, processing_pattern())

    @classmethod
    def get_filekey_from_pattern(cls, filename, pattern=None):
        key_pattern_rx = re.compile(
            regex_from_filepattern(str(cls.key_pattern) if pattern is None else str(pattern))
        )
        if key_pattern_rx.match(filename) is None:
            return None
        else:
            d = key_pattern_rx.match(filename).groupdict()
            for entry in list(d):
                if entry not in cls._fields:
                    d.pop(entry)
            for wildcard in cls._fields:
                if wildcard not in d:
                    d[wildcard] = "*"
            if d["timestamp"][-1] != "Z":
                d["timestamp"] = convert_to_legend_timestamp(d["timestamp"])
            if "run" in d["run"]:
                d["run"] = convert_to_legend_run(d["run"])
            return cls(**d)

    @classmethod
    def unix_time_from_string(cls, value):
        key_class = cls.from_string(value)
        return unix_time(key_class.timestamp)

    def get_unix_timestamp(self):
        return unix_time(self.timestamp)

    @classmethod
    def parse_keypart(cls, keypart):
        keypart_rx = re.compile(cls.re_pattern)
        d = keypart_rx.match(keypart).groupdict()
        for key in d:
            if d[key] is None:
                d[key] = "*"
        return cls(**d)

    def get_path_from_filekey(self, pattern, **kwargs):
        if kwargs is None:
            return smk.io.expand(pattern, **self._asdict())
        else:
            for entry, value in kwargs.items():
                if isinstance(value, dict):
                    if len(next(iter(set(value).intersection(self._list())))) > 0:
                        kwargs[entry] = value[next(iter(set(value).intersection(self._list())))]
                    else:
                        kwargs.pop(entry)
            return smk.io.expand(pattern, **self._asdict(), **kwargs)

    # get_path_from_key
    @classmethod
    def get_full_path_from_filename(cls, filename, pattern, path_pattern):
        return cls.get_path_from_filekey(
            cls.get_filekey_from_pattern(filename, pattern), path_pattern
        )

    @staticmethod
    def tier_files(setup, keys, tier):
        fn_pattern = get_pattern_tier(setup, tier)
        files = []
        for line in keys:
            tier_filename = FileKey.get_full_path_from_filename(
                line, FileKey.key_pattern, fn_pattern
            )
            files += tier_filename
        return files


class ProcessingFileKey(FileKey):
    _fields = (*FileKey._fields, "processing_step")
    key_pattern = processing_pattern()

    def __new__(cls, experiment, detector, measurement, run, timestamp, processing_step):
        self = super().__new__(cls, experiment, detector, measurement, run, timestamp)
        if "_" in processing_step:
            splits = processing_step.split("_", 2)
            self.processing_type = splits[0]
            self.tier = splits[1]
            if len(splits) > 2:
                self.identifier = splits[2]
            else:
                self.identifier = None
        else:
            self.processing_type = processing_step
            self.tier = None
            self.identifier = None

        return self

    def _list(self):
        return [*super()._list(), self.processing_step]

    def _asdict(self):
        dic = super()._asdict()
        dic["processing_step"] = self.processing_step
        return dic

    @property
    def processing_step(self):
        if self.identifier is not None:
            return f"{self.processing_type}_{self.tier}_{self.identifier}"
        else:
            return f"{self.processing_type}_{self.tier}"

    @property
    def name(self):
        return f"{super().name}-{self.processing_step}"

    def get_path_from_filekey(self, pattern, **kwargs):
        if isinstance(pattern, Path):
            pattern = str(pattern)
        if not isinstance(pattern, str):
            pattern = pattern(self.tier, self.identifier)
        if kwargs is None:
            return smk.io.expand(pattern, **self._asdict())
        else:
            for entry, value in kwargs.items():
                if isinstance(value, dict):
                    if len(next(iter(set(value).intersection(self._list())))) > 0:
                        kwargs[entry] = value[next(iter(set(value).intersection(self._list())))]
                    else:
                        kwargs.pop(entry)
            return smk.io.expand(pattern, **self._asdict(), **kwargs)
