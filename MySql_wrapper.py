#!usr/bin/env python
import MySQLdb

class Mysql_wrapper():

    def __init__(self, host, user, passwd, database, table):
        self.db_connection = \
            MySQLdb.connect(host="%s" % (host,), user="%s" % (user,), passwd="%s" % (passwd,), db="%s" % (database,))
        self.table = table

    def create_table(self):
        # TODO
        pass

    def get_detailed_info_from_db(self, table, repository, tag):
        #TODO
        pass