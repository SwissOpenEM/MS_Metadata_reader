import os
import sys
import json
import h5py
import numpy as np


# collect_types = set()
# {<class 'numpy.uint32'>, <class 'numpy.uint8'>, <class 'numpy.ndarray'>}

def get_ds_dictionaries(name, node):
    # print(name)
    if isinstance(node, h5py.Dataset):
        for item in node:
            if isinstance(item, bytes):
                metadata_dict[name] = json.loads(item.decode('utf-8'))
            elif isinstance(item, np.uint8) or isinstance(item, np.uint32):
                metadata_dict[name] = item


if __name__ == "__main__":

    try:
        if len(sys.argv) != 2:
            raise Exception("Please provide input directory name as an argument: python manual_script.py <directory_name>")

        input_dir = sys.argv[1]
        if not (os.path.exists(input_dir) and os.path.isdir(input_dir)):
            raise Exception(f"Directory with name '{input_dir}' does not exist.")

        for filename in os.listdir(input_dir):
            print("\n" + filename)
            metadata_dict = {}

            if filename.endswith(".prz"):
                try:
                    # --- with numpy ---
                    # f = np.load(os.path.join(input_dir, filename), allow_pickle=True)

                    # meta_data = f["meta_data"].tolist()
                    # data_model = f["data_model"].tolist()

                    # for dict in meta_data:
                    #     metadata_dict.update(dict)
                    # for dict in data_model:
                    #     metadata_dict.update(dict)
                    print("skip")

                except Exception as e:
                    print(e)
                    pass

            elif filename.endswith(".emd"):
                try:
                    # --- with h5py ---
                    f = h5py.File(os.path.join(input_dir, filename), "r")

                    print(f.keys())
                    # keys = ['Application', 'Data', 'Experiment', 'Features', 'Info', 'Operations', 'Presentation', 'Version']
                    # keys = ["Application", "Info", "Version"]

                    f.visititems(get_ds_dictionaries)
                    # print(collect_types)  

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
            with open(output_dir + filename.replace(" ", "_") + "_metadata.json", "w") as outfile:
                json.dump(metadata_dict, outfile, sort_keys=True, indent=4)

    except Exception as e:
        print(e)
