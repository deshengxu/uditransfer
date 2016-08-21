import logging
import os.path
import sys
import datetime

def initialize_logger(output_dir, stream_loglevel = logging.INFO, all_loglevel=logging.DEBUG):
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    except:
        sys.exit("Error happened in create log folder:%s" % output_dir)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(stream_loglevel)
    formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    now = datetime.datetime.now()
    error_log_filename = "error-%4d-%02d-%02d.log" % (now.year, now.month, now.day)
    all_log_filename = "all-%4d-%02d-%02d.log" % (now.year, now.month, now.day)

    # create error file handler and set level to error
    handler = logging.FileHandler(os.path.join(output_dir, error_log_filename), "a+", encoding=None, delay="true")
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # create debug file handler and set level to debug
    handler = logging.FileHandler(os.path.join(output_dir, all_log_filename), "a+")
    handler.setLevel(all_loglevel)
    formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logging.info("Start to log...")

