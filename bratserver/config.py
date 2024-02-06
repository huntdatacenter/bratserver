# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; coding: utf-8; -*-
# This configuration file specifies the global setup of the brat
# server. It is recommended that you use the installation script
# instead of editing this file directly. To do this, run the following
# command in the brat directory:
#
#     ./install.sh
#
# if you wish to configure the server manually, you will first need to
# make sure that this file appears as config.py in the brat server
# root directory. If this file is currently named config_template.py,
# you can do this as follows:
#
#     cp config_template.py config.py
#
# you will then need to edit config.py, minimally replacing all
# instances of the string CHANGE_ME with their appropriate values.
from os.path import dirname, join as path_join
import os
# import sys

TRUTHY = ("true", "1", "yes", "on")

def truthy(val):
    """
    Transform string truthy to bool.
    """
    return str(val).lower() in TRUTHY


# Please note that these values MUST appear in quotes, e.g. as in
#
# ADMIN_CONTACT_EMAIL = 'admin@example.com'
# Contact email for users to use if the software encounters errors
ADMIN_CONTACT_EMAIL = os.getenv('BRAT_ADMIN_CONTACT_EMAIL', 'admin@example.com')
# Directories required by the brat server:
#
#     BASE_DIR: directory in which the server is installed
#     DATA_DIR: directory containing texts and annotations (keep separate from BASE_DIR)
#     WORK_DIR: directory that the server uses for temporary files (keep separate from BASE_DIR)
#
# BASE_DIR = dirname(__file__)
BASE_DIR = dirname(__file__)

# Use annotation-data directory inside current working directory
DEFAULT_DATADIR = path_join(os.getcwd(), 'annotation-data')
DATA_DIR = os.getenv('BRAT_DATA_DIR', DEFAULT_DATADIR)

# Work dir stores BRAT server logs and session data
DEFAULT_WORKDIR = path_join(os.getenv('HOME'), '.brat') if os.getenv('HOME') else path_join(BASE_DIR, 'work')
WORK_DIR = os.getenv('BRAT_WORK_DIR', DEFAULT_WORKDIR)
# If you have installed brat as suggested in the installation
# instructions, you can set up BASE_DIR, DATA_DIR and WORK_DIR by
# removing the three lines above and deleting the initial '#'
# character from the following four lines:
#from os.path import dirname, join
#BASE_DIR = dirname(__file__)
#DATA_DIR = path_join(BASE_DIR, 'data')
#WORK_DIR = path_join(BASE_DIR, 'work')
# To allow editing, include at least one USERNAME:PASSWORD pair below.
# To allow anonymous editing, set `USER_PASSWORD = False`.
# The format is the following:
#
#     'USERNAME': 'PASSWORD',
#
# For example, user `editor` and password `annotate`:
#
#     'editor': 'annotate',
BRAT_AUTH_ENABLED = truthy(os.getenv('BRAT_AUTH_ENABLED', True))
if BRAT_AUTH_ENABLED and not os.getenv('BRAT_PASSWORD'):
    raise Exception("Environment variable not set: 'BRAT_PASSWORD'")

USER_PASSWORD = {
    #  (add USERNAME:PASSWORD pairs below this line.)
    os.getenv('BRAT_USER', 'admin'): os.getenv('BRAT_PASSWORD'),
} if BRAT_AUTH_ENABLED else False

########## ADVANCED CONFIGURATION OPTIONS ##########
# The following options control advanced aspects of the brat server
# setup.  It is not necessary to edit these in a basic brat server
# installation.
# MAX_SEARCH_RESULT_NUMBER
# It may be a good idea to limit the max number of results to a search
# as very high numbers can be demanding of both server and clients.
# (unlimited if not defined or <= 0)
MAX_SEARCH_RESULT_NUMBER = int(os.getenv('BRAT_MAX_SEARCH_RESULT_NUMBER', 1000))
# DEBUG
# Set to True to enable additional debug output
DEBUG = truthy(os.getenv('BRAT_DEBUG', False))
# TUTORIALS
# Unauthorised users can create tutorials (but not edit without a login)
TUTORIALS = False
# LOG_LEVEL
# If you are a developer you may want to turn on extensive server
# logging by enabling LOG_LEVEL = LL_DEBUG
LL_DEBUG, LL_INFO, LL_WARNING, LL_ERROR, LL_CRITICAL = list(range(5))
# LOG_LEVEL = LL_WARNING
LOG_LEVEL = LL_DEBUG
# BACKUP_DIR
# Define to enable backups
# from os.path import join
#BACKUP_DIR = join(WORK_DIR, 'backup')
try:
    assert DATA_DIR != BACKUP_DIR, 'DATA_DIR cannot equal BACKUP_DIR'
except NameError:
    pass  # BACKUP_DIR most likely not defined
# SVG_CONVERSION_COMMANDS
# If export to formats other than SVG is needed, the server must have
# a software capable of conversion like inkscape set up, and the
# following must be defined.
# (SETUP NOTE: at least Inkscape 0.46 requires the directory
# ".gnome2/" in the apache home directory and will crash if it doesn't
# exist.)
# SVG_CONVERSION_COMMANDS = [
#    ('png', 'inkscape --export-area-drawing --without-gui --file=%s --export-png=%s'),
#    ('pdf', 'inkscape --export-area-drawing --without-gui --file=%s --export-pdf=%s'),
#    ('eps', 'inkscape --export-area-drawing --without-gui --file=%s --export-eps=%s'),
# ]
### SIMSTRING
# SIMSTRING_EXECUTABLE = ''
SIMSTRING_DEFAULT_UNICODE = True
