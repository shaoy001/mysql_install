#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Author : Shaoylee
    Date   : 2020/03/01
    Desc   :
    Change LOG :
"""
import pymysql
import time
from threading import Thread
from multiprocessing import Process
from pymysql import cursors, connect
from DBUtils.PooledDB import PooledDB


class Mysql(object):
    def __init__(self,url='192.168.200.228',
                user='lzy001',
                password='12345678!',
                db='hotdb_cloud_management_config',
                port=3306):
        try:
            self.pool = PooledDB(pymysql, 2,
                                 host=url,
                                 user=user,
                                 password=password,
                                 db=db,
                                 port=port,
                                 charset='utf8',
                                 cursorclass=cursors.DictCursor,
                                 autocommit=1)

        except pymysql.err.OperationalError:
            print("数据库连接失败")

    def thread_test(self):
        # 调用insert函数造数据
        t_l = []
        start = time.time()
        for i in range(1, 10):
            # self.insert_date(i)
            t = Thread(target=self.query, args=(i,))  # 多线程
            # t = Process(target=self.insert_date,args = (i,)  # 多进程
            t_l.append(t)
            t.start()
        for t in t_l:
            t.join()
        end = time.time()
        use_time = end - start
        print("创建表总共用时:%.4f" % use_time + "s")

    def query_one(self, sql):
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                return result
        finally:
            conn.close()
    def query_all(self, sql):
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                return result
        finally:
            conn.close()
    def ddl_exc(self, sql):
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                try:
                    response = \
                        cursor.execute(sql)
                    result = cursor.fetchall()
                except Exception as e:
                    result = e.args
                return result

        finally:
            conn.close()


if __name__ == "__main__":
    x = Mysql()
    x.ddl_exc(sql='delete from t1')
