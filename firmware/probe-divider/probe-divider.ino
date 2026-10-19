/*
 * nuc-fan-controller - measure the divider's own ratio with nothing but the Uno
 *
 * Every duty number this project has printed carries a "which resistor pair is actually in the
 * breadboard?" uncertainty: 605 counts is 4.7k + 2.2k over 10k at a 5.0 V top, 512 is 10k over 10k.
 * The two differ by 18 %, which is the difference between the fan following 42 % and following 50 %.
 * A multimeter settles it, and so does this sketch in about a minute with the meter still in the drawer.
 *
 * The trick is that the measurement is ratiometric. Feed the top of the divider chain from the Uno's
 * own 5 V pin and read the tap with the ADC on its DEFAULT reference. Both the excitation and the
 * ADC's full scale come from the same rail, so the rail's actual voltage cancels out completely:
 *
 *     ratio = (counts_tap - counts_gnd) / (counts_full - counts_gnd)
 *
 * Three connections, in any order, one at a time, with A0's wire never moving:
 *
 *   1. the divider's input end to GND            -> counts_gnd, the ADC's own zero
 *   2. the divider's input end to the 5 V pin    -> counts_full, the ADC's own full scale
 *   3. the divider's input end to the 5 V pin,
 *      A0 left on the tap                        -> counts_tap
 *
 * Steps 2 and 3 are the same connection: step 2 is what you get when the chain is bypassed and the
 * pin is tied straight to 5 V. Do 2 with the yellow wire moved from the chain's input end to the 5 V
 * pin directly, then 3 with it back on the chain's input end.
 *
 * Read the ratio it prints against the candidates:
 *
 *   10k over 10k              0.500   -> ADC_AT_100PCT 512 on the Uno, 852 on the 3.3 V board
 *   4.7k + 2.2k over 10k      0.592   -> 605 on the Uno, 918 on the board (the schematic's divider)
 *   10k over 15k              0.400   -> 410
 *   4.7k over 10k             0.680   -> 696
 *
 * Resistor tolerance is the limit here: 5 % parts move the ratio by up to about 2 %, which is
 * already smaller than the 18 % gap this test exists to resolve.
 *
 * What this sketch does NOT settle is the top of the ITE's PWM swing - 5.0 V or 5.5 V - because that
 * needs the duty, and the duty is what the divider is being used to find. That one is a multimeter
 * job on the PWM wire, and the ITE's own dwell levels make it arithmetic: see BUILD.md, "two dwell
 * levels and a meter".
 */

#include <avr/io.h>
#include <math.h>

const uint16_t PIN_PWM_IN = A0;

static uint16_t read_adc(void) {
  long sum = 0;
  for (uint8_t i = 0; i < 64; i++) sum += analogRead(PIN_PWM_IN);   // ~7 ms, ~160 PWM periods
  return (uint16_t)(sum / 64);
}

static void report(const char *phase, uint16_t n) {
  Serial.print(F("counts="));  Serial.print(n);
  Serial.print(F("  as_duty_of_1024=")); Serial.print(100.0f * n / 1024.0f, 2);
  Serial.print(F("  phase=")); Serial.println(phase);
}

void setup() {
  pinMode(PIN_PWM_IN, INPUT);
  analogReference(DEFAULT);            // VCC is the reference, and VCC is also the excitation
  Serial.begin(9600);
  Serial.println(F("divider ratio test: GND, then 5 V direct, then 5 V through the chain"));
}

void loop() {
  static uint16_t gnd = 0, full = 0, tap = 0;
  static uint32_t next = 0;
  uint32_t t = millis();
  if (t < next) return;
  next = t + 1000;

  uint16_t n = read_adc();

  // Which connection is it? Auto-detected, so the three steps can happen in any order.
  const char *phase = "?";
  if (n < 20)            { phase = "gnd";  gnd = n; }
  else if (n > 980)      { phase = "full"; full = n; }
  else if (full > 0)     { phase = "tap";  tap = n; }

  report(phase, n);

  if (gnd && full && tap) {
    float ratio = (float)(tap - gnd) / (float)(full - gnd);
    Serial.print(F("  ratio=")); Serial.print(ratio, 4);
    Serial.print(F("  uno_100pct=")); Serial.print((int)lroundf(ratio * 1024.0f));
    Serial.print(F("  board_100pct_at_3v3=")); Serial.print((int)lroundf(ratio * 1023.0f));
    // The candidates, closest first by construction.
    struct { const char *name; float ratio; } cand[] = {
      {"10k/10k", 0.500f}, {"4.7k+2.2k/10k", 0.592f},
      {"10k/15k", 0.400f}, {"4.7k/10k", 0.680f}, {"1k/10k", 0.909f},
    };
    int best = 0;
    for (int i = 1; i < 5; i++)
      if (fabsf(cand[i].ratio - ratio) < fabsf(cand[best].ratio - ratio)) best = i;
    Serial.print(F("  nearest pair: ")); Serial.println(cand[best].name);
  }
}
