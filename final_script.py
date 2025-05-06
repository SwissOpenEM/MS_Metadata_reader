import os
import sys
import json
import numpy as np
from rsciio.emd import file_reader as emd_reader
from rsciio.pantarhei import file_reader as prz_reader


def flatten_metadata(metadata_dict, parent_key="", sep="."):
    """
    Flattens a nested dictionary into a single-level dictionary with keys as the path to each value.

    Args:
        metadata_dict (dict): The dictionary to flatten.
        parent_key (str): The base key string for recursion (used internally).
        sep (str): Separator to use for flattened keys.

    Returns:
        dict: A flattened dictionary.
    """
    items = []
    for k, v in metadata_dict.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_metadata(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_metadata(item, f"{new_key}[{i}]", sep=sep).items())
                else:
                    items.append((f"{new_key}[{i}]", item))
        else:
            items.append((new_key, v))
    return dict(items)


if __name__ == "__main__":
    """
    Main function to process metadata from files in a given directory.

    This script reads `.emd` and `.prz` files from the specified input directory,
    extracts their metadata, flattens the metadata structure, and saves it as JSON files
    in an output directory. Unsupported file formats are skipped.

    Usage:
        python final_script.py <directory_name>
    """

    try:
        if len(sys.argv) != 2:
            raise Exception("Please provide input directory name as an argument: python final_script.py <directory_name>")

        input_dir = sys.argv[1]
        if not (os.path.exists(input_dir) and os.path.isdir(input_dir)):
            raise Exception(f"Directory with name '{input_dir}' does not exist.")

        for filename in os.listdir(input_dir):
            print("\n" + filename)
            metadata_dict = {}

            if filename.endswith(".emd"):
                try:
                    f = emd_reader(os.path.join(input_dir, filename))

                    if len(f) == 1:
                        metadata_dict.update(f[0]["metadata"])
                        metadata_dict.update(f[0]["original_metadata"])
                        metadata_dict["axes"] = f[0]["axes"]
                    else:
                        metadata_dict["sample_elements"] = []
                        for el in f:
                            if el["metadata"]["General"]["title"] == "EDS":
                                metadata_dict.update(f[0]["metadata"])
                                metadata_dict.update(f[0]["original_metadata"])
                                metadata_dict["axes"] = f[0]["axes"]
                            else:
                                metadata_dict["sample_elements"].append(el["metadata"]["General"]["title"])

                except Exception as e:
                    print(e)
                    pass

            elif filename.endswith(".prz"):
                try:
                    f = prz_reader(os.path.join(input_dir, filename))

                    metadata_dict.update(f[0]["metadata"])
                    metadata_dict.update(f[0]["original_metadata"])
                    metadata_dict["axes"] = f[0]["axes"]

                except Exception as e:
                    print(e)
                    print("Trying again, using numpy...")
                    
                    try:
                        f = np.load(os.path.join(input_dir, filename), allow_pickle=True)

                        meta_data = f["meta_data"].tolist()
                        data_model = f["data_model"].tolist()

                        metadata_dict = {}
                        for data in meta_data:
                            metadata_dict.update(data)
                        for data in data_model:
                            metadata_dict.update(data)
                        print("Success")

                    except Exception as e:
                        print(e)
                        pass

            else:
                print("Unsupported file format.")
                pass

            # create output directory if it doesn't exist
            output_dir = sys.argv[0].replace(".py", "_") + "metadata/"
            os.makedirs(output_dir, exist_ok=True)
            # save metadata as a json file
            flattened_metadata = flatten_metadata(metadata_dict)
            with open(output_dir + filename.replace(" ", "_") + "_metadata.json", "w") as outfile:
                json.dump(flattened_metadata, outfile, sort_keys=True, indent=4)

    except Exception as e:
        print(e)
