#!/bin/bash

final_test() {
    # cleanup & fresh build
    docker compose down
    sudo rm -drf io/_* io/test/_* io/db 
    docker compose build
    docker compose up --detach

    MONGODB_CONNECTION="mongodb://admin:admin@mongo-db:27017"
    DB_ID="test"
    LOGGING="--log warning"

    STEGO_MSG_A="io/test/messageA.txt" # 36 chars
    STEGO_KEY_A="password" # 8 chars
    STEGO_TIMEOUT_A=20 # 20 seconds
    STEGO_MSG_B="io/test/messageB.txt" # 396 chars
    STEGO_KEY_B="this_password_is_ominous" # 24 chars
    STEGO_TIMEOUT_B=30 # 30 seconds

    ################################################################################
    # JFIF TESTS // JSON PIPELINE TESTS // YARA PIPELINE TESTS

    # prepare jfif cover files (333x)
    #./container-metrics $MONGODB_CONNECTION $DB_ID "jfif-cover" scan io/test/cover/jfif --recursive $LOGGING
    #./container-metrics $MONGODB_CONNECTION $DB_ID "jfif-cover" scan io/test/default-stego/camouflage --recursive $LOGGING
    #./container-metrics $MONGODB_CONNECTION $DB_ID "jfif-cover" yara io/jfif_signatures.yara -outid=jfif-cover $LOGGING

    #./container-metrics $MONGODB_CONNECTION $DB_ID "jfif-cover" json "*" -rrd -outid=jfif-cover $LOGGING

    # automatic stego generators: f5, hstego, jsteg, stegosuite
    #./stego-gen f5 io/test/cover/jfif io/test/_f5-36-8-20 $STEGO_MSG_A $STEGO_KEY_A -deo -t $STEGO_TIMEOUT_A
    #./stego-gen f5 io/test/cover/jfif io/test/_f5-396-24-30 $STEGO_MSG_B $STEGO_KEY_B -deo -t $STEGO_TIMEOUT_B
    #./stego-gen hstego io/test/cover/jfif io/test/_hstego-36-8-30 $STEGO_MSG_A $STEGO_KEY_A -deo -t $STEGO_TIMEOUT_B
    #./stego-gen hstego io/test/cover/jfif io/test/_hstego-396-24-30 $STEGO_MSG_B $STEGO_KEY_B -deo -t $STEGO_TIMEOUT_B
    #./stego-gen jsteg io/test/cover/jfif io/test/_jsteg-36-20 $STEGO_MSG_A -deo -t $STEGO_TIMEOUT_A
    #./stego-gen jsteg io/test/cover/jfif io/test/_jsteg-396-30 $STEGO_MSG_B -deo -t $STEGO_TIMEOUT_B
    #./stego-gen stegosuite io/test/cover/jfif io/test/_stegosuite-36-8-20 $STEGO_MSG_A $STEGO_KEY_A -deo -t $STEGO_TIMEOUT_A
    #./stego-gen stegosuite io/test/cover/jfif io/test/_stegosuite-396-24-30 $STEGO_MSG_B $STEGO_KEY_B -deo -t $STEGO_TIMEOUT_B

    # alternatively, load pre-computed stego files from tar archives to skip long waiting times
    #for i in "f5" "hstego" "jsteg" "stegosuite"; do
    #    tar -xzf "io/test/$i-stego.tar.gz" -C "io/test/."
    #    rm -f io/test/_*/*.json
    #done

    # yara rule evaluation and json export (loop stego file sets)
    #for i in "f5-36-8-20" "f5-396-24-30" "hstego-36-8-30" "hstego-396-24-30" "jsteg-36-20" "jsteg-396-30" "stegosuite-36-8-20" "stegosuite-396-24-30"; do
    #    ./container-metrics $MONGODB_CONNECTION $DB_ID "jfif-stego-$i" scan io/test/_$i --recursive $LOGGING
    #    ./container-metrics $MONGODB_CONNECTION $DB_ID "jfif-stego-$i" yara io/jfif_signatures.yara -outid=jfif-stego-$i $LOGGING
    #    ./container-metrics $MONGODB_CONNECTION $DB_ID "jfif-stego-$i" json "data[0].content.jpeg_segments[].[offset,length,raw]" -rrd -outid=jfif-stego-$i $LOGGING
    #done

    ################################################################################
    # MP3 TESTS // SVG PIPELINE TESTS // ARFF PIPELINE TESTS // YARA PIPELINE TESTS

    # prepare mp3 cover files (333x)
    #./container-metrics $MONGODB_CONNECTION $DB_ID "mp3-cover" scan io/test/cover/mp3 --recursive $LOGGING
    #tar -xzf "io/test/mp3stego-stego.tar.gz" -C "io/test/."
    #./container-metrics $MONGODB_CONNECTION $DB_ID "mp3-cover" yara io/mp3_signatures.yara -outid=mp3-cover $LOGGING
    #./container-metrics $MONGODB_CONNECTION $DB_ID "mp3-cover" json "*" -rrd -outid=mp3-cover $LOGGING
    # automatic stego generators: mp3stego, mp3stegolib, tamp3r
    #./stego-gen mp3stego io/test/cover/wav io/test/_mp3stego-36-8-20 $STEGO_MSG_A $STEGO_KEY_A -deo -t $STEGO_TIMEOUT_A
    #./stego-gen mp3stego io/test/cover/wav io/test/_mp3stego-396-24-30 $STEGO_MSG_B $STEGO_KEY_B -deo -t $STEGO_TIMEOUT_B
    #./stego-gen tamp3r io/test/cover/mp3 io/test/_tamp3r-36-8-20 $STEGO_MSG_A -deo -t $STEGO_TIMEOUT_A
    #./stego-gen tamp3r io/test/cover/mp3 io/test/_tamp3r-396-24-30 $STEGO_MSG_B -deo -t $STEGO_TIMEOUT_B

    # alternatively, load pre-computed stego files from tar archives to skip long waiting times
    #tar -xzf "io/test/mp3stego-stego.tar.gz" -C "io/test/."
    #sudo rm -f io/test/_*/*.json

    # yara rule evaluation and json export (loop stego file sets) "mp3stego-36-8-20" "mp3stego-396-24-30" "tamp3r-36-8-20" "tamp3r-396-24-30"
    #for i in "tamp3r-396-24-30"; do
    #    ./container-metrics $MONGODB_CONNECTION $DB_ID "mp3-stego-$i" scan io/test/_$i --recursive $LOGGING
    #    ./container-metrics $MONGODB_CONNECTION $DB_ID "mp3-stego-$i" yara io/mp3_signatures.yara -outid=mp3-stego-$i $LOGGING
    #done
    #./container-metrics $MONGODB_CONNECTION $DB_ID "mp3-stego-mp3stegz" scan io/test/default-stego/mp3stegz $LOGGING
    #./container-metrics $MONGODB_CONNECTION $DB_ID "mp3-stego-mp3stegz" yara io/mp3_signatures.yara -outid=mp3-stego-mp3stegz $LOGGING
    #./container-metrics $MONGODB_CONNECTION $DB_ID "mp3-stego-stegonaut" scan io/test/default-stego/stegonaut $LOGGING
    #./container-metrics $MONGODB_CONNECTION $DB_ID "mp3-stego-stegonaut" yara io/mp3_signatures.yara -outid=mp3-stego-stegonaut $LOGGING

    ################################################################################
    # PDF TESTS // XML PIPELINE TESTS // CSV PIPELINE TESTS // YARA PIPELINE TESTS

    # prepare pdf cover files (333x)
    ./container-metrics $MONGODB_CONNECTION $DB_ID "pdf-cover" scan io/test/cover/pdf --recursive $LOGGING
    #./container-metrics $MONGODB_CONNECTION $DB_ID "pdf-cover" scan io/test/default-stego/cat-pdf --recursive $LOGGING
    ./container-metrics $MONGODB_CONNECTION $DB_ID "pdf-cover" yara io/pdf_signatures.yara -outid=pdf-cover $LOGGING
    #./container-metrics $MONGODB_CONNECTION $DB_ID "pdf-cover" json "*" -outid=pdf-cover $LOGGING

    #./stego-gen boobytrappdf io/test/cover/pdf io/test/_boobytrappdf-36-20 $STEGO_MSG_A -deo -t $STEGO_TIMEOUT_A
    #./stego-gen boobytrappdf io/test/cover/pdf io/test/_boobytrappdf-396-30 $STEGO_MSG_B -deo -t $STEGO_TIMEOUT_B
    #./stego-gen pdfhide io/test/cover/pdf io/test/_pdfhide-36-8-20 $STEGO_MSG_A $STEGO_KEY_A -deo -t $STEGO_TIMEOUT_A
    #./stego-gen pdfhide io/test/cover/pdf io/test/_pdfhide-396-24-30 $STEGO_MSG_B $STEGO_KEY_B -deo -t $STEGO_TIMEOUT_B
    #./stego-gen pdfstego io/test/cover/pdf io/test/_pdfstego-36-8-20 $STEGO_MSG_A $STEGO_KEY_A -deo -t $STEGO_TIMEOUT_A
    #./stego-gen pdfstego io/test/cover/pdf io/test/_pdfstego-396-24-30 $STEGO_MSG_B $STEGO_KEY_B -deo -t $STEGO_TIMEOUT_B

    # alternatively, load pre-computed stego files from tar archives to skip long waiting times
    #tar -xzf "io/test/pdfhide-stego.tar.gz" -C "io/test/."
    #sudo rm -f io/test/_*/*.json

    # yara rule evaluation and json export (loop stego file sets)
    #for i in "pdfstego-396-24-30"; do
    #    ./container-metrics $MONGODB_CONNECTION $DB_ID "pdf-stego-$i" scan io/test/_$i --recursive $LOGGING
    #    ./container-metrics $MONGODB_CONNECTION $DB_ID "pdf-stego-$i" yara io/pdf_signatures.yara -outid=mp3-stego-$i $LOGGING
    #done
    exit

    






    # arff pipeline: stegonaut training example
    jmesq_arff_cover="data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[header.private,header.copyright,header.original] \
    | [map(&to_string([0]), @), map(&to_string([1]), @), map(&to_string([2]), @)] \
    | [[length([@[0] | [?@ == 'true']] | []), length([@[0] | [?@ == 'false']] | []), length([@[1] | [?@ == 'true']] | []), \
      length([@[1] | [?@ == 'false']] | []), length([@[2] | [?@ == 'true']] | []), length([@[2] | [?@ == 'false']] | []), \
      'false']]"
    ./container-metrics $MONGODB_CONNECTION $DB_ID "mp3-cover-files" \
        arff "private set,private unset,copyright set,copyright unset,original set,original unset,is stego" "${jmesq_arff_cover}" --categorical=7 $LOGGING -outid=stegonaut-cover
    jmesq_arff_stego="data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[header.private,header.copyright,header.original] \
    | [map(&to_string([0]), @), map(&to_string([1]), @), map(&to_string([2]), @)] \
    | [[length([@[0] | [?@ == 'true']] | []), length([@[0] | [?@ == 'false']] | []), length([@[1] | [?@ == 'true']] | []), \
      length([@[1] | [?@ == 'false']] | []), length([@[2] | [?@ == 'true']] | []), length([@[2] | [?@ == 'false']] | []), \
      'true']]"
    ./container-metrics $MONGODB_CONNECTION $DB_ID "default-stego-files" \
        arff "private set,private unset,copyright set,copyright unset,original set,original unset,is stego" "${jmesq_arff_stego}" --categorical=7 $LOGGING -outid=stegonaut-stego
    ./merge_arff.sh && sudo rm -f io/_arff/*.arff io/_stegonaut.arff && mv io/_combined.arff io/_stegonaut.arff
        # -> fix io/_stegonaut.arff before further processing in weka!


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
