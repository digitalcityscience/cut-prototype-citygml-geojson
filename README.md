# HCU-Cut CityGMl Converter

## Run locally

follow these instructions if you want to run the code locally, for running all commands from a docker container see below

### Requirements
Install requiremnts

```bash
python3 -m pip install -r requirements.txt
```

### Downloading Data

To get started download and extract the citygml dataset:

```bash
./download_gml.sh
```
after this all xml files should be in `./data/LoD2-DE_HH_2023-04-01`

### Convert Data

run the conversion script to get geojson files for each surface type in folder `./data/out`

```bash
python3 src/main.py convert -d ./data/LoD2-DE_HH_2023-04-01 -o ./data/out
```

### Create DB

create a new sqlite Database from all geosjon files

```bash
python3 src/main.py createdb -p ./data/out/ -d ./data/out/features.db
```

### Run server

start server with a geojson features endpoint:

```bash
python3 src/main.py serve -d ./data/out/features.db -p 5000
```

### Query endpoint

with running server features can be queried from the endpoint:

```bash
curl "http://localhost:5000/features" > /tmp/out.json
curl "http://localhost:5000/features?&surface_type=ground" > /tmp/out.json
curl "http://localhost:5000/features?&surface_type=ground&limit=1000&startindex=1000" > /tmp/out.json
curl "http://localhost:5000/features?bbox=9.966831,53.561622,10.057812,53.611146&surface_type=ground&limit=100" > /tmp/out.json
curl "http://localhost:5000/features?&properties=id,lage" > /tmp/out.json
```

api doc (swagger) can be found under `http://localhost:5000`

### Run tests
Install requiremnts

```bash
python3 -m pip install -r requirements_test.txt
```

Then run all test:
```bash
cd tests
pytest
```


## Docker

### build

```bash
docker build -t cut .
```

### run

use all comannds like above but with `src/run.py` which passed all arguments to the correct docker command, e.g.

```bash
python src/run.py serve
```
