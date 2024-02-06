# Brat package

Update and initialize submodules if cloning the repository
```bash
git submodule update --init --recursive
```

## Installation from git

```bash
python3.8 -m venv venv

source venv/bin/activate

# python3.8 -m pip install .
python3.8 -m pip install git+https://github.com/melissayan/brat-package.git

# Confirm the executable is placed in the path
which brat
```

## How to run brat

Create a test directory that will be used for annotation data:

```bash
mkdir -pv test
cd test

BRAT_PASSWORD=pass4 brat 8081
```

## Environment Variables

Defaults:

```bash
BRAT_DATA_DIR=$(cwd)/annotation-data
BRAT_WORK_DIR=${HOME}/.brat
BRAT_USER=admin
BRAT_PASSWORD=
BRAT_AUTH_ENABLED='true'
BRAT_LOG_REQUESTS='true'
BRAT_MAX_SEARCH_RESULT_NUMBER=1000
BRAT_DEBUG='false'
BRAT_ADMIN_CONTACT_EMAIL='admin@example.com'
BRAT_HOST=''  # empty string means 0.0.0.0
BRAT_PORT=8081
```

All the variables can be overriden if set exporter before running `brat`.

If using `BRAT_AUTH_ENABLED=true` make sure to set `BRAT_PASSWORD`.

Example of disabling login:

```bash
BRAT_AUTH_ENABLED=false brat
```
