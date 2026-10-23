# Bench scripts

These run **inside the container the FTDI is plugged into** — CT 130 on `10.0.5.1`, where
`/dev/ttyUSB0` is the Pro Mini. They are kept here so the bench can be rebuilt from the repo; the
copies that actually produced the measurements in the README live in that container's `/root`.

```sh
scp firmware/bench/*.sh root@10.0.5.1:/tmp/
ssh root@10.0.5.1
pct push 130 /tmp/set.sh /root/set.sh
pct exec 130 -- sh /root/set.sh "f 100" 50
```

| script | what it does |
|---|---|
| `flash-bootloader.sh <sketch>` | compile and flash through the Pro Mini's own bootloader — `-c arduino -b 57600`, with DTR to J5‑1 supplying the reset pulse. No Uno, no ISP wires. |
| `set.sh <cmd> ...` | put the sketch into a state and leave it there, so the port can be released while the board is probed with a scope or a meter. |
| `seq.sh <seconds> <cmd> ...` | drive a timed sequence, print everything the sketch said, and return duty to 0 % at the end. This is how the duty range gets listened to. |
| `verify-flash.sh <sketch>` | read all 32 kB back over ISP and compare the app and boot sections against the compiled hex, then disassemble what is really in the chip. |

Two facts these scripts exist because of:

- **The bootloader eats the first second of commands.** Opening the port pulses DTR, the module
  resets, and `ATmegaBOOT` then waits about a second for a sync byte. Anything sent in that window
  is consumed by the bootloader instead of reaching the sketch. `set.sh` sleeps 3 s and sends the
  command list twice for exactly that reason.
- **A long‑lived console daemon is not trustworthy on this bench.** An earlier version kept the port
  open in a background reader so commands could be dropped into a queue file. That daemon expired
  silently, left commands unread, and nothing reported it — the sketch simply never moved. Both
  `set.sh` and `seq.sh` are self‑contained instead: open, drive, print, release.

The example worth keeping handy, the sweep that confirmed 100 Hz is quiet across the whole range:

```sh
sh seq.sh 10 "f 100" 0 10 20 30 40 50 60 70 80 90 100
```
