import os
import sys
import json
import numpy as np
from rsciio.emd import file_reader as emd_reader
from rsciio.pantarhei import file_reader as prz_reader
from datetime import datetime


def convert_final_valuetypes(metadata_dict):
    """Converts values in the dictionary to their final types."""

    key_to_update = [
        "Optics.AccelerationVoltage",
        "electron_gun.voltage",
        "electron_gun.voltage_target",
        "CustomProperties.StemMagnification.value",
        "scan_driver.magnification",
    ]
    for key in key_to_update:
        if key in metadata_dict:
            metadata_dict[key] = str(int(float(metadata_dict[key])))

    return metadata_dict


def stringify_values(metadata_dict):
    """Recursively converts all values in the dictionary to strings."""

    if isinstance(metadata_dict, dict):
        return {k: stringify_values(v) for k, v in metadata_dict.items()}
    elif isinstance(metadata_dict, list):
        return [stringify_values(item) for item in metadata_dict]
    else:
        return str(metadata_dict)


def flatten_metadata(metadata_dict, parent_key="", sep="."):
    """
    Flattens a nested dictionary into a single-level dictionary with keys as the path to each value.

    Args:
        metadata_dict (dict): The dictionary to flatten.
        parent_key (str): The base key string for recursion (used internally).
        sep (str): Separator to use for flattened keys.
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


def process_emd_metadata(metadata_dict):
    """ Processes the metadata dictionary to identify and categorize detectors."""

    # Identify imaging (camera) detector - there should be only one
    imaging_detector = next(
        (detector for detector in metadata_dict.get("Detectors", {}).values()
        if detector.get("DetectorType") == "ImagingDetector"),
        None # default if not found
    )
    metadata_dict["Detectors"]["Detector-camera"] = imaging_detector

    # Identify analytical detector - do not keep the segments
    prefix = metadata_dict["BinaryResult"]["Detector"]
    # Find first detector with DetectorName starting with prefix
    for key, value in metadata_dict["Detectors"].items():
        if value.get("DetectorName", "").startswith(prefix):
            metadata_dict["Detectors"]["Detector-analytical"] = metadata_dict["Detectors"].pop(key)
            break # stop after first match

    # Identify scanning detectors in use
    scanning_detectors = {
        key: detector
        for key, detector in metadata_dict.get("Detectors", {}).items()
        if detector.get("DetectorType", "") == "ScanningDetector"
        and detector.get("Enabled", "") == "true"
        and detector.get("Inserted", "") == "true"
    }
    for key, value in scanning_detectors.items():
        metadata_dict["Detectors"]["Detector-" + value["DetectorName"]] = metadata_dict["Detectors"].pop(key)

    return metadata_dict


def map_emd_values(metadata_dict):
    """Transforms specific values in the metadata dictionary based on predefined mappings or formats."""

    key_to_update = "Optics.ProbeMode"
    value_map = {
        "1": "Nano probe",
        "2": "Micro probe",
    }
    if key_to_update in metadata_dict:
        current_value = metadata_dict[key_to_update]
        metadata_dict[key_to_update] = value_map[current_value] if current_value in value_map else current_value

    key_to_update = "Optics.OperatingMode"
    value_map = {
        "1": "TEM",
        "2": "STEM",
    }
    if key_to_update in metadata_dict:
        current_value = metadata_dict[key_to_update]
        metadata_dict[key_to_update] = value_map[current_value] if current_value in value_map else current_value

    key_to_update = "Acquisition.AcquisitionStartDatetime.DateTime"
    if key_to_update in metadata_dict:
        dt = datetime.fromtimestamp(int(metadata_dict[key_to_update]))
        metadata_dict[key_to_update] = dt.strftime('%Y-%m-%d %H:%M:%S')

    return metadata_dict


def process_prz_metadata(metadata_dict):
    """ Processes the metadata dictionary to map values."""

    key_to_update = "condenser.mode"
    if key_to_update in metadata_dict:
        probe_info = metadata_dict[key_to_update].split(":")
        metadata_dict[key_to_update] = probe_info[1] if len(probe_info) > 1 else probe_info[0]
        metadata_dict[key_to_update + ".probe_mode"] = probe_info[0]

    key_to_update = "image_size"
    if key_to_update in metadata_dict:
        image_size = tuple(map(int, metadata_dict[key_to_update].strip("()[]").replace(",", " ").split()))
        metadata_dict[key_to_update + ".height"] = str(image_size[0])
        metadata_dict[key_to_update + ".width"] = str(image_size[1]) if len(image_size) > 1 else str(image_size[0])
        del metadata_dict[key_to_update]

    key_to_update = "camera.binning"
    if key_to_update in metadata_dict:
        binning = tuple(map(int, metadata_dict[key_to_update].strip("()[]").replace(",", " ").split()))
        metadata_dict[key_to_update + "[0]"] = str(binning[0])
        metadata_dict[key_to_update + "[1]"] = str(binning[1]) if len(binning) > 1 else str(binning[0])
        del metadata_dict[key_to_update]

    return metadata_dict


def emd_extractor(metadata_dict: dict) -> dict:
    """Reads metadata from an EMD file and processes it."""

    return convert_final_valuetypes(
        map_emd_values(
            flatten_metadata(
                process_emd_metadata(
                    stringify_values(metadata_dict)
                )
            )
        )
    )


def prz_extractor(metadata_dict: dict) -> dict:
    """Reads metadata from an PRZ file and processes it."""

    return convert_final_valuetypes(
        process_prz_metadata(
            flatten_metadata(
                stringify_values(metadata_dict)
            )
        )
    )


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

                    metadata_dict = emd_extractor(metadata_dict)

                except Exception as e:
                    print(e)
                    pass

            elif filename.endswith(".prz"):
                try:
                    f = prz_reader(os.path.join(input_dir, filename))

                    metadata_dict.update(f[0]["metadata"])
                    metadata_dict.update(f[0]["original_metadata"])
                    metadata_dict["axes"] = f[0]["axes"]

                    metadata_dict = prz_extractor(metadata_dict)

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

                        metadata_dict = prz_extractor(metadata_dict)

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
