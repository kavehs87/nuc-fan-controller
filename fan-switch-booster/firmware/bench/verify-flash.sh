#!/bin/sh
# Verify what is actually in the Pro Mini's flash. Reads the whole 32 kB back, splits it
# into app + boot section, and compares both against the compiled sketch hex and the stock
# 3.3 V / 8 MHz bootloader. Then it disassembles the flashed code and checks which registers
# it really touches.
#
# This one reads over the ISP route (Uno-as-ISP on /dev/ttyACM0 at 19200), not the
# bootloader route flash-bootloader.sh writes over - which is the point: it checks the chip
# through a path that does not depend on the bootloader being healthy.
#
# usage: verify-flash.sh fan-switch-ladder

SKETCH=${1:-fan-switch-ladder}

AVR=$(find ~/.arduino15 -name avrdude -type f | head -1)
CONF=$(dirname "$AVR")/../etc/avrdude.conf
OBJ=$(find / -name avr-objcopy -type f 2>/dev/null | head -1)
OBJD=$(find /root/.arduino15 -name avr-objdump -type f | head -1)
CORE=$HOME/.arduino15/packages/arduino/hardware/avr/1.8.8
BL=$CORE/bootloaders/atmega/ATmegaBOOT_168_atmega328_pro_8MHz.hex
HEX=$(find /root/.cache -name "$SKETCH.ino.hex" | head -1)
ELF=$(find /root/.cache -name "$SKETCH.ino.elf" | head -1)
F="-C $CONF -c arduino_as_isp -P /dev/ttyACM0 -b 19200 -p m328p"
cd /root/backup || exit 1

echo "sketch hex : $HEX"
[ -n "$HEX" ] || exit 1

echo
echo "== signature + fuses + lock =="
$AVR $F -v 2>&1 | grep -iE "signature"
$AVR $F -U lfuse:r:-:h -U hfuse:r:-:h -U efuse:r:-:h -U lock:r:-:h 2>&1 | grep -E "^0x"

echo
echo "== read the whole 32 kB flash back =="
$AVR $F -A -U flash:r:vfy-read.hex:i 2>&1 | grep -viE "progress" | tail -2
$OBJ -I ihex -O binary --pad-to 0x8000 --gap-fill 0xff vfy-read.hex vfy-chip.bin

echo
echo "== boot section (top 2 kB) vs the stock 8 MHz bootloader =="
tail -c 2048 vfy-chip.bin > vfy-boot.bin
cmp vfy-boot.bin bl-full.bin && echo "   BOOTLOADER: intact" || echo "   BOOTLOADER: DIFFERS"

echo
echo "== application region vs the compiled sketch =="
$OBJ -I ihex -O binary "$HEX" vfy-sketch.bin
SIZE=$(wc -c < vfy-sketch.bin)
echo "   sketch binary size: $SIZE bytes"
head -c $SIZE vfy-chip.bin > vfy-head.bin
cmp vfy-head.bin vfy-sketch.bin && echo "   APP: intact (byte-for-byte match)" || echo "   APP: DIFFERS"

echo
echo "== every PORTx / DDRx the flashed code writes (io 0x02=PORTC 0x04=DDRB 0x05=PORTB 0x0A=PORTD 0x0B=DDRD) =="
$OBJD -d "$ELF" | grep -oE "out\s+0x0[0-9a-f]," | sort | uniq -c

echo
echo "== setup() as flashed =="
$OBJD -d "$ELF" | sed -n '/<setup>:/,/^$/p' | head -30

echo
echo "== the OCR1A immediates the ladder can produce =="
$OBJD -d "$ELF" | grep -oE "(ldi|ser|movi)[^;]*0x[0-9a-f]+" | sort -u | head -20
