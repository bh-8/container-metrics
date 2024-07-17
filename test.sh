#!/bin/bash

cleanup="io/_csv/ io/_json/ io/_yara/ io/_svg/"
mongodb="mongodb://admin:admin@mongo-db:27017"
input="io/pdfs/ io/jpegs/ io/mp3s/"
collection="test"
log="" #"--log=debug"
#log=""

# "sections[?mime_type=='application/pdf'].segments.body[].[offset,length,object_number,data.data[].data]"

sudo rm -drf $cleanup \
    && docker compose build \
    && ./container-metrics query $mongodb $collection csv "sections[?mime_type=='audio/mpeg'].segments.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length]" "sections[?mime_type=='audio/mpeg'].segments.mpeg_frames[].[header.private,header.copyright,header.original]" $log \
    && ./container-metrics query $mongodb $collection svg "sections[?mime_type=='audio/mpeg'].segments.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length]" "sections[?mime_type=='audio/mpeg'].segments.mpeg_frames[].[header.private,header.copyright,header.original]" $log \
    && ./container-metrics query $mongodb $collection yara io/test.yara io/test2.yara $log \
    && ./container-metrics query $mongodb $collection json $log
