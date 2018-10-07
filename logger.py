# -*- coding: utf-8 -*-

import logging


def start_logging(file=False, label=''):
    # create logger with 'spam_application'
    logger = logging.getLogger(label)
    logger.setLevel(logging.DEBUG)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    ch.setFormatter(console_formatter)

    # add the handlers to the logger
    logger.addHandler(ch)
    if file:
        # create file handler which logs even debug messages
        fh = logging.FileHandler('./logs/%s.log' % label)
        fh.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
        fh.setFormatter(file_formatter)
        logger.addHandler(fh)

    return logger
