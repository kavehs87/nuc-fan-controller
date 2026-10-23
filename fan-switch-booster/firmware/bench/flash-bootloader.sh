#!/bin/sh
# Flash a compiled sketch onto the Pro Mini through its OWN bootloader, over the FTDI.
# No Uno, no ISP wires. Needs a reset pulse, so the FTDI's DTR must reach the Pro Mini's
# RST pin (100 nF between them is the standard Arduino auto-reset circuit).
#
#   usage: flash-bootloader.sh fan-switch-serial
#
# The Pro Mini 3.3V/8MHz bootloader (ATmegaBOOT) talks at 57600, which is why this is a
# different baud from everything else on this bench.

SKETCH=${1:-fan-switch-serial}

AVR=$(find ~/.arduino15 -name avrdude -type f | head -1)
CONF=$(dirname "$AVR")/../etc/avrdude.conf
PORT=/dev/ttyUSB0
BAUD=57600
PROG=arduino

fail() { echo "ABORTED: $1"; exit 1; }

[ -e "$PORT" ] || fail "$PORT is not there - the FTDI is not on the host's USB bus"

echo "== compile =="
arduino-cli compile --fqbn arduino:avr:pro:cpu=8MHzatmega328 "/root/$SKETCH" 2>&1 | tail -4 || fail "compile failed"

HEX=$(find /root/.cache -name "$SKETCH.ino.hex" | head -1)
[ -n "$HEX" ] || fail "no compiled $SKETCH.ino.hex in the arduino-cli cache"
echo "hex: $HEX"

echo
echo "== handshake with the bootloader (this pulses DTR, which resets the Pro Mini) =="
stty -F "$PORT" $BAUD raw -echo -crtscts 2>/dev/null
$AVR -C "$CONF" -c "$PROG" -P "$PORT" -b $BAUD -p m328p -v 2>&1 | tail -12

echo
echo "== write the sketch =="
$AVR -C "$CONF" -c "$PROG" -P "$PORT" -b $BAUD -p m328p \
     -U flash:w:"$HEX":i 2>&1 | grep -viE "progress" | tail -10

echo
echo "== back to 9600 for the sketch's own console =="
stty -F "$PORT" 9600 raw -echo -crtscts -hupcl 2>/dev/null
echo "done: $SKETCH"
