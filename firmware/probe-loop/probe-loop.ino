/*
 * nuc-fan-controller - does the ITE's PWM request answer the tach at all?
 *
 * The sweep left a question open. The ITE's requested duty swings 201-259 in the divider's counts
 * on a roughly 6 s cycle that does not line up with the tach steps, which suggests the demand is
 * coming from the ITE's temperature sensors and not from the tach line. This sketch tests it
 * directly instead of reading a coincidence off a scope.
 *
 * The confound to remove is heat: if the fan speed changes, the heatsink temperature changes, and
 * the ITE's demand changes for a reason that has nothing to do with the tach. So the fan drive is
 * pinned at 90% for the whole test - constant cooling - and only the claimed RPM moves.
 *
 * The claim moves in a ping-pong ladder: 800, 2000, 4500, 2000, repeat, 40 s on each. Ping-pong
 * because a one-way ramp cannot be told apart from the machine slowly cooling or warming during
 * the test; a pattern that goes up and back down twice a cycle can be.
 *
 * What to look for, and it does not depend on the divider's ratio (a wrong ratio only rescales
 * the numbers, it does not move them in time):
 *   - duty_in tracking the ladder, low claim -> high demand, high claim -> low demand  = the ITE
 *     is regulating with the tach, and Mode B's whole premise is live.
 *   - duty_in staying in its own band, unrelated to which rung is active  = the ITE is regulating
 *     with its temperature sensors, and the tach only has to stay plausible.
 * Either answer is useful. The first says the ITE's curve is being steered by the claim; the
 * second says the board follows a demand that is already doing the thinking.
 */

#include <avr/io.h>
#include <math.h>

const uint8_t PIN_TACH = 9;       // OC1A
const uint8_t PIN_FAN = 11;       // OC2A
const uint16_t PIN_PWM_IN = A0;   // divider midpoint

const float FAN_DUTY = 90.0f;     // pinned: constant cooling while the claim moves
const uint16_t DWELL_MS = 40000;  // longer than the ITE's own loop time constant

// Ping-pong: 800 -> 2000 -> 4500 -> 2000 -> repeat. Well inside the ITE's window (it stalls
// below ~700 and stops counting above ~11 000), and 5.6x between the ends.
const uint32_t CLAIMS[] = {800, 2000, 4500, 2000};
const uint8_t N_CLAIMS = sizeof(CLAIMS) / sizeof(CLAIMS[0]);

// The bench divider is two 10k, confirmed by the builder: 512 counts is 100% duty on the Uno's 5 V
// rail. 605 (4.7k + 2.2k over 10k, the schematic's divider) is kept as the alternate.
const uint16_t ADC_AT_100PCT = 512;
const uint16_t ADC_AT_100PCT_ALT = 605;

static uint16_t icr1_for(uint32_t rpm) {
  uint32_t counts = 15UL * (F_CPU / 8UL) / rpm;   // counts per half period
  if (counts > 65536UL) counts = 65536UL;
  if (counts < 2UL) counts = 2UL;
  return (uint16_t)(counts - 1UL);
}

static float emitted_rpm(void) {
  return (float)(F_CPU / 8UL) / (2.0f * (ICR1 + 1)) * 30.0f;
}

static void set_claim(uint32_t rpm) {
  uint16_t icr = icr1_for(rpm);
  ICR1  = icr;
  OCR1A = icr;
}

static uint16_t read_adc(void) {
  long sum = 0;
  for (uint8_t i = 0; i < 16; i++) sum += analogRead(PIN_PWM_IN);   // ~1.8 ms, ~40 PWM periods
  return (uint16_t)(sum / 16);
}

static void report(void) {
  uint16_t adc = read_adc();
  Serial.print(F("claim="));       Serial.print(emitted_rpm(), 0);
  Serial.print(F(" adc="));        Serial.print(adc);
  Serial.print(F(" duty="));       Serial.print((float)adc * 100.0f / ADC_AT_100PCT, 1);
  Serial.print(F(" duty_alt="));   Serial.print((float)adc * 100.0f / ADC_AT_100PCT_ALT, 1);
  Serial.println();
}

void setup() {
  pinMode(PIN_TACH, OUTPUT);
  pinMode(PIN_FAN, OUTPUT);

  TCCR1A = _BV(COM1A0);
  TCCR1B = _BV(WGM12) | _BV(CS11);          // Timer1 CTC on ICR1, OC1A toggles, prescaler /8
  set_claim(CLAIMS[0]);

  // Timer2 fast PWM, TOP = 255, prescaler /2 -> 31.25 kHz. Fixed for the whole test.
  TCCR2A = _BV(WGM21) | _BV(WGM20) | _BV(COM2A1);
  TCCR2B = _BV(CS21);
  OCR2A = (uint8_t)lroundf((100.0f - FAN_DUTY) * 256.0f / 100.0f);

  Serial.begin(9600);
  delay(1500);
  Serial.println(F("nuc-fan-controller tach-vs-demand test (Uno 16MHz)"));
  Serial.print(F("fan pinned at "));
  Serial.print(FAN_DUTY, 0);
  Serial.println(F("% - only the claimed RPM moves"));
  Serial.print(F("ladder: 800 / 2000 / 4500 / 2000 RPM, 40 s each, repeating"));
  Serial.println();
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
    Serial.print(F("== rung "));
    Serial.print(idx + 1);
    Serial.print(F("/"));
    Serial.print(N_CLAIMS);
    Serial.println(F(":"));
    report();
  } else if (t - said >= 1000) {
    said = t;
    report();
  }
}
