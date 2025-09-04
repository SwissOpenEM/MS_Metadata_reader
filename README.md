# Materials Science EM Metadata Extractor

A Python script that extracts metadata from EM data for Materials Science.
The extractor is wrapped by a GoLang orchestrator, which will feed the extracted metadata to the [Converter](https://github.com/osc-em/Converter), for conversion to OSC-EM schema.
Currently supported file formats: `.emd`, `.prz`.

## Description

All materials science data files to be studied so far within the scope of OpenEM are in some form of hdf5 format.
To read them and extract their metadata, we are using extrernal libraries suited for this task.
These extrernal dependecies are the reason this extractor is written in Python, as Go does not support all of them.
In the rare case that a file cannot be processed by a library, the fallback solution is to use numpy, since all hdf5 files can also be read as numpy files.


## Extractor Code

Located in `extractor/__main__.py`.

Working for both `.emd` and `.prz` files, with the exception of some types of `.prz` files, which are still unsupported.
For these unsupported files we use `numpy` for manual extraction.
Note that the metadata of those will not be as complete.

### Dependencies
- python 3.12
- numpy 2.3.2
- h5py 3.14.0
- rsciio 0.10.0
- sparse 0.17.0

### Usage
You can directly run the extractor as it is, with `python3 -m extractor <input_directory> <output_directory>`.
For each file inside <input_directory> with name <file_name>, it will create a metadata file in <output_directory>, named <file_name>_metadata.json, and it will also print out the same results.


## Go Wrapper

To be able to run both Python and Go code together, and to avoid introducing external dependencies, we bundle the extractor into an executable and use a Go wrapper script.
We use `PyInstaller` to create the executable.

### PyInstaller Guide

PyInstaller is a tool that bundles Python applications and all their dependencies into a single executable file.
It packages Python code as bytecode along with a Python interpreter, making it run on systems without Python installed.

#### Step-by-Step Instructions

**1. Set Up Environment:**
Assuming you have a `venv` named `ms_extractor`, in which you have installed the extractor dependecies mentioned above, activate your virtual environment and install PyInstaller.

```bash
source ms_extractor/bin/activate
pip install pyinstaller
```

**2. Usage:**
```bash
pyinstaller --onefile --name=extractor_bin extractor/__main__.py --hidden-import=numpy.core._multiarray_umath --hidden-import=numpy.core._multiarray --collect-all=numpy
```

Where:
- `--onefile`: Creates single executable (slower startup; extracts to temp directory)
- `--name=extractor_bin`: Custom name for the executable
- `--hidden-import`: Add these flags to ensure numpy compatibility
- PyInstaller automatically detected and included:
  - `rsciio` and its dependencies
  - `numpy` and related libraries
  - `h5py` for HDF5 file support
  - `sparse` for n-d array support

This creates:
- `dist/` directory with your executable
- `build/` directory with temporary files
- `.spec` file (build configuration)

**3. After compilation:**
```bash
# Test the executable
./dist/extractor_bin <input_directory> <output_directory>

# Check file type
file dist/extractor_bin

# Check size
ls -lh dist/extractor_bin
```

**4. Cleanup:**
After a successful build, you can remove the temporary files.

```bash
rm -rf build/
rm *.spec  # if you don't need to customize
```

Keep only `dist/extractor_bin` for distribution.

### Using the executable

The Python executable is called by `main.go`, which after completing the metadata extraction, will then call the Go module for convertion to OSC-EM schema.
At the end, `converted.json` will be written inside the same <output_directory>.

#### Usage
```
go build -o ms_reader main.go
./ms_reader <input_directory> <output_directory>
```

#### Notes
For MS we assume that one experiment (one dataset) will only consist of one file.
Hence, <input_directory> should contain one file each time.
Then, the <output_directory> will contain two files: the extracted metadata and the converted one.
That is, the current version of the MS reader does not cover cases where a dataset may consist of multiple files.

For the converter to understand which MS conversion table to use, we read the type of the file inside <input_directory> and instruct the Go module to use the revelant table.
Currently there are two such tables: one for `.emd` and one for `.prz` files.
