package hardware;

import (
    "io"
    "os"
    "fmt"
    "context"
    "os/exec"
    "syscall"

    "github.com/minio/minio-go/v7"
    log "github.com/sirupsen/logrus"
    "gitlab.com/mergetb/tech/shared/storage/decompression"

    "gitlab.com/mergetb/tech/sled2/pkg/comms"
)


func StampImage(name, dest, server string, image *string, decompr *decompression.Decompressor) error {

	mc, err := comms.MarsMinIOImageClient(server)
	if err != nil {
		return fmt.Errorf("minio connect: %v", err)
	}

	obj, err := mc.GetObject(context.TODO(), "images", name, minio.GetObjectOptions{})
	if err != nil {
		return fmt.Errorf("minio get object: %v", err)
	}
	defer obj.Close()

	out, err := os.OpenFile(dest, os.O_WRONLY, 0600)
	if err != nil {
		return fmt.Errorf("open %s: %v", dest, err)
	}
	defer out.Close()

	log.Printf("begin image copy")

	if decompr != nil {
		err = (*decompr)(out, obj)
	} else {
                // err = decompression.MagicDecompressorBySeekable(out, obj)
                io.Copy(out, obj)
	}

	if err != nil {
		return fmt.Errorf("decompress: %v", err)
	}

	(*image) = name
	log.Printf("image download complete")

        err = StampFile(dest, "/dev/nvme0n1")
        if err != nil {
            return fmt.Errorf("error stamping: %v", err)
        }

	return nil
}

func StampFile(src, dest string) error {
    log.Infof("writing %v to %v", src, dest)

    img := fmt.Sprintf("if=%v", src)
    dev := fmt.Sprintf("of=%v", dest)

    cmd := exec.Command("dd", img, dev, "bs=4M", "status=progress", "conv=fsync")
    cmd.Stdout = os.Stdout
    cmd.Stderr = os.Stderr

    if err := cmd.Run(); err != nil {
        return fmt.Errorf("error running dd: %v", err)
    }

    log.Info("sucessfully completed write")

    // Issue a flush to ensure all write caches are cleared
    syscall.Sync();
    
    log.Info("called sync successfully")

    // Load the new partition table on drive
    cmd = exec.Command("partprobe")
    cmd.Stdout = os.Stdout
    cmd.Stderr = os.Stderr

    if err := cmd.Run(); err != nil {
        return fmt.Errorf("error running partprobe: %v", err)
    }

    log.Info("called partprobe successfully")

    // Load the new partition table on drive
    cmd = exec.Command("systemctl", "daemon-reload")
    cmd.Stdout = os.Stdout
    cmd.Stderr = os.Stderr

    if err := cmd.Run(); err != nil {
        return fmt.Errorf("error running systemctl daemon-reload: %v", err)
    }

    log.Info("called systemctl daemon-reload successfully")

    // Adjust firmware to boot into new image
    return AdjustBootToNVME()

}

func AdjustBootToNVME() error {
    cmd := exec.Command("/root/build-eeprom-ssd.sh")
    cmd.Stdout = os.Stdout
    cmd.Stderr = os.Stderr

    if err := cmd.Run(); err != nil {
        return fmt.Errorf("error running /root/build-eeprom-ssd.sh: %v", err)
    }

    log.Info("called /root/build-eeprom-ssd.sh successfully")

    return nil
}

