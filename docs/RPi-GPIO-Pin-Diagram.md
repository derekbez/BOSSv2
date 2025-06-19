|                | Pin      | Physical | Physical | Pin             |                |
|----------------|----------|----------|----------|-----------------|----------------|
|                | 3.3V     | (1)      | (2)      | 5V              |                |
|                | GPIO2    | (3)      | (4)      | 5V              |                |
| standby button | GPIO3    | (5)      | (6)      | GND             |                |
|                | GPIO4    | (7)      | (8)      | GPIO14          | standby light  |
|   gnd          | GND      | (9)      | (10)     | GPIO15          |                |
| mainBtn        | GPIO17   | (11)     | (12)     | GPIO18          |                |
|                | GPIO27   | (13)     | (14)     | GND             |  gnd           |
| mux1 (C/9)     | GPIO22   | (15)     | (16)     | GPIO23          | mux2 (B/10)    |
|                | 3.3V     | (17)     | (18)     | GPIO24          | mux3 (A/11)    |
| btnBlue        | GPIO10   | (19)     | (20)     | GND             |   gnd          |
| muxIn          | GPIO9    | (21)     | (22)     | GPIO25          | btnRed         |
| btnYellow      | GPIO11   | (23)     | (24)     | GPIO8           | btnGreen       |
|                | GND      | (25)     | (26)     | GPIO7           |                |
| tm1637 CLK     | GPIO0    | (27)     | (28)     | GPIO1           | tm1637 DIO     |
| ledBlue        | GPIO5    | (29)     | (30)     | GND             |                |
| ledGreen       | GPIO6    | (31)     | (32)     | GPIO12          | ledYellow      |
| ledRed         | GPIO13   | (33)     | (34)     | GND             |                |
|                | GPIO19   | (35)     | (36)     | GPIO16          |                |
|                | GPIO26   | (37)     | (38)     | GPIO20          |                |
|                | GND      | (39)     | (40)     | GPIO21          |                |

**Legend:**
- `btnRed`, `btnYellow`, `btnGreen`, `btnBlue`: User buttons
- `ledRed`, `ledYellow`, `ledGreen`, `ledBlue`: LEDs
- `mainBtn`: Main "Go" button
- `mux1`, `mux2`, `mux3`, `muxIn`: Multiplexer pins for reading toggle switches
- `tm1637 CLK`, `tm1637 DIO`: 7-segment display
- All GND and 3.3V/5V pins must be connected as per hardware requirements

**Refer to the table in docs.md for exact pin assignments and wire colours.**
