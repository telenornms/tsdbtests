"""
Program for running tsbs to get an benchmark for ingestion and reading of data
Made for use only with Influx, QuestDB, TimeScaleDB or VictoriaMetricsDB
"""

import subprocess
import sys
import re
import pathlib
import tempfile
import json
import argparse
import datetime

def generate_files(path_dict, args, timestamps, run_dict, query_dict):
    """
    Generates files using tsbs_generate_<data/queries>

    Parameters:
        path_dict : dict
            A dict with the path to TSBS, and the use_case
        args : argparse.Namespace
            The list of inline arguments given to the program
        timestamps : dict
            A dict with the timestamps
        run_dict : dict
            A dict containing the current file_number and the current run
        query_dict : dict
            A dict containing the query type and a JSON safe query name
    """

    # The path to your tsbs/bin folder
    run_path = str(pathlib.Path(path_dict["main_path"], "bin", "tsbs_generate_"))

    #The path to your folder storing the TSBS generated files
    file_path = str(pathlib.Path(tempfile.gettempdir(), path_dict["test_file"] + ".gz"))

    use_case = path_dict["use_case"][run_dict["file_number"]]

    # Devops data are 10x the size of the others, so need to shrink
    # Sets it to 10 if scale is smaller than 10
    if use_case == "devops":
        new_scale = args.scale//10
        new_scale = new_scale if new_scale >= 10 else 10
    else:
        new_scale = args.scale

    full_command = (
        " --use-case=" + use_case +
        " --format=" + args.format +
        " --seed=" + str(args.seed + run_dict["run"]) +
        " --scale=" + str(new_scale)
    )

    if args.operation == "write":
        run_path = run_path + "data"

        full_command = (
            run_path +
            full_command +
            " --timestamp-start=" + 
            timestamps[str(run_dict["run"] + (args.runs * run_dict["file_number"]))][0] +
            " --timestamp-end=" + 
            timestamps[str(run_dict["run"] + (args.runs * run_dict["file_number"]))][1] +
            " --log-interval=" + str(args.log_time) + "s"
        )

    elif args.operation == "read":
        run_path = run_path + "queries"

        # Generates a new timestamp for the end point at 1 second past data generation
        time_end = timestamps[str(args.runs-1)][1].split("T")
        time_end = (
            datetime.datetime.strptime(time_end[0] + " " + time_end[1][:-1], "%Y-%m-%d %H:%M:%S") +
            datetime.timedelta(seconds=1)
        )

        date_str = str(time_end).split(" ", maxsplit=1)
        time_end = date_str[0] + "T" + date_str[1] + "Z"

        full_command = (
            run_path +
            full_command +
            " --timestamp-start=" + timestamps["0"][0] +
            " --timestamp-end=" + time_end +
            " --queries=" + str(args.queries) +
            " --query-type=" + query_dict["query"]
        )

    full_command = full_command + " | gzip > " + file_path

    if args.verbose:
        print("Creating file: " + file_path)

    subprocess.run(full_command, shell=True, capture_output=True, check=False)

def process_tsbs(path_dict, args, db_setup):
    """
    Loads the data into the database using tsbs_load_<db_engine>
    Runs the queries against the database using tsbs_run_queries_<db_engine>

    Parameters:
        path_dict : dict
            A dict with the path to TSBS, the use_case, and the file name
        args : argparse.Namespace
            The list of inline arguments given to the program 
        db_setup : dict
            The dict with all metadata about the selected database

    Returns:
        processed_output : tuple
            A tuple containing all the lists from handle_load/queries
    """

    # The path to your tsbs/bin folder
    run_path = str(pathlib.Path(path_dict["main_path"], "bin", "tsbs_"))

    #The path to your folder storing the TSBS generated files
    file_path = str(pathlib.Path(tempfile.gettempdir(), path_dict["test_file"] + ".gz"))

    if args.operation == "write":
        if args.verbose:
            print("Loading data for " + args.format + " with file: " + file_path)
        run_path = run_path + "load_" + args.format
    elif args.operation == "read":
        if args.verbose:
            print("Running query for " + args.format + " with file: " + file_path)
        run_path = run_path + "run_queries_" + args.format

    full_command = (
        "cat " + file_path +
        " | gunzip | " +
        run_path +
        " --workers " + str(args.workers)
    )

    if args.operation == "write":
        full_command = full_command + " --batch-size " + str(args.batch)

    for arg in db_setup[args.format]["extra_args"]:
        full_command = full_command + arg

    output = subprocess.run(full_command, shell=True, capture_output=True, text=True, check=False)

    # Checks if there has been any error in loading with tsbs,
    # and prints the error and exits the program
    for line in output.stderr.strip().split("\n"):
        if re.findall(r'panic', line, re.IGNORECASE):
            print(output.stderr)
            sys.exit("ERROR: Database error!")

    processed_output = ()

    if args.operation == "write":
        processed_output = handle_load(output)
    if args.operation == "read":
        processed_output = handle_query(output)

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
        load_return_dit : dict
            A dict containing total metrics, metrics/sec, rows/sec and time/run
    """

    extracted_floats = []
    totals = []
    time_match = []

    output_lines = output.stdout.strip().split("\n")

    for line in output_lines:
        if "(" in line and ")" in line:
            # Finds all integers that are not followed by a period and digit
            int_matches = re.findall(r"-?\b\d+\b(?!\.\d)", line)

            totals.append(int(int_matches[0]))

            # Finds all floats to grab the time per run
            time_match = re.findall(r"-?\d+\.\d+", line)

            # Find all text within parentheses in the line
            parenthesized_content = re.findall(r"\((.*?)\)", line)

            for content in parenthesized_content:
                # Look for float patterns in the parenthesized content
                float_match = re.findall(r"-?\d+\.\d+", content)

                if float_match:
                    extracted_floats.append(float_match[0])

    load_return_dict = {
        "totals": totals,
        "metrics": int(round(float(extracted_floats[0]))),
        "rows": int(round(float(extracted_floats[1]))),
        "time": round(float(time_match[0]), 2)
    }

    return load_return_dict

def handle_query(output):
    """
    For formatting the output from the query

    Parameters:
        output : str

    Returns:
        query_return_dict : dict
            A dict with the query amount and time
    """

    last_line = ""
    query_match = 0

    output_lines = output.stdout.strip().split("\n")

    for line in output_lines:
        if "(" in line and ")" in line:
            # Finds all floats to grab the time per run
            found_query = re.findall(r"-?\d+\.\d+", line)

            if found_query:
                query_match = int(round(float(found_query[0])))

        last_line = line

    query_return_dict = {
        "query": query_match,
        "time": round(float(re.findall(r"-?\d+\.\d+", last_line)[0]), 2)
    }

    return query_return_dict

def create_averages(db_dict, args):
    """
    Creates the averages for each file per metrics, rows and time for load
    and for time and queries for read

    Parameters:
        db_dict : dict
            A dictionary containing all the data about all the runs; time/run, metrics/sec, 
            rows/sec, and total metrics and rows; or queries/sec
    
    Returns:
        avg_runs_dict : dict
            The same dict as db, but including the average time/run/file, metrics/sec/file, 
            and rows/sec/file; or queries/sec/file
    """

    avg_runs_dict = {}
    for file in db_dict:
        avg_runs_dict[file] = {}
        if args.operation == "write":
            avg_runs_dict[file].update({
                "time_run": db_dict[file]["t_run"],
                "time_avg": round(sum(db_dict[file]["t_run"]) / len(db_dict[file]["t_run"]), 2),
                "metrics_sec": db_dict[file]["metrics"], 
                "total_metrics": db_dict[file]["total_metrics"],
                "metrics_avg": sum(db_dict[file]["metrics"]) // len(db_dict[file]["metrics"]),
                "rows_sec": db_dict[file]["rows"], 
                "total_rows": db_dict[file]["total_rows"],
                "rows_avg": sum(db_dict[file]["rows"]) // len(db_dict[file]["rows"])
            })
        elif args.operation == "read":
            avg_runs_dict[file].update({
                "time_run": db_dict[file]["t_run"],
                "time_avg": round(sum(db_dict[file]["t_run"]) / len(db_dict[file]["t_run"]), 2),
                "queries_sec": db_dict[file]["queries"],
                "queries_avg": sum(db_dict[file]["queries"]) // len(db_dict[file]["queries"])
            })

    return avg_runs_dict

def running_handler(path_dict, args, db_setup, timestamps, read_dict):
    """
    Runs the TSBS scripts for ingesting and querying data

    Parameters:
        path_dict : dict
            A dict with the path to TSBS, and the use_case
        args : argparse.Namespace
            The list of inline arguments given to the program
        db_setup : dict
            The dict with all metadata about the selected database
        timestamps : dict
            A dict with the timestamps
        read_dict : dict
            A dict containing all the different query types

    Returns:
        db_runs_dict : dict
            A dictionary containing all the data about all the runs; time/run, 
            metrics/sec, rows/sec, and total metrics and rows
    """

    use_dict = {}
    db_runs_dict = {}
    file_number = 0

    if args.operation == "write":
        use_dict = path_dict["use_case"]
    elif args.operation == "read":
        use_dict = read_dict


    for key_name in use_dict:
        path_dict["test_file"] = args.format + "_" + key_name
        if args.verbose:
            print("Running with " + path_dict["test_file"])

        for run in range(args.runs):
            if args.verbose:
                print("Run number: " + str(run+1))

            if args.operation == "write":
                run_dict = {"file_number": file_number, "run": run}
                query_dict = {}

                generate_files(path_dict, args, timestamps, run_dict, query_dict)

                load_return_dict = process_tsbs(path_dict, args, db_setup)

                if run == 0:
                    db_runs_dict[key_name] = {
                        "t_run": [load_return_dict["time"]], 
                        "metrics": [load_return_dict["metrics"]], 
                        "total_metrics": load_return_dict["totals"][0], 
                        "rows": [load_return_dict["rows"]], 
                        "total_rows": load_return_dict["totals"][1] 
                    }
                else:
                    db_runs_dict[key_name]["t_run"].append(load_return_dict["time"])
                    db_runs_dict[key_name]["metrics"].append(load_return_dict["metrics"])
                    db_runs_dict[key_name]["rows"].append(load_return_dict["rows"])

            elif args.operation == "read":
                run_dict = {"file_number": 0, "run": run}
                query_dict = {"query": read_dict[key_name], "query_name": key_name}

                generate_files(path_dict, args, timestamps, run_dict, query_dict)

                query_return_dict = process_tsbs(path_dict, args, db_setup)

                if run == 0:
                    db_runs_dict[key_name] = {
                        "t_run": [query_return_dict["time"]],
                        "queries": [query_return_dict["query"]]
                    }
                else:
                    db_runs_dict[key_name]["t_run"].append(query_return_dict["time"])
                    db_runs_dict[key_name]["queries"].append(query_return_dict["query"])

        if args.verbose:
            print("All " + str(args.runs)+ " runs completed\n")
        file_number += 1

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
        description="""
        A script for testing TSBS using multiple runs
        
        EXAMPLE WRITE:
        
        >>> python benchmark.py -f influx -a <influx auth-token> 
        -u devops -o write -t 2025-05 -s 100 -e 1234 -r 3 -w 4
        
        Writes devops data to the influx database with 
        start date 2025-05-01, at a scale of 100, using
        seed number 1234 and repeats 3 times, using 4 parallell workers
        
        EXAMPLE READ:
        
        >>> python benchmark.py victoriametrics -u devops -o write
        -t 2001-12 -s 8654 -e 9876 -r 7 -b 543 -w 10
        
        >>> python benchmark.py victoriametrics -u devops -o read
        -t 2001-12 -s 8654 -e 9876 -r 7 -b 543 -w 10
        
        First writes the data to victoria metrics, before using the
        same parameters to read the data, with start date 2001-12,
        at a scale of 8654, using seed number 9876 and repeates 7 times,
        and then reads reads 543 queries per run, with 10 parallell workers
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )

    # General program running
    parser.add_argument(
        "-f", 
        "--format", 
        help="The database format, REQUIRED",
        choices=["influx", "questdb", "timescaledb", "victoriametrics"],
        required=True,
        type=str
    )
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
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Defines a verbose output"
    )

    # Arguments for data load/query run
    parser.add_argument(
        "-d",
        "--db_name",
        help="The database you are using for test",
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
        if args.password is None:
            sys.exit("TimeScale needs --password")
        if args.db_name is None:
            args.db_name = "benchmark"

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
        "influx": {"extra_args": [" --auth-token ", args.auth_token]},
        "questdb": {"extra_args": []},
        "timescaledb": {"extra_args": [" --db-name ", args.db_name, " --pass ", args.password]},
        "victoriametrics": {"extra_args": []}
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
        "main_path": str(pathlib.Path(pathlib.Path.cwd(), "tsbs")),
        "use_case": ["devops", "iot"]
    }

    # Removes extra use case from path_dict use_case
    if args.use_case:
        path_dict["use_case"] = [args.use_case]

    start_date, timestamps = create_timestamps(args)

    db_runs_dict = running_handler(path_dict, args, db_setup, timestamps, read_dict)

    avg_dict = create_averages(db_runs_dict, args)

    avg_dict["metadata"] = {
        "db_engine": args.format, 
        "scale": args.scale, 
        "seed": args.seed, 
        "workers": args.workers, 
        "runs": args.runs,
        "read_queries": args.queries,
        "start_date": start_date,
        "operation": args.operation
    }

    output_file = "tsbs_" + args.format

    if args.operation == "write":
        output_file += "_write"
    elif args.operation == "read":
        output_file += "_read"
        
    output_file += (
        "_s" + str(args.scale) +
        "_w" + str(args.workers) +
        "_q" + str(args.queries) +
        ".json"
    )

    with open(output_file, "w", encoding="ASCII") as f:
        json.dump(avg_dict, f, indent=4)

    if args.verbose:
        print("Output written to: " + output_file)

if __name__ == "__main__":
    main()
