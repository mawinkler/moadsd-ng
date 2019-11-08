#!/bin/bash
run_env=""
run_inv=""
run_pb=""

env_options=("gcp" "aws" "esx")
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
    *) echo "invalid option $REPLY";;
  esac
done

pb_options=("site" "deploy" "deploy_endpoints" "deploy_deepsecurity" "deploy_smartcheck" "deploy_jenkins" "patch_docker" "terminate")
echo 'Please choose the playbook: '
select opt in "${pb_options[@]}"
do
  run_pb=$opt
  break
done

echo 'Running Playbook'
ansible-playbook --vault-password-file ../.vault-pass.txt -i ${run_inv} --extra-vars="type=${run_env}" ${run_pb}.yml
