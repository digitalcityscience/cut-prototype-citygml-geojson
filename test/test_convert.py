import os
import pathmagic
import tempfile
from convert import extract_all_surface_types, convert

assert pathmagic


def test_extract_all_surface_types(snapshot) -> None:
    df = extract_all_surface_types("./data1")
    assert df["ground"].to_json() == snapshot
    assert df["roof"].to_json() == snapshot


def test_convert(snapshot) -> None:
    tmp = tempfile.TemporaryDirectory()
    dir = tmp.name
    convert("./data1", dir)
    assert open(os.path.join(dir, "ground.geojson")).read() == snapshot
    assert open(os.path.join(dir, "roof.geojson")).read() == snapshot


def test_convert_surface_with_interior(snapshot) -> None:
    tmp = tempfile.TemporaryDirectory()
    dir = tmp.name
    convert("./data2", dir)
    assert open(os.path.join(dir, "roof.geojson")).read() == snapshot
