package main

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"

	conversion "github.com/osc-em/Converter"
)

func runCmd(name string, args ...string) (string, error) {
	var outBuf bytes.Buffer
	cmd := exec.Command(name, args...)
	cmd.Stdout = &outBuf
	err := cmd.Run()
	return outBuf.String(), err
}

func main() {
	inputDir := "/app/input"
	outputDir := "/app/output"

	fmt.Println("Running Python extractor...")
	pythonArgs := []string{"-m", "extractor", inputDir, outputDir}
	data, err := runCmd("python3", pythonArgs...)
	if err != nil {
		fmt.Fprintln(os.Stderr, "Python extractor failed due to:", err)
		os.Exit(1)
	}

	fmt.Println("Running Go converter...")
	out, err := conversion.Convert([]byte(data), "", "", "", outputDir+"/converted.json")
	if err != nil {
		fmt.Fprintln(os.Stderr, "The Go converter failed due to:", err)
		os.Exit(1)
	}
	fmt.Println("\n", string(out))
}
