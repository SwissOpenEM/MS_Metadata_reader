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

    # Identify all imaging (camera) detectors and store them as ImagingDetector1, ImagingDetector2, etc.
    imaging_detectors = [
        detector for detector in metadata_dict.get("Detectors", {}).values()
        if detector.get("DetectorType") == "ImagingDetector"
    ]
    for idx, detector in enumerate(imaging_detectors, start=1):
        metadata_dict["Detectors"][f"ImagingDetector{idx}"] = detector

    # Identify binary result detector
    prefix = metadata_dict["BinaryResult"]["Detector"]
    # Find first detector with key Detectors.Detector-[somenumber] and DetectorName starting with prefix
    for key in list(metadata_dict["Detectors"].keys()):
        if key.startswith("Detector-") and metadata_dict["Detectors"][key].get("DetectorName", "").startswith(prefix):
            metadata_dict["Detectors"]["Detector-BinaryResult"] = metadata_dict["Detectors"].pop(key)
            metadata_dict["Detectors"]["Detector-BinaryResult"]["DetectorName"] = prefix
            break  # stop after first match

    # Keep only detectors with Enabled == "true" and Inserted == "true"
    detectors = metadata_dict.get("Detectors", {})
    keys_to_remove = []
    for key in list(detectors.keys()):
        if key.startswith("Detector-") and key != "Detector-BinaryResult":
            detector = detectors[key]
            if not (detector.get("Enabled", "") == "true" and detector.get("Inserted", "") == "true"):
                keys_to_remove.append(key)
    for key in keys_to_remove:
        detectors.pop(key)

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

    key_to_find_1 = "Instrument.InstrumentClass"
    key_to_find_2 = "Instrument.InstrumentModel"
    if key_to_find_1 in metadata_dict and key_to_find_2 in metadata_dict:
        metadata_dict[key_to_find_2] = metadata_dict[key_to_find_1] + " " + metadata_dict[key_to_find_2]

    return metadata_dict


def process_prz_metadata(metadata_dict):
    """ Processes the metadata dictionary to map values."""

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

    key_to_find_1 = "Acquisition_instrument.TEM.acquisition_mode"
    key_to_find_2 = "General.title"
    key_to_add = "Extractor.operating_mode"
    if key_to_find_1 in metadata_dict and key_to_find_2 in metadata_dict:
        metadata_dict[key_to_add] = metadata_dict[key_to_find_1] + " " + metadata_dict[key_to_find_2]

    key_to_find_1 = "source.detector_config.description"
    key_to_find_2 = "source.name"
    if key_to_find_1 in metadata_dict and key_to_find_2 in metadata_dict:
        if metadata_dict[key_to_find_1] == metadata_dict[key_to_find_2]:
            del metadata_dict[key_to_find_2]

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
    """Reads metadata from a PRZ file and processes it."""

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
        python3 -m extractor <input_directory> <output_directory>
    """

    try:
        if len(sys.argv) != 3:
            raise Exception("Please provide input and output directory names as arguments: python3 -m extractor <input_directory> <output_directory>")

        input_dir = sys.argv[1]
        if not (os.path.exists(input_dir) and os.path.isdir(input_dir)):
            raise Exception(f"Directory with name '{input_dir}' does not exist.")

        output_dir = sys.argv[2]
        os.makedirs(output_dir, exist_ok=True)

        for filename in os.listdir(input_dir):
            print("\n" + filename, file=sys.stderr)
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
                    print(e, file=sys.stderr)
                    pass

            elif filename.endswith(".prz"):
                try:
                    f = prz_reader(os.path.join(input_dir, filename))

                    metadata_dict.update(f[0]["metadata"])
                    metadata_dict.update(f[0]["original_metadata"])
                    metadata_dict["axes"] = f[0]["axes"]

                    metadata_dict = prz_extractor(metadata_dict)

                except Exception as e:
                    print(e, file=sys.stderr)
                    print("Trying again, using numpy...", file=sys.stderr)
                    
                    try:
                        f = np.load(os.path.join(input_dir, filename), allow_pickle=True)

                        meta_data = f["meta_data"].tolist()
                        data_model = f["data_model"].tolist()

                        metadata_dict = {}
                        for data in meta_data:
                            metadata_dict.update(data)
                        for data in data_model:
                            metadata_dict.update(data)
                        print("Success", file=sys.stderr)

                        metadata_dict = prz_extractor(metadata_dict)

                    except Exception as e:
                        print(e, file=sys.stderr)
                        pass

            else:
                print("Unsupported file format.", file=sys.stderr)
                pass

            # save metadata as a json file
            with open(os.path.join(output_dir, filename.replace(" ", "_") + "_metadata.json"), "w") as outfile:
                json.dump(metadata_dict, outfile, sort_keys=True, indent=4)

            print(json.dumps(metadata_dict, sort_keys=True))

    except Exception as e:
        print(e, file=sys.stderr)
