#!/bin/sh
# Put the Pro Mini into a state and leave it there.
#
#   usage: set.sh "f 100" 50
#
# The sketch holds whatever it was last commanded, so the port can be released and the
# bench stays in that state while it is probed with a scope or a meter.
#
# Opening the port pulses DTR, which resets the module. The ATmegaBOOT bootloader then sits
# listening for a sync byte for about a second, and any command sent during that window is
# eaten by the bootloader instead of reaching the sketch - which is how "f 100" once arrived
# as "unknown: j". So: wait the bootloader out, send the list, wait for the sketch to come
# up, and send the list a second time. The commands are idempotent, so the repeat is free.

PORT=/dev/ttyUSB0

stty -F "$PORT" 9600 raw -echo -crtscts -hupcl || exit 1

exec 3<> "$PORT"

( timeout 12 cat <&3 ) &

sleep 3
for c in "$@"; do
    printf '%s\r\n' "$c" >&3
    sleep 0.3
done

sleep 2
for c in "$@"; do
    printf '%s\r\n' "$c" >&3
    sleep 0.3
done

printf '?\r\n' >&3
sleep 1
wait
