# Luge 

Welcome to Luge!

Sled requires kexec, a functionality not widely supported on arm devices, not supported on 
raspberry pis, and generally an issue. 

Luge addresses these issues by taking a much simpler approach. This version of sled writes raw 
image files to a secondary disk, overwrites the boot order on the raspi's EEPROM, and reboots your 
system. No kexec needed!

Luge does have one massive issue. The secondary OS you flash needs to check if it should revert 
back to sled onces its been decomissioned. The companion program `melt` and its daemon process 
`meltc`, should be inserted into your operating system and run on boot.

`./sd-setup.sh /dev/<drive>` will properly install luge onto a fresh install of raspain located on 
`/dev/<drive>`. Its a fairly simple bash script, so I consider it self documenting. Run 
`./sd-setup.sh -h` if you need further clarification.

Details on the luge and melt implementations are below.


### Requirements

`luge` needs to be executed in the raspian operating system. Accessing the EEPROM can be difficult 
and this is the simplest way accomplish that.

`melt` currently mounts the raspian operating system to re-write the EEPROM. This isn't 
technically necessary but you will find other methods difficult.


## Luge

Luge reads an OS from the sled client, writes it to /dev/nvme0n1, and reboots the raspberry pi 
into that operating system.

Luge uses the same communications protocals that sled uses, so it can be used with existing 
versions of sled without issue.

The communications protocol sled uses is fairly basic and can be found in 
`cmd/sledc/main.go:runSled`, but here's a breif overview of the important details:

1) The Sled server will wait for the node to connect before reconciling the node with the 
materialization. This means any materialization involving a node will wait until the node has 
properly connected to sled.

2) Sled can recieve 3 messages: a standby, a stamp, and a kexec message. 


### Standby Message

When standing by, sled shouldn't do anything other than ACK. 


### Stamp Message

When stamping, the message will contain a hard-drive image. If the HD image is the same as the 
current OS, don't do anything. If the image is different, it will be written to /dev/nvme0n1 and 
the EEPROM is adjusted so we can boot from it. The stamp message is sent before the kexec message 
but its possible to have the network glitch and the node only properly respond to the kexec 
message (without stamping the OS). In this very rare case, just reboot the node in luge and all 
will be well.


### Kexec Message

This message contains an initrd and a kernel. For our purposes, this message is simply ACKed and 
the node is rebooted (since the stamp was already recieved).


## Melt

`melt` and `meltc` are effectively the "inverse luge". `meltc` pings the sled container in the 
harbor infrapod (IP address 172.29.0.1) and checks what operating system it should be running. 
Once `meltc` has determined that it should be running `raspi-sled`, it will execute `melt`, which 
re-writes the onboard EEPROM and reboot the machine back into luge.

Technically speaking, `melt` and `meltc` aren't necessary, if your OS makes this check itself. 
Feel free to re-implement melt with your target operating system, its fairly trivial. 
`cmd/meltc/main.go` is a fairly readable example of how reverting to luge should be implemented, 
but I'll document it here for completeness sake.

To implement melt, you need to connect to the grpc port of the sled client at `172.29.0.1:6004` 
(seen in `pkg/comms/connect.go:SledClient`), read the stream from the sled client (seen in 
`cmd/meltc/main.go:runMeltc`), and wait for the `SledWaitResponse_Kexec` message to be sent. Once 
that is received, `/root/melt` is executed, which effectively mounts the raspian OS, exectues an 
EEPROM re-write, and reboot the machine so luge is started up.

Built to be compatible with sled 1 protocol.

Now depends on `dd` to flash OS

Depends on `python3`

depends on `findmnt`

Image Sleded into needs to boot EEPROM

