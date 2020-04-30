#!/bin/bash

kubectl -n opa create configmap ${2} --from-literal=image=${1}

echo "Adding image to whitelist $1 $2"
exit 0
