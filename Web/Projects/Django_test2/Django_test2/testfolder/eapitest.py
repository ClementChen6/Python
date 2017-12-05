import yaml
import datetime
from django.http import HttpResponse, Http404
import json
import ruamel.yaml


config_path = "D:/Documents/UTE/Documents/test2.yaml"
utc_startdatetime = datetime.datetime.utcnow()
utc_stopdatetime = utc_startdatetime + datetime.timedelta(hours=2)



def change_status(des_status=None):
    status_list = ['Activating_Preparing_New', 'Activating_Preparing_OnGoing', 'Active_Ready_Done',
                   'Deactivating_Deleting_New', 'Deactivating_Deleting_OnGoing', 'Deactivating_Deleting_Done',
                   'Completed_Deleted_Done']
    with open(config_path) as f:
        yamlf = yaml.load(f)
        status = yamlf["Status"]
        status_index = status_list.index(status)

    with open(config_path,'w') as outfile:
        if not des_status:
            yamlf["Status"] = [status_list[status_index+1] if status_index < len(status_list)-1 else status_list[-1]][0]
        else:
            yamlf["Status"] = des_status
        yaml.dump(yamlf, outfile, default_flow_style=False)





def create_new_list(topologyID,request):
    global detail
    detail = reservationdetail(topologyID, request)
    return topologyID

class BB3_description():
    def __init__(self,image_url,**detailinfo):
        # self.status = status
        self.detail = detailinfo
        self.task = {
            "message": None,
            "status": "New",
            "type": "BB3_Deployment"
        }
        self.description = {
            "compute_id": self.detail["compute_id"],
            "controller_ip": self.detail["controller_ip"],
            "extra_data": self.detail["extra_data"],
            "image_name": image_url,
            "vlan_map": self.detail["vlan_map"]
        }

    def reservation_detail(self,status):
        result = {}
        self.task["status"] = status.split("_")[1]
        if status.split("_")[0] in ["Deleting", "Deleted"]:
            self.task["type"] = "BB3_TearDown"
        if status in ["Preparing_New","Preparing_OnGoing"]:
            self.description["extra_data"] = ""

        result = {
            "description": self.description,
            "task": self.task,
            "name": "BB3"
            }
        return result



class TestVM_description():
    def __init__(self, **detailinfo):
        # self.status = status
        self.detail = detailinfo
        self.task = {
            "message": None,
            "status": "New",
            "type": "TestVM_Deployment"
        }
        self.description = {
            "compute_id": self.detail["compute_id"],
            "controller_ip": self.detail["controller_ip"],
            "extra_data": self.detail["extra_data"],
            "image_name": self.detail["image_name"],
            "vlan_map": self.detail["vlan_map"]
        }

    def reservation_detail(self, status):
        result = {}
        if status == "Preparing_New":
            self.description["extra_data"] = ""
            self.task["status"] = "New"
        elif status == "Preparing_OnGoing":
            self.description["extra_data"] = ""
            self.task["status"] = "OnGoing"
        elif status == "Ready_Done":
            self.description["extra_data"] = self.detail["extra_data"],
            self.task["status"] = "Done"
        result = {
            "description": self.description,
            "task": self.task,
            "name": "TestVM"
        }
        return result



class reservationdetail():
    def __init__(self, topologyID,request):
        self.topologyID = topologyID
        self.status_list = ['Activating_Preparing_New', 'Activating_Preparing_OnGoing', 'Active_Ready_Done']
        self.request = request
        self.status_terminate = self.status_list[-1]

    def reservation_detail(self):
        request = self.request
        # status = self.status_list[0]
        status = [self.status_list[0] if len(self.status_list)>0 else self.status_terminate ][0]
        self.status_list.pop(0)
        topologyID = self.topologyID

        if request == 'GET':
            yaml_file = open(config_path, 'r')
            reservation_dict = yaml.load(yaml_file)
            functionalities = []
            content = {}
            if topologyID:
                reservation_status = status.split("_")[0]
                TL_status = status.split("_")[1]
                request_status = status.split("_")[2]
                topology_detail = reservation_dict["Topologies"][int(topologyID)]
                testline_id = topology_detail["testline"]
                hardware_dict = topology_detail["HARDWARE"]
                for key, value in hardware_dict.items():
                    for i in range(1, value + 1):
                        if key == "BB3":
                            hardware_detail = reservation_dict["Description"][key][i]
                            soft_url = reservation_dict["Reservation"]["soft_url_map"]["BB3"]["VM_IMAGE"]
                            hardware_description = BB3_description(soft_url,**hardware_detail)
                            functionalities.append(
                                hardware_description.reservation_detail(TL_status + "_" + request_status))
                        elif key == "TestVM":
                            hardware_detail = reservation_dict["Description"][key][i]
                            hardware_description = TestVM_description(**hardware_detail)
                            functionalities.append(
                                hardware_description.reservation_detail(TL_status + "_" + request_status))
                testline_detail = reservation_dict["Testlines"][testline_id]
                testline = {
                    "status": TL_status,
                    "controller_ip": testline_detail["controller_ip"],
                    "compute_id": testline_detail["compute_id"],
                    "cal_image_name": testline_detail["cal_image_name"],
                    "stack_name": testline_detail["stack_name"],
                    "cal_vm_ip": testline_detail["cal_vm_ip"],
                    "topology": {
                        "id": topologyID,
                        "name": topology_detail["name"],
                        "description": topology_detail["description"],
                        "in_use": topology_detail["in_use"]
                    },
                    "task": {
                        "status": [request_status if  request_status != 'New' else 'OnGoing'][0],
                        "type": "TL_Deployment",
                        "message": "None"
                    },
                    "functionalities": functionalities
                }
                duration = (utc_stopdatetime - utc_startdatetime).total_seconds()
                content = {
                    "reservationID": topologyID,
                    "status": reservation_status,
                    "start_date": utc_startdatetime.strftime("%Y-%m-%d %H:%M"),
                    "end_date": utc_stopdatetime.strftime("%Y-%m-%d %H:%M"),
                    "duration": '{:02}:{:02}'.format(int(duration // 3600), int(duration % 3600 // 60)),
                    "testline": testline
                }
            return json.dumps(content)

def get_detail(topologyID,request):
    detail = [ detail if  detail else reservationdetail(topologyID,request)]
    return detail.reservation_detail()

def modify_yaml(file,key,value):
    with open(file) as f:
        yamlf = yaml.load(f)
    with open(file,'w') as outfile:
        yamlf[key] = value
        yaml.dump(yamlf,outfile,default_flow_style=False)



if __name__ == '__main__':
    # detail = reservationdetail(17,'GET')
    create_new_list('17','GET')
    result = detail.reservation_detail()
    print("result is",result)
    result = detail.reservation_detail()
    # print("result is",result)
    change_status('Activating_Preparing_New')
    testdict = {"reservation":{"start_date":datetime.datetime.utcnow()}}
    testdict2 = {"reservation":{"Status":'Activating_Preparing_New'}}
    # modify_yaml(**testdict)
    # modify_yaml(**testdict2)
    #


