import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import xmltodict
from lxml.etree import canonicalize

TEST_DIR = Path(__file__).resolve().parent
TEST_DATA_DIR = TEST_DIR / "data"


@contextmanager
def tmp_cwd():
    """Create a temporary directory and temporarily change the current working directory."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory(dir=TEST_DIR) as tmp_dir:
        try:
            os.chdir(tmp_dir)
            yield tmp_dir
        finally:
            os.chdir(original_cwd)


def xml_to_regular_dict(filepath):
    with filepath.open("rb") as f:
        # use json to convert from OrderedDict to regular dict
        return json.loads(json.dumps(xmltodict.parse(f)))


def canonicalize_xml(filepath, with_comments=True):
    with filepath.open("r") as f:
        return canonicalize(f.read(), with_comments=with_comments)
