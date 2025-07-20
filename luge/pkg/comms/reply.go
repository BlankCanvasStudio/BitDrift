package comms;

import (
    "fmt"
    "time"

    log "github.com/sirupsen/logrus"

    "gitlab.com/mergetb/api/facility/v1/go"
)

var image string

func Nack(stream facility.Sled_WaitClient, mac string, cerr error, retry int) {
	if retry < 0 {
		log.Printf("failed to nack- leaving")
		return
	}

	toSend := &facility.SledWaitRequest{
		Ack: &facility.SledAck{
			Ack:   &facility.SledAck_None{true},
			Error: fmt.Sprintf("%v", cerr),
		},
		Mac: mac,
	}

	err := stream.Send(toSend)
	if err != nil {
		log.Printf("failed to send: %+v, %v", toSend, err)
		time.Sleep(2 * time.Second)

		// recurse
		Nack(stream, mac, cerr, retry-1)
	}

	log.Printf("negative acknowledgement sent: %+v", toSend)
}

func Ack(stream facility.Sled_WaitClient, state facility.SledState_State, mac string, retry int) {
	if retry < 0 {
		log.Printf("failed to ack- leaving")
		return
	}

	resp := &facility.SledAck{}

	// we will set the image to none, so the response as a non-nil
	// string value for server to recognize
	if image == "" {
		image = "none"
	}

	switch state {
	case facility.SledState_Stamp:
		resp.Ack = &facility.SledAck_Stamp{true}
	case facility.SledState_Waiting:
		resp.Ack = &facility.SledAck_Standby{image}
	case facility.SledState_Kexec:
		resp.Ack = &facility.SledAck_Kexec{true}
	default:
		log.Printf("unknown state to ack: %+v", state)
		return
	}

	toSend := &facility.SledWaitRequest{
		Ack: resp,
		Mac: mac,
	}

	err := stream.Send(toSend)
	if err != nil {
		log.Printf("failed to send: %+v, %v", toSend, err)
		time.Sleep(2 * time.Second)

		// recurse
		Ack(stream, state, mac, retry-1)
	}

	log.Printf("acknowledgement sent: %+v", toSend)

	return
}

