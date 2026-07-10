# Reference firmware

The supported reference target is an Arduino Uno-compatible ATmega328P board.
The desktop application and firmware communicate over a newline-delimited ASCII
protocol at 9600 baud.

## Wiring modes

- `uno_active_high` preserves the original board: switches drive inputs high and
  every input needs an external pulldown resistor.
- `uno_internal_pullup` is recommended for new builds: switches connect inputs to
  ground and the MCU enables its internal pullups.

Never leave an input floating. The selected build must match the actual PCB.

## Build

```powershell
cd firmware
pio run
```

Use `pio run -e uno_internal_pullup` for the pullup wiring. Build artifacts are
created under `.pio/build/<environment>/`.

## Protocol v1

The host starts with `HELLO 1` and receives:

```text
READY 1 3.0.0 controls=B0-B3,P0-P3,G0-G3 leds=stream,record
```

It then sends `START`. The firmware emits the existing control events
(`StartRecord`, `ChangeScene B0`, `SetInputVolume P0 512`, and so on). `PING`,
`STOP`, and `LED <0|1> <0|1>` are also supported. Legacy desktop commands remain
accepted for one migration cycle.
