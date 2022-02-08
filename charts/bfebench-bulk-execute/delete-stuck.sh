#!/bin/bash

pods=$(kubectl -n bfebench get pods | grep Running | awk '{print $1}')
for pod in $pods ; do
  kubectl -n bfebench logs "$pod" -c bfebench
  read -p "Pod stuck/delete? [yes/No] "
  if [ "$reply" == "yes" ] ; then
    kubectl -n bfebench delete pod "$pod"
  fi
done
