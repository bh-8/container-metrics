#!/bin/bash

ENV_ARFF="io/_arff/"
ENV_CSV="io/_csv/"
ENV_JSON="io/_json/"
ENV_SVG="io/_svg/"
ENV_YARA="io/_yara/"

ENV_CLEANUP="${ENV_ARFF} ${ENV_CSV} ${ENV_JSON} ${ENV_SVG} ${ENV_YARA}"
ENV_CLEANUP_ALL="${ENV_CLEANUP} io/db/"

ENV_INPUT_DATA="io/pdfs/ io/jpegs/ io/mp3s/"
ENV_MONGODB_CONNECTION="mongodb://admin:admin@mongo-db:27017"
ENV_PROJECT="test"
ENV_SET="test"
ENV_LOGGING="--log warning" # warning"

tests_arff() {
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET arff "part2_3_length granule 0,part2_3_length granule 1" "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | []" $ENV_LOGGING -outid=hdrflds
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET arff "part2_3_length granule 0,part2_3_length granule 1" "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | []" $ENV_LOGGING -outid=hdrflds2 --categorical=1
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET arff "part2_3_length granule 0,part2_3_length granule 1" "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | []" $ENV_LOGGING -outid=hdrflds3 --categorical=1,2
}

tests_csv() {
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET csv "header.private,header.copyright,header.original" "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[header.private,header.copyright,header.original]" $ENV_LOGGING -outid=hdrflds
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET csv "part2_3_length granule 0,part2_3_length granule 1" "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length]" $ENV_LOGGING --output-identifier=p23l
}

tests_json() {
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET json "*" $ENV_LOGGING
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET json "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length]" $ENV_LOGGING -outid=test_plot1
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET json "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | []" $ENV_LOGGING -outid=test_plot2
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET json "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | map(&[], @)" $ENV_LOGGING -outid=test_plot3
}

tests_svg() {
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET svg hist "jpeg segments" "amount" "data[?mime_type=='image/jpeg'].content.jpeg_segments[].name" $ENV_LOGGING -outid=hist
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET svg plot "mpeg frames" "part2_3_length" "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length]" $ENV_LOGGING -outid=p23l1 --width=16 --height=9
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET svg plot "mpeg frames" "part2_3_length" "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | map(&[], @)" $ENV_LOGGING -outid=p23l2 --width=16
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET svg plot "mpeg frames" "part2_3_length 1st derivative" "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | map(&[], @) | zip(@[0:-1], @[1:]) | map(&zip(@[0], @[1]), @) | map(&map(&(@[1] - @[0]), @), @)" $ENV_LOGGING -outid=p23l1stderiv --width=16
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET svg plot "mpeg frames" "part2_3_length 2nd derivative" "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | map(&[], @) | zip(@[0:-1], @[1:]) | map(&zip(@[0], @[1]), @) | map(&map(&(@[1] - @[0]), @), @) | zip(@[0:-1], @[1:]) | map(&zip(@[0], @[1]), @) | map(&map(&(@[1] - @[0]), @), @)" $ENV_LOGGING -outid=p23l2ndderiv --width=16
}

tests_yara() {
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET yara io/signatures.yara $ENV_LOGGING
}

tests_pls() {
    tests_arff
    tests_csv
    tests_json
    tests_svg
    tests_yara
}

tests_all() {
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET scan $ENV_INPUT_DATA $ENV_LOGGING
    tests_pls
}

test_help() {
    echo "Syntax: ./test.sh {mode}"
    echo "  modes:"
    echo "    all   - cleanup + acquisition + all pipelines"
    echo "    pls   - all pipelines"
    echo "    arff  - arff pipeline"
    echo "    csv   - csv pipeline"
    echo "    json  - json pipeline"
    echo "    svg   - svg pipeline"
    echo "    yara  - yara pipeline"
}

if [[ $# > 0 ]]; then
    case $1 in
        all)
            sudo rm -drf $ENV_CLEANUP_ALL
            docker compose build
            tests_all
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
