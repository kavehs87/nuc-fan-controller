/*
 * mosfet-fan-switch - bench debug program for the Pro Mini that sits in the board's sockets
 *
 * Flashed over J6 with an Uno as ISP (five wires: Uno 10->J6-1 MISO, 11->J6-3 SCK, 12->J6-4 MOSI,
 * 9->J6-5 RST, GND->J6-6, and nothing to J6-2). The module powers itself from /P12V while it is
 * programmed, so the board needs its 12 V brick on J1 for the flash to work at all.
 *
 * What this program does, and why each line is here:
 *
 *   /PWM      D9  OC1A   1 kHz fan drive.  Duty is the control law: /DEMAND counts / 775.
 *   /TACH_PWM D10 OC1B   100 Hz tach carrier.  The ITE counts two pulses per revolution, so
 *                        100 Hz is a 3 000 RPM claim.  Running this at the fan drive's 1 kHz
 *                        would claim 30 000 RPM, which is the mistake this file exists to avoid.
 *   /DEMAND   A0         the NUC's PWM request, halved by R7/R8 (10k/10k) and smoothed by C5/C6.
 *                        2.50 V is a full request = 775 counts on the 3.3 V rail.
 *
 * Both outputs come out of Timer 1, which is what the pin map forces: D9 and D10 are OC1A and
 * OC1B, and one timer has one period. So OC1A runs as hardware PWM at 1 kHz, and OC1B is toggled
 * in software every fifth overflow - 1 kHz / 2 x 5 = 100 Hz, exactly, from the same counter.
 *
 * Two modes, picked by DEBUG_LADDER below:
 *
 *   DEBUG_LADDER 1  Ignore A0.  Sweep the fan duty 0, 10, ... 100 % at 1.5 s per step.  Use this
 *                   first, with the NUC unplugged: the fan output average at J3 is duty x 12 V, so
 *                   a multimeter on the fan connector reads the whole gate-booster chain working,
 *                   and you hear the fans step.  Nothing here depends on the divider being right.
 *   DEBUG_LADDER 0  The real control law: duty = min(1.0, counts / 775), read once per 100 ms.
 *                   C5 + C6 make the tap already average, so one analogRead is enough.
 *
 * With REPORT_SERIAL 1 the same numbers go out on TX0 (pad 1) at 57600 - plug the 3.3 V FTDI into
 * J5 with its black wire over BLK to read them. With the FTDI unplugged the serial writes are
 * harmless: they just sit in the UART's buffer and get dropped.
 */

#include <avr/io.h>
#include <Arduino.h>

// ---------------------------------------------------------------------- board map
const uint8_t PIN_PWM    = 9;    // /PWM      - OC1A, into R1 -> Q2 -> Q3 -> Q1's gate
const uint8_t PIN_TACH   = 10;   // /TACH_PWM - OC1B, into R9 -> Q4 -> the NUC's tach input
const uint8_t PIN_DEMAND = A0;   // /DEMAND   - R7/R8 tap, 0 .. 2.50 V

// ---------------------------------------------------------------------- timing
const uint16_t FAN_HZ  = 1000;   // the driver's switching frequency
const uint16_t TACH_HZ = 100;    // 100 Hz -> 3 000 RPM on an ITE that counts 2 pulses/rev

// 8 MHz / prescaler 1 / (ICR1 + 1) = 1000 Hz exactly.
const uint16_t TIMER1_TOP = (F_CPU / FAN_HZ) - 1;      // 7999
const uint16_t FAN_PERIOD = F_CPU / FAN_HZ;            // 8000 timer counts per fan cycle
// OC1B is flipped every TOGGLES overflows: f = FAN_HZ / (2 * TOGGLES).
const uint8_t  TOGGLES = FAN_HZ / (2 * TACH_HZ);       // 5 -> 100.000 Hz

// ---------------------------------------------------------------------- control law
const uint16_t FULL_COUNTS = 775;  // 2.50 V on a 3.3 V reference: 2.50 / 3.30 * 1023

// ---------------------------------------------------------------------- debug switches
#define DEBUG_LADDER   1   // 1 = sweep the duty, ignore A0.  0 = follow /DEMAND.
#define REPORT_SERIAL  1   // 1 = print on TX0 at 57600 (needs the FTDI on J5 to see it)
#define LADDER_STEP_MS 1500
#define READ_MS        100   // /DEMAND is already filtered by C5 + C6
#define PRINT_MS       250

// ---------------------------------------------------------------------- state
static volatile uint8_t  tach_div = 0;
static uint16_t          fan_counts = 0;      // what OC1A is holding right now
static uint16_t          demand_counts = 0;
static uint8_t           ladder_step = 0;

// Timer 1: fast PWM, TOP = ICR1, OC1A non-inverting, OC1B left to software control.
static void timer1_setup(void)
{
    TCCR1A = 0;
    TCCR1B = 0;
    ICR1   = TIMER1_TOP;
    OCR1A  = 0;
    OCR1B  = 0;                      // not used: COM1B stays 0, so PB6 is plain GPIO
    TCCR1A |= _BV(WGM11) | _BV(COM1A1);            // fast PWM, TOP from ICR1, OC1A active high
    TCCR1B |= _BV(WGM12) | _BV(WGM13) | _BV(CS10); // same mode, prescaler 1 (no division)

    pinMode(PIN_TACH, OUTPUT);
    digitalWrite(PIN_TACH, LOW);

    TIMSK1 |= _BV(TOIE1);            // one interrupt per fan cycle: 1 kHz
}

// 1 kHz.  Five of these make one 10 ms tach period.
ISR(TIMER1_OVF_vect)
{
    if (++tach_div >= TOGGLES)
    {
        tach_div = 0;
        PORTB ^= _BV(PB6);           // PB6 is Arduino 10, /TACH_PWM
    }
}

static void fan_duty(float duty)
{
    if (duty <= 0.0f)      fan_counts = 0;
    else if (duty >= 1.0f) fan_counts = FAN_PERIOD;   // no compare match -> OC1A stays high
    else                   fan_counts = (uint16_t)(duty * FAN_PERIOD);
    OCR1A = fan_counts;
}

static float read_demand(void)
{
    uint32_t sum = 0;
    for (uint8_t i = 0; i < 4; i++) sum += analogRead(PIN_DEMAND);
    demand_counts = (uint16_t)(sum / 4);
    return (float)demand_counts / (float)FULL_COUNTS;
}

static void report(float duty)
{
#if REPORT_SERIAL
    static uint32_t last = 0;
    if (millis() - last < PRINT_MS) return;
    last = millis();
    Serial.print("demand ");
    Serial.print(demand_counts);
    Serial.print(" counts  ");
    Serial.print((uint32_t)((uint32_t)demand_counts * 3300UL / 1023UL));
    Serial.print(" mV   duty ");
    Serial.print((int)(duty * 100.0f + 0.5f));
    Serial.print("%  OCR1A ");
    Serial.print(fan_counts);
    Serial.print("/");
    Serial.print(FAN_PERIOD);
    Serial.print("  tach ");
    Serial.print(TACH_HZ);
    Serial.println(" Hz -> 3000 RPM");
#endif
}

void setup(void)
{
    analogReference(DEFAULT);        // the module's own 3.3 V rail, which is what /DEMAND rides on
    timer1_setup();
#if REPORT_SERIAL
    Serial.begin(57600);
    delay(200);                      // let the FTDI settle before the header line
    Serial.println();
    Serial.println("mosfet-fan-switch debug: /PWM D9 1 kHz, /TACH_PWM D10 100 Hz, /DEMAND A0");
    Serial.println(DEBUG_LADDER ? "mode: duty ladder (A0 ignored)" : "mode: follow /DEMAND");
#endif
}

void loop(void)
{
    static uint32_t last_read = 0, last_step = 0;

    if (millis() - last_read < READ_MS) return;
    last_read = millis();

#if DEBUG_LADDER
    if (millis() - last_step >= LADDER_STEP_MS)
    {
        last_step = millis();
        ladder_step = (uint8_t)((ladder_step + 1) % 11);
    }
    float duty = (float)ladder_step / 10.0f;
    fan_duty(duty);
    analogRead(PIN_DEMAND);          // keep the reading fresh so the line still reports it
    report(duty);
#else
    fan_duty(read_demand());
    report((float)fan_counts / (float)FAN_PERIOD);
#endif
}
