#!/usr/bin/env python3 

#############################################################################
#### PA Config Version Pull Script
#### Stores tsg_id: MU_ver,RN_ver,SC_ver in tenant_ver_info.yaml file 
#### Author: Darshna Subashchandran
#############################################################################

from time import sleep
import logging
import json
import yaml
import argparse
import prisma_sase

####################################################
#### Login to the tenant with the client secret
###################################################
def sdk_login_to_controller(filepath):
    with open(filepath) as f:
        client_secret_dict = yaml.safe_load(f)
        client_id = client_secret_dict["client_id"]
        client_secret = client_secret_dict["client_secret"]
        tsg_id_str = client_secret_dict["scope"]
        global tsgid
        tsgid = tsg_id_str.split(":")[1]
        #print(client_id, client_secret, tsgid)
    
    global sdk 
    sdk = prisma_sase.API(controller="https://sase.paloaltonetworks.com/", ssl_verify=False)
    sdk.set_debug(3) 
    sdk.interactive.login_secret(client_id, client_secret, tsgid)
    
    return sdk


def fetch_current_config_version_of_subtenant(tsgid):
    
    url = "https://api.sase.paloaltonetworks.com/sse/config/v1/config-versions/running"
    resp = sdk.rest_call(url=url, method="GET")
    #sdk.set_debug(3)
    #print(resp)

    data_list = resp.json()['data']
    mu_ver, rn_ver, sc_ver = 1,1,1
    for data in data_list:
        if data["device"] == "Mobile Users":
            mu_ver = data["version"]
        if data["device"] == "Remote Networks":
            rn_ver = data["version"]
        if data["device"] == "Service Connections":
            sc_ver = data["version"]

    #print("Subtenant Version {} {} {}".format(mu_ver,rn_ver,sc_ver))
    return mu_ver,rn_ver,sc_ver


if __name__ == "__main__":
    
    #Parsing the arguments to the script
    parser = argparse.ArgumentParser(description='Onboarding the LocalUsers, Service Connection and Security Rules.')
    parser.add_argument('-t1', '--T1Secret', help='Input secret file in .yml format for the tenant(T1) from which the security rules have to be replicated.')  

    args = parser.parse_args()
    T1_secret_filepath = args.T1Secret

    sdk = sdk_login_to_controller(T1_secret_filepath)   

    #Create a yaml file to store the tsg id and their version numbers
    fp = open('ConfigPull.yaml', 'w')

    #fetch the current version of subtenant ID to build a dictionary of sudtenantid: version of config
    mu_ver,rn_ver,sc_ver = fetch_current_config_version_of_subtenant(tsgid)
    subtenant_str = tsgid + ": " + str(mu_ver)+","+ str(rn_ver)+ ","+str(sc_ver)
    #print("Subtenant string to be written into file {}".format(subtenant_str))
    
    #Writing the subtenant_id:GP_subtenant_ver,RN_subtenant_ver,SC_subtenant_ver into a file
    fp.write(subtenant_str)
    fp.write("\n")
    fp.close()
