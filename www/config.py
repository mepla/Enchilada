__author__ = 'Mepla'

import logging
import json

config_path = '/etc/enchilada/config.josn'

default_configs = {
    "debug_mode": True,
    "LOGLEVEL": "DEBUG",
    "DATABASES": {
        "neo4j": {
            "username": "neo4j",
            "password": "Echomybiz",
            "host": "52.10.54.183",
            "port": 7474
        },
        "mongodb": {
            "host": "52.10.54.183",
            "port": 27017
        }
    }
}


try:
    configs = json.load(config_path)
except Exception as exc:
    logging.warning('Could not load config file ({}). Default configs loaded.'.format(config_path))
    configs = default_configs