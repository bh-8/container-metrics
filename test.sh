#!/bin/bash

ENV_CLEANUP="io/_csv/ io/_json/ io/_yara/ io/_svg/"
ENV_CLEANUP_ALL="${ENV_CLEANUP} io/db/"

ENV_INPUT_DATA="io/pdfs/ io/jpegs/ io/mp3s/"
ENV_MONGODB_CONNECTION="mongodb://admin:admin@mongo-db:27017"
ENV_MONGODB_COLLECTION="test"
ENV_LOGGING="" #"--log=debug"

tests_csv()
{
    ./container-metrics query $ENV_MONGODB_CONNECTION $ENV_MONGODB_COLLECTION csv "sections[?mime_type=='audio/mpeg'].segments.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length]" "sections[?mime_type=='audio/mpeg'].segments.mpeg_frames[].[header.private,header.copyright,header.original]" $ENV_LOGGING
}

tests_json()
{
    ./container-metrics query $ENV_MONGODB_CONNECTION $ENV_MONGODB_COLLECTION json $ENV_LOGGING
}

tests_svg()
{
    ./container-metrics query $ENV_MONGODB_CONNECTION $ENV_MONGODB_COLLECTION svg "sections[?mime_type=='audio/mpeg'].segments.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length]" "sections[?mime_type=='audio/mpeg'].segments.mpeg_frames[].[header.private,header.copyright,header.original]" $ENV_LOGGING
}

tests_yara()
{
    ./container-metrics query $ENV_MONGODB_CONNECTION $ENV_MONGODB_COLLECTION yara io/test.yara io/test2.yara $ENV_LOGGING
}

tests_pls()
{
    sudo rm -drf $ENV_CLEANUP
    docker compose build
    tests_csv
    tests_json
    tests_svg
    tests_yara
}

tests_all()
{
    sudo rm -drf $ENV_CLEANUP_ALL
    docker compose build
    ./container-metrics acquire $ENV_MONGODB_CONNECTION $ENV_MONGODB_COLLECTION $ENV_INPUT_DATA $ENV_LOGGING
    tests_csv
    tests_json
    tests_svg
    tests_yara
}

test_help() {
    echo "Syntax: ./test.sh {mode}"
    echo "  modes:"
    echo "    all   - cleanup + acquisition + all pipelines"
    echo "    pls   - all pipelines"
    echo "    csv   - csv pipeline"
    echo "    json  - json pipeline"
    echo "    svg   - svg pipeline"
    echo "    yara  - yara pipeline"
}

if [[ $# > 0 ]]; then
    case $1 in
        all)
            tests_all
            ;;
        pls)
            tests_pls
            ;;
        csv)
            tests_csv
            ;;
        json)
            tests_json
            ;;
        svg)
            tests_svg
            ;;
        yara)
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
