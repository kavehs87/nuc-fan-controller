#!/usr/bin/env python3
"""Crop the focal points out of the bench photos into docs/bench/.

The phone originals are 1280x960 or 720x1280 and carry EXIF rotation, so every crop starts from
the rotated image. Each entry is (source, output, box, caption) where box is left, top, right,
bottom in source pixels. Run with --dry to list what would be written.
"""
import os
import sys
from PIL import Image, ImageOps

SRC = "images"
OUT = "docs/bench"

JOBS = [
    ("photo_1405-07-27 20.52.28.jpeg", "01-bench-overview.jpg", (0, 360, 720, 1010),
     "The bench while the board did not exist yet: the NUC6i3SYB mainboard on the mat with two "
     "12 V fans blown at it, the Uno in a case driving the breadboard, and the four-wire harness "
     "spliced into the NUC's fan header."),

    ("photo_1405-07-27 20.52.42.jpeg", "02-fan-header.jpg", (230, 290, 940, 780),
     "The NUC fan header with the harness in it - red, black, blue and yellow. Intel publishes no "
     "pinout for this connector, so BUILD.md identifies the four wires with a meter before anything "
     "is spliced. The tach and PWM wires go to the breadboard; the header's own fan supply is left "
     "unconnected, which is J2 pin 4 on the board."),

    ("photo_1405-07-27 20.52.44.jpeg", "03-divider-on-breadboard.jpg", (560, 300, 1280, 920),
     "The duty-read chain on the breadboard, the same one the board carries: the ITE's 23 kHz PWM "
     "wire through the series resistors to the tap, the tap to A0, the bottom resistor and the caps "
     "to ground. The Uno's A0 is at the tap - put it at the far end of the chain and nothing divides."),

    ("photo_1405-07-27 20.52.36.jpeg", "04-tach-at-40hz.jpg", (150, 310, 1250, 900),
     "The scope on the tach line: a 10 ms/div window showing the fabricated square wave, with the "
     "scope's own frequency readout at 40 Hz. 40.000 Hz is what Timer1 emits for a 1200 RPM claim, "
     "since RPM = 30 x f. The hardware timer, not the loop, is what makes that exact."),

    ("photo_1405-07-27 20.52.38.jpeg", "05-bios-reads-1186.jpg", (30, 330, 1270, 960),
     "The NUC's hardware monitor reading the fabricated tach: CPU FAN 1186 RPM against a 1200 RPM "
     "claim - 0.988, and one 2 RPM display step from the 1188 read at the same setting. The ITE's own "
     "sensors are on the same screen: CPU 58 C, memory 44 C, motherboard ambient 40 C. Those are what "
     "its fan policy runs on, not the fan speed it is being told."),

    # Three more crops existed here - both ends probed at once, the parts drawer, the whole bench with
    # the scope and the buck. They showed things 01 and 04 already show, and they were dropped in
    # favour of 06-ite-fan-response.svg, which carries the measurements rather than the scenery. The
    # originals are still in images/ (gitignored).
]


def main():
    os.makedirs(OUT, exist_ok=True)
    for src, dst, box, caption in JOBS:
        p = os.path.join(SRC, src)
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        w, h = im.size
        crop = im.crop(box)
        if crop.width < 200 or crop.height < 150:
            print(f"  !! {dst}: crop {crop.size} is too small")
        out = os.path.join(OUT, dst)
        crop.save(out, "JPEG", quality=90)
        print(f"  {out:44s} from {im.size} crop {box} -> {crop.size}  {os.path.getsize(out)/1024:.0f} KB")
        print(f"      {caption[:96]}...")


if __name__ == "__main__":
    main()
