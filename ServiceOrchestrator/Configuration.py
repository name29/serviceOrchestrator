"""
Created on Oct 1, 2014
@author: fabiomignini
@author: gabrielecastellano
"""
import configparser
import inspect
import json
import os


class Configuration(object):
    _instance = None
    _AUTH_SERVER = None
    config_file = ''

    def __new__(cls, *args, **kwargs):

        if not cls._instance:
            cls._instance = super(Configuration, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self,cfgfile):
        self.config_file = cfgfile
        if self._AUTH_SERVER is None:
            self.inizialize()

    def inizialize(self):

        config = configparser.RawConfigParser()
        base_folder = \
        os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])).rpartition('/')[0]
        config.read(base_folder + '/' + self.config_file)
        self._LOG_FILE = config.get('log', 'log_file')
        self._VERBOSE = config.getboolean('log', 'verbose')
        self._DEBUG = config.getboolean('log', 'debug')

    @property
    def LOG_FILE(self):
        return self._LOG_FILE
    @property
    def VERBOSE(self):
        return self._VERBOSE
    @property
    def DEBUG(self):
        return self._DEBUG
