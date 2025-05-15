reset
set terminal svg size 1000,800 enhanced font 'Helvetica,12' 
set output 'performance.svg'

set title "TSDBs ingest performance"

set style data histogram
set style histogram rowstacked
#set style fill solid border -1
set style fill solid
set boxwidth 0.8
set key outside
set key reverse Left

set ylabel "Rows ingested/s"
set xlabel "Tsbs test type"

set datafile separator whitespace

unset border
set style histogram clustered gap 1

set ytics nomirror
set grid ytics
set xtics nomirror


spacify(n) = \
    (n < 1000) ? sprintf("%d", n) : \
    (n < 1000000) ? sprintf("%d %03d", int(n/1000), int(n%1000)) : \
    sprintf("%d %03d %03d", int(n/1000000), int((n%1000000)/1000), int(n%1000))

max_val = 1000000  
do for [val=100000:max_val:50000] {
    set ytics add (sprintf("%s", spacify(val)) val)
}

load 'set2.pal'

plot for [COL=2:5] 'plot_data.tsv' using COL:xtic(1) title columnheader ls (COL-1)
