#!/bin/bash
docker container stop $(docker container ls | grep "container-metrics-cli" | cut -f1 -d" ")
docker container stop $(docker container ls | grep "container-metrics-stego-gen" | cut -f1 -d" ")
exit
