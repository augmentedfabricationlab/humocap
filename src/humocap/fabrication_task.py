from fabrication_control import Fabrication
from ur_fabrication_control.direct_control import URTask
from threading import Thread

__all__ = ['URTask_Humocap',
           'Humocap_Fabrication']
class URTask_Humocap(URTask):
    def __init__(self, server, urscript, req_msg, key=None, human_close=True):
        super(URTask_Humocap, self).__init__(server, urscript, req_msg, key)
        self.human_close = human_close
    
    def run(self, stop_thread, human_close):
        if human_close():
            self.log("Human too close!")
        else:
            super(URTask_Humocap, self).run(stop_thread)

    def perform(self, stop_thread, human_close):
        self.stop_thread = stop_thread()
        self.human_close = human_close()
        if not self.is_running and not self.is_completed:
            self.log("---STARTING TASK---")
            self.t = Thread(target=self.run,
                            args=(lambda: self.stop_thread,
                                  lambda: self.human_close))
            self.t.daemon = True
            self.t.start()
            self.is_running = True
        else:
            if self.t.is_alive():
                return False
            else:
                self.t.join()
                del self.t
                self.log("---COMPLETED TASK---")
                self.is_running = False
                return True

class Humocap_Fabrication(Fabrication):

    def __init__(self, server=None):
        super(Humocap_Fabrication, self).__init__(server)
        self.human_close = True
    
    def _create_threads(self):
        self._stop_thread = False
        self.fab_thread = Thread(target=self.run,
                                  args=(lambda: self._stop_thread,
                                        lambda: self.human_close))
        self.fab_thread.daemon = True

    def run(self, stop_thread, human_close):
        self.current_task = None
        self.log_messages = []
        self.log("FABRICATION: ---STARTING FABRICATION---")
        get_next_task = False
        while self.tasks_available():
            if stop_thread():
                self.log("FABRICATION: ---FORCED STOP---")
                break

            if self.get_next_task() is not None:
                if self.current_task is None:
                    get_next_task = True
                elif self.parallelize:
                    if (self.current_task.is_running
                            and self.current_task.parallelizable
                            and len(self.running_tasks) < self.max_parallel_tasks):
                        get_next_task = True
                elif not self.parallelize:
                    if (self.current_task.is_completed
                            and not self.current_task.is_running):
                        get_next_task = True
            
            if get_next_task:
                print("Getting new task")
                self.current_task = self.get_next_task()
                get_next_task = False         

            if len(self.running_tasks) > 0:
                for task in self.running_tasks:
                    task.perform(stop_thread, human_close)
                    self.log(task.log_messages)
                    if task.is_completed and not task.is_running:
                        self.running_tasks.remove(task)

            if (not self.current_task.is_completed
                  and not self.current_task.is_running
                  and self.current_task not in self.running_tasks):
                print("Initializing task")
                self.current_task.perform(stop_thread, human_close)
                self.running_tasks.append(self.current_task)
                self.log(self.current_task.log_messages)
        else:
            self.log("FABRICATION: All tasks done")
            self.log("FABRICATION: ---STOPPING FABRICATION---")
