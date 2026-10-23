/*
 * mosfet-fan-switch - serial-commanded fan drive for the OLD board (D9 is the drive)
 *
 * Same output as fan-switch-ladder: /PWM on D9 = OC1A, fast PWM, 8 MHz / prescaler 1 /
 * TOP 7999 = 1000 Hz. Only the control changed: duty now comes from the hardware UART
 * on TX0 / RX0 instead of from a fixed ladder.
 *
 * Commands, one per line, at 9600 baud on TX0 / RX0:
 *
 *   0 .. 100   set the duty in percent
 *   ?          report what the pin is doing right now
 *   h          help
 *
 * It is quiet by design. Nothing is printed unless asked for, and every command is
 * acknowledged. That matters more than it looks: the previous sketch printed a line
 * every step, and with the Pro Mini's TX0 wired into the Uno's RX pin those bytes went
 * straight into the Uno's UART while the Uno was running ArduinoISP, which desyncs the
 * STK500 protocol and makes the programmer stop answering. A silent-by-default sketch
 * can share a bench with a programmer.
 *
 * 0 % is handled by taking D9 off Timer 1 and holding it low as plain GPIO. OCR1A = 0 in
 * fast PWM is not 0 % - the datasheet calls it "a narrow spike for each TOP+1 timer clock
 * cycle", 125 ns here - and through the Q2/Q3 booster that spike is worth 10.9 V on Q1's
 * gate for 37 us, a 31 mA kick to the fan a thousand times a second. That is the hum.
 * See set_duty().
 */

#include <Arduino.h>

const uint8_t  PWM_PIN    = 9;        // D9 = OC1A, into R1 -> Q2 -> Q3 -> Q1's gate
const uint16_t PWM_TOP    = 8000 - 1; // 8 MHz / 8000 = 1000 Hz, no prescaling

static uint8_t  duty_pct = 0;
static uint16_t duty_ocr = 0;

static void set_duty(uint8_t pct)
{
    duty_pct = pct;

    if (pct == 0)
    {
        // Take the pin off Timer 1 (COM1A1:0 = 00 -> normal port operation) and hold it low.
        // OCR1A = 0 would instead give a 125 ns spike every 1 ms, which the booster turns
        // into a 37 us, 10.9 V gate pulse. That is the 0 % hum.
        TCCR1A &= (uint8_t)~(_BV(COM1A1) | _BV(COM1A0));
        digitalWrite(PWM_PIN, LOW);
        duty_ocr = 0;
        return;
    }

    TCCR1A = _BV(COM1A1) | _BV(WGM11);
    duty_ocr = (pct >= 100) ? (PWM_TOP + 1)
                            : (uint16_t)((uint32_t)(PWM_TOP + 1) * pct / 100);
    OCR1A = duty_ocr;
}

static void report(const char *why)
{
    Serial.print("duty ");
    Serial.print(duty_pct);
    Serial.print(" %   OCR1A ");
    Serial.print(duty_ocr);
    Serial.print("/");
    Serial.print(PWM_TOP + 1);
    Serial.print("   1 kHz   ");
    Serial.println(why);
}

static void help(void)
{
    Serial.println("commands: <0-100> = duty percent, ? = report, h = this help");
}

// Parse one line. Returns 1 if it was understood.
static int handle(char *s, uint8_t n)
{
    while (n && (s[n - 1] == ' ' || s[n - 1] == '\t')) s[--n] = 0;
    if (!n) return 0;

    if (s[0] == 'h' || s[0] == 'H') { help();   return 1; }
    if (s[0] == '?')                { report("report"); return 1; }

    uint16_t v = 0;
    for (uint8_t i = 0; i < n; i++)
    {
        if (s[i] < '0' || s[i] > '9') { Serial.print("unknown: "); Serial.println(s); return 0; }
        v = v * 10 + (s[i] - '0');
    }
    if (v > 100) { Serial.println("out of range: 0..100"); return 1; }

    set_duty((uint8_t)v);
    report("set");
    return 1;
}

void setup()
{
    pinMode(PWM_PIN, OUTPUT);
    digitalWrite(PWM_PIN, LOW);                        // held low before Timer 1 is started

    noInterrupts();
    TCCR1A = _BV(WGM11);                               // fast PWM mode, COM1A1:0 = 00: OC1A
                                                       // is not connected to D9 yet
    TCCR1B = _BV(WGM13) | _BV(WGM12) | _BV(CS10);      // 16-bit TOP from ICR1, no prescaling
    ICR1   = PWM_TOP;
    OCR1A  = 0;
    interrupts();

    set_duty(0);                                       // fans off at power-up

    Serial.begin(9600);
    delay(200);
    Serial.println();
    Serial.println("mosfet-fan-switch serial drive: /PWM on D9, 1 kHz, 0 % is a true 0 %");
    help();
}

void loop()
{
    static char line[8];
    static uint8_t n = 0;

    while (Serial.available())
    {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r')
        {
            if (n) { handle(line, n); n = 0; }
        }
        else if (c >= ' ' && n < sizeof(line) - 1)
        {
            line[n++] = c;
            line[n] = 0;
        }
    }
}
