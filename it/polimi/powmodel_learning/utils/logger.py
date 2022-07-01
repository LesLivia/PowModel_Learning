import configparser
from enum import Enum
import sys

config = configparser.ConfigParser()
config.sections()
config.read('./resources/config/config.ini')
config.sections()

TO_FILE = True if config['DEFAULT']['TO_FILE'] == 'True' else False
SAVE_PATH = config['RESULTS ANALYSIS']['REP_PATH']

SHA_NAME = sys.argv[2]


class LogLevel(Enum):
    INFO = 1
    DEBUG = 2
    WARNING = 3
    ERROR = 4
    MSG = 99

    def __str__(self):
        if self.value == 1:
            return 'INFO'
        elif self.value == 2:
            return 'DEBUG'
        elif self.value == 3:
            return 'WARNING'
        elif self.value == 4:
            return 'ERROR'
        elif self.value == 99:
            return 'MSG'
        else:
            return ''

    @staticmethod
    def parse_str(s):
        if s == 'INFO':
            return LogLevel.INFO
        elif s == 'DEBUG':
            return LogLevel.DEBUG
        elif s == 'WARNING':
            return LogLevel.WARNING
        elif s == 'ERROR':
            return LogLevel.ERROR
        elif s == 'MSG':
            return LogLevel.MSG
        else:
            return None


# INIT LOGGING LEVEL BASED ON CONFIG FILE
if 'LoggingLevel' in config['DEFAULT']:
    MIN_LOG_LEVEL = LogLevel.parse_str(config['DEFAULT']['LoggingLevel']).value
else:
    MIN_LOG_LEVEL = LogLevel.WARNING.value


#

class Logger:
    def __init__(self, speaker: str):
        self.speaker = speaker
        self.format = "[{}] ({})\t{}"
        with open(SAVE_PATH.format(SHA_NAME), 'w') as log:
            log.truncate(0)

    def info(self, msg):
        if MIN_LOG_LEVEL <= LogLevel.INFO.value:
            s = self.format.format(self.speaker, str(LogLevel.INFO), msg)
            print(s)
            if TO_FILE:
                with open(SAVE_PATH.format(SHA_NAME), 'a') as log:
                    log.write(s + '\n')

    def debug(self, msg):
        if MIN_LOG_LEVEL <= LogLevel.DEBUG.value:
            s = self.format.format(self.speaker, str(LogLevel.DEBUG), msg)
            print(s)
            if TO_FILE:
                with open(SAVE_PATH.format(SHA_NAME), 'a') as log:
                    log.write(s + '\n')

    def warn(self, msg):
        if MIN_LOG_LEVEL <= LogLevel.WARNING.value:
            s = self.format.format(self.speaker, str(LogLevel.WARNING), msg)
            print(s)
            if TO_FILE:
                with open(SAVE_PATH.format(SHA_NAME), 'a') as log:
                    log.write(s + '\n')

    def error(self, msg):
        if MIN_LOG_LEVEL <= LogLevel.ERROR.value:
            s = self.format.format(self.speaker, str(LogLevel.ERROR), msg)
            print(s)
            if TO_FILE:
                with open(SAVE_PATH.format(SHA_NAME), 'a') as log:
                    log.write(s + '\n')

    def msg(self, msg):
        if MIN_LOG_LEVEL <= LogLevel.MSG.value:
            s = self.format.format(self.speaker, str(LogLevel.MSG), msg)
            print(s)
            if TO_FILE:
                with open(SAVE_PATH.format(SHA_NAME), 'a') as log:
                    log.write(s + '\n')
