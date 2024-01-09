import os
import pathmagic
import tempfile
from convert import extract_all_surface_types, convert

assert pathmagic


def test_extract_all_surface_types(snapshot):
    df = extract_all_surface_types("./")
    assert df["ground"].to_json() == snapshot
    assert df["roof"].to_json() == snapshot


def test_convert(snapshot):
    tmp = tempfile.TemporaryDirectory()
    dir = tmp.name
    convert("./", dir)
    assert open(os.path.join(dir, "ground.geojson")).read() == snapshot
    assert open(os.path.join(dir, "roof.geojson")).read() == snapshot
