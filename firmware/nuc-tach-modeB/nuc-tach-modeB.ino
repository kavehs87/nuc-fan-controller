/*
 * NUC fan controller follower - Mode B
 * Board: nuc-fan-controller.kicad_sch / .kicad_pcb
 * Arduino: Pro Mini 3.3 V (the 8 MHz variant), fed from the board's +3V3 rail on VCC.
 *          Flash with a 3.3 V FTDI and Board -> Arduino Pro or Pro Mini,
 *          Processor -> ATmega328 (3.3V, 8MHz). The chip's absolute maximum is
 *          VCC + 0.5 V, so a 5 V FTDI would overdrive every pin it touches.
 *
 * What this version does that Mode A did not:
 *
 *   1. It reads the duty cycle the ITE is asking for (NUC_PWM -> A0 through a divider).
 *   2. It drives a real 12 V two-pin fan at that duty (D11 -> Q2 -> Q3, 31.25 kHz).
 *   3. It reports a tach rate that matches what the fan is actually doing, so the ITE's
 *      closed loop closes instead of hunting.
 *
 * ---------------------------------------------------------------------------
 * The tach side (unchanged from Mode A)
 * ---------------------------------------------------------------------------
 * The ITE IT8607E-DXS counts 2 pulses per revolution, so the RPM the BIOS shows is
 * 30 x the frequency on the tach wire: 40 Hz reads 1200 RPM, 133 Hz reads 4000 RPM.
 *
 * Q1 (BC547B) is open-collector: pulling D9 high sinks NUC_TACH to ground, and the
 * pull-up that makes the high side lives in the NUC. The simulator can only ever sink.
 * A push-pull drive at 3.3 V would hold the tach line 1.7 V under the rail the ITE
 * pulls it to and push that current into the AVR; Q1 cannot do either.
 *
 * D9 is OC1A, so Timer1 builds the square wave in hardware. CTC on ICR1, prescaler /8,
 * OC1A in toggle mode:
 *
 *     f_out = (F_CPU / 8) / (2 x (ICR1 + 1))   ->   ICR1 + 1 = 15 x (F_CPU / 8) / RPM
 *
 * 15 000 000 / RPM on this 8 MHz board. Exact, no jitter, and it is reloaded from
 * software every time the demanded RPM moves - the wave itself never depends on the
 * loop. Base drive at 3.3 V is (3.3 - 0.7)/1k = 2.6 mA, which saturates a BC547B hard
 * against the 1-5 mA a tach pull-up moves (forced beta above 5, Vce 0.1-0.2 V).
 *
 * ---------------------------------------------------------------------------
 * Reading the ITE's demand: NUC_PWM -> A0
 * ---------------------------------------------------------------------------
 * R3 4.7k + R4 2.2k in series, R5 10k to ground: the divider puts
 *
 *     10 / (4.7 + 2.2 + 10) = 0.592
 *
 * of the PWM line on A0, so a 5 V PWM swing peaks at 2.96 V - under the 3.3 V rail with
 * 0.34 V to spare, which is what keeps a 3.3 V part legal. C10 1 uF and C11 100 nF sit
 * on that node against a source impedance of (6.9k || 10k) = 4.14 k, so tau = 4.1 ms:
 * 100 periods of a 25 kHz signal, which is exactly the averaging the fan controller
 * itself is doing. The ADC therefore reads the mean, and the mean of a 5 V square wave
 * is 5 x duty.
 *
 * Two things the divider does NOT do: it does not divide a 12 V PWM swing (measure the
 * amplitude on the PWM wire before trusting 2.96 V - a 12 V swing would put 7.1 V on
 * A0 and that is out of bounds), and it does not tell you the *frequency*, which is why
 * the fan drive runs on its own fixed 31.25 kHz instead of the ITE's clock. Intel's
 * controllers sit anywhere in 21-28 kHz; a fixed 31.25 kHz drive is above all of them,
 * and a 12 V fan does not care which kHz it is pulsed at.
 *
 * ---------------------------------------------------------------------------
 * Driving the fan: D11 -> Q2 -> Q3
 * ---------------------------------------------------------------------------
 * IRFZ44N is not a logic-level FET: its Vgs(th) is 2-4 V, so 3.3 V from a pin is not
 * enough to turn it on. Q2 (BC547B) is the level shifter - it is driven from the AVR,
 * and R8 1k pulls Q3's gate up to +12 V when Q2 is off. R7 10k holds Q2's base down
 * while the AVR's pins are inputs at reset, and R10 10k holds Q3's gate down if Q2's
 * collector ever floats.
 *
 * The gate loop, measured rather than waved at. With Q2 off the gate is fed from +12 V
 * through R8 1k + R9 120 Ω = 1.12 k, and R10 10k forms a divider with it, so the gate
 * lands at 12 × 10 / 11.12 = 10.7 V - above the 10 V at which IRFZ44N's Rds(on) is
 * specified, which is what makes its 2 mΩ real. Turn-on current is therefore
 * 12 / 1.12k = 10.7 mA, not the 12 / 120 = 100 mA a bare R9 would suggest: R8 is the
 * resistor that limits it. Turn-off is the fast half, because the gate dumps through R9
 * 120 Ω alone into Q2's saturated collector - about 89 mA, so the falling edge is under
 * a microsecond.
 *
 * Turn-on is the slow half and the number is worth knowing. Charging Ciss 1.5 nF takes
 * 1.12k × 1.5n = 1.7 µs; then the Miller plateau (Vgs ≈ 4.6 V, Qg2 ≈ 46 nC) holds the
 * gate while (12 - 4.6) / 1.12k - 4.6 / 10k = 6.1 mA walks Vds from 12 V down to 0, about
 * 7.5 µs out of the 32 µs period. At a 0.2 A fan that is ½ × 12 × 0.2 × 7.5 µs = 9 µJ per
 * turn-on, ~10 µJ a cycle, 0.3 W in the FET at 31.25 kHz: warm, not hot, for a TO-220. The
 * cost that matters is that the fan's real duty runs about 7 µs short of the commanded
 * one, which is why the RPM mapping is calibrated at the bench instead of derived here.
 *
 * Q2 inverts once: pin high -> Q2 on -> gate low -> Q3 off -> fan off. The sketch
 * inverts once more, so the fan finally sees the same duty the ITE asked for.
 *
 * D2 (1N5819) from FAN_SW to +12 V catches the fan's own inductive kick every time Q3
 * turns off. A fan is a motor winding; without D2 that edge rings into the 12 V rail,
 * and the buck is not fast enough to clean it up.
 *
 * Timer2 fast PWM on OC2A (D11), prescaler /1, TOP = 255:
 *
 *     f = 8 MHz / 256 = 31.25 kHz
 *
 * In non-inverting fast PWM the pin is high for OCR2A counts out of 256, so the pin's
 * high fraction is OCR2A/256 and the fan's is 1 - OCR2A/256.
 *
 * ---------------------------------------------------------------------------
 * Duty -> RPM: the two-point calibration
 * ---------------------------------------------------------------------------
 * A 12 V fan is not linear all the way down: below its stall duty it simply stops. So
 * the mapping is a straight line between two measured points, and the constants at the
 * top of this file are the ones to change after a bench run. The floor is not cosmetic:
 * the ITE calls a fan stalled when the tach rate falls below roughly 600-700 RPM, and a
 * fan that is commanded below its own stall duty is a fan that is not moving while the
 * sketch claims it is.
 */

// ---- the numbers a bench run is supposed to confirm -------------------------
const float FAN_RPM_FULL  = 3000.0f;   // your fan's RPM at 100 % duty (tach it, or read its datasheet)
const float FAN_RPM_MIN   = 900.0f;    // its RPM at FAN_DUTY_MIN
const float FAN_DUTY_MIN  = 20.0f;     // duty below which this fan stalls
const float TACH_RPM_FLOOR = 700.0f;   // stay above the ITE's stall detect
const float TACH_RPM_CEIL  = 10500.0f; // the ITE stops counting above ~11 000 RPM

// The ITE's tach gate is not exactly one second. Measured on a breadboard Uno into this NUC: a
// claim of 1200 RPM (40.000 Hz straight out of Timer1) read as 1188 in the BIOS - 0.9900 exactly.
// A scope says which side caused it: after applying a gain, if the tach line measures the gained
// frequency the ITE's gate is the reason and this constant belongs here; if it measures the
// ungained one, the driving board's oscillator is 1 % low and the number to fix is the one you
// measure on the finished board, not this one. Left at 1.0 until the Pro Mini is fitted.
const float ITE_READ_GAIN = 1.0f;      // emitted = wanted / gain; the Uno/NUC pair measured 0.9900

// Two-point calibration of the duty read. 918 = 2.96 V / 3.3 V x 1023.
// If a scope says the divider is off, move ADC_AT_100PCT and nothing else.
const uint16_t ADC_AT_0PCT   = 0;
const uint16_t ADC_AT_100PCT = 918;

const uint8_t  PIN_TACH   = 9;    // OC1A -> R2 -> Q1 base
const uint8_t  PIN_FAN    = 11;   // OC2A -> R6 -> Q2 base
const uint8_t  PIN_PWM_IN = A0;   // R3/R4/R5 divider, C10/C11 filtered
const uint16_t UPDATE_MS  = 100;  // control period; also the serial report period
const float    RPM_SLEW   = 400.0f;  // RPM per update: 4000 RPM/s
const float    DEMAND_TAU_S    = 15.0f;  // the pole the ITE's demand is read through
const float    DEMAND_DEADBAND = 1.5f;   // duty points below which the fan is left alone

// -----------------------------------------------------------------------------

static uint32_t tach_rpm = 0;
static uint16_t adc_seen = 0;            // the raw 16-sample mean, for the serial report

static void set_tach(uint32_t rpm) {
  const uint32_t tick = F_CPU / 8UL;                 // Timer1 clock, prescaler /8
  if (ITE_READ_GAIN != 1.0f)
    rpm = (uint32_t)((float)rpm / ITE_READ_GAIN + 0.5f);   // what the ITE should end up SHOWING
  uint32_t counts = 15UL * tick / rpm;               // timer counts per half-period
  const uint32_t counts_min = 15UL * tick / (uint32_t)TACH_RPM_CEIL;
  if (counts > 65536UL) counts = 65536UL;            // ICR1 is 16 bits: 229 RPM floor at 8 MHz
  if (counts < counts_min) counts = counts_min;      // ceiling: the ITE's own counting limit
  noInterrupts();
  ICR1  = (uint16_t)(counts - 1);
  OCR1A = ICR1;                                      // match at TOP: one toggle per cycle
  interrupts();
}

static void set_fan(float duty_pct) {
  if (duty_pct < 0.0f)   duty_pct = 0.0f;
  if (duty_pct > 100.0f) duty_pct = 100.0f;
  // Q2 inverts, so ask for the complement on the pin.
  uint16_t ocr = (uint16_t)lroundf((100.0f - duty_pct) * 256.0f / 100.0f);
  if (ocr > 255) ocr = 255;
  OCR2A = (uint8_t)ocr;
}

static float read_duty(void) {
  long sum = 0;
  for (uint8_t i = 0; i < 16; i++) sum += analogRead(PIN_PWM_IN);
  adc_seen = (uint16_t)(sum / 16);
  float adc = (float)adc_seen;
  float duty = (adc - (float)ADC_AT_0PCT) * 100.0f
             / (float)(ADC_AT_100PCT - ADC_AT_0PCT);
  if (duty < 0.0f)   duty = 0.0f;
  if (duty > 100.0f) duty = 100.0f;
  return duty;
}

static float rpm_for_duty(float duty) {
  // duty is never below FAN_DUTY_MIN (the loop clamps it), so this branch only fires if a
  // constant is set badly: claim the floor duty's own RPM, not a number nothing produces.
  if (duty <= FAN_DUTY_MIN) return FAN_RPM_MIN > TACH_RPM_FLOOR ? FAN_RPM_MIN : TACH_RPM_FLOOR;
  float f = (duty - FAN_DUTY_MIN) / (100.0f - FAN_DUTY_MIN);
  float rpm = FAN_RPM_MIN + f * (FAN_RPM_FULL - FAN_RPM_MIN);
  if (rpm < TACH_RPM_FLOOR) rpm = TACH_RPM_FLOOR;
  if (rpm > TACH_RPM_CEIL)  rpm = TACH_RPM_CEIL;
  return rpm;
}

void setup() {
  pinMode(13, OUTPUT);                    // onboard LED: heartbeat
  pinMode(PIN_TACH, OUTPUT);
  pinMode(PIN_FAN, OUTPUT);

  // Timer1: tach. CTC on ICR1, OC1A toggling, prescaler /8.
  TCCR1A = _BV(COM1A0);
  TCCR1B = _BV(WGM12) | _BV(CS11);
  OCR1A  = 0;
  ICR1   = (uint16_t)(15UL * (F_CPU / 8UL) / (uint32_t)TACH_RPM_FLOOR - 1);

  // Timer2: fan drive. Fast PWM, TOP = 0xFF, non-inverting OC2A, prescaler /1
  // -> 31.25 kHz on the 8 MHz board. Start with the fan off until the first read.
  TCCR2A = _BV(WGM21) | _BV(WGM20) | _BV(COM2A1);
  TCCR2B = _BV(CS20);
  OCR2A  = 255;                           // pin high all the time -> Q2 on -> fan off

  analogReference(DEFAULT);               // the 3.3 V rail on VCC is the reference
  Serial.begin(9600);
  Serial.println(F("nuc-fan-controller mode B"));
}

void loop() {
  static uint32_t next = 0;
  static float duty_seen = 0.0f;
  uint32_t t = millis();
  digitalWrite(13, (t / 500) & 1);        // 1 Hz heartbeat, every pass
  if (t < next) return;
  next = t + UPDATE_MS;

  float duty = read_duty();

  // The demand is filtered hard, and the measurement is why. At a constant 33 C package this ITE
  // dwells at two duty levels 58 counts apart - 11 duty points - and ramps between them in 1-3 s:
  // 535 of 716 seconds moved by more than 3 counts. A 300 ms pole hands that whole dance to the fan,
  // which then pumps at about 0.3 Hz for no thermal reason. The signal worth following is +3.7 counts
  // per C, i.e. 37 counts for a 10 C change that takes minutes to happen. tau 15 s with a 1.5 point
  // deadband drops the pump and keeps the response: the lag at 0.1 C/s is 0.6 points, inside the
  // deadband, so the fan sits at most 1.5 duty points behind the ITE's own set point.
  if (duty_seen == 0.0f) duty_seen = duty;                 // seed at boot, do not ramp up from zero
  else if (fabsf(duty - duty_seen) > DEMAND_DEADBAND)
    duty_seen += (UPDATE_MS / 1000.0f) / (DEMAND_TAU_S + (UPDATE_MS / 1000.0f)) * (duty - duty_seen);

  // Below the fan's stall duty the ITE is asking for less than the fan can give. Command
  // the stall duty and report the RPM that duty really produces: a fan held at its stall
  // duty idles, whereas commanding 0 % stops the fan while the tach still claims 700 RPM -
  // the ITE would never learn the difference, and the CPU would get nothing.
  float applied_duty = duty_seen < FAN_DUTY_MIN ? FAN_DUTY_MIN : duty_seen;
  set_fan(applied_duty);

  // Slew the reported RPM instead of jumping to it: the ITE integrates the tach over
  // about a second, and a step in the reported rate reads to it as a fan that surged.
  float want = rpm_for_duty(applied_duty);
  int32_t step = (int32_t)want - (int32_t)tach_rpm;
  const int32_t slew = (int32_t)RPM_SLEW;
  if (step >  slew) step =  slew;
  if (step < -slew) step = -slew;
  tach_rpm = (uint32_t)((int32_t)tach_rpm + step);
  if (tach_rpm < (uint32_t)TACH_RPM_FLOOR) tach_rpm = (uint32_t)TACH_RPM_FLOOR;
  set_tach(tach_rpm);

  Serial.print(F("duty_in="));   Serial.print(duty, 1);
  Serial.print(F(" duty_fan=")); Serial.print(applied_duty, 1);
  Serial.print(F(" rpm="));      Serial.print(tach_rpm);
  Serial.print(F(" hz="));       Serial.print((float)tach_rpm / 30.0f, 2);
  Serial.print(F(" adc="));      Serial.println(adc_seen);
}
