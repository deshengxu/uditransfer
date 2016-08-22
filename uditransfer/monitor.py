import sys
import logging
import time
import argparse
import os
import shutil
import tarfile

sys.path.append(".")

try:
    from . import util
    from . import configuration
except:
    import util
    import configuration

def get_hl7_message_files(my_config):
    return get_file_list(my_config.folder_localoutbox)

def is_valid_hl7_message(hl7_fullname):
    try:

        tar = tarfile.open(hl7_fullname, 'r:gz')
        for tar_info in tar:
            name_info = (tar_info.name).upper()
            if "SUBMISSION.XML" in name_info:
                logging.info("%s is a valid HL7 message tar.gz package!" % hl7_fullname)
                return True

        return False
    except tarfile.ReadError as re:
        logging.info(hl7_fullname + " " + str(re))
        return False
    except Exception as e:
        logging.error("Unacceptable HL7 tar.gz package received. it will be ignored!")
        logging.exception("Exception")
        return False

    return False

def is_valid_hl7(my_config, hl7_file):
    if my_config.hl7_operation_delay > 0:
        time.sleep(my_config.hl7_operation_delay)

    return is_valid_hl7_message(os.path.join(my_config.folder_localoutbox, os.path.basename(hl7_file)))



def get_file_list(folder):
    onlyfiles = [f for f in os.listdir(folder)
                 if (os.path.isfile(os.path.join(folder, f)) and (not f.startswith('.')))]
    return onlyfiles


def create_ack1_flag_from_hl7(my_config, hl7_file):
    try:
        src_file = os.path.join(my_config.folder_localoutbox, hl7_file)
        target_file = os.path.join(my_config.folder_ack1flag, hl7_file)
        #if my_config.hl7_operation_delay>0:
        #    time.sleep(my_config.hl7_operation_delay)

        logging.debug("Start to copy %s to %s" % (src_file, target_file))
        shutil.copyfile(src_file, target_file)
        logging.info("Successfully copied %s to %s!" % (src_file, target_file))
        return True
    except IOError as (errno, strerror):
        logging.error("I/O error({0}): {1}".format(errno, strerror))
        return False
    except Exception as e:
        logging.error("Unexpected error:", sys.exc_info()[0])
        logging.exception("Error happened in copy %s to ack1_flag folder!" % hl7_file)
        return False


def copy_or_move_hl7_to_remoteoutbox(my_config, hl7_file):
    try:
        src_file = os.path.join(my_config.folder_localoutbox, hl7_file)
        target_file = os.path.join(my_config.folder_remoteoutbox, hl7_file)

        if my_config.hl7_operation_method_is_copy:
            logging.debug("Start to copy %s to %s" % (src_file, target_file))
            shutil.copyfile(src_file, target_file)
            logging.info("Successfully copied %s to %s!" % (src_file, target_file))
            os.remove(src_file)
            logging.info("Successfully removed source file after copy:%s" % src_file)
        else:
            logging.debug("Start to move %s to %s" % (src_file, target_file))
            shutil.move(src_file, target_file)
            logging.info("Successfully moved %s to %s!" % (src_file, target_file))

        return True
    except IOError as (errno, strerror):
        logging.error("I/O error({0}): {1}".format(errno, strerror))
        return False
    except Exception as e:
        logging.error("Unexpected error:{0}".format(sys.exc_info()[0]))
        logging.exception("Error happened in copy %s to remote outbox folder!" % hl7_file)
        return False

def process_hl7_message(my_config):
    logging.info("Start to process HL7 message in local outbox folder...")
    if not os.path.exists(my_config.folder_localoutbox):
        logging.error("Local outbox folder doesn't exist! Please check your configuration file!")
        return

    file_list = get_hl7_message_files(my_config)
    for hl7_file in file_list:
        if is_valid_hl7(my_config, hl7_file):
            ack1_flag_copy_status = create_ack1_flag_from_hl7(my_config, hl7_file)
            if ack1_flag_copy_status:
                hl7_copy_status = copy_or_move_hl7_to_remoteoutbox(my_config, hl7_file)
        else:
            logging.warning("Unknown file found in HL7 local outbox folder:%s" % os.path.basename(hl7_file))
    logging.info("Processing in local outbox folder has been finished!")


def detect_ack_file(my_config, orphan, file_content,
                                    ack1_flag_files, ack2_flag_files, ack3_flag_files):
    file_name = os.path.basename(orphan)

    logging.info("Start to detect ack types!")
    logging.info("Looking for file name:%s in ack1-flag folder" % file_name)
    if file_name in ack1_flag_files:
        logging.info("Found ack1 flag:%s" % file_name)
        return 'ACK1', True
    else:
        logging.info("This is not a ACK1 for CCM")

    logging.info("Looking for message ID from potential ack2 content:%s" % orphan)
    message_id = get_messageid_from_ack2_content(file_content)

    if message_id:
        logging.info("Found message ID from ack2:%s" % message_id)
        if message_id in ack2_flag_files:
            logging.info("Found this message ID in ack2 flag folder!")
            return 'ACK2', True
        else:
            logging.info("This message ID is not for CCM!")
            return 'ACK2', False
    else:
        logging.info("Couldn't find message ID from this content. it's not a ACK2 file!")

    logging.info("Try to look for core ID from ack3 content")
    core_id = get_coreid_from_ack3_content(file_content)

    if core_id:
        logging.info("Found core id:%s" % core_id)
        if core_id in ack3_flag_files:
            logging.info("Found this core id in ack3 flag folder!")
            return 'ACK3', True
        else:
            logging.info("This cord ID is not for CCM!")
            return 'ACK3', False
    else:
        logging.info("Couldn't find CoreID from this content. This is not a ACK3 file!")

    logging.info("Nothing detected!")
    return '', False


def get_coreid_from_ack2_content(file_content):
    logging.debug(file_content)
    CORE_ID = r'CoreId:'
    DATA_RECEIVED = r'DateTime Receipt Generated:'

    int_start = file_content.find(CORE_ID)
    int_end = file_content.find(DATA_RECEIVED, int_start)

    if int_start>=0 and int_end>=0:
        coreId = file_content[int_start+len(CORE_ID) : int_end]
        if coreId:
            return coreId.strip()

    return None


def get_coreid_from_ack3_content(file_content):
    logging.debug(file_content)
    ACK3_XML1 = r'<?xml version="1.0" encoding="UTF-8"?>'
    ACK3_XML2 = r'<submission>'
    CORE_ID_START = r'<coreId>'
    CORE_ID_END = r'</coreId>'
    #print(file_content)
    if file_content.find(ACK3_XML1)>=0 and file_content.find(ACK3_XML2)>=0:
        int_start = file_content.find(CORE_ID_START)
        int_end = file_content.find(CORE_ID_END)
        if int_start>=0 and int_end>=0:
            return file_content[int_start+len(CORE_ID_START):int_end]

    return None


def get_messageid_from_ack1_content(file_content):
    logging.debug(file_content)
    return file_content[file_content.find("<")+1 : file_content.find(">")]


def get_messageid_from_ack2_content(file_content):
    '''
    get message id from ACK2
    :param file_content:
    :return:
    '''
    logging.debug(file_content)
    if file_content.find('MessageId')>=0:
        logging.info("Found MessageID in ack2 content!")
        return (file_content[file_content.find("<")+1:file_content.rfind(">")]).strip()
    else:
        return None


def touch(file_name):
    ''' create an empty file with specific name
    '''
    with open(file_name, 'a'):
        os.utime(file_name, None)


def read_content_from_orphan(my_config, orphan):
    with open(os.path.join(my_config.folder_remoteorphan, orphan), 'r') as content_file:
        return content_file.read()

def create_file(my_config, source_file, target_file, file_content, notes):
    if my_config.operation_delay>0:
        time.sleep(my_config.operation_delay)

    try:
        if my_config.operation_method_is_move:
            shutil.move(source_file, target_file)
            logging.info("Successfully moved %s to %s for %s file." %
                         (source_file, target_file, notes))
        elif my_config.operation_method_is_copy:
            shutil.copyfile(source_file, target_file)
            logging.info("Successfully copied %s to %s for %s file." %
                         (source_file, target_file, notes))
        else:
            if my_config.recheck_content:
                new_file_content = read_content_from_orphan(my_config, os.path.basename(source_file))
                if not file_content == new_file_content:
                    logging.debug("%s file content has been changed since ACK detect, "
                                  "it will be ignored this time." % notes)
            with open(target_file, "w") as target:
                target.write(file_content)
                logging.info("Successfully write down %s content into file:%s" % (notes,target_file))

        return True
    except Exception as e:
        logging.exception("Error happened in %s file operation!" % notes)
        return False

    return False

def process_ack1_file(my_config, orphan, file_content):
    try:
        message_id = get_messageid_from_ack1_content(file_content)

        source_file = os.path.join(my_config.folder_remoteorphan, orphan)
        target_file = os.path.join(my_config.folder_localinbox, orphan)
        ack1_flag = os.path.join(my_config.folder_ack1flag, orphan)
        ack2_flag = os.path.join(my_config.folder_ack2flag, message_id)
        file_tobedelete = os.path.join(my_config.folder_tobedeleted, orphan)

        # copy or write, it's a question. let's try from write content!
        # shutil.copyfile(source_file, target_file)
        logging.debug("Start to write ack1 content into local inbox folder!")
        if not create_file(my_config, source_file, target_file, file_content, "ACK1"):
            logging.error("Unexpected error happened in ack1 file creation!")
            return

        touch(ack2_flag)
        logging.info("Successfully create an empty ack2 flag file:%s" % ack2_flag)
        touch(file_tobedelete)
        logging.info("Successfully create an empty file to be deleted:%s" % file_tobedelete)

        try:
            if not my_config.operation_method_is_move:
                os.remove(source_file)
                logging.info("Successfully removed original source file from remote orphan folder:%s" % source_file)
            os.remove(file_tobedelete)
            logging.info("Successfully removed flag of file to be deleted!")
            os.remove(ack1_flag)
            logging.info("Successfully removed ack1 flag!")
        except IOError as (errno, strerror):
            logging.error("process_ack1_file remove I/O error({0}): {1}".format(errno, strerror))
        except Exception as e:
            logging.exception("process_ack1_file remove Unexpected error:{0}".format(sys.exc_info()[0]))
    except UnicodeDecodeError as ude:
        logging.error(("%s has invalid content as ack1 file, error message:" % orphan)+ str(ude))
        logging.exception("process_ack1_file UnicodeDecodeError: %s" % orphan)
    except IOError as (errno, strerror):
        logging.error("process_ack1_file I/O error({0}): {1}".format(errno, strerror))
    except Exception as e:
        logging.exception("process_ack1_file Unexpected error:", sys.exc_info()[0])


def process_ack2_file(my_config, orphan, file_content):
    try:

        message_id = get_messageid_from_ack2_content(file_content)
        core_id = get_coreid_from_ack2_content(file_content)

        source_file = os.path.join(my_config.folder_remoteorphan, orphan)
        target_file = os.path.join(my_config.folder_localinbox, orphan)
        ack2_flag = os.path.join(my_config.folder_ack2flag, message_id)
        ack3_flag = os.path.join(my_config.folder_ack3flag, core_id)
        file_tobedelete = os.path.join(my_config.folder_tobedeleted, orphan)

        # shutil.copyfile(source_file, target_file)
        logging.debug("Start to write down content to ACK2 file!")
        if not create_file(my_config, source_file, target_file, file_content, "ACK2"):
            logging.error("Unexpected error happened in ack2 file creation!")
            return

        touch(ack3_flag)
        logging.info("Successfully create an empty ack3 flag:%s" % ack3_flag)
        touch(file_tobedelete)
        logging.info("Successfully create an empty flag for file to be delete")

        try:
            if not my_config.operation_method_is_move:
                os.remove(source_file)
                logging.info("Successfully removed original source file:%s" % source_file)
            os.remove(file_tobedelete)
            logging.info("Successfully removed flag of file to be delete!")
            os.remove(ack2_flag)
            logging.info("Successfully removed ack2 flag!")
        except IOError as (errno, strerror):
            logging.error("process_ack2_file remove I/O error({0}): {1}".format(errno, strerror))
        except Exception as e:
            logging.exception("process_ack2_file remove Unexpected error:{0}".format(sys.exc_info()[0]))
    except UnicodeDecodeError as ude:
        logging.error(("%s has invalid content as ack2 file, error message:" % orphan)+ str(ude))
        logging.exception("process_ack2_file UnicodeDecodeError: %s" % orphan)
    except IOError as (errno, strerror):
        logging.error("process_ack2_file I/O error({0}): {1}".format(errno, strerror))
    except Exception as e:
        logging.exception("process_ack2_file Unexpected error:{0}".format(sys.exc_info()[0]))


def process_ack3_file(my_config, orphan, file_content):
    try:
        core_id = get_coreid_from_ack3_content(file_content)
        source_file = os.path.join(my_config.folder_remoteorphan, orphan)
        target_file = os.path.join(my_config.folder_localinbox, orphan)
        ack3_flag = os.path.join(my_config.folder_ack3flag, core_id)
        file_tobedelete = os.path.join(my_config.folder_tobedeleted, orphan)

        logging.debug("Start process_ack3_file...")
        if not create_file(my_config, source_file, target_file, file_content, "ACK3"):
            logging.error("Unexpected error happened in ack3 file creation!")
            return

        #logging.info("Start to create flag file to be deleted:%s" % file_tobedelete)
        touch(file_tobedelete)
        logging.info("Successfully created an empty flag file to be deleted")

        try:
            if not my_config.operation_method_is_move:
                os.remove(source_file)
                logging.info("Successfully removed original source file:%s" % source_file)
            os.remove(file_tobedelete)
            logging.info("Successfully removed flag file to be deleted!")
            os.remove(ack3_flag)
            logging.info("Successfully removed ack3 flag!")
        except IOError as (errno, strerror):
            logging.error("process_ack3_file remove I/O error({0}): {1}".format(errno, strerror))
        except Exception as e:
            logging.exception("process_ack3_file remove Unexpected error:{0}".format(sys.exc_info()[0]))
    except UnicodeDecodeError as ude:
        logging.error(("%s has invalid content as ack3 file, error message:" % orphan)+ str(ude))
        logging.exception("process_ack3_file UnicodeDecodeError: %s" % orphan)
    except IOError as (errno, strerror):
        logging.error("process_ack3_file I/O error({0}): {1}".format(errno, strerror))
    except Exception as e:
        logging.exception("process_ack3_file Unexpected error:{0}".format(sys.exc_info()[0]))


def process_orphan_acks(my_config):
    logging.info("Start to process ack(s) folder...")
    ack1_flag_files = get_file_list(my_config.folder_ack1flag)
    logging.debug("ACK1, ACK2, ACK3, Orphan list:")
    logging.debug(ack1_flag_files)
    ack2_flag_files = get_file_list(my_config.folder_ack2flag)
    logging.debug(ack2_flag_files)
    ack3_flag_files = get_file_list(my_config.folder_ack3flag)
    logging.debug(ack3_flag_files)

    orphan_files = get_file_list(my_config.folder_remoteorphan)
    logging.debug(orphan_files)

    for orphan in orphan_files:
        # in order for safe access, read all it's content first.
        logging.info("Proccessing %s from ack(s) folder." % orphan)
        try:
            file_content = read_content_from_orphan(my_config, orphan)
            ack_type, is_for_ccm = detect_ack_file(my_config, orphan, file_content,
                                                   ack1_flag_files, ack2_flag_files, ack3_flag_files)
            if is_for_ccm:
                logging.debug("\tFound ACK type:%s" % ack_type)
                if ack_type == 'ACK1':
                    process_ack1_file(my_config, orphan, file_content)
                elif ack_type == 'ACK2':
                    process_ack2_file(my_config, orphan, file_content)
                elif ack_type == 'ACK3':
                    process_ack3_file(my_config, orphan, file_content)
            else:
                logging.debug("\tThis file is not for CCM!")

        except IOError as (errno, strerror):
            logging.error("I/O error({0}): {1}".format(errno, strerror))
        except Exception as e:
            logging.exception("process_orphan_acks Unexpected error:{0}".format(sys.exc_info()[0]))
    logging.info("Processing in ack(s) folder has been finished!")


def process_folders(my_config):
    logging.info("Start processing")
    process_hl7_message(my_config)
    process_orphan_acks(my_config)


def main():
    parser = argparse.ArgumentParser(description='Arguments for UDI Transfer')
    parser.add_argument('-l', action="store", dest="logpath", required=False,
                        help = "path to store logs")
    parser.add_argument('-c', action="store", dest="configuration", required=False,
                        help="configuration file")
    parser.add_argument('-p', action="store_true", dest="periodical", required=False, default=False,
                        help="periodically run with interval time defined in configuration.")

    args = parser.parse_args()
    if not args.configuration:
        sys.exit("please provide a configuration file!")

    my_config = configuration.monitor_configuration(args.configuration)
    if args.logpath:
        util.initialize_logger(args.logpath)
    else:
        util.initialize_logger(my_config.folder_logs, my_config.stdout_log, my_config.all_file_log)

    logging.info("Configuration and Logs have been settled down!")

    if args.periodical:
        try:
            while True:
                process_folders(my_config)
                logging.info("sleeping...\n\n")
                time.sleep(my_config.sleeptime)
        except KeyboardInterrupt:
            logging.info("Process stopped!")
    else:
        process_folders(my_config)






if __name__=='__main__':
    main()