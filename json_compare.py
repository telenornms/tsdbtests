"""
Compares the json files from benchmark
"""
import json
import argparse
import os

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
    metadata_dict = {}

    for file in json_list:
        for key in file.keys():
            if key != "metadata":
                compare_dict.setdefault(key, {})[
                        file["metadata"]["db_engine"]
                    ] = [
                        file[key]["time_run"], file[key]["time_avg"]
                    ]
            elif key == "metadata":
                metadata_dict = file["metadata"]

    return compare_dict, metadata_dict

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

    for key in compare_dict.keys():
        score_dict[key] = {
            "ranking": {},
            "variation": {}
        }

        for inner in compare_dict[key]:
            score_dict[key]["ranking"].update({
                inner: compare_dict[key][inner][1]
            })
            score_dict[key]["variation"].update({
                inner: {"largest_var": 0}
            })

            for i in compare_dict[key][inner][0]:
                comp = score_dict[key]["variation"][inner]["largest_var"]
                if abs(compare_dict[key][inner][1] - i) > comp:
                    score_dict[key]["variation"].update({
                        inner: {
                            "largest_var": round(abs(compare_dict[key][inner][1] - i), 2),
                            "percent": round(abs(100 - ((compare_dict[key][inner][1]/i) * 100)), 2)
                            }
                    })

    return score_dict

def order_ranking(score_dict):
    """
    Gets the numbers and ranks the dbs
    
    Parameters:
        score_dict : dict
            The dict with all the ranks, unranked
            
    Returns:
        ordered_score_dict : dict
            The dict with all the ranked, actually ranked properly 
    """

    ordered_score_dict = {}

    for key in score_dict:
        ordered_score_dict[key] = {
            "ranking": dict(sorted(score_dict[key]["ranking"].items(), key=lambda item: item[1])), 
            "variation": {}
        }

        for db in ordered_score_dict[key]["ranking"]:
            ordered_score_dict[key]["variation"][db] = score_dict[key]["variation"][db]

    return ordered_score_dict

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
    compare_dict, metadata_dict = create_compare_dict(json_list)
    score_dict = get_scores(compare_dict)
    ordered_score_dict = order_ranking(score_dict)

    ordered_score_dict["metadata"] = {
        "scale": metadata_dict["scale"],
        "seed": metadata_dict["seed"],
        "workers": metadata_dict["workers"],
        "runs": metadata_dict["runs"],
        "read_queries": metadata_dict["read_queries"],
        "start_date": metadata_dict["start_date"]
    }

    output_file = "tsbs_ranking.json"

    print("Output written to: " + output_file)

    with open(output_file, "w", encoding="ASCII") as f:
        json.dump(ordered_score_dict, f, indent=4)

if __name__ == "__main__":
    main()
