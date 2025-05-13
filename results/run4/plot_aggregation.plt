#!/usr/bin/gnuplot
# Usage: gnuplot -c plot_performance.gp <input_tsv_file> [output_format]

if (!exists("ARG1")) {
    print "Error: Input TSV file not specified"
    print "Usage: gnuplot -c plot_performance.gp <input_tsv_file> [output_format]"
    exit
}

input_file = ARG1

set datafile separator "\t"
set key autotitle columnhead
set datafile commentschars "#"

if (exists("ARG2")) {
    output_format = ARG2
} else {
    output_format = "png"
}

if (output_format eq "png") {
    set terminal png size 1200,800 enhanced font 'Helvetica,12'
} else if (output_format eq "svg") {
    set terminal svg size 1200,800 enhanced font 'Helvetica,12'
} else if (output_format eq "pdf") {
    set terminal pdfcairo size 10,7 enhanced font 'Helvetica,12'
}

set grid
set key outside right top
set pointsize 1.5

# colorscheme
load 'set2.pal'

set style line 1 lw 3 pt 7
set style line 2 lw 3 pt 9
set style line 3 lw 3 pt 5
set style line 4 lw 3 pt 11
set style line 5 lw 3 pt 13
set style line 6 lw 3 pt 3
set style line 7 lw 3 pt 4
set style line 8 lw 3 pt 6
set style data linespoints

# Function to get the list of unique databases in the input file
getDBs = "awk -F'\\t' 'NR>1 {print $2}' ".input_file." | sort | uniq"
dbList = system(getDBs)
dbCount = words(dbList)

# Format x-axis
set xlabel 'Scale Factor' font 'Helvetica,14'
set xtics nomirror
set format x '%.0f'

# Format y-axis
set ylabel 'Rows per Second (avg)' font 'Helvetica,14'
set ytics nomirror
set format y '%.0f'

##############################################
# Plot for DevOps workload
##############################################
set output 'devops_performance.'.output_format
set title 'DevOps Workload - Database Performance Comparison' font 'Helvetica,16'

# Build the plot command
plot_cmd = ""
i = 0

# For each database engine, create a plot command
do for [db in dbList] {
    i = i + 1
    style_index = (i % 8 == 0) ? 8 : (i % 8)
    
    if (strlen(plot_cmd) > 0) {
        plot_cmd = plot_cmd.", "
    }
    
    # Filter data for this database and the devops workload
    plot_cmd = plot_cmd."'< grep \"".db."[[:space:]]devops\" ".input_file." | grep -v \"^scale\"' using 1:4 "
    plot_cmd = plot_cmd."with linespoints ls ".style_index." title '".db."'"
}

# Execute the plot command
eval("plot ".plot_cmd)

##############################################
# Plot for IoT workload
##############################################
set output 'iot_performance.'.output_format
set title 'IoT Workload - Database Performance Comparison' font 'Helvetica,16'

# Build the plot command
plot_cmd = ""
i = 0

# For each database engine, create a plot command
do for [db in dbList] {
    i = i + 1
    style_index = (i % 8 == 0) ? 8 : (i % 8)
    
    if (strlen(plot_cmd) > 0) {
        plot_cmd = plot_cmd.", "
    }
    
    # Filter data for this database and the iot workload
    plot_cmd = plot_cmd."'< grep \"".db."[[:space:]]iot\" ".input_file." | grep -v \"^scale\"' using 1:4 "
    plot_cmd = plot_cmd."with linespoints ls ".style_index." title '".db."'"
}

# Execute the plot command
eval("plot ".plot_cmd)

print "Generated charts:"
print "- devops_performance.".output_format
print "- iot_performance.".output_format
