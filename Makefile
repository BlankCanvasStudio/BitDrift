.DEFAULT_GOAL := install


.PHONY: depends
depends:
	if command -v dnf >/dev/null; then \
		dnf install -y unison ssh git; \
	elif command -v apt >/dev/null; then \
		apt install -y unison ssh git; \
	elif command -v pacman >/dev/null; then \
		pacman -S unison openssh git; \
	else \
		echo "failed to detect package manager"; \
		exit 1; \
	fi


.PHONY: install
install: \
	depends \
	/etc/bitdrift/bitdrift.conf \
	/usr/local/bin/bitdrift \
	/etc/systemd/system/bitdrift.service


/etc/bitdrift/bitdrift.conf: conf/bitdrift.conf
	mkdir -p /etc/bitdrift
	cp conf/bitdrift.conf /etc/bitdrift/bitdrift.conf

/usr/local/bin/bitdrift: cmd/bitdrift
	cp cmd/bitdrift /usr/local/bin/bitdrift

/etc/systemd/system/bitdrift.service: conf/bitdrift.service
	cp conf/bitdrift.service /etc/systemd/system/bitdrift.service

