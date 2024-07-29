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
ENV_LOGGING="--log warning"

tests_arff() {
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET arff "part2_3_length granule 0,part2_3_length granule 1" "sections[?mime_type=='audio/mpeg'].segments.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | []" $ENV_LOGGING -outid=hdrflds
}

tests_csv() {
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET csv "header.private,header.copyright,header.original" "sections[?mime_type=='audio/mpeg'].segments.mpeg_frames[].[header.private,header.copyright,header.original]" $ENV_LOGGING -outid=hdrflds
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET csv "part2_3_length granule 0,part2_3_length granule 1" "sections[?mime_type=='audio/mpeg'].segments.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length]" $ENV_LOGGING --output-identifier=p23l
}

tests_json() {
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET json $ENV_LOGGING
}

tests_svg() {
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET svg "mpeg frames" "part2_3_length" "sections[?mime_type=='audio/mpeg'].segments.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length]" $ENV_LOGGING
}

tests_yara() {
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET yara io/test.yara $ENV_LOGGING -outid=test
    ./container-metrics $ENV_MONGODB_CONNECTION $ENV_PROJECT $ENV_SET yara io/test2.yara $ENV_LOGGING -outid=test2
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
