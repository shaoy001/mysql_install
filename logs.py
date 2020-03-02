#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Author : Shaoylee
    Date   : 2020/03/02
    Desc   :
    Change LOG :
"""
import logging
import logging.handlers
import sys


class Logger(object):
    """
        Public logs hander for logging
    """

    def __init__(self, name, logfile='/data/mysql_install.log', DEBUG=True, size=5 * 10 ** 8, counts=5):
        """
        :param name:
        :param logfile:
        :param DEBUG:
        :return:
        """
        self.debug = DEBUG
        self.level = 0 if DEBUG else 3
        self.name = name
        self.logfile = logfile
        self.logger = logging.getLogger(self.name)
        self.fh = logging.handlers.RotatingFileHandler(self.logfile, maxBytes=size, backupCount=counts, encoding='utf8')
        self.ch = logging.StreamHandler(sys.stdout)

    def config(self):
        """
            Init the logger and return the logger object
        """
        levels = {0: logging.DEBUG,
                  3: logging.INFO,
                  2: logging.WARNING,
                  1: logging.ERROR}
        level = levels.get(self.level, logging.NOTSET)
        self.logger.setLevel(level)
        formater = logging.Formatter('%(asctime)s %(name)-18s %(levelname)-5s %(message)s', '%Y-%m-%d %H:%M:%S')
        self.fh.setFormatter(formater)
        self.logger.addHandler(self.fh)
        if self.debug:
            self.ch.setLevel(level)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
            self.ch.setFormatter(formatter)
            self.logger.addHandler(self.ch)

    def get_logger(self):
        """
        :return:
        """
        self.logger.handlers.clear() # 及时清理（logger.handlers.clear),解决重复日志
        self.config()
        return self.logger

    def close_log(self):
        """
        回收内存
        :return:
        """
        self.logger.removeFilter(self.fh)
        self.fh.close()
        self.logger.removeFilter(self.ch)
        self.ch.close()


if __name__ == "__main__":
    test_log = Logger('ERRO')
    test_log.get_logger().error("瑶瑶")
    test_log1 = Logger('ERRO1')
    test_log1.get_logger().info("123412412")