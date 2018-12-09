# Known ROM codes
This is a list that tries to maps some of the hundreds of mask ROMs that have been written by engineers and used in the several different devices.

| ROM  | DEVICE  | DESCRIPTION  | FEATURES  | DUMP STATE |
|---|---|---|---|---|
| D553C-024  | ??  | Random Part on eBay | Outputs a signal which is about 1.4kHz about 1:10 duty at 400kHz Clock ? | Yes |
| D553C-200  | Sony TA-AX44  | Audio Power Amplifier  | Audio Signal Processing ( Digital channel/volume/eq selection ) / Memory IC / Remote Controller / VFD display | Yes |
|   |   |   |   |   |
|   |   |   |   |   |

# D553C-024

This IC has a totally unknown origin. A quick look into the ROM code reveals that at least one 7-Segment is driven due to the fact that there is sort of "lookup" table with jumps and so (addr. 0x0140).
At boot, it toggles a PIN high (like a Chip Select) and for the entire duration of the HIGH level on this pin, it toggles several pins (16). There is no obvious pattern, but a strobe signal seems to be there as well.

# D553C-200

Sony TA-AX 44 Amplifier. Interesting for understanding logic of the Remote Control protocol which is not documented anywhere.
