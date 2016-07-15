#!usr/bin/env python
from warnings import filterwarnings
import MySQLdb
import farmer_log

filterwarnings("ignore", category = MySQLdb.Warning)

class Mysql_wrapper():

    def __init__(self, host, user, passwd):
        self.connection = \
            MySQLdb.Connect(host="%s" % (host,), user="%s" % (user,), passwd="%s" % (passwd,), db="%s" % ("mysql",))

    def __del__(self):
        self.connection.close()

    def init_database(self):
        """
        Perpare for MYSQL database and table
        Args:
            NULL

        Returns:
        """
        cursor = self.connection.cursor()
        create_database = "CREATE DATABASE IF NOT EXISTS animations;"
        use_database = "USE animations;"
        create_table  = "CREATE TABLE IF NOT EXISTS docker_images (id INT NOT NULL AUTO_INCREMENT, REPOSITORY VARCHAR(500) NOT NULL, TAG VARCHAR(500) NOT NULL,CUDA_VERSION FLOAT NOT NULL,CUDA_VERSION_STRING VARCHAR(500) NOT NULL,CUDNN_VERSION FLOAT NOT NULL,CUDNN_VERSION_STRING VARCHAR(500) NOT NULL,TENSORFLOW BOOL NOT NULL, CAFFE BOOL NOT NULL,PRIMARY KEY (id));"
        sql_cmd = use_database + create_table
        farmer_log.info("init database command : [%s]" % create_database)
        cursor.execute(create_database)
        farmer_log.info("init table : [%s]" % sql_cmd)
        cursor.execute(sql_cmd)
        farmer_log.debug("rowcount : [%d]" % cursor.rowcount)
        if -1 != cursor.rowcount:
            result = cursor.fetchall()
            farmer_log.info(result)
        cursor.close()

    def has_image_in_db_by_rep_tag(self, repository, tag):
        result = False
        cursor = self.connection.cursor()
        try:
            use_table = "USE animations;"
            seach_image = "SELECT repository, tag FROM docker_images WHERE REPOSITORY = '%s' AND TAG = '%s';" % (repository, tag)
            sql_command = use_table + seach_image
            farmer_log.debug(sql_command)
            cursor.execute(seach_image)
            farmer_log.debug(cursor.rowcount)
            if (-1 != cursor.rowcount) and (0 != cursor.rowcount):
                result = True
            output = cursor.fetchall()
            farmer_log.info(output)
        except Exception as e:
            farmer_log.error("has_image_in_db_by_rep_tag:" + e.message)
            cursor.rollback()
        finally:
            cursor.close()
        return result

    def inert_item_in_docker_images_table(self, repository, tag, cuda_version, cuda_version_str, cudnn_version, cudnn_version_str, have_tensorflow, have_caffe):
        cursor = self.connection.cursor()
        try:
            use_table = "USE animations;"
            inserted_sql = 'INSERT INTO docker_images (REPOSITORY, TAG,\
             CUDA_VERSION, CUDA_VERSION_STRING, CUDNN_VERSION,\
             CUDNN_VERSION_STRING, TENSORFLOW, CAFFE) \
             VALUES("%s", "%s", %f, "%s", %f, "%s", %d, %d);' % \
              (repository, tag, cuda_version, cuda_version_str, cudnn_version,\
               cudnn_version_str, have_tensorflow, have_caffe)
            sql_command = use_table + inserted_sql
            farmer_log.debug(sql_command)
            cursor.execute(inserted_sql)
            self.connection.commit()
            output = cursor.fetchall()
            farmer_log.info(output)
        except Exception as e:
            self.connection.rollback()
            farmer_log.error("inert_item_in_docker_images_table:" + e.message)
        finally:
            cursor.close()

    def has_image_in_db_by_cuda_cuddn(self, cuda_string, cuddn_string):
        result = False
        cursor = self.connection.cursor()
        try:
            use_table = "USE animations;"
            seach_image = "SELECT repository, tag FROM docker_images WHERE CUDA_VERSION_STRING = '%s' AND CUDNN_VERSION_STRING = '%s';" % (cuda_string, cuddn_string)
            sql_command = use_table + seach_image
            farmer_log.debug(sql_command)
            cursor.execute(seach_image)
            farmer_log.debug(cursor.rowcount)
            if (-1 != cursor.rowcount) and (0 != cursor.rowcount):
                result = True
            output = cursor.fetchall()
            farmer_log.info(output)
        except Exception as e:
            self.connection.rollback()
            farmer_log.error("has_image_in_db_by_cuda_cuddn" + e.message)
        finally:
            cursor.close()
        return result

    def get_detailed_info_from_db(self, repository, tag):
        row = None
        cursor = self.connection.cursor()
        try:
            use_table = "USE animations;"
            select_sql = "SELECT * FROM docker_images WHERE REPOSITORY = '%s' AND TAG = '%s';" % (repository, tag)
            farmer_log.info(use_table)
            cursor.execute(use_table)
            farmer_log.info(select_sql)
            cursor.execute(select_sql)
            numrows = int(cursor.rowcount)
            if numrows == 1:
                row = cursor.fetchone()
            else:
                farmer_log.error("the result numrows[%d] which is not 1." % numrows)
            output = cursor.fetchall()
            farmer_log.info(output)
        except Exception as e:
            farmer_log.error("get_detailed_info_from_db" + e.message)
        finally:
            cursor.close()
        return row



if __name__ == "__main__":
    wrapper = Mysql_wrapper("localhost", "root", "RACQ4F6c")
    wrapper.init_database()
    #wrapper.inert_item_in_docker_images_table("nvidia/cuda", "7.5-cudnn5.1rc-devel-ubuntu14.04-caffe-pcs", 7.5,
    #                                         "cuda_7.5.18", 5.0, "cudnn-7.5-linux-x64-v5.0-rc", False, True)
    print wrapper.get_detailed_info_from_db("nvidia/cuda", "7.5-cudnn5.1rc-devel-ubuntu14.04-caffe-pcs")
    #print wrapper.has_image_in_db_by_cuda_cuddn("cuda_7.5.18", "cudnn-7.5-linux-x64-v5.0-rc")

    ##print wrapper.has_image_in_db_by_cuda_cuddn("cuda_7.5.18", "cudnn-7.5-linux-x64-v5.0-rc")
