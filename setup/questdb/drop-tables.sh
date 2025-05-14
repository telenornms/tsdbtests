TABLES=$(curl -s -G 'http://localhost:9000/exec' --data-urlencode "query=SELECT table_name FROM tables;" | jq -r '.dataset[] | .[0]')

echo "deleting all tables"
echo $TABLES

if [[ -n "$TABLES" ]]; then
  echo "$TABLES" | while IFS= read -r table; do
    echo "Dropping table: $table"
    curl -G 'http://localhost:9000/exec' --data-urlencode "query=DROP TABLE \"$table\";"
    echo "" 
  done
else
  echo "No tables found."
fi

