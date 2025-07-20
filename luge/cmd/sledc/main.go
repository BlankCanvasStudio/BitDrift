package main

import (
        "os"
	"io"
	"fmt"
	"time"
        "strings"
	"context"

	"github.com/spf13/cobra"
	log "github.com/sirupsen/logrus"

	"gitlab.com/mergetb/api/facility/v1/go"

        "gitlab.com/mergetb/tech/sled2/pkg/comms"
        "gitlab.com/mergetb/tech/sled2/pkg/hardware"
        "gitlab.com/mergetb/tech/sled2/pkg/benchmark"
)

var (
	mac       string
	image     = "raspi-sled"
	retries   = 10
	should_benchmark = false
)

func main() {

	root := &cobra.Command{
		Use:   "sledc",
		Short: "The Sled imaging client",
	}

	run := &cobra.Command{
		Use:   "run",
		Short: "Run the Sled imaging client",
		Args:  cobra.NoArgs,
		Run:   func(*cobra.Command, []string) { runClient() },
	}
	run.Flags().BoolVarP(
		&should_benchmark, "should_benchmark", "b", should_benchmark, "continously run the image copying and decrypting, for should_benchmarking")
	root.AddCommand(run)

	var server string
	stamp := &cobra.Command{
		Use:   "stamp <image> <disk>",
		Short: "Stamp an image on the disk from a remote S3 server",
		Args:  cobra.ExactArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			err := hardware.StampImage(args[0], args[1], server, &image, nil)
			if err != nil {
				log.Fatal(err)
			}
		},
	}
	stamp.Flags().StringVarP(
		&server, "server", "s", "images:9000", "S3 server to fetch image from")
	root.AddCommand(stamp)

	root.Execute()

}

func runClient() {

	log.Printf("starting sled")

        hardware.ReadLinkInfo()

	// preparation loop
	for {
		err := hardware.Prepare(&mac)
		if err != nil {
			log.Printf("%+v\n", err)
			time.Sleep(1 * time.Second)
			continue
		}
		break
	}

	for {
		err := runSled()
		if err != nil {
			log.Printf("%+v\n", err)
			time.Sleep(1 * time.Second)
                        continue
		}
	}
}

func runSled() error {

	// connect to sled apiserver
	client, conn, err := comms.SledClient()
	if err != nil {
		return err
	}
	defer conn.Close()

	// wait for events
	stream, err := client.Wait(context.Background())
	if err != nil {
		return err
	}

        file, err := os.Create("/tmp/harddrive")
        if err != nil {
            return fmt.Errorf("error crating /tmp/harddrive: %v", err)
        }
        file.Close()

	err = stream.Send(&facility.SledWaitRequest{Mac: mac, Ack: nil})
	if err != nil {
		return err
	}
	log.Infof("sent initial request: %s", mac)

	log.Infof("entering event loop")
	for {

		resp, err := stream.Recv()
		if err == io.EOF {
			log.Infof("got EOF from sledapi")
			break
		}
		if err != nil {
		    return fmt.Errorf("stream recv: %v", err)
		}

		switch r := resp.WaitResponse.(type) {
		case *facility.SledWaitResponse_Standby:
			log.Infof("got standby request")
			comms.Ack(stream, facility.SledState_Waiting, mac, retries)

		case *facility.SledWaitResponse_Stamp:

			// prevent duplicated work
			if strings.Contains(r.Stamp.Image, "raspi-sled") {
				log.Infof("[stamp] same image, nothing to do")
				comms.Ack(stream, facility.SledState_Stamp, mac, retries)
			} else {
			    log.Infof("[stamp] %+v", r.Stamp)

                            if should_benchmark {
                                    benchmark.BenchImages(r.Stamp.Device, r.Stamp.Server)
                                    os.Exit(0)
                            }

                            err = hardware.StampImage(r.Stamp.Image, "/tmp/harddrive", r.Stamp.Server, &image, nil)
                            if err != nil {
                                    log.Errorf("stamp image error: %v", err)
                                    comms.Nack(stream, mac, err, retries)

                                    // if we get an error stamping, this is going to force the client
                                    // to reset the loop to try forever until the server tells the client
                                    // to do something different.
                                    return err
                            } else {
                                    comms.Ack(stream, facility.SledState_Stamp, mac, retries)
                            }
			}

		case *facility.SledWaitResponse_Kexec:

			// prevent duplicated work
			if strings.Contains(r.Kexec.Kernel, "raspi-sled") {
				log.Infof("[kexec] same image, nothing to do")
				comms.Ack(stream, facility.SledState_Kexec, mac, retries)
                        } else {
			    log.Infof("[kexec] %+v", r.Kexec)

                            err = hardware.WriteCmdline(r.Kexec.Cmdline)
                            if err != nil {
                                comms.Nack(stream, mac, err, retries)
                                hardware.UnmountNvme() // ok if it dies
                                log.Fatalf("failed to update infravid: %v", err)
                                return fmt.Errorf("failed to update infravid")
                            }

                            err = hardware.AdjustBootToNVME()
                            if err != nil {
                                comms.Nack(stream, mac, err, retries)
                                log.Fatalf("failed to adjust boot to nvme: %v", err)
                            }

                            comms.Ack(stream, facility.SledState_Kexec, mac, retries)
                            hardware.Restart()
                        }
                }
	}

	return nil
}

