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
            "jenkins_create_credentials" "deploy_gitlab_runners"
            "pause" "resume" "terminate" "terminate_site" "manual")

echo 'Please choose the playbook: '
select opt in "${pb_options[@]}"
do
  # case $opt in
  #   "manual")
  #   select manual_pb in "${pb_manual[@]}"
  #   do
  #     # case $manual_pb
  #     opt=$manual_pb
  #     run_pb=$opt
  #     break
  #       # ;;
  #     # esac
  #   done
  #   ;;
  #   *) run_pb=$opt
  #   break
  #   ;;
  # esac
  run_pb=$opt
  break
done

if [ $run_pb = "manual" ]
then
  pb_manual=( $(find . -maxdepth 1 -name deploy_\*.yml  -exec basename {} .yml \; | sort ) )
  echo 'Please choose the playbook: '
  select opt in "${pb_manual[@]}"
  do
    # case $manual_pb
    run_pb=$opt
    break
  done
fi

echo Running ansible-playbook --vault-password-file ../.vault-pass.txt -i ${run_inv} --extra-vars="type=${run_env}" ${run_pb}.yml
ansible-playbook --vault-password-file ../.vault-pass.txt -i ${run_inv} --extra-vars="type=${run_env}" ${run_pb}.yml
