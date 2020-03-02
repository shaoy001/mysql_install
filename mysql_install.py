#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Author : Shaoylee
    Date   : 2020/03/01
    Desc   :
    Change LOG :
"""
import mysql_conn
import os
import sys
import tarfile
import shutil
import fileinput
import argparse
import subprocess
import time
from logs import Logger
file_name = sys.argv[0]

pro_path = os.path.dirname(sys.path[0])
sys.path.append(pro_path)

# mysql安装路径
BASE_PATH_ROOT = '/data/mysqlbase'
DATA_PATH_ROOT = '/data/mysqldata'
mysql_cnf = '/data/5.7my.cnf'
mysqlserver = '/data/mysql.server'


class mysql_install():
    # 查询并返回实例的加密后的密码
    def __init__(self):
        self.port = args.port
        self.mem = args.mem
        self.conn = args.connections
        self.mysql_package = args.mysql_package
        self.mysql_cnf = mysql_cnf
        self.mysql_base = os.path.join(BASE_PATH_ROOT, 'mysql' + str(self.port))
        self.mysql_data_path = os.path.join(DATA_PATH_ROOT, 'mysql' + str(self.port))
        self.mysqlserver = mysqlserver
        self.mysql_document = os.path.join(self.mysql_data_path, self.mysql_package[:-7])
        self.service = os.path.join(self.mysql_base, 'bin', 'mysql.server.' + str(self.port))
        self.file_name = file_name

    def run(self):

        self.env_check()
        if not self.dir_make():
            Logger(self.file_name).get_logger().info("mysql dir make failed")
            return 20002, 'mysql dir make failed'
        if not self.cnf_make():
            Logger(self.file_name).get_logger().info("my.cnf update failed")
            return 20001, 'my.cnf update failed'
        if not self.mysql_install():
            Logger(self.file_name).get_logger().info("mysql install failed")
            return 20003, 'mysql install failed'
        time.sleep(15)
        if not self.mysql_user_grant():
            Logger(self.file_name).get_logger().info("grants failed")
            return 20010, 'grants failed'
        return True

    def env_check(self):
        mbase = os.path.isdir(self.mysql_base)
        mdatap = os.path.isdir(self.mysql_data_path)
        mpak = os.path.exists(self.mysql_package)
        if not self.group_check():
            os.system('groupadd mysql')
        if not self.user_check():
            os.system('useradd -r -g mysql -s /sbin/nologin mysql')
        if mbase == False:
            if mdatap == False:
                if mpak == False:
                    Logger(self.file_name).get_logger().info("mysql package not exist")
                    return False
            else:
                Logger(self.file_name).get_logger().info("mysql data path exist")
                return False
        else:
            Logger(self.file_name).get_logger().info("mysql base path exist")
            return False
        return True

    def dir_make(self):
        """

        :return:
        """
        userid = int(os.popen("cat /etc/passwd |grep -w mysql|awk -F':' '{print $3}'").read().strip('\n'))
        groupid = int(os.popen("cat /etc/passwd |grep -w mysql|awk -F':' '{print $4}'").read().strip('\n'))

        os.makedirs(self.mysql_data_path, mode=0o751, exist_ok=True)
        os.makedirs(self.mysql_data_path + '/mydata', mode=0o751, exist_ok=True)
        os.makedirs(self.mysql_data_path + '/binlog', mode=0o751, exist_ok=True)
        os.makedirs(self.mysql_data_path + '/innodb_ts', mode=0o751, exist_ok=True)
        os.makedirs(self.mysql_data_path + '/innodb_log', mode=0o751, exist_ok=True)
        os.makedirs(self.mysql_data_path + '/relaylog', mode=0o751, exist_ok=True)
        os.makedirs(self.mysql_data_path + '/tmpdir', mode=0o751, exist_ok=True)
        os.makedirs(self.mysql_data_path + '/log', mode=0o751, exist_ok=True)
        os.makedirs(self.mysql_data_path + '/sock', mode=0o751, exist_ok=True)
        os.makedirs(self.mysql_data_path + '/backup', mode=0o751, exist_ok=True)
        os.makedirs(self.mysql_base, mode=0o751, exist_ok=True)

        # skip the ownership change
        if os.getuid() == 0:
            os.chown(self.mysql_data_path, userid, groupid)
            os.chown(self.mysql_data_path + '/mydata', userid, groupid)
            os.chown(self.mysql_data_path + '/binlog', userid, groupid)
            os.chown(self.mysql_data_path + '/innodb_ts', userid, groupid)
            os.chown(self.mysql_data_path + '/innodb_log', userid, groupid)
            os.chown(self.mysql_data_path + '/relaylog', userid, groupid)
            os.chown(self.mysql_data_path + '/tmpdir', userid, groupid)
            os.chown(self.mysql_data_path + '/log', userid, groupid)
            os.chown(self.mysql_data_path + '/sock', userid, groupid)
            os.chown(self.mysql_data_path + '/backup', userid, groupid)
            os.chown(self.mysql_base, userid, groupid)
        return True

    def user_check(self):
        muser = os.popen("cat /etc/passwd |grep -w mysql|awk -F':' '{print $1}'").read().strip('\n')
        if not muser == '':
            return True
        Logger(self.file_name).get_logger().info("user check fial2")
        return False

    def group_check(self):
        mgroup = os.popen("cat /etc/group |grep -w mysql|awk -F':' '{print $1}'").read().strip('\n')
        if not mgroup == '':
            return True
        Logger(self.file_name).get_logger().error("group check fail2")
        return False

    def cnf_make(self):

        mem = int(self.mem)
        conn = int(self.conn)
        # 2 G  1G
        if mem <= 8:
            percent = 0.4
        elif mem <= 16:
            percent = 0.5
        else:
            percent = 0.6
        innodb_buffer_pool_size = 'innodb_buffer_pool_size=' + str(round(mem * percent * 1024)) + 'M'

        sort_buffer_size = 'sort_buffer_size=' + str(
            round(((mem * 4 / 10 * 1024 * 1024) / conn / 9) * 4)) + 'K'
        join_buffer_size = 'join_buffer_size=' + str(
            round(((mem * 4 / 10 * 1024 * 1024) / conn / 9) * 1)) + 'K'
        read_buffer_size = 'read_buffer_size=' + str(
            round(((mem * 4 / 10 * 1024 * 1024) / conn / 9) * 2)) + 'K'
        read_rnd_buffer_size = 'read_rnd_buffer_size=' + str(
            round(((mem * 4 / 10 * 1024 * 1024) / conn / 9) * 2)) + 'K'
        innodb_log_file_size = 'innodb_log_file_size=' + '512M'
        innodb_log_buffer_size = 'innodb_log_buffer_size=' + '32M'

        mc = self.mysql_cnf
        mpc = self.mysql_data_path + '/' + 'my.cnf.' + self.port
        shutil.copy(mc, mpc)

        max_connect = 'max_connections=%s' % (int(self.conn))
        for line in fileinput.input(mpc, backup='.bak', inplace=1):
            line = line.replace('3306', self.port)
            print(line.strip())

        for line3 in fileinput.input(mpc, backup='.bak', inplace=1):
            line3 = line3.replace('innodb_buffer_pool_size=2G', innodb_buffer_pool_size)
            print(line3.strip())

        for line4 in fileinput.input(mpc, backup='.bak', inplace=1):
            line4 = line4.replace('sort_buffer_size=8M', sort_buffer_size)
            print(line4.strip())

        for line5 in fileinput.input(mpc, backup='.bak', inplace=1):
            line5 = line5.replace('join_buffer_size=4M', join_buffer_size)
            print(line5.strip())

        for line6 in fileinput.input(mpc, backup='.bak', inplace=1):
            line6 = line6.replace('read_buffer_size=1M', read_buffer_size)
            print(line6.strip())

        for line7 in fileinput.input(mpc, backup='.bak', inplace=1):
            line7 = line7.replace('read_rnd_buffer_size=8M', read_rnd_buffer_size)
            print(line7.strip())

        for line8 in fileinput.input(mpc, backup='.bak', inplace=1):
            line8 = line8.replace('max_connections=8000', max_connect)
            print(line8.strip())

        for line9 in fileinput.input(mpc, backup='.bak', inplace=1):
            line9 = line9.replace('innodb_buffer_pool_size=2G', innodb_buffer_pool_size)
            print(line9.strip())
        for line10 in fileinput.input(mpc, backup='.bak', inplace=1):
            line10 = line10.replace('innodb_log_file_size=1G', innodb_log_file_size)
            print(line10.strip())
        for line11 in fileinput.input(mpc, backup='.bak', inplace=1):
            line11 = line11.replace('innodb_log_buffer_size=64M', innodb_log_buffer_size)
            print(line11.strip())
        return True

    def mysql_install(self):
        t = tarfile.open(self.mysql_package, "r:gz")
        t.extractall(path=self.mysql_data_path)
        t.close()
        # path
        os.renames(self.mysql_document, self.mysql_base)
        cmd_own_confirm = "chown -R mysql.mysql {}".format(self.mysql_base)
        if not subprocess.call(cmd_own_confirm, shell=True) == 0:
            Logger(self.file_name).get_logger().info("chown mysql base fail")
            return False
        cmd_mod_green = "chmod -R g+rw {}".format(self.mysql_data_path)
        if not subprocess.call(cmd_mod_green, shell=True) == 0:
            Logger(self.file_name).get_logger().info("chow mysql data fail")
            return False
        cmd_mod = ['chmod -R 755 %s' % self.mysql_base, 'chmod -R 750 %s/bin' % self.mysql_base]
        for cmd in cmd_mod:
            subprocess.call(cmd, shell=True)
            result = self.mysql_base + '/bin/mysqld ' + ' --defaults-file=' + self.mysql_data_path + '/my.cnf.' \
                     + self.port + ' --initialize-insecure --user=mysql >>/dev/null 2>&1'
            if not subprocess.call(result, shell=True) == 0:
                Logger(self.file_name).get_logger().info("chmod mysql data or base fail")
                return False
        shutil.copy(self.mysqlserver, self.service)
        cmds = ["sed -i 's/PORT/%s/g' %s" % (self.port, self.service),
                "sed -i 's/PATH_ROOT/\%s/g' %s" % ('/data', self.service),
                "chmod 755 %s" % self.service,
                "rm -rf /etc/my.cnf",
                "rm -rf %s/my.cnf" % self.mysql_base]
        for cmd in cmds:
            subprocess.call(cmd, shell=True)
        return True

    def mysql_user_grant(self):
        """

        :return:
        """
        self.hotdb_root = "root"
        self.hotdb_root_pd = "123456"
        self.user = "lzy001"
        self.passwd = "12345678!"

        sql = ["delete from mysql.user where user='' or host not in ('localhost')",
               "alter user %s@'localhost' IDENTIFIED BY '%s'" % (self.hotdb_root, self.hotdb_root_pd),
               "create user %s@'%%' IDENTIFIED BY '%s'" % (self.user, self.passwd),
               "GRANT ALL PRIVILEGES ON *.* TO %s@'*'" % (self.user),
               "flush privileges"]
        self.conn = mysql_conn.Mysql(url='127.0.01',
                                     user='root',
                                     password='',
                                     db='',
                                     port=self.port)
        for sql1 in sql:
            self.conn.ddl_exc(sql1)
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mysql_package", type=str, help="mysql_package_name",
                        default='mysql-5.7.26-linux-glibc2.12-x86_64.tar.gz')
    parser.add_argument('--port', type=str, help='mysql port', default='3306')
    parser.add_argument('--mem', type=str, help='mysql use mem', default='2')
    parser.add_argument('--connections', type=str, help='mysql instance max_connections', default='300')
    args = parser.parse_args()
    x = mysql_install()
    x.run()
