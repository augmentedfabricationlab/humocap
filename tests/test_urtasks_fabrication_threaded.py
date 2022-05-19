import time
import keyboard
from humocap import Humocap_Fabrication
from fabrication_control import TCPFeedbackServer
from humocap import URTask_Humocap
from ur_fabrication_control.direct_control import URScript

ur_address = ("192.168.56.102", 30002)
server_address = ("192.168.56.104", 50005)

server = TCPFeedbackServer(server_address[0], server_address[1])

def get_urscript(req_msg):
    # Simple URScript
    ur_script = URScript(ur_address[0], ur_address[1])
    ur_script.start()
    ur_script.socket_open(server_address[0], server_address[1], "FBserver")
    ur_script.get_current_pose_cartesian("FBserver", send=True)
    ur_script.socket_send_line_string(req_msg, "FBserver")
    ur_script.socket_close("FBserver")
    ur_script.textmessage(req_msg, True)
    ur_script.end()
    ur_script.generate()
    return ur_script

human_close = True

tasks = []
for i in range(5):
    req_msg = "Task {} done".format(i)
    ur_script = get_urscript(req_msg)
    urtask = URTask_Humocap(server, ur_script, req_msg, key=i, human_close=human_close)
    tasks.append(urtask)

stop_thread = False

fabrication = Humocap_Fabrication(server)
fabrication.set_tasks(tasks)
fabrication.human_close = human_close
fabrication.start()

t0 = time.time()
try:
    while fabrication.tasks_available():
        if time.time()-t0 > 5:
            fabrication.human_close = True
        elif time.time()-t0 > 4:
            fabrication.human_close = False
except KeyboardInterrupt:
    print("User interruption")
    stop_thread = True
    fabrication._stop_thread = stop_thread
    fabrication.current_task.perform(lambda: stop_thread, lambda: human_close)
    fabrication.log(fabrication.current_task.log_messages)

print(fabrication.log_messages)
time.sleep(1)
fabrication.server.shutdown()
print(fabrication.server.msgs)

