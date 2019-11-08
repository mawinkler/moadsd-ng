#!/usr/bin/python
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ds_protection_status

short_description: Retrieves the current protection status of a computer

version_added: "2.6"

description:
    - "This module retrieves the current protection status of a computer
       along with the list of rule IDs which are covering the CVEs"

options:
    hostname:
        description:
            - The hostname to be queried
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
  ds_protection_status:
    hostname: "dockerhost.example.com"
    dsm_url: "https://{{ deepsecurity_manager }}:4119"
    api_key: "{{ deepsecurity_api_key }}"
  register: ds_result
'''

RETURN = '''
ds_protection_status:
    description: The current protection status realized with the HIPS module
    type: dict
    sample:
        "changed": false,
        "failed": false,
        "json": {
            "cves_covered": [
                "CVE-2015-1716",
                "CVE-2015-4000",
                "CVE-2016-8858"
            ],
            "rules_covering": [
                3712,
                5555
            ]
        },
        "message": ""
'''

from ansible.module_utils.basic import AnsibleModule
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import requests
import json
import sys

def build_rules_cves_map(dsm_url, api_key):
    '''
    Build dictionary of intrusion prevention rules with the ability to cover CVEs
    '''
    # Constants
    RESULT_SET_SIZE = 1000
    MAX_RULE_ID= 10000

    # Return dictionary
    rules_cves = {}
    rules_id = {}

    for i in range(0, MAX_RULE_ID, RESULT_SET_SIZE):
        url = dsm_url + "/api/intrusionpreventionrules/search"
        data = { "maxItems": RESULT_SET_SIZE,
                 "searchCriteria": [ { "fieldName": "CVE", "stringTest": "not-equal", "stringValue": "" },
                                     { "fieldName": "ID", "idTest": "greater-than-or-equal", "idValue": i },
                                     { "fieldName": "ID", "idTest": "less-than", "idValue": i + RESULT_SET_SIZE } ] }
        post_header = { "Content-type": "application/json",
                        "api-secret-key": api_key,
                        "api-version": "v1"}
        response = requests.post(url, data=json.dumps(data), headers=post_header, verify=False).json()

        # Error handling
        if 'message' in response:
            if response['message'] == "Invalid API Key":
                raise ValueError("Invalid API Key")
        if 'intrusionPreventionRules' not in response:
            if 'message' in response:
                raise KeyError(response['message'])
            else:
                raise KeyError(response)

        rules = response['intrusionPreventionRules']

        # Build dictionary ID: CVEs
        for rule in rules:
            cves = set()

            if 'CVE' in rule:
                for cve in rule['CVE']:
                    cves.add(str(cve.strip()))

            cves = sorted(cves)
            rules_cves[str(rule['ID']).strip()] = { "identifier": str(rule['identifier']).strip(), "cves": cves}

    return rules_cves

def run_module():

    # Argument & parameter definitions
    module_args = dict(
        hostname=dict(type='str', required=True),
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
    rules_cves = {}

    try:
        rules_cves = build_rules_cves_map(module.params['dsm_url'], module.params['api_key'])
    except ValueError as e:
        module.fail_json(msg=e.message, **result)
    except KeyError as e:
        module.fail_json(msg=e.message, **result)

    # Retrieve requested computer object
    url = module.params['dsm_url'] + "/api/computers/search"
    data = { "maxItems": 1,
             "searchCriteria": [ { "fieldName": "hostName",
                                   "stringTest": "equal",
                                   "stringValue": "%" + module.params['hostname'] + "%",
                                   "stringWildcards": "true" } ] }
    post_header = { "Content-type": "application/json",
                    "api-secret-key": module.params['api_key'],
                    "api-version": "v1"}
    computer = requests.post(url, data=json.dumps(data), headers=post_header, verify=False).json()
    computer_attributes = computer['computers']

    # Populate result set with covered CVEs and rule IDs covering
    cves = set()
    rules = set()
    for attribute in computer_attributes:
        for ruleID in attribute['intrusionPrevention']['ruleIDs']:
            if str(ruleID) in rules_cves:
                # Update result set with ruleID
                rules.add(rules_cves[str(ruleID)]['identifier'])
                # Update result set with CVEs covered
                cves.update(rules_cves[str(ruleID)]['cves'])

    # Populate result set
    result['json'] = { "cves_covered": cves,
                       "rules_covering": rules }

    # We didn't change anything on the host
    result['changed'] = False

    # Return key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
