#!/usr/bin/python
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ds_ips

short_description: Adds or deletes IPS rules to or from a computer

version_added: "2.6"

description:
    - "This module adds a to be assigned or deletes an assigned IPS rule
       from a computer"

options:
    hostname:
        description:
            - The hostname to be queried
        required: true
    identifier:
        description:
            - The identifier of the rule
        required: true
    state:
        description:
            - The desired state. Choices present or absent
        required: true
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
import json
import sys

def search_computer(hostname, dsm_url, api_key):
    '''
    Searches for computer and returns ID if present.
    Returns -1 is absent
    '''

    url = dsm_url + "/api/computers/search"
    data = { "maxItems": 1, "searchCriteria": [ { "fieldName": "hostName", "stringTest": "equal", "stringValue": hostname } ] }
    post_header = { "Content-type": "application/json",
                    "api-secret-key": api_key,
                    "api-version": "v1"}
    response = requests.post(url, data=json.dumps(data), headers=post_header, verify=False).json()

    # Error handling
    if 'message' in response:
        if response['message'] == "Invalid API Key":
            raise ValueError("Invalid API Key")

    computer_id = -1
    computer_ruleIDs = {}

    if len(response['computers']) > 0:
        if 'ID' in response['computers'][0]:
            computer_id = response['computers'][0]['ID']

    if 'ruleIDs' in response['computers'][0]['intrusionPrevention']:
        computer_ruleIDs = response['computers'][0]['intrusionPrevention']['ruleIDs']

    return { "ID": computer_id, "ruleIDs": computer_ruleIDs }

def search_ipsrule(identifier, dsm_url, api_key):
    '''
    Searches for IPS rule and returns ID if present.
    Returns -1 is absent
    '''
    url = dsm_url + "/api/intrusionpreventionrules/search"
    data = { "maxItems": 1,
             "searchCriteria": [ { "fieldName": "identifier",
                                   "stringTest": "equal",
                                   "stringValue": identifier
                                 } ] }
    post_header = { "Content-type": "application/json",
                    "api-secret-key": api_key,
                    "api-version": "v1"}
    response = requests.post(url, data=json.dumps(data), headers=post_header, verify=False).json()

    # Error handling
    if 'intrusionPreventionRules' not in response:
        if 'message' in response:
            raise KeyError(response['message'])
        else:
            raise KeyError(response)
    
    rule_id = -1
    if len(response['intrusionPreventionRules']) > 0:
        if 'ID' in response['intrusionPreventionRules'][0]:
            rule_id = response['intrusionPreventionRules'][0]['ID']

    return { "ID": rule_id }

def rule_present(computer, rule, dsm_url, api_key):
    '''
    Ensure rule is present
    '''

    if rule['ID'] not in computer['ruleIDs']:
        # url = module.params['dsm_url'] + "/api/computers/" + str(computer_attributes[0]['ID']) + "/intrusionprevention/assignments"
        url = dsm_url + "/api/computers/" + str(computer['ID']) + "/intrusionprevention/assignments"
        data = { "ruleIDs": str(rule['ID']) }
        post_header = { "Content-type": "application/json",
                        "api-secret-key": api_key,
                        "api-version": "v1"}
        computer_response = requests.post(url, data=json.dumps(data), headers=post_header, verify=False).json()
        
        # Rule added
        return 201

    # Rule already present
    return 200

def rule_absent(computer, rule, dsm_url, api_key):
    '''
    Ensure rule is absent
    '''

    if rule['ID'] in computer['ruleIDs']:
        # url = module.params['dsm_url'] + "/api/computers/" + str(computer_attributes[0]['ID']) + "/intrusionprevention/assignments"
        url = dsm_url + "/api/computers/" + str(computer['ID']) + "/intrusionprevention/assignments/" + str(rule['ID'])
        data = { }
        post_header = { "Content-type": "application/json",
                        "api-secret-key": api_key,
                        "api-version": "v1"}
        computer_response = requests.delete(url, data=json.dumps(data), headers=post_header, verify=False).json()
        
        # Rule deleted
        return 201

    # Rule already absent
    return 200


def run_module():

    # Argument & parameter definitions
    module_args = dict(
        hostname=dict(type='str', required=True),
        identifier=dict(type='str', required=True),
        state=dict(Type='str', required=True),
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
    # Build intrusion prevention ips rules CVEs dictionary

    # Retrieve requested computer object
    computer = search_computer(module.params['hostname'], module.params['dsm_url'], module.params['api_key'])

    # Retrieve requested IPS rule by identifier
    rule = search_ipsrule(module.params['identifier'], module.params['dsm_url'], module.params['api_key'])

    # Choose between absent or present and execute
    task_result = 0
    if module.params['state'] == 'present':
        task_result = rule_present(computer, rule, module.params['dsm_url'], module.params['api_key'])
    elif module.params['state'] == 'absent':
        task_result = rule_absent(computer, rule, module.params['dsm_url'], module.params['api_key'])
    else:
        module.fail_json(msg="allowed states present or absent", **result)

    # Populate result set

    # We didn't change anything on the host
    if task_result == 200:
        result['changed'] = False
    else:
        result['changed'] = True

    # Return key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
