all: build/sledc build/meltc

PKG_SOURCES := $(shell find pkg -name '*.go')

SLEDC_SOURCES := $(shell find cmd/sledc -name '*.go')
build/sledc: $(SLEDC_SOURCES) $(PKG_SOURCES)
	GOARCH=arm64 go build -o $@ cmd/sledc/main.go


MELTC_SOURCES := $(shell find cmd/meltc -name '*.go')
build/meltc: $(MELTC_SOURCES) $(PKG_SOURCES)
	mkdir -p build
	GOARCH=arm64 go build -o $@ cmd/meltc/main.go


.PHONY: clean
clean:
	@rm -rf build

