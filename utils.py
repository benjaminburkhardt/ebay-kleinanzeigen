# -*- coding: utf-8 -*-
import logging
import os
from telegram import Bot
from telegram.utils.request import Request


def get_logger():
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    return logger


def get_bot(token):
    # Default size from the library, 4 workers + 4 additional
    request = Request(con_pool_size=8)
    return Bot(token=token, request=request)
