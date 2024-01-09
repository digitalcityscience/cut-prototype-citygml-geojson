import pathmagic
import pytest
import tempfile
import os
from server import Server
import pandas  # import before freezegun to import errors
from freezegun import freeze_time

from convert import convert
from create_db import create_db

assert pathmagic
assert pandas


def setupdb():
    dbpath = os.path.join(dir, "test.db")
    convert("./", dir)
    create_db(dir, dbpath)
    return dbpath


freezer = freeze_time("2024-01-01 12:00:01")
freezer.start()

tmp = tempfile.TemporaryDirectory()
dir = tmp.name

# use this to keep the data dir after test run
# dir = tempfile.mkdtemp()
# print(dir)

dbpath = setupdb()


@pytest.fixture
def app():
    yield Server(5000, dbpath).app


@pytest.fixture
def client(app):
    return app.test_client()
