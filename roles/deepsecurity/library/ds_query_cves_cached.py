#!/usr/bin/python
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ds_query_cves_cached

short_description: Retrieves IPS rule identifiers coverering a given list of CVEs

version_added: "2.6"

description:
    - "This module retrieves IPS rule identifiers to protect against a list of
       CVEs. The results includes the number of covered and uncovered CVEs.
       This module is suitable for long lists of CVEs because of it's
       internal IPS rule cache."

options:
    query:
        description:
            - The list of CVEs to be checked
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
# Retrieve IPS rule identifiers coverering a given list of CVEs
- name: Query Deep Security for IPS rule identifieres matching a list of CVEs
  ds_query_cves:
    query: "{{ query }}"
    dsm_url: "https://{{ dsm_url }}:4119"
    api_key: "{{ api_key }}"
  register: ds_result

# Shell example
ansible-playbook ds_query_cves.yml --extra-vars '{"dsm_url":"<URL>",
                                                  "api_key":"<API-KEY>",
                                                  "query":[CVE-2018-5019, CVE-2018-8236]}'  
'''

RETURN = '''
ds_query_cves:
    description: The list of IPS rules covering a list of CVEs
    type: dict
    sample:
        "changed": false,
        "failed": false,
        "json": {
            "msg": {
                "cves_matched": 2,
                "cves_unmatched": 0,
                "rules_covering": [
                    "1009137",
                    "1009207"
                ]
            }
        },
        "message": ""
'''

from ansible.module_utils.basic import AnsibleModule
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import requests
import json
import sys
import os
import time
import pickle
import os.path

def build_rules_cves_map(dsm_url, api_key):
    '''
    Build dictionary of intrusion prevention rules with the ability to cover CVEs
    '''
    # Constants
    RESULT_SET_SIZE = 1000
    MAX_RULE_ID= 10000

    # Return dictionary
    rules_cves = {}

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
            rules_cves[str(rule['ID']).strip()] = cves

    return rules_cves

def run_module():

    # Argument & parameter definitions
    module_args = dict(
        query=dict(type='list', required=True),
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

    # Retrieves intrusion prevention rules based on a list of given CVEs
    rules = set()
    rules_mapping = set()
    matched_list = set()
    unmatched_list = set()
    match_counter = 0
    unmatch_counter = len(module.params['query'])

    cves_list = {}
    if os.path.isfile('cves_network.cache'):
        with open('cves_network.cache', 'rb') as fp:
            cves_list = pickle.load(fp)

    for cve in module.params['query']:
        matched = False
        attack_vector = ""
        criticality = ""
        for rule in rules_cves:
            if str(cve) in cves_list:
                attack_vector = " NETWORK"
                criticality = " : " + cves_list[str(cve)]
            if str(cve) in rules_cves[str(rule)]:
                # Query rule identifier
                url = module.params['dsm_url'] + "/api/intrusionpreventionrules/search"
                data = { "maxItems": 1,
                         "searchCriteria": [ { "fieldName": "ID",
                                               "idTest": "equal",
                                               "idValue": str(rule) } ] }
                post_header = { "Content-type": "application/json",
                                "api-secret-key": module.params['api_key'],
                                "api-version": "v1"}
                response = requests.post(url, data=json.dumps(data), headers=post_header, verify=False).json()
                rules.add(response['intrusionPreventionRules'][0]['identifier'])
                rules_mapping.add(response['intrusionPreventionRules'][0]['identifier'] + " (" + str(cve) + ")" + attack_vector + criticality)
                matched_list.add(str(cve) + attack_vector + criticality)
                if (matched == False):
                    match_counter += 1
                    unmatch_counter -= 1
                    matched = True
        if (matched == False):
            unmatched_list.add(str(cve) + attack_vector + criticality)

    # Populate result set
    result['json'] = { "rules_covering": rules,
                       "rules_mapping": rules_mapping,
                       "cves_matched": matched_list,
                       "cves_unmatched": unmatched_list,
                       "cves_matched_count": match_counter,
                       "cves_unmatched_count": unmatch_counter }

    # We didn't change anything on the host
    result['changed'] = False

    # Return key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
