#!/bin/bash

cleanup="io/_csv/ io/_json/ io/_yara/ io/db/"
mongodb="mongodb://admin:admin@mongo-db:27017"
input="io/pdfs/ io/jpegs/ io/mp3s/"
collection="test"
log="--log=info"
#log=""

docker compose build \
    && sudo rm -drf $cleanup \
    && ./container-metrics acquire $mongodb $collection $input $log \
    && ./container-metrics query $mongodb $collection json $log