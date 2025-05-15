reset
set terminal svg size 1000,800 enhanced font 'Helvetica,12' 
set output 'performance.svg'
set style data histogram
set style histogram clustered gap 1
set style fill solid 1.0 
set boxwidth 0.8
set key outside
set key reverse Left
set ylabel "Ingest performance (rows/s)"
set xlabel "Test Type"
set xtics rotate by -45
set datafile separator whitespace
set ytics nomirror
unset border
set grid ytics

load 'set2.pal'

spacify(n) = \
    (n < 1000) ? sprintf("%d", n) : \
    (n < 1000000) ? sprintf("%d %03d", int(n/1000), int(n%1000)) : \
    sprintf("%d %03d %03d", int(n/1000000), int((n%1000000)/1000), int(n%1000))

max_val = 1000000  
do for [val=100000:max_val:50000] {
    set ytics add (sprintf("%s", spacify(val)) val)
}

plot for [COL=2:5] 'plot_data.tsv' using COL:xtic(1) title columnheader ls (COL-1)
