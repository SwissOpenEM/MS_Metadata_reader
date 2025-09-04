package main

import (
	"bytes"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	conversion "github.com/osc-em/Converter"
)

func getFileTypeFromDir(dirPath string) (string, error) {
	entries, err := os.ReadDir(dirPath)
	if err != nil {
		return "", err
	}

	// Find the first regular file (not directory)
	for _, entry := range entries {
		if !entry.IsDir() {
			filename := entry.Name()
			ext := strings.ToLower(filepath.Ext(filename))
			return strings.TrimPrefix(ext, "."), nil
		}
	}
	return "", fmt.Errorf("no regular file found in directory")
}

func runCmd(name string, args ...string) (string, error) {
	var outBuf bytes.Buffer
	cmd := exec.Command(name, args...)
	cmd.Stdout = &outBuf
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	return outBuf.String(), err
}

func main() {
	inputDir := flag.String("i", "", "Input directory containing the file to process (required)")
	outputDir := flag.String("o", "", "Output directory for results (required)")

	flag.Parse()
	if *inputDir == "" || *outputDir == "" {
		fmt.Fprintf(os.Stderr, "Usage: %s -i <input_directory> -o <output_directory>\n", os.Args[0])
		flag.PrintDefaults()
		os.Exit(1)
	}

	// Get file type from input directory
	fileExt, err := getFileTypeFromDir(*inputDir)
	if err != nil {
		fmt.Fprintln(os.Stderr, "Failed to detect file type:", err)
		os.Exit(1)
	}

	// Ensure output dir exists
	if err := os.MkdirAll(*outputDir, 0755); err != nil {
		fmt.Fprintln(os.Stderr, "Failed to create output dir:", err)
		os.Exit(1)
	}

	execPath, err := os.Executable()
	if err != nil {
		fmt.Fprintln(os.Stderr, "Failed to get executable path:", err)
		os.Exit(1)
	}
	execDir := filepath.Dir(execPath)
	extractorPath := filepath.Join(execDir, "dist/extractor_bin")

	fmt.Println("=== Running Python extractor ===")
	args := []string{*inputDir, *outputDir}
	data, err := runCmd(extractorPath, args...)
	if err != nil {
		fmt.Fprintln(os.Stderr, "Extractor failed due to:", err)
		os.Exit(1)
	}

	fmt.Println("=== Running Go converter ===")
	// Point to the CSV file in the Converter project
	converterCSVPath := filepath.Join("..", "Converter", "csv", "ms_conversions_"+fileExt+".csv")
	out, err := conversion.Convert([]byte(data), converterCSVPath, "", "", *outputDir+"/converted.json")
	if err != nil {
		fmt.Fprintln(os.Stderr, "Converter failed due to:", err)
		os.Exit(1)
	}

	fmt.Println("\n=== MS Reader results ===")
	fmt.Println(string(out))
}
