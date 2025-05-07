#!/bin/bash

services=("influx" "questdb" "timescaledb" "victoriametrics")

header="# TestType"
for service in "${services[@]}"; do
  header+=" \"${service}\""
done

echo "$header" >histogram_data.dat

test_types=("devops" "iot" "cpu_only")

# Collect data for each test type across all services
for test in "${test_types[@]}"; do
  test_averages=()
  for service in "${services[@]}"; do
    file="tsbs_test_${service}-1000.json"
    if [ -f "$file" ]; then
      average=$(jq -r ".${service}_test_${test}.rows_avg" "$file")
      # remove floating point precision
      truncd_avg=${average%.*}
      test_averages+=("$truncd_avg")
    else
      echo "Warning: File '$file' not found for service '$service' and test '$test'."
      test_averages+=("NaN")
    fi
  done
  echo "\"${test}\" ${test_averages[*]}" >>histogram_data.dat
done

echo "Data for histogram generated in histogram_data.dat"
