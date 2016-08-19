import sys
import os
import logging
import codecs

from ConfigParser import SafeConfigParser

class monitor_configuration():
    def __init__(self, configuration_file):
        self.folder_localinbox = None
        self.folder_localoutbox = None
        self.folder_remoteinbox = None
        self.folder_remoteoutbox = None
        self.folder_remoteorphan = None
        self.folder_hl7flag = None
        self.folder_ack1flag = None
        self.folder_ack2flag = None
        self.folder_ack3flag = None
        self.folder_tobedeleted = None
        self.folder_logs = None

        self.sleeptime = 100

        self.validate_configuration(configuration_file)

    def __get_log_option(self, log_str, default_log):
        log_dict = {
            'DEBUG':logging.DEBUG,
            'INFO':logging.INFO,
            'WARNING':logging.WARNING,
            'ERROR':logging.ERROR,
            'CRITICAL':logging.CRITICAL
        }

        return log_dict.get(log_str, default_log)

    def validate_configuration(self, configuration_file):
        parser = SafeConfigParser()
        with codecs.open(configuration_file,'r', encoding='utf-8') as cf:
            parser.readfp(cf)

        self.folder_localinbox = parser.get('General','folder_localinbox')
        self.folder_localoutbox = parser.get('General','folder_localoutbox')
        self.folder_remoteinbox = parser.get('General','folder_remoteinbox')
        self.folder_remoteoutbox = parser.get('General','folder_remoteoutbox')
        self.folder_remoteorphan = parser.get('General','folder_remoteorphan')
        self.folder_hl7flag = parser.get('General','folder_hl7flag')
        self.folder_ack1flag = parser.get('General','folder_ack1flag')
        self.folder_ack2flag = parser.get('General','folder_ack2flag')
        self.folder_ack3flag = parser.get('General','folder_ack3flag')
        self.folder_tobedeleted = parser.get('General','folder_tobedeleted')
        self.folder_logs = parser.get('General', 'folder_logs')
        self.stdout_log = self.__get_log_option(parser.get('General', 'stdout_log'), logging.INFO)
        self.all_file_log = self.__get_log_option(parser.get('General', 'all_file_log'), logging.DEBUG)


        self.sleeptime = int(parser.get('General', 'sleeptime'))

        tmp_folder = self.folder_localinbox
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        tmp_folder = self.folder_localoutbox
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        tmp_folder = self.folder_remoteinbox
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        tmp_folder = self.folder_remoteoutbox
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        tmp_folder = self.folder_remoteorphan
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        tmp_folder = self.folder_hl7flag
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        tmp_folder = self.folder_ack1flag
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        tmp_folder = self.folder_ack2flag
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        tmp_folder = self.folder_ack3flag
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        tmp_folder = self.folder_tobedeleted
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        tmp_folder = self.folder_logs
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

if __name__=='__main__':
    my_config = monitor_configuration(r'../sample/sample_config.ini')
    print(my_config.folder_localinbox)

