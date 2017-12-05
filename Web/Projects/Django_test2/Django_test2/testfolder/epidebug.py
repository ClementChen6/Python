import os
import yaml
import datetime




# from django.http import HttpResponse, Http404
# from django.views.decorators.csrf import csrf_exempt
# from django.contrib.auth.decorators import login_required, user_passes_test
# import json
# from django.shortcuts import get_object_or_404
# from django.views import View
# from django.http.response import HttpResponseBadRequest, HttpResponseNotAllowed,\
#     HttpResponseNotFound
# from cam_rest.tl_data_collect import TlDataCollect
# from django.utils import timezone
#
# from rest_framework.authentication import SessionAuthentication, BasicAuthentication
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework.decorators import api_view, authentication_classes,\
#     permission_classes

config_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../daemon/configfiles/emu_api/emu_api.yaml"))
utc_startdatetime = datetime.datetime.utcnow()
utc_stopdatetime = utc_startdatetime + datetime.timedelta(hours=2)


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
        topologyID = self.topologyID

        if request.method == 'GET':
            yaml_file = open(config_path, 'r')
            reservation_dict = yaml.load(yaml_file)
            functionalities = []
            content = {}
            if topologyID:
                reservation_status = status.split("_")[0]
                TL_status = status.split("_")[1]
                request_status = status.split("_")[2]
                topology_detail = reservation_dict["Topologies"][topologyID]
                testline_id = topology_detail["testline"]
                hardware_dict = topology_detail["HARDWARE"]
                for key, value in hardware_dict.items():
                    for i in range(1, value + 1):
                        if key == "BB3":
                            hardware_detail = reservation_dict["Description"][key][i]
                            hardware_description = BB3_description(**hardware_detail)
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
                        "status": request_status,
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
            return content
