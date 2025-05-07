import os
import subprocess
import sys
import re
import pathlib
import json
import argparse

def generate_data(main_file_path, file_name, db_format, scale, seed, time_start, time_stop):
    # The use cases for the files
    use_case = ["devops", "iot", "cpu-only"]

    run_path = main_file_path + "bin/tsbs_generate_data"
    
    file_path = "/tmp/"
    
    file_number = 1

    print("Generating data for " + db_format + ":")

    for case in use_case:
        # Devops data are 10x the size of the others, so need to shrink
        if case == "devops":
            new_scale = int(scale)//10
        else:
            new_scale = scale

        full_file_path = file_path+db_format+"_"+file_name[file_number-1]+".gz"

        print(str(file_number)+": "+full_file_path)
        
        full_command = run_path + " --use-case="+case + " --format="+db_format + " --seed="+str(seed) + " --scale="+str(new_scale) + " --timestamp-start="+time_start + " --timestamp-end="+time_stop + " --log-interval=10s" + " | gzip > " + full_file_path

        subprocess.run(full_command, shell=True)

        file_number += 1

def load_data(main_file_path, db_engine, test_file, extra_commands = [], workers = "4", runs = 5):
    # The path to your tsbs/bin folder
    run_path = main_file_path + "bin/tsbs_load_" + db_engine

    #The path to your folder for storing tsbs generated load files
    file_path = "/tmp/" + test_file + ".gz"
    
    full_command = "cat " + file_path + " | gunzip | " + run_path + " --workers " + workers
    for command in extra_commands:
        full_command += command

    metrics_list = []
    rows_list = []
    time_list = []

    print("Loading data for " + db_engine + " with file " + file_path + ":")

    for i in range(runs):
        print("Run number: " + str(i+1), end="\r")

        output = subprocess.run(full_command, shell=True, capture_output=True, text=True)

        for line in output.stderr.strip().split("\n"):
            if re.findall(r'panic', line, re.IGNORECASE):
                print(output.stderr)
                sys.exit("Database error!")

        output_lines = output.stdout.strip().split("\n")

        extracted_floats = []
        extracted_ints = []

        for line in output_lines:
            if "(" in line and ")" in line:                
                # Look for integer patterns that are not part of floats
                # This regex finds integers that are not followed by a period and digit
                int_matches = re.findall(r"-?\b\d+\b(?!\.\d)", line)
                
                extracted_ints.append(int(int_matches[0]))
                
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

        metrics_list.append(float(extracted_floats[0]))
        rows_list.append(float(extracted_floats[1]))
        time_list.append(float(time_match[0]))

    print("All " + str(runs)+ " runs completed")

    return extracted_ints, metrics_list, rows_list, time_list

def create_averages(db_runs_dict):
    
    avg_runs_dict = {}

    for file in db_runs_dict:
        avg_runs_dict[file] = {"time_run": db_runs_dict[file]["time_run"], "metrics_sec": db_runs_dict[file]["metrics"], "total_metrics": db_runs_dict[file]["total_metrics"]}
        avg_runs_dict[file]["metrics_avg"] = sum(db_runs_dict[file]["metrics"]) / len(db_runs_dict[file]["metrics"])
        avg_runs_dict[file].update({"rows_sec": db_runs_dict[file]["rows"], "total_rows": db_runs_dict[file]["total_rows"]})
        avg_runs_dict[file]["rows_avg"] = sum(db_runs_dict[file]["rows"]) / len(db_runs_dict[file]["rows"])

    return avg_runs_dict

def handle_args():
    
    parser = argparse.ArgumentParser(description="A program for testing tsbs for Influx, QuestDB, TimeScaleDB and VictoriaMetrics")

    # Arguments for data load
    parser.add_argument("-f", "--format", help="The database format", choices=["influx", "questdb", "timescaledb", "victoriametrics"], required=True)
    parser.add_argument("-d", "--admin_db_name", help="The database you are using for test, REQUIRED for TimeScale")
    parser.add_argument("-p", "--password",  help="The password for the database/user, REQUIRED for TimeScale")
    parser.add_argument("-a", "--auth_token", help="The token for the database/user, REQUIRED for Influx")
    parser.add_argument("-w", "--workers", help="The number of simultanious processes to run the database load, default=4")
    parser.add_argument("-r", "--runs", help="The number of runs per file, default=5")
    
    # Arguments for data generation
    parser.add_argument("-s", "--scale", help="The scale for the files, default=1000 for iot and cpu, default=100 for devops")
    parser.add_argument("-e", "--seed", help="The seed for data generation, same data across all formats, default=123")
    parser.add_argument("--timestamp_start", help="Data start, default=2025-05-01T00:00:00Z")
    parser.add_argument("--timestamp_stop", help="Data stop, default=2025-05-02T00:00:00Z")

    args = parser.parse_args()

    # Check if right arguments for the format
    if args.format == "influx":
        if args.auth_token is None:
            sys.exit("Influx needs --auth_token")
    elif args.format == "timescaledb":
        if args.admin_db_name is None or args.password is None:
            sys.exit("TimeScale needs --admin_db_name and --password")

    if args.workers is None:
        args.workers = "4"
    if args.runs is None:
        args.runs = 5

    if args.scale is None:
        args.scale = 1000
    if args.seed is None:
        args.seed = 123
    if args.timestamp_start is None:
        args.timestamp_start = "2025-05-01T00:00:00Z"
    if args.timestamp_stop is None:
        args.timestamp_stop = "2025-05-02T00:00:00Z"

    return args

def main():

    args = handle_args()

    # The database setups
    db_setup = {
    "influx": {
        "db_engine": "influx", 
        "test_files": ["influx_devops", "influx_iot", "influx_cpu_only"], 
        "extra_commands": [" --auth-token ", args.auth_token]
        }, 
     "questdb": {
         "db_engine": "questdb", 
         "test_files": ["questdb_devops", "questdb_iot", "questdb_cpu_only"],
         "extra_commands": []
         },
     "timescaledb": {
         "db_engine": "timescaledb",
         "test_files": ["timescaledb_devops", "timescaledb_iot", "timescaledb_cpu_only"],
         "extra_commands": [" --admin-db-name ", args.admin_db_name, " --pass ", args.password]
         },
     "victoriametrics": {
         "db_engine": "victoriametrics",
         "test_files": ["victoriametrics_devops", "victoriametrics_iot", "victoriametrics_cpu_only"],
         "extra_commands": []
         }
    }

    # The file path for where you stored tsbs
    # Default is home folder
    main_file_path = str(pathlib.Path.home()) + "/tsbs/"
    
    file_name = ["devops", "iot", "cpu_only"]

    # Generating the data
    generate_data(main_file_path, file_name, args.format, args.scale, args.seed, args.timestamp_start, args.timestamp_stop)

    database_runs_dict = {}
    
    file_number = 0

    # Runs the process for all files
    for test_file in db_setup[args.format]["test_files"]:
        extra_ints, metrics_list, rows_list, time_list = load_data(main_file_path, db_setup[args.format]["db_engine"], test_file, db_setup[args.format]["extra_commands"], args.workers, args.runs)
        database_runs_dict[file_name[file_number]] = {"time_run": time_list, "metrics": metrics_list, "total_metrics": extra_ints[0], "rows": rows_list, "total_rows": extra_ints[1]}
        file_number += 1

    avg_dict = create_averages(database_runs_dict)

    avg_dict["metadata"] = {"db_engine": args.format, "scale": args.scale, "seed": args.seed, "workers": args.workers, "runs": args.runs}
    
    output_file = "tsbs_" + args.format + "_" + args.scale + ".json"
    
    with open(output_file, "w") as f:
        json.dump(avg_dict, f, indent=4)

if __name__ == "__main__":
    main()
