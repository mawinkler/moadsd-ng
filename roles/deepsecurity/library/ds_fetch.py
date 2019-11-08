#!/usr/bin/python
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ds_config

short_description: GET or PUT a configuration

version_added: "2.6"

description:
    - "This module works like M(copy), but in reverse. It is used for fetching
      files from remote machines and storing them locally in a file tree,
      organized by hostname. Note that this module is written to transfer
      log files that might not be present, so a missing remote file won't
      be an error unless fail_on_missing is set to 'yes'."

options:
    src:
        description:
            - The configuration on the deep security to fetch. This must be
              one of the following:
                  - system_settings
        required: true
        default: null
    dest:
        description:
            - A directory to save the configuration into.
        required: true
        default: null
    flat:
        version_added: "1.2"
        description:
            - Allows you to override the default behavior of appending
              hostname/path/to/file to the destination.
    dsm_url:
        description:
            - The Deep Security Manager URL to query
        required: true
    api_key:
        description:
            - The API Key to access the Deep Security REST API

author:
    - Markus Winkler (markus_winkler@trendmicro.com)
'''

EXAMPLES = '''
# Retriece covered CVEs and rules covering
- name: Query Deep Security Protection Status
  ds_ips:
    hostname: "dockerhost.example.com"
    identifier: "1008793"
    state: present
    dsm_url: "https://{{ deepsecurity_manager }}:4119"
    api_key: "{{ deepsecurity_api_key }}"
  register: ds_result
'''

RETURN = '''
ds_ips:
    description: Returns changed true or false if a change within Deep Security was made
    type: dict
    sample:
        "changed": true,
        "failed": false,
        "message": ""
'''

from ansible.module_utils.basic import AnsibleModule
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import requests
from urllib.parse import urlsplit
import json
import sys
import pickle
import os.path

def get_system_settings(dsm_url, api_key):
    '''
    Gets the system settings.
    '''

    url = dsm_url + "/api/systemsettings"
    data = { }
    post_header = { "Content-type": "application/json",
                    "api-secret-key": api_key,
                    "api-version": "v1"}
    response = requests.get(url, data=json.dumps(data), headers=post_header, verify=False).json()

    # Error handling
    if 'message' in response:
        if response['message'] == "Invalid API Key":
            raise ValueError("Invalid API Key")

    return response

def run_module():

    # Argument & parameter definitions
    module_args = dict(
        src=dict(type='str', required=True),
        dest=dict(type='str', required=False),
        flat=dict(type='str', default='yes', choices=['yes', 'no']),
        dsm_url=dict(type='str', required=True),
        api_key=dict(type='str', required=True)
    )

    # Result dictionary
    result = dict(
        changed=False,
        message=''
    )

    # The AnsibleModule
    # We support check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # If in check mode return empty result set
    if module.check_mode:
        return result

    #
    # Module logic
    #

    # Choose between absent or present and execute
    task_result = {}
    if module.params['src'] == 'system_settings':
        task_result = get_system_settings(module.params['dsm_url'], module.params['api_key'])
        filename = 'system_settings.json'
        outname = ""
        if module.params['flat'] != 'yes':
            hostname = "{0.hostname}/".format(urlsplit(module.params['dsm_url']))
            if not os.path.exists(hostname):
                os.makedirs(hostname)
            outname = hostname + filename
        else:
            outname = filename
        with open(outname, 'wb') as fp:
            pickle.dump(task_result, fp)
    else:
        module.fail_json(msg="nothing to fetch", **result)

    # Populate result set

    # We didn't change anything on the host
    result['changed'] = False
    # if task_result == {}:
    #     result['changed'] = False
    # else:
    #     result['changed'] = True

    # Return key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
