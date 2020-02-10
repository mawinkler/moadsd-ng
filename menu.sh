#!/bin/bash
run_env=""
run_inv=""
run_pb=""

env_options=("gcp" "aws" "esx"
             "site_secrets"
             "switch_to_gcp" "switch_to_aws" "switch_to_esx")
echo 'Please choose the target environment: '
select opt in "${env_options[@]}"
do
  case $opt in
    "gcp")
    run_env=$opt
    run_inv="gcp_inventory.gcp.yml"
    break
    ;;
    "aws")
    run_env=$opt
    run_inv="ec2.py"
    break
    ;;
    "esx")
    run_env=$opt
    run_inv="hosts"
    break
    ;;
    "site_secrets")
    echo Running ansible-vault edit --vault-password-file ../.vault-pass.txt ./vars/site_secrets.yml
    ansible-vault edit --vault-password-file ../.vault-pass.txt ./vars/site_secrets.yml
    exit 0
    ;;
    "switch_to_gcp")
    echo Running ansible-playbook --vault-password-file ../.vault-pass.txt --extra-vars="type=gcp" switch_to_gcp.yml
    ansible-playbook --vault-password-file ../.vault-pass.txt --extra-vars="type=gcp" switch_to_gcp.yml
    exit 0
    ;;
    "switch_to_aws")
    echo Running ansible-playbook --vault-password-file ../.vault-pass.txt --extra-vars="type=aws" switch_to_aws.yml
    ansible-playbook --vault-password-file ../.vault-pass.txt --extra-vars="type=aws" switch_to_aws.yml
    exit 0
    ;;
    "switch_to_esx")
    echo Running ansible-playbook --vault-password-file ../.vault-pass.txt --extra-vars="type=esx" switch_to_esx.yml
    ansible-playbook --vault-password-file ../.vault-pass.txt --extra-vars="type=esx" switch_to_esx.yml
    exit 0
    ;;
    *) echo "invalid option $REPLY";;
  esac
done

pb_options=("site" "deploy" "deploy_endpoints"
            "jenkins_create_credentials"
            "pause" "resume" "terminate" "terminate_site")
echo 'Please choose the playbook: '
select opt in "${pb_options[@]}"
do
  run_pb=$opt
  break
done

echo Running ansible-playbook --vault-password-file ../.vault-pass.txt -i ${run_inv} --extra-vars="type=${run_env}" ${run_pb}.yml
ansible-playbook --vault-password-file ../.vault-pass.txt -i ${run_inv} --extra-vars="type=${run_env}" ${run_pb}.yml
