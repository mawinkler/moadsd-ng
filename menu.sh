#!/bin/bash
run_env=""
run_inv=""
run_pb=""

source ./.project
source ./.user

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
    # run_inv="ec2.py"
    run_inv="aws_ec2.yml"
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
    echo Running ansible-playbook --vault-password-file ../.vault-pass.txt --limit tag_project_${PROJECT},localhost --extra-vars=\"type=gcp run_pb=switch_to_gcp\" switch_to_gcp.yml
    ansible-playbook --vault-password-file ../.vault-pass.txt --limit tag_project_${PROJECT},localhost --extra-vars="type=gcp run_pb=switch_to_gcp" switch_to_gcp.yml
    exit 0
    ;;
    "switch_to_aws")
    echo Running ansible-playbook --vault-password-file ../.vault-pass.txt --limit tag_project_${PROJECT},localhost --extra-vars=\"type=aws run_pb=switch_to_aws\" switch_to_aws.yml
    ansible-playbook --vault-password-file ../.vault-pass.txt --limit tag_project_${PROJECT},localhost --extra-vars="type=aws run_pb=switch_to_aws" switch_to_aws.yml
    exit 0
    ;;
    "switch_to_esx")
    echo Running ansible-playbook --vault-password-file ../.vault-pass.txt --limit tag_project_${PROJECT},localhost --extra-vars=\"type=esx run_pb=switch_to_esx\" switch_to_esx.yml
    ansible-playbook --vault-password-file ../.vault-pass.txt --limit tag_project_${PROJECT},localhost --extra-vars="type=esx run_pb=switch_to_esx" switch_to_esx.yml
    exit 0
    ;;
    *) echo "invalid option $REPLY";;
  esac
done

pb_options=("site" "deploy" "deploy_endpoints"
            "jenkins_create_credentials" "deploy_gitlab_runners"
            "pause" "pause_scheduled" "pause_scheduled_cancel" "resume"
            "terminate" "terminate_site" "configuration" "manual")
echo 'Please choose the playbook: '
select opt in "${pb_options[@]}"
do
  run_pb=$opt
  break
done

if [ $run_pb = "configuration" ]
then
  ansible-vault edit --vault-password-file ../.vault-pass.txt ./configuration.yml
  ansible-playbook --vault-password-file ../.vault-pass.txt -i ${run_inv} --extra-vars="type=${run_env} run_pb=configurator" configurator.yml
  exit 0
fi

if [ $run_pb = "manual" ]
then
  pb_manual=( $(find . -maxdepth 1 -name deploy_\*.yml  -exec basename {} .yml \; | sort ) )
  echo 'Please choose the playbook: '
  select opt in "${pb_manual[@]}"
  do
    run_pb=$opt
    break
  done
fi

if [ $run_pb = "site" ]
then
  echo Running ansible-playbook --vault-password-file ../.vault-pass.txt -i ${run_inv} --extra-vars=\"type=${run_env} run_pb=${run_pb} user=${USER}\" ${run_pb}.yml
  ansible-playbook --vault-password-file ../.vault-pass.txt -i ${run_inv} --extra-vars="type=${run_env} run_pb=${run_pb} user=${USER}" ${run_pb}.yml
elif [ $run_pb = "pause" ]
then
  echo Running ansible-playbook --vault-password-file ../.vault-pass.txt -i ${run_inv} --extra-vars=\"type=${run_env} run_pb=${run_pb} user=${USER}\" ${run_pb}_${run_env}.yml
  ansible-playbook --vault-password-file ../.vault-pass.txt -i ${run_inv} --extra-vars="type=${run_env} run_pb=${run_pb} user=${USER}" ${run_pb}_${run_env}.yml
else
  echo Running ansible-playbook --vault-password-file ../.vault-pass.txt -i ${run_inv} --extra-vars=\"type=${run_env} run_pb=${run_pb} user=${USER}\" ${run_pb}.yml
  ansible-playbook --vault-password-file ../.vault-pass.txt -i ${run_inv} --extra-vars="type=${run_env} run_pb=${run_pb} user=${USER}" ${run_pb}.yml
fi
