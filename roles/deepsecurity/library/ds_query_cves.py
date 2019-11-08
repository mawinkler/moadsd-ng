#!/usr/bin/python
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ds_query_cves

short_description: Retrieves IPS rule identifiers coverering a given list of CVEs

version_added: "2.6"

description:
    - "This module retrieves IPS rule identifiers to protect against a list of
       CVEs. The results includes the number of covered and uncovered CVEs."

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
    # Retrieves intrusion prevention rules based on a list of given CVEs
    rules = set()
    match_counter = 0
    unmatch_counter = len(module.params['query'])
    RESULT_SET_SIZE = 1000

    for cve in module.params['query']:
        matched = False

        # Query rule identifier
        url = module.params['dsm_url'] + "/api/intrusionpreventionrules/search"
        data = { "maxItems": RESULT_SET_SIZE,
                 "searchCriteria": [ { "fieldName": "CVE",
                                       "stringTest": "equal",
                                       "stringValue": "%" + cve + "%",
                                       "stringWildcards": "true" } ] }
        post_header = { "Content-type": "application/json",
                        "api-secret-key": module.params['api_key'],
                        "api-version": "v1"}
        response = requests.post(url, data=json.dumps(data), headers=post_header, verify=False).json()

        if 'intrusionPreventionRules' not in response:
            matched = False
        else:
            results = response['intrusionPreventionRules']
            for rule in results:
                rules.add(rule['identifier'])
                if (matched == False):
                    match_counter += 1
                    unmatch_counter -= 1
                    matched = True

    # Populate result set
    result['json'] = { "rules_covering": rules,
                       "cves_matched": match_counter,
                       "cves_unmatched": unmatch_counter }

    # We didn't change anything on the host
    result['changed'] = False

    # Return key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
