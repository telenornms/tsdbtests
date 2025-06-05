"""
Compares the json files from benchmark
"""
import json
import argparse
import pathlib
import matplotlib.pyplot as plt
import numpy as np
# import sys

def get_file_list(args):
    """
    Gets the list of files from either the file list or directory
    
    Parameters:
        args : argparse.Namespace
            The args for the file, either files or folder
            
    Returns:
        file_list : list
            A list of all filenames
    """

    file_list = []

    if args.files:
        file_list = args.files
    elif args.dir:
        try:
            # Gets all objects in the folder and adds it to file_list, if it is a file
            file_list = [str(f) for f in pathlib.Path(args.dir).iterdir() if f.is_file()]

        except FileNotFoundError:
            print("Directory not found")

    return file_list

def read_json(file_list):
    """
    Reads the json files
    
    Parameters:
        file_list : list
            The list of all filenames
            
    Returns:
        json_list : list
            The list of all the content of the files
    """

    json_list = []

    for filename in file_list:
        if pathlib.Path(filename).suffix != ".json":
            print("SKIPPED: " + filename)
            continue
        try:
            print("READING: " + filename)
            with open(filename, "r", encoding="ASCII") as file:
                data = json.load(file)
                json_list.append(data)
        except FileNotFoundError:
            print("File not found")

    return create_compare_dict(json_list)

def create_compare_dict(json_list):
    """
    Takes the data from the files and pulls out the comparable bits

    Parameters:
        json_list : list
            The list with all the content from the files
            
    Returns:
        compare_dict : dict
            The dict with all the time usage
    """

    compare_dict = {}

    for file in json_list:
        compare_dict.setdefault(
            "s" + str(file["metadata"]["scale"]) +
            "e" + str(file["metadata"]["seed"] )+
            "r" + str(file["metadata"]["runs"]) +
            "w" + str(file["metadata"]["workers"]) +
            "q" + str(file["metadata"]["read_queries"])
            , {}
        )
        for key in file.keys():
            if key != "metadata":
                compare_dict[
                    "s" + str(file["metadata"]["scale"]) +
                    "e" + str(file["metadata"]["seed"] )+
                    "r" + str(file["metadata"]["runs"]) +
                    "w" + str(file["metadata"]["workers"]) +
                    "q" + str(file["metadata"]["read_queries"])
                ].setdefault(key, {})[
                    file["metadata"]["db_engine"]
                    ] = [
                        file[key]["time_run"], file[key]["time_avg"]
                    ]

            elif key == "metadata":
                compare_dict[
                    "s" + str(file["metadata"]["scale"]) +
                    "e" + str(file["metadata"]["seed"] )+
                    "r" + str(file["metadata"]["runs"]) +
                    "w" + str(file["metadata"]["workers"]) +
                    "q" + str(file["metadata"]["read_queries"])
                ]["metadata"] = file["metadata"]

    return get_scores(compare_dict)

def get_scores(compare_dict):
    """
    Compares the times and gets the ranking and variation
    
    Parameters:
        compare_dict : dict
            The dict with all the time usage
            
    Returns:
        score_dict : dict
            The dict with all the ranks, unranked
    """
    score_dict = {}

    for meta_key in compare_dict.keys():
        score_dict[meta_key] = {}
        for key in compare_dict[meta_key].keys():
            if key != "metadata":
                score_dict[meta_key][key] = {
                    "ranking": {},
                    "variation": {}
                }

                for inner, times in compare_dict[meta_key][key].items():

                    score_dict[meta_key][key]["ranking"].update({
                        inner: times[1]
                    })
                    score_dict[meta_key][key]["variation"].update({
                        inner: calculate_variation(times)
                    })

            elif key == "metadata":
                score_dict[meta_key]["metadata"] = compare_dict[meta_key]["metadata"]

    return order_ranking(score_dict)

def calculate_variation(times):
    """
    Calculates the variation between the average time and the largest outlier
    
    Parameters:
        times : list
            A list containing a list of times and the average time
            
    Returns:
        variation_dict : dict
            A dict containing the largest variation and the percentage of the variation
    """

    time_list, avg_time = times[0], times[1]
    largest_var = 0
    percent = 0
    variation_dict = {}

    for time in time_list:
        variation = abs(avg_time - time)
        if variation > largest_var:
            largest_var = round(variation, 2)
            percent = round(abs(100 - ((avg_time / time) * 100)), 2)

    variation_dict = {"largest_var": largest_var, "percent": percent}

    return variation_dict

def order_ranking(score_dict):
    """
    Gets the numbers and ranks the dbs
    
    Parameters:
        score_dict : dict
            The dict with all the ranks, unranked
            
    Returns:
        o_dict : dict
            The dict with all the dbs ranked, actually ranked properly 
    """

    o_dict = {}

    for meta_key in score_dict:
        o_dict[meta_key] = {}
        for key in score_dict[meta_key].keys():
            if key != "metadata":
                score = score_dict[meta_key][key]
                o_dict[meta_key][key] = {
                    "ranking": dict(
                        sorted(score["ranking"].items(), key=lambda item: item[1])
                    ),
                    "variation": {}
                }

                for db in o_dict[meta_key][key]["ranking"]:
                    o_dict[meta_key][key]["variation"][db] = score["variation"][db]

            elif key == "metadata":
                o_dict[meta_key]["metadata"] = {
                    "scale": score_dict[meta_key]["metadata"]["scale"],
                    "seed": score_dict[meta_key]["metadata"]["seed"],
                    "workers": score_dict[meta_key]["metadata"]["workers"],
                    "runs": score_dict[meta_key]["metadata"]["runs"],
                    "read_queries": score_dict[meta_key]["metadata"]["read_queries"],
                    "start_date": score_dict[meta_key]["metadata"]["start_date"],
                }

    return o_dict

def draw_plot(ordered_dict):
    """
    Creates bar graphs for each use-case, ranked by time
    Saves them to file
    
    Parameters:
        ordered_dict : dict
            The dict with all the dbs ranked, actually ranked properly 
    """
    
    name_colors = {
        "influx": "#AEE0D7",
        "questdb": "#FFFFC9",
        "timescaledb": "#D1CEE4",
        "victoriametrics": "#A5C8E0"
    }
    
    for meta, data in ordered_dict.items():
        
        num_cases = 0

        del data["metadata"]
        num_cases = len(data)

        fig, axes = plt.subplots(1, num_cases, figsize=(5*num_cases, 6))
        
        # colors = plt.cm.Set3(np.linspace(0, 1, 10))
        
        for idx, (use_case, case_data) in enumerate(data.items()):
            ax = axes[idx]
            
            rankings = case_data["ranking"]
            variation = case_data["variation"]
            
            sorted_items = sorted(rankings.items(), key=lambda x: x[0])
            sorted_dbs = [item[0] for item in sorted_items]
            
            x_labels = sorted_dbs
            y_values = [rankings[db] for db in sorted_dbs]
            errors = [variation[db]["largest_var"] for db in sorted_dbs]
            bar_colors = [name_colors[db] for db in sorted_dbs]
            
            bars = ax.bar(
                x_labels, 
                y_values, 
                yerr=errors, 
                capsize=5,
                ecolor="black",
                color=bar_colors,
                alpha=0.7,
                edgecolor="black",
                linewidth=1
            )
            
            ax.set_title(f"{use_case.title()}", fontsize=14, fontweight="bold")
            ax.set_xlabel("Databases", fontsize=12)
            ax.set_ylabel("Time", fontsize=12)
            ax.grid(True, alpha=0.3, axis="y")
            
            for bar, value, error in zip(bars, y_values, errors):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width()/2., 
                    height + error,
                    f"{value:.1f}±{error:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold"
                )
                
            if len(x_labels) > 3:
                ax.tick_params(axis="x", rotation=45)
                
        plt.tight_layout()
        save_path = str(meta) + ".svg"
        plt.savefig(save_path, format="svg", bbox_inches="tight")
        print("Saved graph to: " + save_path)

def main():
    """
    Runs the program
    """

    parser = argparse.ArgumentParser(description="Read multiple JSON files to compare")

    parser.add_argument(
        "-f",
        "--files",
        nargs="*",
        help="The files to open",
        type=str
    )

    parser.add_argument(
        "-d",
        "--dir",
        help="The directory of the files",
        type=str
    )

    args = parser.parse_args()

    file_list = get_file_list(args)
    ordered_dict = read_json(file_list)

    output_file = "tsbs_ranking.json"

    print("Output written to: " + output_file)

    with open(output_file, "w", encoding="ASCII") as f:
        json.dump(ordered_dict, f, indent=4)
        
    draw_plot(ordered_dict)

if __name__ == "__main__":
    main()
