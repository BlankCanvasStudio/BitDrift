#!/bin/sh

# Only works on the pi 5
FILNAME=""

get_bootloader_filename() {
   CURDATE=$(date -d "$(vcgencmd bootloader_version |  head -n 1)" +%Y%m%d)
   FILNAME=""
   EEBASE=$(rpi-eeprom-update | grep RELEASE | sed 's/.*(//g' | sed 's/[^\/]*)//g')
   if grep FIRMWARE_RELEASE_STATUS /etc/default/rpi-eeprom-update | egrep -Eq "stable|latest"; then
      EEPATH="${EEBASE}/latest/pieeprom*.bin"
   else
      EEPATH="${EEBASE}/default/pieeprom*.bin"
   fi
   EXACT_MATCH=0
   for filename in $(find $EEPATH -name "pieeprom*.bin" 2>/dev/null | sort); do
      FILDATE=$(date -d "$(echo $filename | sed 's/.*\///g' | cut -d - -f 2- | cut -d . -f 1)" +%Y%m%d)
      FILNAME=$filename
      if [ $FILDATE -eq $CURDATE ]; then
         EXACT_MATCH=1
         break
      fi
   done
   if [ $EXACT_MATCH != 1 ]; then
      if [ "$INTERACTIVE" = True ]; then
         whiptail --yesno "Current EEPROM version $(date -d $CURDATE +%Y-%m-%d) or newer not found.\n\nTry updating the rpi-eeprom APT package.\n\nInstall latest local $(basename $FILNAME) anyway?" 20 70 3
         DEFAULTS=$?
         if [ "$DEFAULTS" -ne 0 ]; then
            FILNAME="none" # no
         fi
      fi
   fi
}

# Define the EEPROM configuration file path
EEPROM_CONFIG="/tmp/eeprom_config.txt"

EEPROM_BIN=$(find / | grep pieeprom | sort -V | tail -1)

# Dump current EEPROM config
rpi-eeprom-config > "$EEPROM_CONFIG"

# Modify BOOT_ORDER and add PCIE_PROBE if not present
grep -q '^BOOT_UART=' "$EEPROM_CONFIG" || echo 'BOOT_UART=1' >> "$EEPROM_CONFIG"
grep -q '^POWER_OFF_ON_HALT=' "$EEPROM_CONFIG" || echo 'POWER_OFF_ON_HALT=1' >> "$EEPROM_CONFIG"
sed -i '/^BOOT_ORDER=/c\BOOT_ORDER=0xf461' "$EEPROM_CONFIG"
grep -q '^PCIE_PROBE=' "$EEPROM_CONFIG" || echo 'PCIE_PROBE=1' >> "$EEPROM_CONFIG"

# Apply the updated EEPROM configuration
get_bootloader_filename
rpi-eeprom-config --apply "$EEPROM_CONFIG" "$FILNAME"

# Remove temporary file
rm "$EEPROM_CONFIG"

echo "EEPROM configuration updated."

