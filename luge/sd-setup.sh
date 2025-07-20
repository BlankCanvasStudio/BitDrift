#!/bin/bash

DRIVE=""
FRESH=false
INFRA="d8:3a:dd:e2:d7:59"


show_help() {
    echo -e ""
    echo -e "Welcome to the luge build! This program installs a custom version of 'sled' on raspberry pis"
    echo -e ""
    echo -e "This program is very simple, it simply stuffs all the necessary sled components into a raspbian image installed at <drive>'s 2nd partition"
    echo -e "\tie /dev/sda2"
    echo -e ""
    echo -e "Luge NEEDS to run on raspian, as it overwrites the firmware and this is the simplest way to do that."
    echo -e ""
    echo -e "Usage: ./sd-setup.sh [options] <drive> [fresh]"
    echo -e ""
    echo -e "<drive> is the root device you ALREADY have raspbian installed on"
    echo -e ""
    echo -e "'fresh' is an optional parameter you can pass in to resize the second partition to take up the whole drive. Not all installers do this by default"
    echo -e ""
    echo -e "Options:"
    echo -e "\t-h | --help shows this menu"
    echo -e "\t-i | --infra specified the inframac MAC address. default is $INFRA"
    echo -e ""
}


# Parse out drive
while [[ $# -gt 0 ]]; do

    case $1 in
        -h | --help)
            show_help
            shift
            ;;
        -i | --infra)
            shift
            INFRA="$1"
            shift
            ;;
        "fresh")
            FRESH=true;
            shift
            ;;

        *)
            if [ ! "$DRIVE" = "" ]; then
                echo "Unknown cli parameter $1"
                echo "Exiting..."
                exit 1
            fi

            if [ ! -b "$1" ]; then
                echo "Invalid device name: $1"
                echo "Exiting..."
                exit 1
            fi

            echo "Using drive: $1"
            DRIVE=$1
            shift
            ;;

    esac
done



if [ "$DRIVE" = "" ]; then
    echo "Please specify a drive to install luge on!"
    exit 1
fi


set -ex


make build/sledc
make build/meltc


BOOT="${DRIVE}1"
PART="${DRIVE}2"

# Ensure the partition exists
if [ ! -b "$PART" ]; then
    echo "Partition $PART not found!"
    exit 1
fi

# Expand partition if requested
if [ "$FRESH" = "true" ]; then
    
    # Detect filesystem type
    FS_TYPE=$(sudo blkid -o value -s TYPE "$PART")
    echo "file system type: $FS_TYPE"

     # Grow partition
    echo "Resizing partition..."
    DRIVE=$(echo "$PART" | sed 's|[0-9]||g')
    PART_NUM=$(echo $PART | sed 's#[a-zA-Z]##g' | sed 's#\/##g')
    sudo growpart "$DRIVE" "$PART_NUM"
   
    # Resize filesystem based on type
    echo "Resizing filesystem..."
    case "$FS_TYPE" in
        ext4)  sudo resize2fs "$PART" ;;
        f2fs)  sudo resize.f2fs "$PART" ;;
        xfs)   sudo xfs_growfs "$PART" ;;
        *)     echo "Unsupported filesystem: $FS_TYPE"; exit 1 ;;
    esac
    
    echo "Resize complete!"
fi


# Copy over necessary files
sudo mount $PART /mnt

# Add in sled services & related files
sudo cp build/sledc /mnt/root
# sudo cp ./pi/sledc.service /mnt/etc/systemd/system/multi-user.target.wants/sledc.service
sudo cp pi/sledc.service /mnt/usr/lib/systemd/system/sledc.service
sudo cp pi/build-eeprom-* /mnt/root

# Update /etc/hosts
echo "172.29.0.1        sled"   >> /mnt/etc/hosts
echo "172.29.0.1        images" >> /mnt/etc/hosts

# Symlink the service so its already enabled
sudo touch /usr/lib/systemd/system/sledc.service
sudo ln -sf /usr/lib/systemd/system/sledc.service /mnt/etc/systemd/system/multi-user.target.wants/sledc.service
sudo rm /usr/lib/systemd/system/sledc.service

sudo umount /mnt

# Add cmdline args
sudo mount $BOOT /mnt

if [ "$(cat /mnt/cmdline.txt | grep inframac)" = "" ]; then
    echo "$(cat /mnt/cmdline.txt) inframac=$INFRA" > /mnt/cmdline.txt
fi

sudo umount /mnt

