"""
Compares the json files from benchmark
"""
import json
import argparse
import os
# import sys

def read_json(args):
    """
    Reads the json files
    
    Parameters:
        args: argparse.Namespace
            The args for the file, either files or folder
            
    Returns:
        json_list : list
            The list of all the content of the files
    """

    json_list = []

    if args.files:
        for filename in args.files:
            try:
                with open(filename, "r", encoding="ASCII") as file:
                    data = json.load(file)
                    json_list.append(data)
            except FileNotFoundError:
                print("File not found")
    elif args.dir:
        try:
            items = os.listdir(args.dir)

            for item in items:
                file_path = os.path.join(args.dir, item)
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, "r", encoding="ASCII") as file:
                            data = json.load(file)
                            json_list.append(data)
                    except FileNotFoundError:
                        print("File not found")
        except FileNotFoundError:
            print("Directory not found")

    return json_list

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

    return compare_dict

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

    return score_dict

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

    print(times)
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
            The dict with all the ranked, actually ranked properly 
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

    json_list = read_json(args)
    compare_dict = create_compare_dict(json_list)
    score_dict = get_scores(compare_dict)
    ordered_dict = order_ranking(score_dict)

    # ordered_dict["metadata"] = {
    #     "scale": metadata_dict["scale"],
    #     "seed": metadata_dict["seed"],
    #     "workers": metadata_dict["workers"],
    #     "runs": metadata_dict["runs"],
    #     "read_queries": metadata_dict["read_queries"],
    #     "start_date": metadata_dict["start_date"]
    # }

    output_file = "tsbs_ranking.json"

    print("Output written to: " + output_file)

    with open(output_file, "w", encoding="ASCII") as f:
        json.dump(ordered_dict, f, indent=4)

if __name__ == "__main__":
    main()
