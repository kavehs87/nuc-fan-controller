/*
 * nuc-fan-controller - ITE tach gain sweep
 *
 * Two readings from the bench: a 1200 RPM claim (40.000 Hz at the pin) read as 1188, and a
 * 1212 RPM claim read as 1198. Both fit "the ITE reads 0.9900 of what is emitted, and the
 * display steps by 2 RPM" - 1188.0 is already on a step, 1199.9 truncated to one is 1198.
 * They also fit "the ITE reads 0.98845 of what is emitted". At 1200 RPM the two hypotheses
 * are 3 RPM apart, which is inside the ITE's own step, so they cannot be told apart there.
 *
 * This sketch emits a ladder of exact claims and dwells on each long enough for the ITE to
 * report it. The hypotheses separate as the speed rises, because the gain difference is
 * proportional while the display step is not:
 *
 *   claim  emitted Hz   gain 0.9900   gain 0.98845   apart
 *     900    30.000        891.0          889.6        1.4
 *    1200    40.000       1188.0         1186.1        1.9
 *    2000    66.667       1980.0         1976.9        3.1
 *    3000   100.000       2970.0         2965.3        4.6
 *
 * Watch the NUC's fan reading (BIOS, or the hwmon fan input in the OS) while it steps and read
 * off which column it lands on. The ITE's own fan curve will react to the changing tach - that
 * is expected, it is the loop doing its job.
 *
 * The claims here are what the timer EMITS, gain not applied, because the point is to measure
 * the gain. probe-uno is the sketch that uses the measured gain.
 */

#include <avr/io.h>
#include <math.h>

const uint8_t PIN_TACH = 9;    // OC1A
const uint8_t PIN_FAN  = 11;   // OC2A (also SPI MOSI - unused here)
const uint16_t PIN_PWM_IN = A0; // the divider's midpoint, if the PWM wire is actually wired

// Measured on this NUC's fan header: 23 kHz square (Intel's 4-wire spec is 25 kHz +/-10%, so
// the ITE is inside it) at 45% duty while the sweep walks the tach claim.
//
// On the Uno the ADC's reference is its own 5 V rail. The bench divider is two 10k (confirmed by the
// builder), so the tap is half the PWM line and 100% duty lands at 0.500 * 1024 = 512 counts. The
// schematic's 4.7k + 2.2k over 10k would land at 605; report.py compares the two against the scope's
// duty reading. On the finished board the reference is 3.3 V, where the same 5 V top lands at 775
// counts for 10k/10k or 918 for the schematic's divider - and a 5.5 V top lands at 1009, 1.4% from
// full scale. The Uno cannot show that problem; the board can, which is why ADC_AT_100PCT is a bench
// measurement and not a calculation.
const uint16_t ADC_AT_100PCT = 512;

const float FAN_DUTY = 40.0f;              // starting value only, until the divider is read
const float FAN_DUTY_MIN = 30.0f;          // never stop the fan, whatever the divider reads
// The fan now follows the ITE's own demand instead of sitting at a fixed 40%. That is what the
// finished board does (Mode B), and it is what keeps the heatsink covered while the sweep runs.
// 20 s, not 8: the ITE's own loop was still moving a second after a step (adc 433 -> 360 inside
// one dwell), and a duty read taken while its controller is still chasing the new tach number is
// not a measurement of anything. The dwell has to be longer than the ITE's settling time.
const uint16_t DWELL_MS = 20000;

const uint32_t CLAIMS[] = {900, 1000, 1100, 1200, 1500, 2000, 2500, 3000};
const uint8_t N_CLAIMS = sizeof(CLAIMS) / sizeof(CLAIMS[0]);

const float GAIN_A = 0.9900f;              // 1188 shown for a 1200 claim
const float GAIN_B = 1198.0f / 1212.0f;    // 0.98845: 1198 shown for a 1212 claim

static uint16_t icr1_for(uint32_t rpm) {
  uint32_t counts = 15UL * (F_CPU / 8UL) / rpm;   // counts per half period
  if (counts > 65536UL) counts = 65536UL;
  if (counts < 2UL) counts = 2UL;
  return (uint16_t)(counts - 1UL);
}

// What the timer really produces for that ICR1, as an RPM claim.
static float emitted_rpm(void) {
  return (float)(F_CPU / 8UL) / (2.0f * (ICR1 + 1)) * 30.0f;
}

static void set_claim(uint32_t rpm) {
  uint16_t icr = icr1_for(rpm);
  ICR1  = icr;
  OCR1A = icr;                 // match at TOP: one OC1A toggle per cycle
}

static float duty_of(uint16_t adc) {
  float d = (float)adc * 100.0f / (float)ADC_AT_100PCT;
  if (d < 0.0f)   d = 0.0f;
  if (d > 100.0f) d = 100.0f;
  return d;
}

static void report(void) {
  long sum = 0;
  for (uint8_t i = 0; i < 16; i++) sum += analogRead(PIN_PWM_IN);   // ~1.8 ms, ~40 PWM periods
  uint16_t adc = (uint16_t)(sum / 16);

  // Two readings of the same count. The bench ratio is confirmed 0.500 (two 10k), so duty is the
  // 512-count reading; the 605-count one is printed alongside for the schematic's divider.
  float duty      = duty_of(adc);
  float duty_sch  = (float)adc * 100.0f / 605.0f;

  // Drive the fan with the ITE's demand, floored so it never stops.
  float drive = duty < FAN_DUTY_MIN ? FAN_DUTY_MIN : duty;
  if (drive > 100.0f) drive = 100.0f;
  OCR2A = (uint8_t)lroundf((100.0f - drive) * 256.0f / 100.0f);

  float e = emitted_rpm();
  Serial.print(F("claim="));       Serial.print(e, 1);
  Serial.print(F(" emitted_hz=")); Serial.print(e / 30.0f, 3);
  Serial.print(F(" bios_if_0.9900="));   Serial.print(e * GAIN_A, 1);
  Serial.print(F(" bios_if_0.98845="));  Serial.print(e * GAIN_B, 1);
  Serial.print(F("  adc="));       Serial.print(adc);
  Serial.print(F(" duty(6.9k/10k)="));  Serial.print(duty, 1);
  Serial.print(F(" duty(sch divider)="));   Serial.print(duty_sch, 1);
  Serial.print(F(" fan_drive="));       Serial.print(drive, 1);
  Serial.println(F("%"));
}

void setup() {
  pinMode(PIN_TACH, OUTPUT);
  pinMode(PIN_FAN, OUTPUT);

  // Timer1: CTC on ICR1, OC1A in toggle mode -> one flip per timer cycle, exact.
  TCCR1A = _BV(COM1A0);
  TCCR1B = _BV(WGM12) | _BV(CS11);          // prescaler /8
  set_claim(CLAIMS[0]);

  // Timer2: fast PWM, TOP = 255, non-inverting OC2A, prescaler /2 -> 31.25 kHz on 16 MHz.
  TCCR2A = _BV(WGM21) | _BV(WGM20) | _BV(COM2A1);
  TCCR2B = _BV(CS21);
  OCR2A = (uint8_t)lroundf((100.0f - FAN_DUTY) * 256.0f / 100.0f);

  Serial.begin(9600);
  delay(1500);                              // let the CDC port settle after the reset
  Serial.println(F("nuc-fan-controller ITE tach gain sweep (Uno 16MHz)"));
  Serial.println(F("fan follows the ITE's measured demand, floored at 30% - D11 is the complement"));
  Serial.print(F("each claim held for "));
  Serial.print(DWELL_MS / 1000);
  Serial.println(F(" s - watch the NUC's fan reading and see which column it lands on"));
  report();
}

void loop() {
  static uint8_t idx = 0;
  static uint32_t step_at = 0;
  static uint32_t said = 0;
  uint32_t t = millis();

  if (t >= step_at) {
    idx = (idx + 1) % N_CLAIMS;
    step_at = t + DWELL_MS;
    set_claim(CLAIMS[idx]);
    said = 0;
    Serial.print(F("step "));
    Serial.print(idx + 1);
    Serial.print(F("/"));
    Serial.print(N_CLAIMS);
    Serial.println(F(":"));
    report();
  } else if (t - said >= 1000) {
    said = t;
    report();                               // heartbeat so the two timelines line up
  }
}
