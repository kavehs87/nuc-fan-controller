/*
 * nuc-fan-controller - breadboard probe sketch (Uno edition)
 *
 * Purpose: give the scope something exact to look at while the BC547 stages are on the
 * breadboard. Both waveforms are built by hardware timers, so their frequency is a property
 * of the timer, not of the loop - if the scope says 40.000 Hz, the stage is doing what the
 * real board will do.
 *
 * Uno is 5 V / 16 MHz; the target board is 3.3 V / 8 MHz. Two constants move because of that:
 *   Timer1 tach:  ICR1 + 1 = 15 * (F_CPU/8) / RPM  -> 30 000 000 / RPM here, 15 000 000 / RPM there
 *   Timer2 fan:   16 MHz / (2 * 256) = 31.25 kHz here (prescaler /2), 8 MHz / (1 * 256) there (/1)
 * The frequency the scope should read is the same on both.
 *
 *   D9  (OC1A) -> R2 1k -> Q1 base   tach simulator, open collector: Q1 pulls the tach line low
 *   D11 (OC2A) -> R6 1k -> Q2 base   fan drive level shifter: Q2's collector is the complement
 *
 * Q1 and Q2 both invert, so what the pin does and what the collector does are opposites. That
 * is the thing worth probing.
 */

#include <avr/io.h>
#include <math.h>

const uint8_t PIN_TACH = 9;    // OC1A
const uint8_t PIN_FAN  = 11;   // OC2A (also SPI MOSI - unused here)

const float TACH_RPM  = 1200.0f;  // the ITE reads RPM = 30 * f_tach, so this is 40.000 Hz
const float FAN_DUTY  = 40.0f;    // % the fan side gets; the pin gets the complement

static uint16_t icr1_for(uint32_t rpm) {
  uint32_t counts = 15UL * (F_CPU / 8UL) / rpm;   // counts per half period
  if (counts > 65536UL) counts = 65536UL;
  if (counts < 2UL) counts = 2UL;
  return (uint16_t)(counts - 1UL);
}

void setup() {
  pinMode(PIN_TACH, OUTPUT);
  pinMode(PIN_FAN, OUTPUT);

  // Timer1: CTC on ICR1, OC1A in toggle mode -> one flip per timer cycle, exact.
  TCCR1A = _BV(COM1A0);
  TCCR1B = _BV(WGM12) | _BV(CS11);          // prescaler /8
  uint16_t icr = icr1_for((uint32_t)TACH_RPM);
  ICR1  = icr;
  OCR1A = icr;                              // match at TOP: one toggle per cycle

  // Timer2: fast PWM, TOP = 255, non-inverting OC2A, prescaler /2 -> 31.25 kHz on 16 MHz.
  TCCR2A = _BV(WGM21) | _BV(WGM20) | _BV(COM2A1);
  TCCR2B = _BV(CS21);
  uint8_t ocr2 = (uint8_t)lroundf((100.0f - FAN_DUTY) * 256.0f / 100.0f);
  OCR2A = ocr2;

  Serial.begin(9600);
  delay(1500);                              // let the CDC port settle after the reset
  Serial.println(F("nuc-fan-controller probe (Uno 16MHz)"));
  Serial.print(F("ICR1="));        Serial.println(ICR1);
  Serial.print(F("OCR2A="));       Serial.println(OCR2A);
  Serial.print(F("tach pin D9:  "));
  Serial.print((float)(F_CPU / 8UL) / (2.0f * (ICR1 + 1)), 3);
  Serial.println(F(" Hz, 50% duty"));
  Serial.print(F("tach line (Q1 collector, pull-up to 5V): "));
  Serial.print((float)(F_CPU / 8UL) / (2.0f * (ICR1 + 1)), 3);
  Serial.println(F(" Hz, INVERTED - low while D9 is high"));
  Serial.print(F("fan pin D11:  31250 Hz, high for "));
  Serial.print((float)ocr2 * 100.0f / 256.0f, 1);
  Serial.println(F("%"));
  Serial.print(F("fan side (Q2 collector): 31250 Hz, high for "));
  Serial.print(100.0f - (float)ocr2 * 100.0f / 256.0f, 1);
  Serial.println(F("%"));
}

void loop() {
  static uint32_t next = 0;
  uint32_t t = millis();
  if (t < next) return;
  next = t + 1000;
  Serial.print(F("running: tach_hz="));
  Serial.print((float)(F_CPU / 8UL) / (2.0f * (ICR1 + 1)), 3);
  Serial.print(F(" fan_hz=31250 fan_duty="));
  Serial.print(100.0f - (float)OCR2A * 100.0f / 256.0f, 1);
  Serial.println(F("%"));
}
