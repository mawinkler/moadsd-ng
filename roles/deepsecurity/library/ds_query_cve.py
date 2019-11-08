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
            - The API Key to access the Deep Security REST APPI

author:
    - Markus Winkler (markus_winkler@trendmicro.com)
'''

EXAMPLES = '''
# Retriece IPS rule identifiers coverering a given CVE
  - name: Query Deep Security for CVE covering IPS rules
    ds_query_cve:
      query: "{{ query }}"
      dsm_url: "https://{{ dsm_url }}:4119"
      api_key: "{{ api_key }}"
    register: ds_result

# Shell example
ansible-playbook ds_query_cve.yml --extra-vars '{"dsm_url":"<URL>",
                                                 "api_key":"<API-KEY>",
                                                 "query":"CVE-2015-1716"}'
'''

RETURN = '''
ds_query_cves:
    description: The list of IPS rules covering a given CVE
    type: dict
    sample:
    "msg": {
        "matched": true,
        "rules_covering": [
            "1006741",
            "1006740"
        ]
    }
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
        query=dict(type='str', required=True),
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
    # Retrieves intrusion prevention rules based on a given CVE
    rules = set()
    matched = False
    RESULT_SET_SIZE = 1000

    # Query rule identifier
    url = module.params['dsm_url'] + "/api/intrusionpreventionrules/search"
    data = { "maxItems": RESULT_SET_SIZE,
             "searchCriteria": [ { "fieldName": "CVE", "stringTest": "equal", "stringValue": "%"+module.params['query']+"%", "stringWildcards": "true" } ] }
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
            matched = True

    # Populate result set
    result['json'] = { "rules_covering": rules,
                       "matched": matched }

    # We didn't change anything on the host
    result['changed'] = False

    # Return key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
