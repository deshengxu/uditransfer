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
        self.cleanse_files()

    def test_sample_data(self):
        assert(os.path.exists(self.folder_sample))
        assert(os.path.exists(self.folder_hl7))
        assert(os.path.exists(self.folder_acks))
        assert(len(list(os.listdir(self.folder_hl7)))>0)
        assert (len(list(os.listdir(self.folder_acks))) > 0)
        assert(os.path.exists(self.config.folder_localinbox))

    def test_detect_ack_file(self):
        ack1_file = r'../sample/ACKs/fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack2_file = r'../sample/ACKs/ACK2_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack3_file = r'../sample/ACKs/ACK3_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        row_message_id = r'fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        row_core_id = r'fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gzCOREID'

        assert(os.path.exists(ack1_file))
        ack1_content = self.read_file_content(ack1_file)
        message_id = monitor.get_messageid_from_ack1_content(ack1_content)
        assert(row_message_id == message_id)

        core_id = monitor.get_coreid_from_ack2_content(ack1_content)
        assert(not core_id)

        assert(os.path.exists(ack2_file))
        ack2_content = self.read_file_content(ack2_file)
        message_id = monitor.get_messageid_from_ack2_content(ack2_content)
        assert(message_id == row_message_id)

        core_id = monitor.get_coreid_from_ack2_content(ack2_content)
        assert(core_id == row_core_id)

        assert(os.path.exists(ack3_file))
        ack3_content = self.read_file_content(ack3_file)
        core_id = monitor.get_coreid_from_ack3_content(ack3_content)
        assert(core_id == row_core_id)

        core_id = monitor.get_coreid_from_ack3_content(ack1_content)
        assert(not core_id)

        core_id = monitor.get_coreid_from_ack3_content(ack2_content)
        assert(not core_id)

    def test_is_valid_hl7_message(self):
        hl7_1_file = r'../sample/HL7/fda_15ff7927-91f6-4fd8-80cb-bbddc6fa0cd1.tar.gz'
        hl7_2_file = r'../sample/HL7/fda_a383c97e-5749-4c0c-aff9-1f3883a34191.tar.gz'
        hl7_3_file = r'../sample/HL7/fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack1_file = r'../sample/ACKs/fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack2_file = r'../sample/ACKs/ACK2_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack3_file = r'../sample/ACKs/ACK3_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        assert (monitor.is_valid_hl7_message(hl7_1_file))
        assert (monitor.is_valid_hl7_message(hl7_2_file))
        assert (monitor.is_valid_hl7_message(hl7_3_file))

        assert (not monitor.is_valid_hl7_message(ack1_file))
        assert (not monitor.is_valid_hl7_message(ack2_file))
        assert (not monitor.is_valid_hl7_message(ack3_file))


    def test_process_orphan_acks(self):
        ack1_file = r'fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack2_file = r'ACK2_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack3_file = r'ACK3_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'

        assert(os.path.exists(self.config.folder_remoteorphan))

        ack_files = monitor.get_file_list(self.folder_acks)
        #ack_files = [ack1_file, ack2_file, ack3_file]
        for ack in ack_files:
            src_file = os.path.join(self.folder_acks, ack)
            target_file = os.path.join(self.config.folder_remoteorphan, ack)
            shutil.copyfile(src_file, target_file)
        #print(os.listdir(self.config.folder_remoteorphan))
        assert(len(ack_files) == len(list(os.listdir(self.config.folder_remoteorphan))))
        assert(os.path.exists(os.path.join(self.config.folder_remoteorphan, ack1_file)))
        assert (os.path.exists(os.path.join(self.config.folder_remoteorphan, ack2_file)))
        assert (os.path.exists(os.path.join(self.config.folder_remoteorphan, ack3_file)))

        hl7_files = monitor.get_file_list(self.folder_hl7)
        for hl7 in hl7_files:
            if hl7 in ack_files:
                src_file = os.path.join(self.folder_hl7, hl7)
                target_file = os.path.join(self.config.folder_ack1flag, hl7)
                shutil.copyfile(src_file, target_file)

        orphan_files = monitor.get_file_list(self.config.folder_remoteorphan)
        #assert(len(orphan_files) == len(ack_files))

        monitor.process_orphan_acks(self.config)
        local_inbox_files = monitor.get_file_list(self.config.folder_localinbox)
        assert (len(local_inbox_files) == 1)

        monitor.process_orphan_acks(self.config)
        local_inbox_files = monitor.get_file_list(self.config.folder_localinbox)
        assert (len(local_inbox_files) == 2)

        monitor.process_orphan_acks(self.config)

        local_inbox_files = monitor.get_file_list(self.config.folder_localinbox)
        assert(len(local_inbox_files) == 3)
        assert (os.path.exists(os.path.join(self.config.folder_localinbox, ack1_file)))
        assert (os.path.exists(os.path.join(self.config.folder_localinbox, ack2_file)))
        assert (os.path.exists(os.path.join(self.config.folder_localinbox, ack3_file)))

        #assert(not os.path.exists(ack1_flag))



    def test_process_hl7_message(self):
        assert(self.config)
        assert(self.config.folder_localoutbox)
        hl7_1_file = r'../sample/HL7/fda_15ff7927-91f6-4fd8-80cb-bbddc6fa0cd1.tar.gz'
        hl7_2_file = r'../sample/HL7/fda_a383c97e-5749-4c0c-aff9-1f3883a34191.tar.gz'
        hl7_3_file = r'../sample/HL7/fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'

        onlyfiles = [hl7_1_file, hl7_2_file, hl7_3_file]

        for hl7_file in onlyfiles:
            srcfile = os.path.join(self.folder_hl7, os.path.basename(hl7_file))
            tgtfile = os.path.join(self.config.folder_localoutbox, os.path.basename(hl7_file))
            shutil.copyfile(srcfile, tgtfile)
            assert(os.path.exists(tgtfile))

        total_files = len(onlyfiles)
        files_in_localoutbox = monitor.get_file_list(self.config.folder_localoutbox)
        assert (len(files_in_localoutbox) == total_files)

        monitor.process_hl7_message(self.config)

        files_in_localoutbox = monitor.get_file_list(self.config.folder_localoutbox)
        assert(len(files_in_localoutbox)==0)

        files_in_ac1flag = monitor.get_file_list(self.config.folder_ack1flag)
        assert(len(files_in_ac1flag) == total_files)

        files_in_remoteoutbox = monitor.get_file_list(self.config.folder_remoteoutbox)
        assert(len(files_in_remoteoutbox) == total_files)

    def read_file_content(self, file_name):
        with open(file_name, 'r') as content_file:
            return content_file.read()

    def cleanse_files(self):

        folder_list = [self.config.folder_localinbox, self.config.folder_localoutbox,
                       self.config.folder_remoteinbox, self.config.folder_remoteoutbox,
                       self.config.folder_remoteorphan, self.config.folder_ack1flag,
                       self.config.folder_ack2flag, self.config.folder_ack3flag,
                       self.config.folder_tobedeleted]

        for one_folder in folder_list:
            onlyfiles = monitor.get_file_list(one_folder)
            for one_file in onlyfiles:
                file_tobedelete = os.path.join(one_folder, one_file)
                os.remove(file_tobedelete)

if __name__=="__main__":
    util.initialize_logger("../temp/logs/")
    unittest.main()

