#!usr/bin/env python
from warnings import filterwarnings
import MySQLdb
import farmer_log

filterwarnings("ignore", category = MySQLdb.Warning)

class Mysql_wrapper():

    def __init__(self, host, user, passwd):
        self.db_connection = \
            MySQLdb.connect(host="%s" % (host,), user="%s" % (user,), passwd="%s" % (passwd,), db="%s" % ("mysql",))

    def init_database(self):
        """
        Perpare for MYSQL database and table
        Args:
            NULL

        Returns:
        """
        conn = self.db_connection.cursor()
        create_database = "CREATE DATABASE IF NOT EXISTS animations;"
        use_database = "USE animations;"
        create_table  = "CREATE TABLE IF NOT EXISTS docker_images (id INT NOT NULL AUTO_INCREMENT, REPOSITORY VARCHAR(500) NOT NULL, TAG VARCHAR(500) NOT NULL,CUDA_VERSION FLOAT NOT NULL,CUDA_VERSION_STRING VARCHAR(500) NOT NULL,CUDNN_VERSION FLOAT NOT NULL,CUDNN_VERSION_STRING VARCHAR(500) NOT NULL,TENSORFLOW BOOL NOT NULL, CAFFE BOOL NOT NULL,PRIMARY KEY (id));"
        sql_cmd = use_database + create_table
        farmer_log.info("init database command : [%s]" % create_database)
        conn.execute(create_database)
        farmer_log.info("init table : [%s]" % sql_cmd)
        conn.execute(sql_cmd)
        farmer_log.debug("rowcount : [%d]" % conn.rowcount)
        if -1 != conn.rowcount:
            result = conn.fetchall()
            farmer_log.info(result)
        conn.close()


    def get_detailed_info_from_db(self, table, repository, tag):
        #TODO
        pass

if __name__ == "__main__":
    wrapper = Mysql_wrapper("localhost", "root", "RACQ4F6c")
    wrapper.init_database()