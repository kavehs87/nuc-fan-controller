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

const float FAN_DUTY = 40.0f;              // % the fan side gets; the pin gets the complement
const uint16_t DWELL_MS = 8000;            // long enough for the ITE to re-read and report

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

static void report(void) {
  float e = emitted_rpm();
  Serial.print(F("claim="));       Serial.print(e, 1);
  Serial.print(F(" emitted_hz=")); Serial.print(e / 30.0f, 3);
  Serial.print(F("  if_gain_0.9900="));  Serial.print(e * GAIN_A, 1);
  Serial.print(F("  if_gain_0.98845=")); Serial.print(e * GAIN_B, 1);
  Serial.println();
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
  Serial.print(F("fan pin D11: 31250 Hz, high for "));
  Serial.print((float)OCR2A * 100.0f / 256.0f, 1);
  Serial.println(F("%  |  fan side: complement"));
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
