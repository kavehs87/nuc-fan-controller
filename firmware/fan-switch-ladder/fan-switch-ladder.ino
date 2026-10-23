/*
 * mosfet-fan-switch - duty ladder for the OLD board (Pro Mini in sockets, D9 is the drive)
 *
 * One output only: /PWM on D9 = OC1A, 100 Hz, the carrier the bench measured quiet.
 * Nothing is done with D10 or A0 - this board has no tach path and no /DEMAND tap, and D10
 * is the pin the Uno-as-ISP programmer sits next to when you flash over J6.
 *
 * The sequence, then it repeats:
 *
 *    0 %     10 s   everything truly off, pin held low as GPIO. What your meter reads with
 *                    nothing running.
 *   100 %    60 s   full drive.
 *    90 %    60 s
 *    80 %    60 s
 *    70 %    60 s
 *    60 %    60 s
 *    50 %    60 s   the ladder stops here. It never goes below 50 %.
 *
 * STEP_PCT is the size of each step: 10 gives 100, 90, 80, 70, 60, 50. Change it to 25 and
 * you get 100, 75, 50. STEP_MS is how long each step is held.
 *
 * Timer 1 runs as fast PWM with TOP from ICR1: 8 MHz / prescaler 8 / 10 000 = 100 Hz exactly.
 * The prescaler of 8 is what lets a 100 Hz carrier fit in a 16-bit ICR1 at all, since 8 MHz
 * / 100 Hz is 80 000 counts. It is 100 Hz rather than 1 kHz because the booster's off-going
 * edge costs a fixed ~170 us whatever the carrier is: at 1 kHz that ate 34 % of the off
 * half-period, so 50 % commanded came out as 68 % delivered and the fan hummed; at 100 Hz it
 * is 3 %, the scope read 48.1 % delivered for 50 % commanded, and the noise was gone. See the
 * README section "Why the carrier is 100 Hz".
 * In non-inverting fast PWM OC1A is cleared on compare match and set when the counter wraps,
 * so the duty is OCR1A / 10000 - but only for 1 <= OCR1A. The two extremes are special cases
 * the datasheet calls out:
 *
 *   OCR1A = 10000 (above TOP)  the compare never fires, OC1A is never cleared: a true 100 %.
 *   OCR1A = 0     (BOTTOM)     NOT 0 %. It is a 125 ns spike high once every 10 ms.
 *
 * The 0 % spike is why this version stops driving D9 through Timer 1 during the stopped
 * window and holds it low as plain GPIO instead. Through the Q2/Q3 booster that spike is
 * worth 10.9 V on Q1's gate for tens of microseconds, i.e. the fan hums while "off". See
 * set_duty() below for the numbers.
 *
 * The Serial lines only matter with a 3.3 V FTDI on J5. With nothing plugged in they are
 * harmless: the bytes sit in the UART's buffer and get dropped.
 */

#include <Arduino.h>

const uint8_t  PWM_PIN    = 9;        // D9 = OC1A, into R1 -> Q2 -> Q3 -> Q1's gate
const uint16_t PWM_TOP    = 10000 - 1; // 8 MHz / prescaler 8 / 10 000 = 100 Hz

const uint8_t  FULL_PCT   = 100;      // first step after the stopped window
const uint8_t  FLOOR_PCT  = 50;       // the ladder stops here
const uint8_t  STEP_PCT   = 10;       // 100, 90, 80, 70, 60, 50
const unsigned long ZERO_MS = 10000;  // the 10 s stopped window
const unsigned long STEP_MS = 60000;  // one minute per duty step

static uint16_t set_duty(uint8_t pct)
{
    uint16_t ocr;

    if (pct == 0)
    {
        // OCR1A = 0 in fast PWM is NOT 0 %. The datasheet is explicit: "if the OCR1x is set
        // equal to BOTTOM (0x0000) the output will be a narrow spike for each TOP+1 timer
        // clock cycle" - here 125 ns high, once every 10 ms. That spike is not harmless on
        // this board: it lifts /LGATE to 3.0 V, pulls /BOOT from 12 V to 8 V, turns Q3 on,
        // and lands 10.9 V on Q1's gate for tens of microseconds. The fan gets a kick of tens
        // of mA a hundred times a second - not enough to spin it, enough to make it hum,
        // which is what the bench heard at 0 %.
        // So take the pin off Timer 1 entirely (COM1A1:0 = 00 -> normal port operation)
        // and hold it low as plain GPIO.
        TCCR1A &= (uint8_t)~(_BV(COM1A1) | _BV(COM1A0));
        digitalWrite(PWM_PIN, LOW);
        return 0;
    }

    TCCR1A = _BV(COM1A1) | _BV(WGM11);                 // back to OC1A driven by Timer 1
    if (pct >= 100)              ocr = PWM_TOP + 1;    // above TOP -> never cleared
    else                         ocr = (uint32_t)(PWM_TOP + 1) * pct / 100;
    OCR1A = ocr;
    return ocr;
}

// The next rung of the ladder. Never steps past FLOOR_PCT, and always lands on it exactly,
// even when FULL_PCT - FLOOR_PCT is not a whole multiple of STEP_PCT.
static uint8_t next_duty(uint8_t pct)
{
    if (pct <= FLOOR_PCT || pct - FLOOR_PCT <= STEP_PCT) return FLOOR_PCT;
    return pct - STEP_PCT;
}

void setup()
{
    pinMode(PWM_PIN, OUTPUT);
    digitalWrite(PWM_PIN, LOW);                        // held low before Timer 1 is started

    noInterrupts();
    TCCR1A = _BV(WGM11);                               // fast PWM mode, but COM1A1:0 = 00, so
                                                       // OC1A is not connected to D9 yet
    TCCR1B = _BV(WGM13) | _BV(WGM12) | _BV(CS11);      // 16-bit TOP from ICR1, prescaler /8
    ICR1   = PWM_TOP;
    OCR1A  = 0;                                        // start stopped
    interrupts();

    Serial.begin(9600);
}

void loop()
{
    set_duty(0);
    Serial.println("duty 0 %   OCR1A 0   (10 s, nothing running)");
    delay(ZERO_MS);

    for (uint8_t pct = FULL_PCT; ; pct = next_duty(pct))
    {
        uint16_t ocr = set_duty(pct);
        Serial.print("duty ");
        Serial.print(pct);
        Serial.print(" %   OCR1A ");
        Serial.print(ocr);
        Serial.print("/");
        Serial.print(PWM_TOP + 1);
        Serial.println("   (60 s)");
        delay(STEP_MS);

        if (pct == FLOOR_PCT) break;                   // bottom rung reached: restart
    }
}
