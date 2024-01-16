import pathmagic
import pytest
import tempfile
import os
from server import Server
import pandas  # import before freezegun to import errors
from freezegun import freeze_time
from flask import Flask
from flask.testing import FlaskClient
from typing import Generator

from convert import convert
from create_db import create_db

assert pathmagic
assert pandas


def setupdb(dir: str) -> str:
    dbpath = os.path.join(dir, "test.db")
    convert("./data1", dir)
    create_db(dir, dbpath)
    return dbpath


freezer = freeze_time("2024-01-01 12:00:01")
freezer.start()

tmp = tempfile.TemporaryDirectory()
dir = tmp.name

# use this to keep the data dir after test run
# dir = tempfile.mkdtemp()
# print(dir)

dbpath = None


@pytest.fixture
def app() -> Generator[Flask, None, None]:
    global dbpath
    if dbpath is None:
        dbpath = setupdb(dir)
    yield Server(5000, dbpath).app


@pytest.fixture
def client(app) -> FlaskClient:
    return app.test_client()
