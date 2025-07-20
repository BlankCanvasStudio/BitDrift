package hardware;

import (
    "os"
    "fmt"
    "net"
    "time"
    "bytes"
    "errors"
    "context"

    "gitlab.com/mergetb/tech/rtnl"
    "github.com/vishvananda/netlink"
    log "github.com/sirupsen/logrus"
    "github.com/insomniacslk/dhcp/dhcpv4"
    "github.com/u-root/u-root/pkg/dhclient"
)

func ReadLinkInfo() {
    rtx, err := rtnl.OpenDefaultContext()
    if err != nil {
            log.Fatalf("rtnl open: %v", err)
    }
    defer rtx.Close()

    lnks, err := rtnl.ReadLinks(rtx, nil)
    if err != nil {
            log.Fatalf("rtnl read links: %v", err)
    }

    for _, l := range lnks {
            fmt.Printf("lnk %s: %+v", l.Info.Name, l)
    }

}

func FindInfranetLink() (string, error) {

	// read the infranet kernel paramter supplied to us from Mars
	macstr, err := readKernelParam("inframac")
	if err != nil {
		return "", fmt.Errorf("read kernelparam inframac: %v", err)
	}

        mac, err := net.ParseMAC(macstr)
	if err != nil {
		return "", fmt.Errorf("parse MAC %s: %v", macstr, err)
	}

	rtx, err := rtnl.OpenDefaultContext()
	if err != nil {
		return "", fmt.Errorf("rtnl open: %v", err)
	}
	defer rtx.Close()

	lnks, err := rtnl.ReadLinks(rtx, nil)
	if err != nil {
		return "", fmt.Errorf("rtnl read lniks: %v", err)
	}

	for _, l := range lnks {
		if bytes.Equal(mac, l.Info.Address) {
			return l.Info.Name, nil
		}
	}

	return "", fmt.Errorf("could not find link with MAC address %s", macstr)

}

func Prepare(mac *string) error {

	ifx, err := FindInfranetLink()
	if err != nil {
		return fmt.Errorf("error finding infranet link: %v", err)
	}

	// bring the infranet network interface up
	lnk, err := dhclient.IfUp(ifx, time.Duration(10*time.Second))
	if err != nil {
		return fmt.Errorf("error bringing link %v up: %v", lnk, err)
	}

	(*mac) = lnk.Attrs().HardwareAddr.String()

	// DHCP
	results := dhclient.SendRequests(
		context.TODO(), []netlink.Link{lnk}, true, false, dhclient.Config{
			Timeout:  15 * time.Second,
			Retries:  3,
			LogLevel: dhclient.LogDebug,
			V4ServerAddr: &net.UDPAddr{
				IP:   net.IPv4bcast,
				Port: dhcpv4.ServerPort,
			},
		},
		30*time.Second,
	)

	for result := range results {
		if result.Err != nil {
			log.Printf("lease error: %v", result.Err)
			continue
		}

		err := result.Lease.Configure()
		if err != nil && !errors.Is(err, os.ErrExist) {
			return fmt.Errorf("lease configure: %v", err)
		}

		return nil
	}

	return fmt.Errorf("dhcp failed")

}

