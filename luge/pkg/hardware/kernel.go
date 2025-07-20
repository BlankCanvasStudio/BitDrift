package hardware;

import (
    "os"
    "fmt"
    "regexp"
    "os/exec"
    "strings"
    "strconv"
    "io/ioutil"
)

func readKernelParam(name string) (string, error) {

	cmdline, err := ioutil.ReadFile("/proc/cmdline")
	if err != nil {
		return "", fmt.Errorf("failed to read /proc/cmdline: %v", err)
	}

	args := strings.Fields(string(cmdline))
	var value string
	for _, x := range args {
		parts := strings.Split(x, "=")
		if len(parts) == 2 {
			if parts[0] == name {
				value = parts[1]
			}
		}
	}

	if value == "" {
		return "", fmt.Errorf("%s kernel parameter not found", name)
	}

	return value, nil

}

func WriteCmdline(cmdline string) error {
    infravid := 0
    var err error

    params := strings.Fields(cmdline)
    inframac, err := readKernelParam("inframac")
    if err != nil {
        return fmt.Errorf("failed to read inframac from current /proc/cmdline")
    }

    for _, param := range params {
        if !strings.Contains(param, "infravid") { continue }
        infravid, err = strconv.Atoi(strings.Split(param, "=")[1])
        if err != nil {
            return fmt.Errorf("failed to part %v to an int", err)
        }
    }

    cmd := "mount /dev/nvme0n1p1 /mnt"
    args := strings.Fields(cmd)
    res := exec.Command(args[0], args[1:]...)
    res.Stdout = os.Stdout
    res.Stderr = os.Stderr
    if err := res.Run(); err != nil {
        return fmt.Errorf("error running %v: %v", cmd, err)
    }

    content, err := ioutil.ReadFile("/mnt/cmdline.txt")
    if err != nil {
        return fmt.Errorf("error reading file: %v", err)
    }

    newLine := updateCmdline(string(content), inframac, infravid)

    // Write the updated line back to the file (overwrite)
    err = ioutil.WriteFile("/mnt/cmdline.txt", []byte(newLine), 0644)
    if err != nil {
        return fmt.Errorf("error writing to file: %v", err)
    }

    return UnmountNvme()
}


func updateCmdline(cmdline string, inframac string, infravid int) string {
    // Remove annoying cmdline
    cmdline = strings.Replace(cmdline, "\n", "", -1)

    // Replace inline
    if strings.Contains(cmdline, "infravid") {
        m1 := regexp.MustCompile(`infravid=[0-9]*`)
        newInfra := fmt.Sprintf("infravid=%v", infravid)
        cmdline = m1.ReplaceAllString(cmdline, newInfra)
    } else {
        cmdline = fmt.Sprintf("%s infravid=%v", cmdline, infravid)
    }

    if strings.Contains(cmdline, "inframac") {
        m1 := regexp.MustCompile(`inframac=[0-9a-fA-F:]*`)
        newInfra := fmt.Sprintf("inframac=%v", inframac)
        cmdline = m1.ReplaceAllString(cmdline, newInfra)
    } else {
        cmdline = fmt.Sprintf("%s inframac=%v", cmdline, inframac)
    }

    // // Construct the updated line by appending it
    // newLine := fmt.Sprintf("%s infravid=%v inframac=%v", cmdline, infravid)

    return cmdline
}


func UnmountNvme() error {
    cmd := "umount /mnt"
    args := strings.Fields(cmd)
    res := exec.Command(args[0], args[1:]...)
    res.Stdout = os.Stdout
    res.Stderr = os.Stderr
    if err := res.Run(); err != nil {
        return fmt.Errorf("error running %v: %v", cmd, err)
    }

    return nil
}


func Restart() error {
    cmd := exec.Command("reboot")

    err := cmd.Run()
    if err != nil {
            return err
    }

    // Lmao
    return nil
}

