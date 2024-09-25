#!/bin/bash

final_test() {
    # cleanup & fresh build
    #docker compose down
    sudo rm -drf io/_* io/test/_* # io/db 
    docker compose build
    #docker compose up --detach

    # generate stego files
    #STEGO_MSG="io/test/messageA.txt" # 36 chars
    #STEGO_KEY="password" # 8 chars

    #./stego-gen boobytrappdf io/test/cover/pdf io/test/_boobytrappdf $STEGO_MSG -deo -t 16
    #./stego-gen f5 io/test/cover/jfif io/test/_f5 $STEGO_MSG $STEGO_KEY -deo -t 16
    #./stego-gen hstego io/test/cover/jfif io/test/_hstego $STEGO_MSG $STEGO_KEY -deo -t 16
    #./stego-gen jsteg io/test/cover/jfif io/test/_jsteg $STEGO_MSG -deo -t 16
    #./stego-gen mp3stego io/test/cover/wav io/test/_mp3stego $STEGO_MSG $STEGO_KEY -deo -t 16
    #./stego-gen pdfhide io/test/cover/pdf io/test/_pdfhide $STEGO_MSG $STEGO_KEY -deo -t 16
    #./stego-gen pdfstego io/test/cover/pdf io/test/_pdfstego $STEGO_MSG $STEGO_KEY -deo -t 16

    # definitions
    MONGODB_CONNECTION="mongodb://admin:admin@mongo-db:27017"
    DB_ID="test"
    LOGGING="--log warning"

    # scan cover/stego files
    #./container-metrics $MONGODB_CONNECTION $DB_ID "jfif-cover-files" scan io/test/cover/jfif/ --recursive $LOGGING
    #./container-metrics $MONGODB_CONNECTION $DB_ID "mp3-cover-files" scan io/test/cover/mp3/ --recursive $LOGGING
    #./container-metrics $MONGODB_CONNECTION $DB_ID "pdf-cover-files" scan io/test/cover/pdf/ --recursive $LOGGING
    #./container-metrics $MONGODB_CONNECTION $DB_ID "default-stego-files" scan io/test/default-stego/ --recursive $LOGGING

    # json pipeline
    #./container-metrics $MONGODB_CONNECTION $DB_ID "pdf-cover-files" \
    #    json "data[?mime_type=='application/pdf'].content.whitespaces[].raw" $LOGGING -outid=openpuff -rrd
    #./container-metrics $MONGODB_CONNECTION $DB_ID "default-stego-files" \
    #    json "data[?mime_type=='application/pdf'].content.whitespaces[].raw" $LOGGING -outid=openpuff -rrd

    # arff pipeline
    jmesq_arff_cover="data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[header.private,header.copyright,header.original] | [map(&to_string([0]), @), map(&to_string([1]), @), map(&to_string([2]), @)] | [[length([@[0] | [?@ == 'true']] | []), length([@[0] | [?@ == 'false']] | []), length([@[1] | [?@ == 'true']] | []), length([@[1] | [?@ == 'false']] | []), length([@[2] | [?@ == 'true']] | []), length([@[2] | [?@ == 'false']] | []), 'false']]"
    jmesq_arff_stego="data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[header.private,header.copyright,header.original] | [map(&to_string([0]), @), map(&to_string([1]), @), map(&to_string([2]), @)] | [[length([@[0] | [?@ == 'true']] | []), length([@[0] | [?@ == 'false']] | []), length([@[1] | [?@ == 'true']] | []), length([@[1] | [?@ == 'false']] | []), length([@[2] | [?@ == 'true']] | []), length([@[2] | [?@ == 'false']] | []), 'true']]"
    ./container-metrics $MONGODB_CONNECTION $DB_ID "mp3-cover-files" \
        arff "private set,private unset,copyright set,copyright unset,original set,original unset,is stego" "${jmesq_arff_cover}" $LOGGING -outid=stegonaut-cover
    ./container-metrics $MONGODB_CONNECTION $DB_ID "default-stego-files" \
        arff "private set,private unset,copyright set,copyright unset,original set,original unset,is stego" "${jmesq_arff_stego}" $LOGGING -outid=stegonaut-stego
    ./arff_merge.sh

    exit

    # csv pipeline
    ./container-metrics $MONGODB_CONNECTION $DB_ID "default-stego-files" \
        csv "header.private,header.copyright,header.original" \
        "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[header.private,header.copyright,header.original]" \
        -outid=headerbits $LOGGING
    ./container-metrics $MONGODB_CONNECTION $DB_ID "default-stego-files" \
        csv "part2_3_length granule 0,part2_3_length granule 1" \
        "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length]" \
        -outid=part23length $LOGGING

    # svg pipeline
    ./container-metrics $MONGODB_CONNECTION $DB_ID "jfif-cover-files" \
        svg hist "jpeg segments" "amount" \
        "data[?mime_type=='image/jpeg'].content.jpeg_segments[].name" \
        -outid=histogram $LOGGING
    ./container-metrics $MONGODB_CONNECTION $DB_ID "default-stego-files" \
        svg plot "mpeg frames" "part2_3_length" \
        "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | map(&[], @)" \
        --width=16 -outid=p23l $LOGGING
    ./container-metrics $MONGODB_CONNECTION $DB_ID "default-stego-files" \
        svg plot "mpeg frames" "part2_3_length 1st derivative" \
        "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | map(&[], @) | zip(@[0:-1], @[1:]) | map(&zip(@[0], @[1]), @) | map(&map(&(@[1] - @[0]), @), @)" \
        --width=16 -outid=p23lderiv1 $LOGGING
    ./container-metrics $MONGODB_CONNECTION $DB_ID "default-stego-files" \
        svg plot "mpeg frames" "part2_3_length 2nd derivative" \
        "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | map(&[], @) | zip(@[0:-1], @[1:]) | map(&zip(@[0], @[1]), @) | map(&map(&(@[1] - @[0]), @), @) | zip(@[0:-1], @[1:]) | map(&zip(@[0], @[1]), @) | map(&map(&(@[1] - @[0]), @), @)" \
        --width=16 -outid=p23lderiv2 $LOGGING

    # xml pipeline
    ./container-metrics $MONGODB_CONNECTION $DB_ID "default-stego-files" \
        xml "data[?mime_type=='application/pdf'].content.body" $LOGGING -outid=js
    ./container-metrics $MONGODB_CONNECTION $DB_ID "default-stego-files" \
        xml "*" $LOGGING

    # apply yara rules
    ./container-metrics $MONGODB_CONNECTION $DB_ID "default-stego-files" \
        yara io/signatures.yara -outid=default $LOGGING
}

final_test

exit 0

test_help() {
    echo "Syntax: ./test.sh {mode}"
    echo "  modes:"
    echo "    all   - cleanup + acquisition + all pipelines"
    echo "    rscn  - rescan"
    echo "    pls   - all pipelines"
    echo "    arff  - arff pipeline"
    echo "    csv   - csv pipeline"
    echo "    json  - json pipeline"
    echo "    svg   - svg pipeline"
    echo "    xml   - xml pipeline"
    echo "    yara  - yara pipeline"
}

if [[ $# > 0 ]]; then
    case $1 in
        all)
            sudo rm -drf $ENV_CLEANUP_ALL
            docker compose build
            tests_all
            ;;
        rscn)
            sudo rm -drf $ENV_CLEANUP_DB
            docker compose build
            tests_scan
            ;;
        pls)
            sudo rm -drf $ENV_CLEANUP
            docker compose build
            tests_pls
            ;;
        arff)
            sudo rm -drf $ENV_ARFF
            docker compose build
            tests_arff
            ;;
        csv)
            sudo rm -drf $ENV_CSV
            docker compose build
            tests_csv
            ;;
        json)
            sudo rm -drf $ENV_JSON
            docker compose build
            tests_json
            ;;
        svg)
            sudo rm -drf $ENV_SVG
            docker compose build
            tests_svg
            ;;
        xml)
            sudo rm -drf $ENV_XML
            docker compose build
            tests_xml
            ;;
        yara)
            sudo rm -drf $ENV_YARA
            docker compose build
            tests_yara
            ;;
        *)
            test_help
            exit 1
            ;;
    esac
else
    test_help
    exit 1
fi
exit 0
