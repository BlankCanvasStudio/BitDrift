package main

import (
    "io"
    "fmt"
    "time"
    "context"
    "strings"
    "os/exec"

    log "github.com/sirupsen/logrus"

    "gitlab.com/mergetb/api/facility/v1/go"

    "gitlab.com/mergetb/tech/sled2/pkg/comms"
    "gitlab.com/mergetb/tech/sled2/pkg/hardware"
)

var (
	mac       string
	image     = "efi/sce-kernel"
	retries   = 10
)


func main() {
    fmt.Println("starting luge")

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
        err := runMeltc()
        if err != nil {
                log.Printf("%+v\n", err)
                time.Sleep(1 * time.Second)
                continue
        }
    }
}


func runMeltc() error {
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

	err = stream.Send(&facility.SledWaitRequest{Mac: mac, Ack: nil})
	if err != nil {
		return err
	}
	log.Infof("sent initial request: %s", mac)

	log.Infof("entering event loop")
	for {
            log.Infof("reading message")
		resp, err := stream.Recv()
		if err == io.EOF {
			log.Infof("got EOF from sledapi")
			break
		}
                log.Infof("message read")
		if err != nil {
			return fmt.Errorf("stream recv: %v", err)
		}


		switch r := resp.WaitResponse.(type) {
		case *facility.SledWaitResponse_Standby:
			log.Infof("got standby request")
			comms.Ack(stream, facility.SledState_Waiting, mac, retries)

		case *facility.SledWaitResponse_Stamp:
			log.Infof("[stamp] %+v", r.Stamp)
			comms.Ack(stream, facility.SledState_Stamp, mac, retries)

		case *facility.SledWaitResponse_Kexec:
			log.Infof("[kexec] %+v", r.Kexec)

                        log.Infof("kexec message: %+v. Contains: %v", r.Kexec, strings.Contains(r.Kexec.Kernel, "sce"))

			// prevent duplicated work
			if strings.Contains(r.Kexec.Kernel, "sce") {
				log.Infof("same image, nothing to do")
				comms.Ack(stream, facility.SledState_Kexec, mac, retries)
                        } else {
                            comms.Ack(stream, facility.SledState_Kexec, mac, retries)

                            err := Melt()
                            if err != nil {
                                log.Errorf("error melting: %v", err)
                                continue
                            }

                            hardware.Restart()
                        }
                default:
                    log.Info("unknown message type recieved: %+v", resp)
                }

                log.Infof("read message. sleeping")
                time.Sleep(time.Duration(2) * time.Second)
	}

        return fmt.Errorf("runMeltc unexpected exit. left normal control flow")
}


func Melt() error {
    cmd := exec.Command("/root/melt")    

    err := cmd.Run()
    if err != nil {
            return err
    }

    return nil
}

