#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import Queue
import threading
import time
from enum import Enum
from common import *
 
class Task_Manager():
    
    TASK_STATE = Enum("Pending", "Running", "Finish", "Failure", "Cancel")
    
    def __init__(self):
        self._task_queue = Queue.Queue()
        self.cur_task = {}

    def async_call(self, function, callback, *args, **kwargs):
        self._task_queue.put({
            'function': function,
            'callback': callback,
            'args': args,
            'kwargs': kwargs,
            'state': self.TASK_STATE.Pending 
        })

    def _task_queue_consumer(self):
        while True:
            try:
                self.cur_task = self._task_queue.get()
                function      = self.cur_task.get('function')
                callback      = self.cur_task.get('callback')
                args          = self.cur_task.get('args')
                kwargs        = self.cur_task.get('kwargs')
                try:
                    if callback:
                        if self.cur_task['state'] == self.TASK_STATE.Cancel:
                            continue
                        self.cur_task['state'] = self.TASK_STATE.Running
                        callback(function(*args, **kwargs))
                        self.cur_task['state'] = self.TASK_STATE.Finish
                except Exception as ex:
                    self.cur_task['state'] = self.TASK_STATE.Failure
                    if callback:
                        callback(ex)
                finally:
                    self._task_queue.task_done()
            except Exception as ex:
                logging.warning(ex)

    def start(self):
        thread = threading.Thread(target=self._task_queue_consumer)
        thread.daemon = True 
        thread.start()
        self._task_queue.join()

    def test(self, count):
        self.async_call(mysleep, handle_result, count)

    def show(self):
        self._task_queue.mutex.acquire()
        queue = self._task_queue.queue
        for item in queue:
            print item 
        self._task_queue.mutex.release()
   
    def getTasksInfo(self):
        result = []
        self._task_queue.mutex.acquire()
        result.append(TaskInfo(self.cur_task.get('args'), self.cur_task.get('state')))
        queue = self._task_queue.queue
        for item in queue:
            result.append(TaskInfo(item.get('args'), item.get('state')))
        self._task_queue.mutex.release()
        return result
 
def handle_result(result):
    print(type(result), result)

def mysleep(sleep_time):
    time.sleep(sleep_time)
    return sleep_time
 
if __name__ == "__main__":
    t = threading.Thread(target=_task_queue_consumer)
    t.daemon = False 
    t.start()
    _task_queue.join()
    async_call(mysleep, handle_result, 2)
    async_call(mysleep, handle_result, 3)
    async_call(mysleep, handle_result, 1)   
    async_call(mysleep, handle_result, 5)
    async_call(func_c, handle_result, 1, 2, 3)
    async_call(func_c, handle_result,  2, 3, 4)

    _task_queue.join()
  
