#!/bin/bash

filename="plot_data.tsv"
services=("influx" "questdb" "timescaledb" "victoriametrics")

header="\"TestType\""
for service in "${services[@]}"; do
  header+=" \"${service}\""
done

echo "$header" >${filename}

test_types=("devops" "iot" "cpu_only")

for test in "${test_types[@]}"; do
  test_averages=()
  for service in "${services[@]}"; do
    file="tsbs_${service}_1000.json"
    if [ -f "$file" ]; then
      average=$(jq -r ".${test}.rows_avg" "$file")
      test_averages+=("$average")
    else
      echo "Warning: File '$file' not found for service '$service' and test '$test'."
      test_averages+=("NaN")
    fi
  done
  echo "\"${test//_/ }\" ${test_averages[*]}" >>${filename}
done

echo "generated ${filename}"

gnuplot benchmark.plt
