import sys
import logging
import time
import argparse
import os
import shutil


sys.path.append(".")

try:
    from . import util
    from . import configuration
except:
    import util
    import configuration

def get_hl7_message_files(my_config):
    return get_file_list(my_config.folder_localoutbox)


def is_valid_hl7(hl7_file):
    return True


def get_file_list(folder):
    onlyfiles = [f for f in os.listdir(folder)
                 if os.path.isfile(os.path.join(folder, f))]
    return onlyfiles


def create_ack1_flag_from_hl7(my_config, hl7_file):
    try:
        src_file = os.path.join(my_config.folder_localoutbox, hl7_file)
        target_file = os.path.join(my_config.folder_ack1flag, hl7_file)
        logging.debug("Start to copy %s to %s" % (src_file, target_file))
        shutil.copyfile(src_file, target_file)
        logging.info("Successfully copied %s to %s!" % (src_file, target_file))
        return True
    except IOError as (errno, strerror):
        logging.critical("I/O error({0}): {1}".format(errno, strerror))
        return False
    except:
        logging.critical("Unexpected error:", sys.exc_info()[0])
        logging.debug("Error happened in copy %s to ack1_flag folder!" % hl7_file)
        return False


def copy_hl7_to_remoteoutbox(my_config, hl7_file):
    try:
        src_file = os.path.join(my_config.folder_localoutbox, hl7_file)
        target_file = os.path.join(my_config.folder_remoteoutbox, hl7_file)
        logging.debug("Start to copy %s to %s" % (src_file, target_file))
        shutil.copyfile(src_file, target_file)
        logging.info("Successfully copied %s to %s!" % (src_file, target_file))
        return True
    except IOError as (errno, strerror):
        logging.critical("I/O error({0}): {1}".format(errno, strerror))
        return False
    except:
        logging.critical("Unexpected error:", sys.exc_info()[0])
        logging.debug("Error happened in copy %s to remote outbox folder!" % hl7_file)
        return False


def delete_hl7_message(my_config, hl7_file):
    try:
        target_file = os.path.join(my_config.folder_localoutbox, hl7_file)
        logging.debug("Start to remove file:%s" % target_file)
        os.remove(target_file)
        logging.info("Successfully removed file:%s" % target_file)
        return True
    except IOError as (errno, strerror):
        logging.critical("I/O error({0}): {1}".format(errno, strerror))
        return False
    except:
        logging.critical("Unexpected error:", sys.exc_info()[0])
        logging.debug("Failed to remove file:%s" % hl7_file)
        return False


def process_hl7_message(my_config):
    logging.info("Start to process HL7 message in local outbox folder...")
    if not os.path.exists(my_config.folder_localinbox):
        logging.critical("Local inbox folder doesn't exist! Please check your configuration file!")
        return

    file_list = get_hl7_message_files(my_config)
    for hl7_file in file_list:
        if is_valid_hl7(hl7_file):
            ack1_flag_copy_status = create_ack1_flag_from_hl7(my_config, hl7_file)
            if ack1_flag_copy_status:
                hl7_copy_status = copy_hl7_to_remoteoutbox(my_config, hl7_file)
                if hl7_copy_status:
                    hl7_delete_status = delete_hl7_message(my_config, hl7_file)
        else:
            logging.warnning("Unknown file found in HL7 local outbox folder:%s" % os.path.basename(hl7_file))
    logging.info("Processing in local outbox folder is finished!")


def detect_ack_file(my_config, orphan, file_content,
                                    ack1_flag_files, ack2_flag_files, ack3_flag_files):
    file_name = os.path.basename(orphan)

    if file_name in ack1_flag_files:
        return 'ACK1', True

    message_id = get_messageid_from_ack2_content(file_content)

    if message_id and message_id in ack2_flag_files:
        return 'ACK2', True

    core_id = get_coreid_from_ack3_content(file_content)

    if core_id and core_id in ack3_flag_files:
        return 'ACK3', True

    return None, False


def get_coreid_from_ack2_content(file_content):
    CORE_ID = r'CoreId:'
    DATA_RECEIVED = r'DateTime Receipt Generated:'

    int_start = file_content.index(CORE_ID)
    int_end = file_content.index(DATA_RECEIVED, int_start)

    if int_start>=0 and int_end>=0:
        coreId = file_content.index(int_start+len(CORE_ID)+1, int_end)
        if coreId:
            return coreId.strip()

    return None


def get_coreid_from_ack3_content(file_content):
    ACK3_XML1 = r'<?xml version="1.0" encoding="UTF-8"?>'
    ACK3_XML2 = r'<submission>'
    CORE_ID_START = r'<coreId>'
    CORE_ID_END = r'</coreId>'
    if file_content.lindex(ACK3_XML1)>=0 and file_content.lindex(ACK3_XML2)>=0:
        int_start = file_content.index(CORE_ID_START)
        int_end = file_content.index(CORE_ID_END)
        if int_start>=0 and int_end>=0:
            return file_content[int_start+1:int_end]

    return None


def get_messageid_from_ack1_content(file_content):
    return file_content[file_content.index("<")+1 : file_content.index(">")]


def get_messageid_from_ack2_content(file_content):
    '''
    get message id from ACK2
    :param file_content:
    :return:
    '''
    if file_content.lindex('MessageId')>0:
        return file_content[file_content.lindex("<")+1:file_content.rindex(">")]
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


def process_ack1_file(my_config, orphan, file_content):
    message_id = get_messageid_from_ack1_content(file_content)

    source_file = os.path.join(my_config.folder_remoteorphan, orphan)
    target_file = os.path.join(my_config.folder_localinbox, orphan)
    ack2_flag = os.path.join(my_config.folder_ack2flag, message_id)
    file_tobedelete = os.path.join(my_config.folder_tobedeleted, orphan)

    try:
        # copy or write, it's a question. let's try from write content!
        # shutil.copyfile(source_file, target_file)
        with open(target_file, "w") as target_ack1:
            target_ack1.write(file_content)

        touch(ack2_flag)
        touch(file_tobedelete)

        try:
            os.remove(source_file)
            os.remove(file_tobedelete)
        except IOError as (errno, strerror):
            logging.critical("I/O error({0}): {1}".format(errno, strerror))
        except:
            logging.critical("Unexpected error:", sys.exc_info()[0])
    except IOError as (errno, strerror):
        logging.critical("I/O error({0}): {1}".format(errno, strerror))
    except:
        logging.critical("Unexpected error:", sys.exc_info()[0])


def process_ack2_file(my_config, orphan, file_content):
    core_id = get_coreid_from_ack2_content(file_content)

    source_file = os.path.join(my_config.folder_remoteorphan, orphan)
    target_file = os.path.join(my_config.folder_localinbox, orphan)
    ack3_flag = os.path.join(my_config.folder_ack3flag, core_id)
    file_tobedelete = os.path.join(my_config.folder_tobedeleted, orphan)

    try:
        # shutil.copyfile(source_file, target_file)
        with open(target_file, "w") as target_ack2:
            target_ack2.write(file_content)
        touch(ack3_flag)
        touch(file_tobedelete)

        try:
            os.remove(source_file)
            os.remove(file_tobedelete)
        except IOError as (errno, strerror):
            logging.critical("I/O error({0}): {1}".format(errno, strerror))
        except:
            logging.critical("Unexpected error:", sys.exc_info()[0])
    except IOError as (errno, strerror):
        logging.critical("I/O error({0}): {1}".format(errno, strerror))
    except:
        logging.critical("Unexpected error:", sys.exc_info()[0])


def process_ack3_file(my_config, orphan, file_content):
    source_file = os.path.join(my_config.folder_remoteorphan, orphan)
    target_file = os.path.join(my_config.folder_localinbox, orphan)
    file_tobedelete = os.path.join(my_config.folder_tobedeleted)

    try:
        with open(target_file, "w") as target_ack3:
            target_ack3.write(file_content)
        touch(file_tobedelete)

        try:
            os.remove(source_file)
            os.remove(file_tobedelete)
        except IOError as (errno, strerror):
            logging.critical("I/O error({0}): {1}".format(errno, strerror))
        except:
            logging.critical("Unexpected error:", sys.exc_info()[0])
    except IOError as (errno, strerror):
        logging.critical("I/O error({0}): {1}".format(errno, strerror))
    except:
        logging.critical("Unexpected error:", sys.exc_info()[0])


def process_orphan_acks(my_config):
    ack1_flag_files = get_file_list(my_config.folder_ack1flag)
    ack2_flag_files = get_file_list(my_config.folder_ack2flag)
    ack3_flag_files = get_file_list(my_config.folder_ack3flag)

    orphan_files = get_file_list(my_config.folder_remoteorphan)

    for orphan in orphan_files:
        # in order for safe access, read all it's content first.
        logging.info("\tProccessing %s" % orphan)
        try:
            file_content = read_content_from_orphan(my_config, orphan)
            ack_type, is_for_ccm = detect_ack_file(my_config, orphan, file_content,
                                                   ack1_flag_files, ack2_flag_files, ack3_flag_files)
            if is_for_ccm:
                if ack_type == 'ACK1':
                    process_ack1_file(my_config, orphan, file_content)
                elif ack_type == 'ACK2':
                    process_ack2_file(my_config, orphan, file_content)
                else:
                    process_ack3_file(my_config, orphan, file_content)

        except IOError as (errno, strerror):
            logging.critical("I/O error({0}): {1}".format(errno, strerror))
        except:
            logging.critical("Unexpected error:", sys.exc_info()[0])


def process_folders(my_config):
    logging.warning("Process starting...")
    process_hl7_message(my_config)
    process_orphan_acks(my_config)


def main():
    parser = argparse.ArgumentParser(description='Arguments for UDI Transfer')
    parser.add_argument('-l', action="store", dest="logpath", required=False,
                        help = "path to store logs")
    parser.add_argument('-c', action="store", dest="configuration", required=False,
                        help="configuration file")
    args = parser.parse_args()
    if not args.configuration:
        sys.exit("please provide a configuration file!")

    my_config = configuration.monitor_configuration(args.configuration)
    if args.logpath:
        util.initialize_logger(args.logpath)
    else:
        util.initialize_logger(my_config.folder_logs)

    logging.info("Configuration and Logs have been settled down!")

    try:
        while True:
            process_folders(my_config)
            time.sleep(my_config.sleeptime)
    except KeyboardInterrupt:
        logging.info("Process stopped!")






if __name__=='__main__':
    main()