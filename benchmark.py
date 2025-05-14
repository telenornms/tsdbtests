"""
Program for running tsbs to get an benchmark for ingestion and reading of data
Made for use only with Influx, QuestDB, TimeScaleDB or VictoriaMetricsDB
"""

import subprocess
import sys
import re
import pathlib
import json
import argparse
import datetime

def generate_data(path_dict, args, timestamps, file_number, run):
    """
    Generates files using tsbs_generate

    Parameters:
        path_dict : dict
            A dict with the path to TSBS, and the use_case
        args : argparse.Namespace
            The list of inline arguments given to the program
        timestamps : dict
            A dict with the timestamps
        run : int
            The current run of the use case
        file_number : int
            The index for the use case, 0 = devops, 1 = iot
    """

    run_path = path_dict["main_path"] + "bin/tsbs_generate_data"

    use_case = path_dict["use_case"][file_number]

    # Devops data are 10x the size of the others, so need to shrink
    # Sets it to 1 if scale is smaller than 10
    if use_case == "devops":
        new_scale = args.scale//10
        new_scale = new_scale if new_scale >= 10 else 10
    else:
        new_scale = args.scale

    file_path = "/tmp/" + path_dict["test_file"] + "_" + str(run+1) + ".gz"

    print("Creating file: " + file_path)

    full_command = (
        run_path +
        " --use-case=" + use_case +
        " --format=" + args.format +
        " --seed=" + str(args.seed) +
        " --scale=" + str(new_scale) +
        " --timestamp-start=" + timestamps[str(run + (args.runs * file_number))][0] +
        " --timestamp-end=" + timestamps[str(run + (args.runs * file_number))][1] +
        " --log-interval=" + str(args.log_time) + "s" + 
        " | gzip > " + 
        file_path
    )

    subprocess.run(full_command, shell=True, check=False)

def generate_query(path_dict, args, timestamps, read_dict, query_type):
    """
    Generates files using tsbs_generate

    Parameters:
        path_dict : dict
            A dict with the path to TSBS, and the use_case
        args : argparse.Namespace
            The list of inline arguments given to the program
        timestamps : dict
            A dict with the timestamps
        read_dict : dict
            A dict with all the queries and a JSON friendly format
        query_type : str
            The type of query to be ran, chosen from the list of query types
    """

    run_path = path_dict["main_path"] + "bin/tsbs_generate_queries"

    use_case = path_dict["use_case"][0]

    # Devops data are 10x the size of the others, so need to shrink
    # Sets it to 1 if scale is smaller than 10
    new_scale = args.scale//10
    new_scale = new_scale if new_scale >= 10 else 10

    file_path = "/tmp/" + path_dict["test_file"] + "_" + query_type + ".gz"

    # Generates a new timestamp for the end point at 1 second past data generation
    time_end = timestamps[str(args.runs-1)][1].split("T")
    time_end = (
        datetime.datetime.strptime(time_end[0]+" "+time_end[1][:-1], "%Y-%m-%d %H:%M:%S") +
        datetime.timedelta(seconds=1)
    )

    date_str = str(time_end).split(" ", maxsplit=1)
    time_end = date_str[0] + "T" + date_str[1] + "Z"

    print("Creating file: " + file_path)

    full_command = (
        run_path +
        " --use-case=" + use_case +
        " --seed=" + str(args.seed) +
        " --scale=" + str(new_scale) +
        " --timestamp-start=" + timestamps["0"][0] +
        " --timestamp-end=" + time_end +
        " --format=" + args.format +
        " --queries=" + str(args.queries) +
        " --query-type=" + read_dict[query_type] +
        " | gzip > " + 
        file_path
    )

    subprocess.run(full_command, shell=True, check=False, capture_output=True)

def load_data(path_dict, args, db_setup, run):
    """
    Loads the data into the database using tsbs_load_<db_engine>
    and gets the number of metrics per sec, rows per sec, overall time per run
    and total number of metrics and rows

    Parameters:
        path_dict : dict
            A dict with the path to TSBS, the use_case, and the file name
        args : argparse.Namespace
            The list of inline arguments given to the program 
        db_setup : dict
            The dict with all metadata about the selected database
        run : int
            The current run of the use case

    Returns:
        processed_output : tuple
            A tuple containing totals, metrics_list, rows_list, time_list from handle_load()
    """

    # The path to your tsbs/bin folder
    run_path = path_dict["main_path"] + "bin/tsbs_load_" + db_setup["db_engine"]

    #The path to your folder for storing tsbs generated load files
    file_path = "/tmp/" + path_dict["test_file"] + "_" + str(run+1) + ".gz"

    full_command = (
        "cat " + file_path +
        " | gunzip | " +
        run_path +
        " --workers " + str(args.workers) + 
        " --batch-size " + str(args.batch)
    )

    for command in db_setup["extra_commands"]:
        full_command += command

    print("Loading data for " + db_setup["db_engine"] + " with file: " + file_path)

    output = subprocess.run(full_command, shell=True, capture_output=True, text=True, check=False)

    # Checks if there has been any error in loading with tsbs,
    # and prints the error and exits the program
    for line in output.stderr.strip().split("\n"):
        if re.findall(r'panic', line, re.IGNORECASE):
            print(output.stderr)
            sys.exit("Database error!")

    processed_output = handle_load(output)

    # Removes the file after done loading
    path_file_path = pathlib.Path(file_path)
    pathlib.Path.unlink(path_file_path)

    return processed_output

def handle_load(output):
    """
    Takes the output from the tsbs_load and returns the requested metrics

    Parameters:
        output : str
            The full output from the completed run
    
    Returns:
        totals : list
            The list of total numbers of metrics and rows
        metrics_list : list
            The list of metrics/sec for each run, rounded to 0 decimals
        rows_list : list
            The list of rows/sec for each run, rounded to 0 decimals
        time_list : list
            The list of time for each run, rounded to 2 decimals
    """

    metrics_list = []
    rows_list = []
    time_list = []
    extracted_floats = []
    totals = []
    time_match = ""

    output_lines = output.stdout.strip().split("\n")

    for line in output_lines:
        if "(" in line and ")" in line:
            # Look for integer patterns that are not part of floats
            # This regex finds integers that are not followed by a period and digit
            int_matches = re.findall(r"-?\b\d+\b(?!\.\d)", line)

            totals.append(int(int_matches[0]))

            # Finds all floats to grab the time per run
            time_match = re.findall(r"-?\d+\.\d+", line)

            # Find all text within parentheses in the line
            parenthesized_content = re.findall(r"\((.*?)\)", line)

            # Extract float numbers from the parenthesized content
            for content in parenthesized_content:
                # Look for float patterns in the parenthesized content
                float_match = re.findall(r"-?\d+\.\d+", content)

                if float_match:
                    # Convert match to actual float values
                    extracted_floats.append(float_match[0])

    metrics_list.append(int(round(float(extracted_floats[0]))))
    rows_list.append(int(round(float(extracted_floats[1]))))
    time_list.append(round(float(time_match[0]), 2))

    return totals, metrics_list, rows_list, time_list

def run_query(path_dict, args, db_setup, query_type):
    """
    Running the query against the database

    Parameters:

    Returns:
    """

    # The path to your tsbs/bin folder
    run_path = path_dict["main_path"] + "bin/tsbs_run_queries_" + db_setup["db_engine"]

    #The path to your folder for storing tsbs generated files
    file_path = "/tmp/" + path_dict["test_file"] + "_" + query_type + ".gz"

    full_command = (
        "cat " + file_path +
        " | gunzip | " +
        run_path +
        " --workers " + str(args.workers)
    )

    for command in db_setup["extra_commands"]:
        full_command += command

    print("Running query for " + db_setup["db_engine"] + " with file: " + file_path)

    output = subprocess.run(full_command, shell=True, capture_output=True, text=True, check=False)

    # Checks if there has been any error in loading with tsbs,
    # and prints the error and exits the program
    for line in output.stderr.strip().split("\n"):
        if re.findall(r'panic', line, re.IGNORECASE):
            print(output.stderr)
            sys.exit("Database error!")

    processed_output = handle_query(output)

    return processed_output

def handle_query(output):
    """
    For formatting the output from the query
    """

    last_line = ""
    query_match = ""
    time_used = ""
    query_list = []
    time_list = []

    output_lines = output.stdout.strip().split("\n")

    for line in output_lines:
        if "(" in line and ")" in line:
            # Finds all floats to grab the time per run
            query_match = re.findall(r"-?\d+\.\d+", line)

            if query_match:
                query_list.append(int(round(float(query_match[0]))))

        last_line = line

    time_used = re.findall(r"-?\d+\.\d+", last_line)
    time_list.append(round(float(time_used[0]), 2))

    return query_list, time_list

def create_averages(db_dict, args):
    """
    Creates the averages for each file per metrics, rows and tiem

    Parameters:
        db_dict : dict
            A dictionary containing all the data about all the runs; time/run, metrics/sec, 
            rows/sec, and total metrics and rows
    
    Returns:
        avg_runs_dict : dict
            The same dict as db, but including the average metrics/sec/file, 
            rows/sec/file, and time/run/file
    """

    avg_runs_dict = {}
    for file in db_dict:
        avg_runs_dict[file] = {}
        if args.operation == "write":
            avg_runs_dict[file].update({
                "time_run": db_dict[file]["time_run"],
                "time_avg": round(sum(db_dict[file]["time_run"]) / len(db_dict[file]["time_run"]), 2),
                "metrics_sec": db_dict[file]["metrics"], 
                "total_metrics": db_dict[file]["total_metrics"],
                "metrics_avg": sum(db_dict[file]["metrics"]) // len(db_dict[file]["metrics"]),
                "rows_sec": db_dict[file]["rows"], 
                "total_rows": db_dict[file]["total_rows"],
                "rows_avg": sum(db_dict[file]["rows"]) // len(db_dict[file]["rows"])
            })
        elif args.operation == "read":
            avg_runs_dict[file].update({
                "time_run": db_dict[file]["time_run"],
                "time_avg": round(sum(db_dict[file]["time_run"]) / len(db_dict[file]["time_run"]), 2),
                "queries_sec": db_dict[file]["queries"],
                "queries_avg": sum(db_dict[file]["queries"]) // len(db_dict[file]["queries"])
            })

    return avg_runs_dict

def run_tsbs_load(path_dict, args, db_setup, timestamps):
    """
    Runs the tsbs scripts for ingesting data

    Parameters:
        path_dict : dict
            A dict with the path to TSBS, and the use_case
        args : argparse.Namespace
            The list of inline arguments given to the program
        db_setup : dict
            The dict with all metadata about the selected database
        timestamps : dict
            A dict with the timestamps

    Returns:
        db_runs_dict : dict
            A dictionary containing all the data about all the runs; time/run, 
            metrics/sec, rows/sec, and total metrics and rows
    """

    db_runs_dict = {}
    file_number = 0

    # Running for each file the number of set runs
    for test_file in db_setup[args.format]["test_files"]:
        print("Running with " + test_file)
        path_dict["test_file"] = test_file

        for run in range(args.runs):
            print("Run number: " + str(run+1))
            # Generating the data through TSBS
            generate_data(path_dict, args, timestamps, file_number, run)

            # Loading the data through TSBS
            totals, metrics_list, rows_list, time_list = load_data(
                path_dict,
                args,
                db_setup[args.format],
                run
            )

            if run == 0:
                db_runs_dict[path_dict["use_case"][file_number]] = {
                    "time_run": time_list, 
                    "metrics": metrics_list, 
                    "total_metrics": totals[0], 
                    "rows": rows_list, 
                    "total_rows": totals[1] 
                }
            else:
                db_runs_dict[path_dict["use_case"][file_number]]["time_run"].extend(time_list)
                db_runs_dict[path_dict["use_case"][file_number]]["metrics"].extend(metrics_list)
                db_runs_dict[path_dict["use_case"][file_number]]["rows"].extend(rows_list)

        print("All " + str(args.runs)+ " runs completed\n")
        file_number += 1

    return db_runs_dict

def run_tsbs_query(path_dict, args, db_setup, timestamps, read_dict):
    """
    Runs the script for reading data

    Parameters:

    Returns:

    """
    db_runs_dict = {}

    path_dict["test_file"] = db_setup[args.format]["test_files"][0]

    for query in read_dict:
        print("Running with query: " + read_dict[query])
        generate_query(path_dict, args, timestamps, read_dict, query)
        for run in range(args.runs):
            print("Run number: " + str(run+1))
            query_list, time_list = run_query(
                path_dict,
                args,
                db_setup[args.format],
                query
            )

            if run == 0:
                db_runs_dict[query] = {
                    "time_run": time_list,
                    "queries": query_list
                }
            else:
                db_runs_dict[query]["time_run"].extend(time_list)
                db_runs_dict[query]["queries"].extend(query_list)

        print("All " + str(args.runs)+ " runs completed\n")

        # Removes the file after done loading
        path_file_path = pathlib.Path("/tmp/" + path_dict["test_file"] + "_" + query + ".gz")
        pathlib.Path.unlink(path_file_path)

    return db_runs_dict

def create_timestamps(args):
    """
    Creates a dict with the timestamps for each run

    Parameters:
        args : argparse.Namespace
            The inline arguments for the file

    Returns:
        start_date : str
            A string for adding the start date of the run to the JSON ouput
        timestamps : dict
            A dict with start and stop timestamps for each run of the files 
            to create distinct data for all runs
    """

    timestamps = {}

    # Splits the argument for time into year and month
    year_month_list = list(map(int, args.time.split("-")))

    # Creating the different timestamps for use in files
    datestamp = datetime.datetime(year_month_list[0], year_month_list[1], 1)
    start_date = str(datestamp).split(" ", maxsplit=1)[0]

    for i in range(args.runs*2):
        date_str = str(datestamp).split(" ", maxsplit=1)[0]
        timestamps[str(i)] = [date_str + "T00:00:00Z", date_str + "T23:59:59Z"]

        datestamp += datetime.timedelta(days=1)

    return start_date, timestamps

def handle_args():
    """
    Handles the inline arguments for the running of the file

    Returns:
        args : argparse.Namespace
            The object with the arguments, it handles arguments...
    """

    parser = argparse.ArgumentParser(
        description="A script for testing TSBS"
    )

    # General program running
    parser.add_argument(
        "-o",
        "--operation",
        help="Which type of operation you want to run, REQUIRED",
        choices=["read", "write"],
        required=True,
        type=str
    )
    parser.add_argument(
        "-u",
        "--use_case",
        help="If you only want to ingest one use case",
        choices=["devops", "iot"],
        type=str
    )

    # Arguments for data load
    parser.add_argument(
        "-f", 
        "--format", 
        help="The database format, REQUIRED",
        choices=["influx", "questdb", "timescaledb", "victoriametrics"],
        required=True,
        type=str
    )
    parser.add_argument(
        "-d",
        "--db_name",
        help="The database you are using for test, REQUIRED for TimeScale",
        type=str
    )
    parser.add_argument(
        "-p",
        "--password",
        help="The password for the database/user, REQUIRED for TimeScale",
        type=str
    )
    parser.add_argument(
        "-a",
        "--auth_token",
        help="The token for the database/user, REQUIRED for Influx",
        type=str
    )
    parser.add_argument(
        "-w",
        "--workers",
        help="The number of simultaneous processes to run the database load, default=4",
        type=int
    )
    parser.add_argument(
        "-r",
        "--runs",
        help="The number of runs per file, default=5",
        type=int
    )
    parser.add_argument(
        "-b",
        "--batch",
        help="Number of items to batch together in a single run, default=10000",
        type=int
    )

    # Arguments for data generation
    parser.add_argument(
        "-s",
        "--scale",
        help="The scale for the files, default=1000 for iot and cpu, default=100 for devops",
        type=int
    )
    parser.add_argument(
        "-e",
        "--seed",
        help="The seed for data generation, same data across all formats, default=123",
        type=int
    )
    parser.add_argument(
        "-t",
        "--time",
        help="The start time for the data generation, format YYYY-MM, REQUIRED",
        type=str,
        required=True
    )
    parser.add_argument(
        "-l",
        "--log_time",
        help="The time between data points, in seconds, default=10",
        type=int
    )

    # Arguments for query generation
    parser.add_argument(
        "-q",
        "--queries",
        help="The number of queries to be ran, default=5000",
        type=int
    )

    args = parser.parse_args()

    # Check if right arguments for the format
    if args.format == "influx":
        if args.auth_token is None:
            sys.exit("Influx needs --auth_token")
    elif args.format == "timescaledb":
        if args.db_name is None or args.password is None:
            sys.exit("TimeScale needs --db_name and --password")

    args.workers = fix_args({"workers": args.workers})

    args.runs = fix_args({"runs": args.runs})

    args.scale = fix_args({"scale": args.scale})

    args.seed = fix_args({"seed": args.seed})

    args.batch = fix_args({"batch": args.batch})

    args.log_time = fix_args({"log_time": args.log_time})

    args.queries = fix_args({"queries": args.queries})

    if not re.findall(r"\d\d\d\d-\d\d", args.time, re.IGNORECASE):
        args.time = "2025-01"

    return args

def fix_args(argument_dict):
    """
    Handles bad inputs on the int values and sets them to default values if not fixable

    Parameters:
        argument_dict : dict
            A dict with the name of the argparse argument and its value
    
    Returns:
        argument : int
            Returns the fixed argument for the integers
    """

    try:
        argument = int(list(argument_dict.values())[0])
        if argument <= 0:
            raise ValueError("No numbers below 0")
    except (ValueError, TypeError):
        if list(argument_dict.keys())[0] == "workers":
            argument = 4
        elif list(argument_dict.keys())[0] == "runs":
            argument = 5
        elif list(argument_dict.keys())[0] == "scale":
            argument = 1000
        elif list(argument_dict.keys())[0] == "seed":
            argument = 123
        elif list(argument_dict.keys())[0] == "batch":
            argument = 10000
        elif list(argument_dict.keys())[0] == "log_time":
            argument = 10
        elif list(argument_dict.keys())[0] == "queries":
            argument = 5000

    return argument

def main():
    """
    Runs the program
    """

    args = handle_args()

    # The database setups
    db_setup = {
    "influx": {
        "db_engine": "influx", 
        "test_files": ["influx_devops", "influx_iot"], 
        "extra_commands": [" --auth-token ", args.auth_token]
        },
     "questdb": {
         "db_engine": "questdb", 
         "test_files": ["questdb_devops", "questdb_iot"],
         "extra_commands": []
         },
     "timescaledb": {
         "db_engine": "timescaledb",
         "test_files": ["timescaledb_devops", "timescaledb_iot"],
         "extra_commands": [" --db-name ", args.db_name, " --pass ", args.password]
         },
     "victoriametrics": {
         "db_engine": "victoriametrics",
         "test_files": ["victoriametrics_devops", "victoriametrics_iot"],
         "extra_commands": []
         }
    }

    read_dict = {
        "single_groupby_1_1_1": "single-groupby-1-1-1", 
        "single_groupby_1_1_12": "single-groupby-1-1-12", 
        "single_groupby_1_8_1": "single-groupby-1-8-1", 
        "single_groupby_5_1_1": "single-groupby-5-1-1", 
        "single_groupby_5_1_12": "single-groupby-5-1-12", 
        "single_groupby_5_8_1": "single-groupby-5-8-1", 
        "cpu_max_all_1": "cpu-max-all-1", 
        "cpu_max_all_8": "cpu-max-all-8", 
        "double_groupby_1": "double-groupby-1", 
        "double_groupby_5": "double-groupby-5", 
        "double_groupby_all": "double-groupby-all"
    }

    # The file path for where tsbs is stored, default is in the project folder
    # The use cases for the files
    path_dict = {
        "main_path": str(pathlib.Path.cwd()) + "/tsbs/",
        "use_case": ["devops", "iot"]
    }

    # Removes the opposite file from the db_setup test_files of the chosen use case
    # Also Removes it from path_dict use_case
    if args.use_case:
        for db in db_setup:
            if args.use_case == "devops":
                db_setup[db]["test_files"].pop(1)
            elif args.use_case == "iot":
                db_setup[db]["test_files"].pop(0)
        path_dict["use_case"] = [args.use_case]

    start_date, timestamps = create_timestamps(args)

    db_runs_dict = {}

    if args.operation == "write":
        db_runs_dict = run_tsbs_load(path_dict, args, db_setup, timestamps)
    elif args.operation == "read":
        db_runs_dict = run_tsbs_query(path_dict, args, db_setup, timestamps, read_dict)

    avg_dict = create_averages(db_runs_dict, args)

    avg_dict["metadata"] = {
        "db_engine": args.format, 
        "scale": args.scale, 
        "seed": args.seed, 
        "workers": args.workers, 
        "runs": args.runs,
        "read_queries": args.queries,
        "start_date": start_date
    }

    output_file = ""

    if args.operation == "write":
        output_file = (
            "tsbs_" + args.format +
            "_write" +
            "_s" + str(args.scale) +
            "_w" + str(args.workers) +
            ".json"
        )
    elif args.operation == "read":
        output_file = (
            "tsbs_" + args.format +
            "_read" +
            "_s" + str(args.scale) +
            "_w" + str(args.workers) +
            "_q" + str(args.queries) +
            ".json"
        )

    with open(output_file, "w", encoding="ASCII") as f:
        json.dump(avg_dict, f, indent=4)

    print("Output written to: " + output_file)

if __name__ == "__main__":
    main()
