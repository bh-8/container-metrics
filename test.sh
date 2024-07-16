#!/bin/bash

cleanup="io/_csv/ io/_json/ io/_yara/ io/db/"
mongodb="mongodb://admin:admin@mongo-db:27017"
input="io/pdfs/ io/jpegs/ io/mp3s/"
collection="test"
log="" #"--log=debug"
#log=""

sudo rm -drf $cleanup \
    && docker compose build \
    && ./container-metrics acquire $mongodb $collection $input $log \
    && ./container-metrics query $mongodb $collection json $log \
    && ./container-metrics query $mongodb $collection csv application/pdf:xref:offset,length $log \
    && ./container-metrics query $mongodb $collection yara io/test.yara $log