import sys
import os

from pathlib import Path

bratserver_path = Path(os.path.dirname(__file__))
BRATSERVER_INSTALLATION_PATH = str(bratserver_path)
# print(BRATSERVER_INSTALLATION_PATH, file=sys.stderr)

BRAT_INSTALLATION_PATH = os.path.join(bratserver_path.parent, 'brat')
# print(BRAT_INSTALLATION_PATH, file=sys.stderr)

os.environ['BRATSERVER_INSTALLATION_PATH'] = BRATSERVER_INSTALLATION_PATH
os.environ['BRAT_INSTALLATION_PATH'] = BRAT_INSTALLATION_PATH

sys.path.append(BRATSERVER_INSTALLATION_PATH)
sys.path.append(os.path.join(BRAT_INSTALLATION_PATH, 'server/src'))

import stats  # noqa


def get_config_py_path():
    """
    Override config.py location
    """
    return os.path.join(BRATSERVER_INSTALLATION_PATH, 'config.py')


stats.get_config_py_path = get_config_py_path

from bratserver.standalone import main  # noqa


def run():
    sys.exit(main(sys.argv))


if __name__ == "__main__":
    run()
