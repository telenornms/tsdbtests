#!/bin/bash

workers=$1

filename="averages_w${workers}.tsv"
services=("influx" "questdb" "timescaledb" "victoriametrics")

header="\"TestType\""
for service in "${services[@]}"; do
  header+=" \"${service}\""
done

echo "$header" >"${filename}"

test_types=("devops" "iot")

for test in "${test_types[@]}"; do
  test_averages=()
  for service in "${services[@]}"; do
    file="tsbs_${service}_s1000_w${workers}.json"
    if [ -f "$file" ]; then
      average=$(jq -r ".${test}.rows_avg" "$file")
      test_averages+=("$average")
    else
      echo "Warning: File '$file' not found for service '$service' and test '$test'."
      test_averages+=("NaN")
    fi
  done
  echo "\"${test//_/ }\" ${test_averages[*]}" >>"${filename}"
done

echo "generated ${filename}"

gnuplot -c comp_histogram.plt "$workers"
