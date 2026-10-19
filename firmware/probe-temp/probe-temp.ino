/*
 * nuc-fan-controller - does the ITE's demand follow temperature?
 *
 * The ladder test settled the tach half: 800 / 2000 / 4500 RPM claims moved the ITE's requested
 * duty by 2.5 counts out of 233 (-1.1%), while the same claim swung 195-260 on its own with a 6 s
 * autocorrelation peak. So the demand is not coming from the reported speed. This sketch goes the
 * other way: hold the claim absolutely still and move the temperature instead, by loading the
 * NUC's cores.
 *
 * Everything that is not temperature is pinned:
 *   - the tach claim is one exact number, 1500 RPM (50.000 Hz), for the whole run
 *   - the fan drive is fixed at 90%, so the board is not changing the cooling either
 * Whatever the divider then reads is the ITE reacting to its own sensors or to nothing at all.
 *
 * The NUC side runs a load profile with a shape: idle, load, idle again. A duty change that rises
 * with the load and falls again when the load is removed is a response. A duty change that happens
 * once and stays is drift, and a duty that never moves is a demand the temperature does not drive
 * either.
 */

#include <avr/io.h>
#include <math.h>

const uint8_t PIN_TACH = 9;       // OC1A
const uint8_t PIN_FAN = 11;       // OC2A
const uint16_t PIN_PWM_IN = A0;   // divider midpoint

const uint32_t CLAIM_RPM = 1500;  // 30 000 000 / 1500 = 20 000 counts -> ICR1 19999 -> 50.000 Hz
const float FAN_DUTY = 90.0f;     // pinned

// Whichever resistor pair was built: 605 counts is 6.9k over 10k at a 5.0 V top, 512 is 10k/10k.
const uint16_t ADC_AT_100PCT = 605;
const uint16_t ADC_AT_100PCT_ALT = 512;

static uint16_t read_adc(void) {
  long sum = 0;
  for (uint8_t i = 0; i < 16; i++) sum += analogRead(PIN_PWM_IN);   // ~1.8 ms, ~40 PWM periods
  return (uint16_t)(sum / 16);
}

void setup() {
  pinMode(PIN_TACH, OUTPUT);
  pinMode(PIN_FAN, OUTPUT);

  TCCR1A = _BV(COM1A0);
  TCCR1B = _BV(WGM12) | _BV(CS11);          // Timer1 CTC on ICR1, OC1A toggles, prescaler /8
  uint32_t counts = 15UL * (F_CPU / 8UL) / CLAIM_RPM;
  ICR1  = (uint16_t)(counts - 1UL);
  OCR1A = ICR1;

  TCCR2A = _BV(WGM21) | _BV(WGM20) | _BV(COM2A1);
  TCCR2B = _BV(CS21);                       // Timer2 fast PWM, TOP 255, prescaler /2 -> 31.25 kHz
  OCR2A = (uint8_t)lroundf((100.0f - FAN_DUTY) * 256.0f / 100.0f);

  Serial.begin(9600);
  delay(1500);
  Serial.print(F("nuc-fan-controller temperature test (Uno 16MHz). claim="));
  Serial.print(CLAIM_RPM);
  Serial.print(F(" RPM ("));
  Serial.print((float)(F_CPU / 8UL) / (2.0f * (ICR1 + 1)), 3);
  Serial.print(F(" Hz), fan pinned at "));
  Serial.print(FAN_DUTY, 0);
  Serial.println(F("%"));
}

void loop() {
  static uint32_t said = 0;
  uint32_t t = millis();
  if (t - said < 1000) return;
  said = t;
  uint16_t adc = read_adc();
  Serial.print(F("claim="));       Serial.print(CLAIM_RPM);
  Serial.print(F(" adc="));        Serial.print(adc);
  Serial.print(F(" duty="));       Serial.print((float)adc * 100.0f / ADC_AT_100PCT, 1);
  Serial.print(F(" duty_alt="));   Serial.print((float)adc * 100.0f / ADC_AT_100PCT_ALT, 1);
  Serial.println();
}
