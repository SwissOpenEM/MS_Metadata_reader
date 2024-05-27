import os
import sys
import json
from rsciio.emd import file_reader as emd_reader
from rsciio.pantarhei import file_reader as prz_reader


if __name__ == "__main__":

    try:
        if len(sys.argv) != 2:
            raise Exception("Please provide input directory name as an argument: python rsciio_script.py <directory_name>")

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
