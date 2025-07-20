package comms;

import (
	"fmt"

	"google.golang.org/grpc"
	"github.com/minio/minio-go/v7"
	log "github.com/sirupsen/logrus"
	"github.com/minio/minio-go/v7/pkg/credentials"

	"gitlab.com/mergetb/api/facility/v1/go"
)


func MarsMinIOImageClient(server string) (*minio.Client, error) {

	return minio.New(
		fmt.Sprintf("%s", server),
		&minio.Options{
			Creds: credentials.NewStaticV4(
				"image",
				"imageread",
				"",
			),
			//TODO Secure: true, // implies ssl
		})

}

// read <name>=<value> from kernel parameters
func SledClient() (facility.SledClient, *grpc.ClientConn, error) {

	log.Printf("connecting to sled")

	conn, err := grpc.Dial("sled:6004", grpc.WithInsecure())
	if err != nil {
		return nil, nil, fmt.Errorf("dial sled: %v", err)
	}

	client := facility.NewSledClient(conn)

	return client, conn, err

}

