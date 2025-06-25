import os
import sys
import json
import hyperspy


if __name__ == "__main__":

    try:
        if len(sys.argv) != 2:
            raise Exception("Please provide input directory name as an argument: python hyperspy_script.py <directory_name>")

        input_dir = sys.argv[1]
        if not (os.path.exists(input_dir) and os.path.isdir(input_dir)):
            raise Exception(f"Directory with name '{input_dir}' does not exist.")

        for filename in os.listdir(input_dir):
            print("\n" + filename)
            metadata_dict = {}

            if filename.endswith(".emd"):
                # read file using the hyperspy library
                # f is a list of hyperspy classes of different acquisitions
                # we keep the general metadata from the first EDSTEMSpectrum
                # we keep Scan, Stage, Optics, Detectors and Instrument metadata for HAADF
                # we keep the list of different elements used in the acquisitions
                # .metadata and .original_metadata are of type 'hyperspy.misc.utils.DictionaryTreeBrowser'
                
                try:
                    f = hyperspy.api.load(os.path.join(input_dir, filename))

                    if len(f) == 1:
                        for el in f:
                            metadata_dict["STEM_HAADF"] = {
                                "Acquisition_instrument": el.metadata.get_item("Acquisition_instrument").as_dictionary(),
                                "General": el.metadata.get_item("General").as_dictionary(),
                                "Signal": el.metadata.get_item("Signal").as_dictionary()
                            }
                    else:
                        for el in f:
                            if hyperspy._signals.eds_tem and isinstance(el, hyperspy._signals.eds_tem.EDSTEMSpectrum):
                                metadata_dict[
                                    el.metadata.get_item("General").get_item("title")
                                ] = {
                                    "Acquisition_instrument": el.metadata.get_item("Acquisition_instrument").as_dictionary(),
                                    "General": el.metadata.get_item("General").as_dictionary(),
                                    "Signal": el.metadata.get_item("Signal").as_dictionary(),
                                    "Sample": el.metadata.get_item("Sample").as_dictionary(),
                                }
                            elif isinstance(el, hyperspy._signals.signal2d.Signal2D) and el.metadata.get_item("General").get_item("title") == "HAADF":
                                metadata_dict[
                                    el.metadata.get_item("General").get_item("title")
                                ] = {
                                    "Signal": el.metadata.get_item("Signal").as_dictionary(),
                                    "Scan": el.original_metadata.get_item("Scan").as_dictionary(),
                                    "Stage": el.original_metadata.get_item("Stage").as_dictionary(),
                                    "Optics": el.original_metadata.get_item("Optics").as_dictionary(),
                                    "Detectors": el.original_metadata.get_item("Detectors").as_dictionary(),
                                    "Instrument": el.original_metadata.get_item("Instrument").as_dictionary()
                                }

                    # create output directory if it doesn't exist
                    output_dir = sys.argv[0].replace(".py", "_") + "metadata/"
                    os.makedirs(output_dir, exist_ok=True)
                    # save metadata as a json file
                    with open(output_dir + filename.replace(" ", "_") + "_metadata.json", "w") as outfile:
                        json.dump(metadata_dict, outfile, sort_keys=True, indent=4)

                except Exception as e:
                    print(e)
                    pass

            elif filename.endswith(".prz"):
                # this version of hyperspy does not support .prz files
                # adding this part of code to preserve the original error messages

                try:
                    f = hyperspy.api.load(os.path.join(input_dir, filename))

                except Exception as e:
                    print(e)
                    pass

            else:
                print("Unsupported file format.")
                pass

    except Exception as e:
        print(e)
