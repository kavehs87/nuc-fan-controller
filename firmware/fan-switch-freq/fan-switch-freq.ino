/*
 * mosfet-fan-switch - duty AND carrier frequency from the serial port (OLD board, D9)
 *
 * Why this sketch exists: on the bench, 0 % is silent and 100 % runs smoothly, but the
 * 50 % rung of a 1 kHz carrier hums badly. That says the noise is the chopping, not the
 * fan - 1 kHz is squarely inside the audible band, and a brushless fan has its own driver
 * electronics that stutter once per carrier cycle. The usual answer is to put the carrier
 * above hearing; the 4-pin fan PWM standard uses 25 kHz for exactly that reason.
 *
 * Proving it needs the same duty at two carrier frequencies, which reflashing every time
 * makes tedious. So the carrier is a command too.
 *
 * Commands, one per line, at 9600 baud:
 *
 *   0 .. 100    set the duty in percent
 *   f <Hz>      set the carrier in HERTZ: 16 .. 25000 accepted (f 1000 = 1 kHz)
 *   ?           report what the pin is doing right now
 *   h           help
 *
 * Carriers are given in hertz rather than kilohertz because the low end matters as much as
 * the high end here. The bench showed the fan humming at every chopped duty from 60 % down
 * to 10 % on a 1 kHz carrier, silently at 0 % and at 100 %, so the carrier is the suspect -
 * and finding out whether some carrier is quiet means being able to sit well below 1 kHz as
 * well as well above it.
 *
 * What the bench found, and why the default carrier is now 100 Hz rather than 1 kHz:
 * the booster's off-going edge is slow, and the slowness is a fixed TIME, not a fixed
 * percentage. At 1 kHz the scope measured /GATE high for 652 us when it was told to be high
 * for 500 us, and /DRAIN low for 680 us - the two agree, so the fan really is conducting
 * about 170 us longer than commanded. That is 34 % of the off half-period at 1 kHz, which
 * is why 50 % came out as 68 % duty and hummed. At 25 kHz the off half is 20 us against a
 * 170 us fall, so the output is simply stuck on. At 100 Hz the same 170 us is 3 % of the
 * off half, and the scope reads 48.1 % delivered for 50 % commanded - honest control, and
 * the fan is quiet. The default is therefore 100 Hz: the board comes up quiet after any
 * power cycle or reset instead of coming up hummming at 1 kHz.
 *
 * Below 1250 Hz the timer runs through a prescaler of 8, because 8 MHz / 100 Hz is 80 000
 * counts and ICR1 is only 16 bits. Above that it runs with no prescaler. Every carrier
 * below divides 8 MHz exactly: 10 000, 5 000 and 2 000 counts at 100, 200 and 500 Hz;
 * 8 000, 4 000, 1 600, 800, 400 and 320 counts at 1, 2, 5, 10, 20 and 25 kHz.
 *
 * 0 % is still a true 0 %: OCR1A = 0 in fast PWM is not off, it is a 125 ns spike every
 * carrier cycle, and through the Q2/Q3 booster that is worth about 10.9 V on Q1's gate for
 * tens of microseconds. See set_duty(). At 25 kHz that spike would be 125 ns out of 400 ns,
 * which is why 0 % has to leave the timer entirely rather than just being given a zero.
 */

#include <Arduino.h>

const uint8_t  PWM_PIN = 9;         // D9 = OC1A, into R1 -> Q2 -> Q3 -> Q1's gate
const uint32_t F_CPU_HZ = 8000000;  // the module is 3.3 V / 8 MHz

// Carrier limits, in hertz. Below 1250 Hz the timer needs a prescaler of 8 to fit in ICR1.
const uint16_t HZ_MIN = 16;         // 8e6 / 8 / 65536 = 15.3 Hz
const uint16_t HZ_MAX = 25000;      // 8e6 / 320

static uint8_t  duty_pct  = 0;
const uint16_t  DEFAULT_HZ = 100;      // the quiet carrier, see the header
static uint16_t top       = 10000 - 1; // ICR1: 8 MHz / 8 / 100 Hz, so 10 000 counts
static uint16_t duty_ocr  = 0;
static uint16_t carrier_hz = DEFAULT_HZ;

// Put Timer 1 into fast PWM for one carrier. No range check and no printing, so setup() can
// reach the power-up default before the UART exists.
static void apply_carrier(uint16_t hz)
{
    uint8_t  cs;                       // TCCR1B CS12:CS10
    uint16_t counts;
    if (hz >= 1250)
    {
        cs     = _BV(CS10);            // no prescaler: 8e6 / hz fits in 16 bits
        counts = (uint16_t)(F_CPU_HZ / hz);
    }
    else
    {
        cs     = _BV(CS11);            // /8: 1e6 / hz fits in 16 bits
        counts = (uint16_t)(F_CPU_HZ / 8 / hz);
    }

    carrier_hz = hz;
    top        = counts - 1;

    noInterrupts();
    ICR1   = top;
    TCCR1B = _BV(WGM13) | _BV(WGM12) | cs;
    // OCR1A has to be re-derived for the new period, or the old count silently means a
    // different duty. At 0 % OC1A is off the pin anyway, so leave it at zero.
    OCR1A  = duty_pct ? ((duty_pct >= 100) ? counts
                                           : (uint16_t)((uint32_t)counts * duty_pct / 100))
                      : 0;
    interrupts();

    duty_ocr = OCR1A;
}

static void set_carrier(uint16_t hz)
{
    if (hz < HZ_MIN || hz > HZ_MAX)
    {
        Serial.print("carrier out of range: ");
        Serial.print(HZ_MIN);
        Serial.print(" .. ");
        Serial.println(HZ_MAX);
        return;
    }
    apply_carrier(hz);
}

static void set_duty(uint8_t pct)
{
    duty_pct = pct;

    if (pct == 0)
    {
        // COM1A1:0 = 00 takes OC1A off the pin; Timer 1 keeps running, connected to nothing.
        // OCR1A = 0 would instead give a narrow spike every carrier cycle - the 0 % hum.
        TCCR1A &= (uint8_t)~(_BV(COM1A1) | _BV(COM1A0));
        OCR1A = 0;                       // written, not just reported, so the report cannot
                                         // show a stale count left over from the last duty
        digitalWrite(PWM_PIN, LOW);
        duty_ocr = 0;
        return;
    }

    TCCR1A = _BV(COM1A1) | _BV(WGM11);
    duty_ocr = (pct >= 100) ? (top + 1)
                            : (uint16_t)((uint32_t)(top + 1) * pct / 100);
    OCR1A = duty_ocr;
}

static void report(const char *why)
{
    Serial.print("duty ");
    Serial.print(duty_pct);
    Serial.print(" %   OCR1A ");
    Serial.print(duty_ocr);
    Serial.print("/");
    Serial.print(top + 1);
    Serial.print("   carrier ");
    Serial.print(carrier_hz);
    Serial.print(" Hz   ");
    Serial.println(why);
}

static void help(void)
{
    Serial.println("commands: <0-100> = duty percent, f <16..25000> = carrier in Hz,");
    Serial.println("          ? = report, h = this help");
}

// Parse one line. Returns 1 if it was understood.
static int handle(char *s, uint8_t n)
{
    while (n && (s[n - 1] == ' ' || s[n - 1] == '\t')) s[--n] = 0;
    if (!n) return 0;

    if (s[0] == 'h' || s[0] == 'H') { help();   return 1; }
    if (s[0] == '?')                { report("report"); return 1; }

    // "f 25000" - carrier change, in hertz. Accepts "f25000" too.
    if (s[0] == 'f' || s[0] == 'F')
    {
        uint16_t v = 0;
        uint8_t  i = 1;
        while (i < n && (s[i] == ' ' || s[i] == '\t')) i++;
        for (; i < n; i++)
        {
            if (s[i] < '0' || s[i] > '9') { Serial.println("usage: f <16..25000> Hz"); return 0; }
            v = v * 10 + (s[i] - '0');
        }
        set_carrier(v);
        report("carrier");
        return 1;
    }

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
    TCCR1A = _BV(WGM11);                               // fast PWM, COM1A1:0 = 00: OC1A not on
                                                       // the pin yet
    interrupts();

    apply_carrier(DEFAULT_HZ);                         // TOP and prescaler for 100 Hz
    set_duty(0);                                       // fan off at power-up

    Serial.begin(9600);
    delay(200);
    Serial.println();
    Serial.println("mosfet-fan-switch serial drive: /PWM on D9, duty and carrier from serial");
    help();
}

void loop()
{
    static char line[10];
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
