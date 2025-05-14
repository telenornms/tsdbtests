#!/bin/bash
services=("influx" "questdb" "timescaledb" "victoriametrics")
test_types=("devops" "iot" "cpu_only")

header="\"TestType\""
for service in "${services[@]}"; do
  header+=" \"${service}\""
done
echo "$header" >plot_data.tsv

for test in "${test_types[@]}"; do
  line="\"${test//_/ }\""
  for service in "${services[@]}"; do
    file="tsbs_test_${service}-1000.json"
    if [ -f "$file" ]; then
      average=$(jq -r ".${service}_test_${test}.rows_avg" "$file")
      truncd_avg=${average%.*}
      line+=" $truncd_avg"
    else
      echo "Warning: File '$file' not found for service '$service' and test '$test'."
      line+=" NaN"
    fi
  done
  echo "$line" >>plot_data.tsv
done
echo "Data for histogram generated in plot_data.tsv"
