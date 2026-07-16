# Hardware and wiring

## Supported reference target

The reference build targets an Arduino Uno-compatible 5 V ATmega328P board. It is
not a universal wiring specification. Verify voltage, current, pin capabilities,
USB isolation, enclosure, strain relief, and applicable regulations before making
or selling hardware. Disconnect USB power before changing wiring.

## Pin map

| Function | Control ID | Arduino pin | Behavior |
| --- | --- | --- | --- |
| Record control | dedicated | D9 | Emits start on press, stop on release |
| Stream control | dedicated | D8 | Emits start on press, stop on release |
| Scene buttons | B0–B3 | D10, D11, D12, D13 | Emits scene event on press |
| Potentiometers | P0–P3 | A0, A1, A2, A3 | Emits filtered 10-bit values |
| Automation buttons | G0–G3 | D3, D4, D5, D6 | Emits automation event on press |
| Stream status LED | LED 0 | D7 | High turns reference LED circuit on |
| Record status LED | LED 1 | D2 | High turns reference LED circuit on |

All devices must share ground. Every LED needs a correctly sized series resistor;
never connect an LED directly between an I/O pin and ground. Stay within the board
and microcontroller current limits. D13 includes board-specific circuitry on many
Uno variants, which should be considered when validating the B3 input.

## Choose one digital-input profile

### Internal pull-up (`uno_internal_pullup`, recommended)

Connect each switch between its input pin and ground. The firmware enables
`INPUT_PULLUP`, so released reads high and pressed reads low. No external input
resistor is normally required.

```text
Arduino input ───── switch ───── GND
       │
       └── internal pull-up to 5 V
```

### External pulldown (`uno_active_high`, legacy board)

Connect each switch between 5 V and its input, and connect that input to ground
through an external pulldown resistor appropriate for the circuit (10 kΩ is a
common starting value). Released reads low and pressed reads high.

```text
5 V ───── switch ───── Arduino input
                            │
                       pulldown resistor
                            │
                           GND
```

Never leave a digital input floating. Do not flash the active-high build onto the
pull-up circuit or vice versa: behavior will be inverted or unstable.

## Potentiometers

Use linear potentiometers suitable for the board's ADC. Connect the outer terminals
to 5 V and ground and the wiper to A0–A3. The reference firmware reports
`1023 - analogRead(pin)`, so swapping the outer terminals changes which physical
direction increases volume. Choose one orientation for all four controls and verify
the endpoints in the application before assembly.

Keep analog wiring short and routed away from noisy LED or USB power paths. The
firmware applies an integer low-pass filter, a tolerance threshold, and an emission
rate limit; wiring noise still needs to be solved electrically rather than hidden
with an excessive software threshold.

## Suggested prototype bill of materials

- One genuine or electrically compatible Arduino Uno-class board.
- Ten momentary controls: four scene, four automation, record, and stream.
- Four linear potentiometers.
- Two LEDs and two calculated series resistors.
- External pulldown resistors only for the legacy active-high profile.
- Insulated wire, USB data cable, non-conductive enclosure, and strain relief.

This list is for a bench prototype, not a manufacturing BOM. A product BOM must
identify exact approved parts, tolerances, alternates, lifecycle state, suppliers,
and compliance evidence.

## Build and flash

```powershell
python -m pip install -e ".[firmware]"
pio run -d firmware -e uno_internal_pullup
pio device list
pio run -d firmware -e uno_internal_pullup -t upload --upload-port COM3
```

Replace `COM3` with the enumerated device. For an existing active-high PCB, use
`uno_active_high` consistently for build and upload. Build artifacts appear below
`firmware/.pio/build/` and are not committed.

## Bench acceptance checklist

1. Inspect for shorts, reversed LEDs, missing resistors, and floating inputs.
2. Verify supply rails and common ground before inserting the microcontroller.
3. Confirm `READY 1 <firmware-version>` at 9600 baud.
4. Press and release every control once; ensure no duplicate bounce events.
5. Sweep every potentiometer slowly through its complete range.
6. Confirm both LEDs and their host state synchronization.
7. Disconnect/reconnect USB repeatedly and after a firmware reset.
8. Run an eight-hour powered soak while observing event rate, temperature, serial
   errors, and desktop worker counts.

Production hardware additionally needs a controlled schematic/PCB revision,
programming fixture, test points, serialized test record, enclosure evaluation,
ESD/EMC work, firmware provenance, and a compliance assessment for every market.
