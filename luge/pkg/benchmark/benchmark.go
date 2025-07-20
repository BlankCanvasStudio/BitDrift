package benchmark;

import (
    "fmt"
    "time"
    "reflect"
    "runtime"

    log "github.com/sirupsen/logrus"

    "gitlab.com/mergetb/tech/sled2/pkg/hardware"

    "gitlab.com/mergetb/tech/shared/storage/decompression"

)

var (
	benchmark_runs = 2
)

func BenchImages(dest, server string) error {

	log.Printf("Starting image benchmark")

	boots := []string{
		"bios",
		"efi",
	}

	rootfses := []string{
		"tc12-rootfs",
		"tc13-rootfs",
		"bullseye-rootfs",
		"buster-rootfs",
		"1804-rootfs",
		"2004-rootfs",
		"hypervisor-rootfs",
	}

	exts := []struct {
		Ext     string
		Decompr decompression.Decompressor
	}{
		{".gz", decompression.DecompressGZIP},
		{".xz", decompression.DecompressXZ},
		{".raw", decompression.DecompressRAW},
		{".zst3", decompression.DecompressZSTDGolang},
		{".zst22", decompression.DecompressZSTDGolang},
		{".zst3", decompression.DecompressZSTDBinary},
		{".zst22", decompression.DecompressZSTDBinary},
		{".lz4", decompression.DecompressLZ4},
	}

	dests := []string{
		"/dev/null",
		dest,
	}

	for _, mapping := range exts {
		for _, boot := range boots {
			for _, rootfs := range rootfses {
				for _, loc := range dests {
					ext := mapping.Ext
					decompr := mapping.Decompr

					image := fmt.Sprintf("%s/%s%s", boot, rootfs, ext)

					err := benchImage(image, loc, server, &image, decompr)
					if err != nil {
						log.Printf("benchImage: %v", err)
					}
				}
			}
		}
	}

	log.Printf("Image benchmark complete!")

	return nil

}

func benchImage(name, dest, server string, image *string, decompr decompression.Decompressor) error {

	var total time.Duration

	for runs := 0; runs < benchmark_runs; runs++ {

		start := time.Now()
		err := hardware.StampImage(name, dest, server, image, &decompr)
		taken := time.Since(start)

		if err != nil {
			log.Printf("stamp image err: %v", err)
			time.Sleep(5 * time.Second)
		} else {
			total += taken
		}

	}

	fname := runtime.FuncForPC(reflect.ValueOf(decompr).Pointer()).Name()
	average := total / time.Duration(benchmark_runs)

	log.Printf("\n\nImage: %s\nFunction: %s\nDest: %s\n  Runs: %d\n  Total: %s\n  Average: %s\n\n", name, fname, dest, benchmark_runs, total.String(), average.String())

	return nil

}
