#!/bin/bash

# Default values
SCALE_MIN=100
SCALE_MAX=1000
SCALE_STEP=100
WORKERS=20
DATABASES="influx,questdb,timescaledb,victoriametrics"
OUTPUT_FILE="database_performance.tsv"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
  --scale-min)
    SCALE_MIN="$2"
    shift 2
    ;;
  --scale-max)
    SCALE_MAX="$2"
    shift 2
    ;;
  --scale-step)
    SCALE_STEP="$2"
    shift 2
    ;;
  --workers)
    WORKERS="$2"
    shift 2
    ;;
  --databases)
    DATABASES="$2"
    shift 2
    ;;
  --output)
    OUTPUT_FILE="$2"
    shift 2
    ;;
  *)
    echo "Unknown option: $1"
    exit 1
    ;;
  esac
done

# Split databases string into array
IFS=',' read -ra DB_ARRAY <<<"$DATABASES"

# Create header for TSV file
echo -e "scale\tengine\tworkload\trows_avg" >"$OUTPUT_FILE"

# Process each database and scale combination
for DB in "${DB_ARRAY[@]}"; do
  for ((SCALE = SCALE_MIN; SCALE <= SCALE_MAX; SCALE += SCALE_STEP)); do
    # Define the filename
    FILENAME="tsbs_${DB}_s${SCALE}_w${WORKERS}.json"

    # Check if file exists
    if [[ ! -f "$FILENAME" ]]; then
      echo "Warning: File $FILENAME not found. Skipping."
      continue
    fi

    echo "Processing $FILENAME..."

    # Extract and process data using jq
    # For devops workload
    DEVOPS_ROWS_AVG=$(jq -r '.devops.rows_avg // "null"' "$FILENAME")
    if [[ "$DEVOPS_ROWS_AVG" != "null" ]]; then
      echo -e "${SCALE}\t${DB}\tdevops\t${DEVOPS_ROWS_AVG}" >>"$OUTPUT_FILE"
    fi

    # For iot workload
    IOT_ROWS_AVG=$(jq -r '.iot.rows_avg // "null"' "$FILENAME")
    if [[ "$IOT_ROWS_AVG" != "null" ]]; then
      echo -e "${SCALE}\t${DB}\tiot\t${IOT_ROWS_AVG}" >>"$OUTPUT_FILE"
    fi

    echo "Completed processing $FILENAME"
  done
done

# Sort the output file by scale, engine, and workload
TMP_FILE="${OUTPUT_FILE}.tmp"
head -1 "$OUTPUT_FILE" >"$TMP_FILE" # Preserve header
tail -n +2 "$OUTPUT_FILE" | sort -n -k1,1 -k2,2 -k3,3 >>"$TMP_FILE"
mv "$TMP_FILE" "$OUTPUT_FILE"

echo "Generated TSV file: $OUTPUT_FILE"
echo "Format: scale | engine | workload | rows_avg"
echo "Sample:"
head -5 "$OUTPUT_FILE"
echo "..."
echo "Total entries: $(wc -l <"$OUTPUT_FILE") (including header)"
