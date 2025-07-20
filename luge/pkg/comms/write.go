package comms;

import (
    "io"
    "os"
    "fmt"
    "context"

    log "github.com/sirupsen/logrus"

    "github.com/minio/minio-go/v7"
)

func writeTemp(mc *minio.Client, server, source, dest string) error {

	obj, err := mc.GetObject(context.TODO(), "images", source, minio.GetObjectOptions{})
	if err != nil {
		return fmt.Errorf("minio get object: %v", err)
	}

	out, err := os.Create(dest)
	if err != nil {
		return fmt.Errorf("open %s: %v", dest, err)
	}
	defer out.Close()

	log.Printf("begin file copy")

        var bytesOut []byte;
        _, err = obj.Read(bytesOut)
        if err != nil {
            fmt.Printf("\nerror reading custom bytes object: %v\n", err)
        } else {
            fmt.Printf("\nbytes out: %v", string(bytesOut))
        }

	_, err = io.Copy(out, obj)
	if err != nil {
		return fmt.Errorf("io.Copy: %v", err)
	}

	log.Printf("file copy complete")

	return nil

}
