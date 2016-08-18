import unittest
import sys
import os
import shutil
import logging

try:
    from uditransfer import monitor
    from uditransfer import configuration
    from uditransfer import util
except:
    sys.path.append("..")
    from uditransfer import monitor
    from uditransfer import configuration
    from uditransfer import util

class MonitorTestCase(unittest.TestCase):

    def setUp(self):
        self.flag = True

        self.folder_sample = "../sample"
        self.folder_hl7 = "../sample/HL7"
        self.folder_acks = "../sample/ACKs"
        self.config = configuration.monitor_configuration("../sample/sample_config.ini")

    def test_sample_data(self):
        assert(os.path.exists(self.folder_sample))
        assert(os.path.exists(self.folder_hl7))
        assert(os.path.exists(self.folder_acks))
        assert(len(list(os.listdir(self.folder_hl7)))>0)
        assert (len(list(os.listdir(self.folder_acks))) > 0)
        assert(os.path.exists(self.config.folder_localinbox))

    def test_process_orphan_acks(self):
        assert(os.path.exists(self.config.folder_remoteorphan))

        ack_files = self.get_file_list(self.folder_acks)
        for ack in ack_files:
            src_file = os.path.join(self.folder_acks, ack)
            target_file = os.path.join(self.config.folder_remoteorphan, ack)
            shutil.copyfile(src_file, target_file)

        hl7_files = self.get_file_list(self.folder_hl7)
        ack1_flag = ""
        for hl7 in hl7_files:
            if hl7 in ack_files:
                src_file = os.path.join(self.folder_hl7, hl7)
                target_file = os.path.join(self.config.folder_ack1flag, hl7)
                shutil.copyfile(src_file, target_file)
                ack1_flag = target_file

        orphan_files = self.get_file_list(self.config.folder_remoteorphan)
        assert(len(orphan_files) == len(ack_files))

        monitor.process_orphan_acks(self.config)
        monitor.process_orphan_acks(self.config)
        monitor.process_orphan_acks(self.config)

        local_inbox_files = self.get_file_list(self.config.folder_localinbox)
        assert(len(local_inbox_files) == len(ack_files))
        assert(not os.path.exists(ack1_flag))



    def test_process_hl7_message(self):
        assert(self.config)
        assert(self.config.folder_localoutbox)
        onlyfiles = self.get_file_list(self.folder_hl7)

        for hl7_file in onlyfiles:
            srcfile = os.path.join(self.folder_hl7, hl7_file)
            tgtfile = os.path.join(self.config.folder_localoutbox, hl7_file)
            shutil.copyfile(srcfile, tgtfile)
            assert(os.path.exists(tgtfile))

        total_files = len(onlyfiles)

        monitor.process_hl7_message(self.config)

        files_in_localoutbox = monitor.get_file_list(self.config.folder_localoutbox)
        assert(len(files_in_localoutbox)==0)

        files_in_ac1flag = monitor.get_file_list(self.config.folder_ack1flag)
        assert(len(files_in_ac1flag) == total_files)

        files_in_remoteoutbox = monitor.get_file_list(self.config.folder_remoteoutbox)
        assert(len(files_in_remoteoutbox) == total_files)

    def get_file_list(self, folder):
        onlyfiles = [f for f in os.listdir(folder)
                     if os.path.isfile(os.path.join(folder, f))]
        return onlyfiles

if __name__=="__main__":
    util.initialize_logger("../temp/logs/")
    unittest.main()

