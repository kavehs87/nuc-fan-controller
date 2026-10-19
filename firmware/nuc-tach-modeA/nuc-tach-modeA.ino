/*
 * NUC tach simulator - Mode A (fixed RPM)
 * Board: nuc-tach-sim.kicad_sch
 * Arduino: Pro Mini 3.3 V (the 8 MHz variant). The fan header's 5 V goes to the Pro
 * Mini's RAW pin - its regulator makes the 3.3 V. Its VCC pin is the regulated rail,
 * not an input, so never feed 5 V there. Flash with a 3.3 V FTDI and the matching IDE
 * board selection, or the fuses/bootloader will not match the crystal on the board.
 *
 * The ITE IT8607E-DXS fan controller in a 6th-gen NUC counts 2 tach pulses per
 * revolution, so the RPM the BIOS shows is 30 x the frequency on the tach wire:
 *
 *     f_tach = RPM / 30        40 Hz reads 1200 RPM, 133 Hz reads 4000 RPM
 *
 * Q1 (BC547B) is open-collector: driving D9 high pulls NUC_TACH low, and the pull-up
 * that makes the high side lives in the NUC, not on this board. The simulator can only
 * ever sink current. That matters more at 3.3 V than at 5 V: a push-pull pin would
 * hold the tach line 1.7 V under the rail the ITE pulls it to, and source the pull-up
 * current into the AVR. Q1 cannot do either, and its Vceo (45 V) is indifferent to
 * whatever rail the ITE chose.
 *
 * D9 is the ATmega328P's OC1A pin, so Timer1 builds the square wave in hardware: no
 * jitter, no CPU time, and the frequency is exact rather than micros()-based. CTC with
 * ICR1 as TOP and OC1A in toggle mode gives
 *
 *     f_out = (F_CPU / 8) / (2 x (ICR1 + 1))   ->   ICR1 + 1 = 15 x (F_CPU / 8) / RPM
 *
 * so the constant is 15 000 000 / RPM on an 8 MHz board and 30 000 000 / RPM on a 16
 * MHz one. The sketch derives it from F_CPU and is correct on either. The 3.3 V Pro
 * Mini is 8 MHz because the ATmega328P's own speed grade reaches only 8 MHz at
 * 2.7-5.5 V (automotive table) or 10 MHz (industrial table): a 16 MHz crystal at 3.3 V
 * is outside the datasheet, and a crystal outside its spec is a crystal that may not
 * start when the machine is cold. Nothing in this circuit wants CPU speed - the wave is
 * hardware and loop() only blinks an LED.
 *
 * Base drive at 3.3 V: (3.3 - 0.7) / 1k = 2.6 mA. A tach pull-up moves ~1-5 mA of
 * collector current, so that is a forced beta of 5 or better - Q1 stays hard saturated,
 * Vce ~0.1-0.2 V, exactly as it was on the 5 V board. R1 stays 1 k.
 */

// What the BIOS will read. Change this one number and rebuild.
const uint32_t RPM = 1200;

void setup() {
  pinMode(13, OUTPUT);            // onboard LED: heartbeat, see loop()

  const uint32_t tick = F_CPU / 8UL;                    // Timer1 clock, prescaler /8
  uint32_t counts = 15UL * tick / RPM;                  // timer counts per half-period
  if (counts > 65536UL) counts = 65536UL;               // ICR1 is 16 bits: 458 RPM @16 MHz, 229 @8 MHz
  const uint32_t counts_min = 15UL * tick / 11000UL;    // ceiling: the ITE stops counting above ~11000 RPM
  if (counts < counts_min) counts = counts_min;

  DDRB  |= _BV(PB1);                                    // D9 = OC1A, drive it
  TCCR1A = _BV(COM1A0);                                 // OC1A toggles on compare match
  TCCR1B = _BV(WGM12) | _BV(CS11);                      // CTC on ICR1, prescaler /8
  ICR1  = (uint16_t)(counts - 1);
  OCR1A = ICR1;                                         // match at TOP: one toggle per cycle
}

void loop() {
  // 1 Hz blink. It says "the sketch is running" without a scope on TP1, and it is
  // the only thing this loop does - the tach wave is entirely hardware.
  digitalWrite(13, (millis() / 500) & 1);
}
