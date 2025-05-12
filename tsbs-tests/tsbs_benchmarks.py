import subprocess
import sys
import re
import pathlib
import json
import argparse
import datetime

def generate_data(path_dict, args, timestamps, run, file_number):
    """
    Generates files using tsbs_generate

    Arguments:
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

    file_path = "/tmp/"

    use_case = path_dict["use_case"][file_number]

    # Devops data are 10x the size of the others, so need to shrink
    if use_case == "devops":
        new_scale = args.scale//10
        new_scale = new_scale if new_scale >= 1 else 1
    else:
        new_scale = args.scale

    full_file_path = file_path + args.format + "_" + use_case + "_" + str(run+1) + ".gz"

    use_case_str = " --use-case="+use_case
    format_str = " --format="+args.format
    seed_str = " --seed="+str(args.seed)
    scale_str = " --scale="+str(new_scale)
    t_start_str = " --timestamp-start="+timestamps[str(run+args.runs*file_number)][0]
    t_stop_str = " --timestamp-end="+timestamps[str(run+args.runs*file_number)][1]

    print("Creating file: " + full_file_path)

    full_command = run_path + use_case_str + format_str + seed_str + scale_str + t_start_str + t_stop_str + " --log-interval=10s" + " | gzip > " + full_file_path

    subprocess.run(full_command, shell=True, check=False)

def load_data(path_dict, args, db_setup, test_file, run):
    """
    Loads the data into the database using tsbs_load_<db_engine>
    and gets the number of metrics per sec, rows per sec, overall time per run
    and total number of metrics and rows

    Arguments:
        path_dict : dict
            A dict with the path to TSBS, and the use_case
        db_engine : str
            The type of database, influx, questdb, timescaledb or victoriametrics
        test_file : str
            The string path for the file to be read into the database
        args : argparse.Namespace
            The list of inline arguments given to the program 
        run : int
            The current run of the use case

    Returns:
        processed_output : tuple
            A tuple containing totals, metrics_list, rows_list, time_list from handle_load()
    """

    # The path to your tsbs/bin folder
    run_path = path_dict["main_path"] + "bin/tsbs_load_" + db_setup["db_engine"]

    #The path to your folder for storing tsbs generated load files
    file_path = "/tmp/" + test_file + "_" + str(run+1) +".gz"

    workers_str = " --workers " + str(args.workers)
    batch_str = " --batch-size " + str(args.batch)

    #full_command = "cat " + file_path + " | gunzip | " + run_path + " --workers " + str(workers) + " --batch-size " + str(batch)
    full_command = "cat " + file_path + " | gunzip | " + run_path + workers_str + batch_str
    for command in db_setup["extra_commands"]:
        full_command += command

    print("Loading data for " + db_setup["db_engine"] + " with file " + file_path)

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

    Arguments:
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


def create_averages(db_runs_dict):
    """
    Creates the averages for each file per metrics, rows and tiem

    Arguments:
        db_runs_dict : dict
            A dictionary containing all the data about all the runs; time/run, metrics/sec, rows/sec,
            and total metrics and rows
    
    Returns:
        avg_runs_dict : dict
            The same dict as db_runs_dict, but including the average metrics/sec/file, rows/sec/file,
            and time/run/file
    """

    avg_runs_dict = {}

    for file in db_runs_dict:
        avg_runs_dict[file] = {"time_run": db_runs_dict[file]["time_run"]}
        avg_runs_dict[file]["time_avg"] = round(sum(db_runs_dict[file]["time_run"]) / len(db_runs_dict[file]["time_run"]), 2)
        avg_runs_dict[file].update({"metrics_sec": db_runs_dict[file]["metrics"], "total_metrics": db_runs_dict[file]["total_metrics"]})
        avg_runs_dict[file]["metrics_avg"] = sum(db_runs_dict[file]["metrics"]) // len(db_runs_dict[file]["metrics"])
        avg_runs_dict[file].update({"rows_sec": db_runs_dict[file]["rows"], "total_rows": db_runs_dict[file]["total_rows"]})
        avg_runs_dict[file]["rows_avg"] = sum(db_runs_dict[file]["rows"]) // len(db_runs_dict[file]["rows"])

    return avg_runs_dict

def create_timestamps(args):
    """
    Creates a dict with the timestamps for each run

    Arguments:
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
    start_date = str(datestamp).split(" ")[0]

    for i in range(args.runs*2):
        date_str = str(datestamp).split(" ")[0]
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

    parser = argparse.ArgumentParser(description="A program for testing tsbs for Influx, QuestDB, TimeScaleDB and VictoriaMetrics")

    # Arguments for data load
    parser.add_argument("-f", "--format", help="The database format", choices=["influx", "questdb", "timescaledb", "victoriametrics"], required=True, type=str)
    parser.add_argument("-d", "--admin_db_name", help="The database you are using for test, REQUIRED for TimeScale", type=str)
    parser.add_argument("-p", "--password",  help="The password for the database/user, REQUIRED for TimeScale", type=str)
    parser.add_argument("-a", "--auth_token", help="The token for the database/user, REQUIRED for Influx", type=str)
    parser.add_argument("-w", "--workers", help="The number of simultanious processes to run the database load, default=4", type=int)
    parser.add_argument("-r", "--runs", help="The number of runs per file, default=5", type=int)
    parser.add_argument("-b", "--batch", help="Number of items to batch together in a single run, default=10000", type=int)

    # Arguments for data generation
    parser.add_argument("-s", "--scale", help="The scale for the files, default=1000 for iot and cpu, default=100 for devops", type=int)
    parser.add_argument("-e", "--seed", help="The seed for data generation, same data across all formats, default=123", type=int)
    parser.add_argument("-t", "--time", help="The start time for the data generation, format YYYY-MM", type=str, required=True)

    args = parser.parse_args()

    # Check if right arguments for the format
    if args.format == "influx":
        if args.auth_token is None:
            sys.exit("Influx needs --auth_token")
    elif args.format == "timescaledb":
        if args.admin_db_name is None or args.password is None:
            sys.exit("TimeScale needs --admin_db_name and --password")

    args.workers = fix_args({"workers": args.workers})

    args.runs = fix_args({"runs": args.runs})

    args.scale = fix_args({"scale": args.scale})

    args.seed = fix_args({"seed": args.seed})

    args.batch = fix_args({"batch": args.batch})

    if not re.findall(r"\d\d\d\d-\d\d", args.time, re.IGNORECASE):
        args.time = "2025-01"

    return args

def fix_args(argument_dict):
    """
    Handles bad inputs on the int values and sets them to default values if not fixable

    Arguments:
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
    except:
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
         "extra_commands": [" --admin-db-name ", args.admin_db_name, " --pass ", args.password]
         },
     "victoriametrics": {
         "db_engine": "victoriametrics",
         "test_files": ["victoriametrics_devops", "victoriametrics_iot"],
         "extra_commands": []
         }
    }

    # The file path for where tsbs is stored, default is in the project folder
    # The use cases for the files
    path_dict = {
        "main_path": str(pathlib.Path.cwd()) + "/../tsbs/",
        "use_case": ["devops", "iot"]
    }

    start_date, timestamps = create_timestamps(args)

    db_runs_dict = {}
    file_number = 0

    # Running for each file the number of set runs
    for test_file in db_setup[args.format]["test_files"]:
        print("Running with " + test_file)

        for run in range(args.runs):
            print("Run number: " + str(run+1))
            # Generating the data through TSBS
            generate_data(path_dict, args, timestamps, run, file_number)

            # Loading the data through TSBS
            totals, metrics_list, rows_list, time_list = load_data(path_dict, args, db_setup[args.format], test_file, run)
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

    avg_dict = create_averages(db_runs_dict)

    avg_dict["metadata"] = {
        "db_engine": args.format, 
        "scale": args.scale, 
        "seed": args.seed, 
        "workers": args.workers, 
        "runs": args.runs, 
        "start_date": start_date
    }

    output_file = "tsbs_" + args.format + "_s" + str(args.scale) + "_w" + str(args.workers) + ".json"

    with open(output_file, "w", encoding="ASCII") as f:
        json.dump(avg_dict, f, indent=4)

if __name__ == "__main__":
    main()
