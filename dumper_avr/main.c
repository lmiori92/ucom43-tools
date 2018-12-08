/*
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Lorenzo Miori (C) 2018 [ 3M4|L: memoryS60<at>gmail.com ]

    Version History
        * 1.0 initial

*/

#include <avr/io.h>
#include <util/delay.h>
#include <avr/cpufunc.h>
#include <stdio.h>
#include <stdbool.h>
#include <stdio.h>
#include <ctype.h>
#include <avr/wdt.h>

#include "uart.h"

#define D553C_CLOCK_PIN   (PIN2)
#define D553C_RESET_PIN   (PIN3)
#define D553C_TEST_PIN    (PIN4)

#define SET_PIN(port, pin)  (port |= (1<<(pin)))
#define UNSET_PIN(port, pin)    (port &= ~(1<<(pin)))

#define D553C_ENABLE_TEST       SET_PIN(PORTD, D553C_TEST_PIN)
#define D553C_DISABLE_TEST      UNSET_PIN(PORTD, D553C_TEST_PIN)

#define D553C_MODE0_SET        SET_PIN(PORTB, PIN5)
#define D553C_MODE0_CLEAR      UNSET_PIN(PORTB, PIN5)
#define D553C_MODE1_SET        SET_PIN(PORTC, PIN0)
#define D553C_MODE1_CLEAR      UNSET_PIN(PORTC, PIN0)

#define PUTCHAR_MACRO(c)     loop_until_bit_is_set(UCSR0A, UDRE0); UDR0 = c;

/** This macro asks the watchdog to reset the CPU by software */
#define soft_reset()        \
do                          \
{                           \
    wdt_enable(WDTO_15MS);  \
    for(;;)                 \
    {                       \
    }                       \
} while(0)

/**
 * Setup the clock delay. Actually, much lower than the specification
 * but this seems not to be a problem.
 */
static void setup_clock_timer(void)
{
    TCCR1A = 0;

    TCCR1B |= (1 << WGM12) | (1 << CS10);
    // Mode = CTC, Prescaler = 1

    // max match counter
    OCR1A = 547;
}

void d553c_run_clock_num_cycles(uint16_t num_cycles);

void d553c_reset(void)
{
    // machine is reset with 16 clock cycles (4 machine cycles)
    // if reset is "HIGH" i.e. near 0V i.e. ULN2003A output active
    UNSET_PIN(PORTD, D553C_RESET_PIN);
    d553c_run_clock_num_cycles(64);
    SET_PIN(PORTD, D553C_RESET_PIN);
}

void d553c_run_clock(void)
{
    while(1)
    {
        SET_PIN(PORTD, D553C_CLOCK_PIN);
        loop_until_bit_is_set(TIFR1, OCF1A);    /* wait for timer */
        TIFR1 |= _BV(OCF1A);                     /* clear the timer */
        UNSET_PIN(PORTD, D553C_CLOCK_PIN);
        loop_until_bit_is_set(TIFR1, OCF1A);    /* wait for timer */
        TIFR1 |= _BV(OCF1A);                     /* clear the timer */
    }
}

void d553c_run_clock_num_cycles(uint16_t num_cycles)
{
    do
    {
        UNSET_PIN(PORTD, D553C_CLOCK_PIN);
        loop_until_bit_is_set(TIFR1, OCF1A);    /* wait for timer */
        TIFR1 |= _BV(OCF1A);                     /* clear the timer */
        SET_PIN(PORTD, D553C_CLOCK_PIN);
        loop_until_bit_is_set(TIFR1, OCF1A);    /* wait for timer */
        TIFR1 |= _BV(OCF1A);                     /* clear the timer */
    }
    while((uint16_t)--num_cycles);
}

// PD4 5 6 7 : higher 4 bits (PORT C 553C)
int main(void)
{
    volatile uint8_t opcode = 0x00;

    // set as output OCRA1
    //DDRB |= (1 << PIN1);
    //start_400khz_clock();
    uart_init();

    setup_clock_timer();

    // set as output CLOCK
    DDRD |= (1 << D553C_CLOCK_PIN);
    // set as output RESET
    DDRD |= (1 << D553C_RESET_PIN);
    // set as output TEST
    DDRD |= (1 << D553C_TEST_PIN);
    // set as output MODE0
    DDRB |= (1 << PIN5);
    // set as output MODE1
    DDRC |= (1 << PIN0);

    // set data inputs
    DDRD &= ~(1 << PIN5);
    DDRD &= ~(1 << PIN6);
    DDRD &= ~(1 << PIN7);

    DDRB &= ~(1 << PIN0);
    DDRB &= ~(1 << PIN1);
    DDRB &= ~(1 << PIN2);
    DDRB &= ~(1 << PIN3);
    DDRB &= ~(1 << PIN4);

    // enable pull-ups
    SET_PIN(PORTD, PIN5);
    SET_PIN(PORTD, PIN6);
    SET_PIN(PORTD, PIN7);

    SET_PIN(PORTB, PIN0);
    SET_PIN(PORTB, PIN1);
    SET_PIN(PORTB, PIN2);
    SET_PIN(PORTB, PIN3);
    SET_PIN(PORTB, PIN4);

    UNSET_PIN(PORTD, D553C_CLOCK_PIN);
    D553C_DISABLE_TEST;

    _delay_ms(10);     /* give some time to the rig to fully power up */

    d553c_reset();      /* reset the microcontroller first */

    /* setup the initial MODE pins for start dumping the ROM */
    D553C_MODE0_SET;
    D553C_MODE1_CLEAR;
    D553C_ENABLE_TEST;  /* enable test mode */

    _delay_ms(10);     /* give some time to the rig to fully power up */

    PUTCHAR_MACRO('z');

    do
    {
        do
        {
            if (bit_is_set(UCSR0A, RXC0))
            {
                /* byte received on UART */
                char c = UDR0;
                if (c == 'r')
                {
                    /* To make the operation repeatable, we can hard-reset the CPU */
                    soft_reset();   /* invoke the watchdog without feeding it */
                }
                else if (c == 's')
                {
                    UNSET_PIN(PORTD, D553C_CLOCK_PIN);
                    loop_until_bit_is_set(TIFR1, OCF1A);        /* wait for timer */
                    TIFR1 |= _BV(OCF1A);                        /* clear the timer */

                    /* Sample instruction at falling edge */
                    opcode = ((PIND >> 5) | (((PINB & 0x1F) << 3)));

                    SET_PIN(PORTD, D553C_CLOCK_PIN);
                    loop_until_bit_is_set(TIFR1, OCF1A);        /* wait for timer */
                    TIFR1 |= _BV(OCF1A);                        /* clear the timer */

                    PUTCHAR_MACRO(opcode);
                }
                else if (c == 'u')
                {
                    D553C_DISABLE_TEST;
                }
                else if (c == 't')
                {
                    D553C_ENABLE_TEST;
                }
//                else if (c == 'j')
//                {  // JUMP
//                    D553C_DISABLE_TEST;
//                    d553c_run_clock_num_cycles(4); /* the instruction takes 1 machine cycles to execute */
//                    D553C_ENABLE_TEST;
//                }
//                else if (c == 'h')
//                {  // JUMP
//                    D553C_DISABLE_TEST;
//                    d553c_run_clock_num_cycles(8); /* the instruction takes 2 machine cycles to execute */
//                    D553C_ENABLE_TEST;
//                }
            }
        } while(1);

    } while(1);
}
