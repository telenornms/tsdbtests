reset
set terminal svg size 1000,800 enhanced font 'Helvetica,12' 
set output sprintf('benchmark_w%s.svg', ARG1)
set title "TSDBs ingest performance"

# Define the colors directly for Set2 ColorBrewer
set linetype 1 lc rgb "#66c2a5"  # teal/mint
set linetype 2 lc rgb "#fc8d62"  # light orange
set linetype 3 lc rgb "#8da0cb"  # periwinkle blue
set linetype 4 lc rgb "#e78ac3"  # pink
set linetype 5 lc rgb "#a6d854"  # lime green

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

# Custom number formatting function with space as thousands separator
# Handles numbers up to 999 999 999
spacify(n) = \
    (n < 1000) ? sprintf("%d", n) : \
    (n < 1000000) ? sprintf("%d %03d", int(n/1000), int(n%1000)) : \
    sprintf("%d %03d %03d", int(n/1000000), int((n%1000000)/1000), int(n%1000))

# Set the ytic format to use custom formatting
set format y ""  # Clear default formatting
set ytics add ("0" 0)  # Add zero explicitly

# Add formatted ytics manually based on your data range
# Adjust these values based on your actual data range
max_val = 1000000  # Set this to match your max data value
do for [val=100000:max_val:100000] {
    set ytics add (sprintf("%s", spacify(val)) val)
}

# horizontal bars
set style data histograms
# read data into arrays

# Use the defined line types
plot for [COL=2:5] sprintf('averages_w%s.tsv', ARG1) using COL:xtic(1) title columnheader
