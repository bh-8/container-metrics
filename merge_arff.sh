#!/bin/bash

out_file=io/_combined.arff

is_headline=1
for file in io/_arff/*.arff; do
    if [ "$is_headline" -eq 1 ]; then
        is_headline=0
        cat $file > $out_file
        echo "" >> $out_file
    else
        awk "/@DATA/{flag=1; next} flag" "$file" >> $out_file
    fi
done

exit