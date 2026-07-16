# Serial protocol

## Transport

Protocol v1 uses 9600 baud, 8 data bits, no parity, one stop bit, and newline
(`LF`, byte `0x0A`) delimited ASCII messages. `CRLF` is accepted. The reference
firmware input buffer accepts at most 95 message bytes before the newline; hosts
should use substantially shorter commands. The desktop parser bounds device lines
and decodes invalid UTF-8 defensively.

Opening an Arduino Uno serial port commonly resets the board. The host waits for
the reset, negotiates the protocol, and only reports a successful connection after
`START` is acknowledged.

## Session state

```text
Host                              Device
  │ -------- HELLO 1 ------------> │
  │ <--- READY 1 3.0.0 ... ------- │  negotiated, stopped
  │ -------- START ---------------> │
  │ <------- ACK START ------------ │  active; events enabled
  │ -------- PING ----------------> │
  │ <------ PONG 123456 ----------- │
  │ -------- STOP ----------------> │
  │ <------- ACK STOP ------------- │  stopped
```

Commands and replies are case-sensitive unless explicitly marked as legacy. One
message occupies one line and contains no embedded newline or NUL. The device does
not emit control events before `START` or after `STOP`.

## Negotiation

The host sends:

```text
HELLO 1
```

The reference firmware responds:

```text
READY 1 3.0.0 controls=B0-B3,P0-P3,G0-G3 leds=stream,record
```

`READY` fields are:

1. literal `READY`;
2. negotiated integer protocol version;
3. firmware version without spaces;
4. zero or more `key=value` capability tokens without spaces.

Peers must ignore unknown capability keys. Firmware that makes an incompatible
syntax change must negotiate a new protocol version instead of presenting it as
v1. A firmware version and a protocol version are independent: firmware can change
without breaking protocol compatibility.

## Host-to-device commands

| Command | Success response | Meaning |
| --- | --- | --- |
| `HELLO 1` | `READY ...` | Negotiate protocol and capabilities |
| `START` | `ACK START` | Enable control event emission |
| `STOP` | `ACK STOP` | Disable control event emission |
| `PING` | `PONG <milliseconds>` | Liveness check; counter is device uptime and may wrap |
| `LED 0 0` / `LED 0 1` | `ACK LED` | Set stream LED off/on |
| `LED 1 0` / `LED 1 1` | `ACK LED` | Set record LED off/on |

Invalid commands return a bounded diagnostic such as:

```text
NACK unknown_command
NACK invalid_led_command
NACK line_too_long
```

`START`, `STOP`, and absolute LED state changes are idempotent. V1 has no sequence
identifier and no acknowledgement for device-originated control events. Consumers
must therefore tolerate duplicate state-setting requests after a reconnect; future
protocols should add sequence IDs if guaranteed event delivery is required.

## Device-to-host events

| Event | Argument | Meaning |
| --- | --- | --- |
| `StartRecord` | none | Dedicated record control became pressed |
| `StopRecord` | none | Dedicated record control became released |
| `StartStream` | none | Dedicated stream control became pressed |
| `StopStream` | none | Dedicated stream control became released |
| `ChangeScene B0` … `B3` | control ID | Scene button press |
| `SetInputVolume P0 0` … `P3 1023` | control ID, ADC value | Filtered potentiometer movement |
| `ExecuteScript G0` … `G3` | control ID | Automation button press |

Control identifiers are stable hardware identities, not OBS names. Mapping them to
scenes, inputs, or automation names is a host responsibility. Hosts clamp volume
values to the advertised/reference `0..1023` range before conversion.

## Legacy migration

The desktop can attempt one legacy handshake when `READY` is unavailable. The
reference firmware temporarily accepts lowercase `start`/`stop` and legacy LED
commands (`StreamOnLed`, `StreamOffLed`, `RecordOnLed`, `RecordOffLed`). This path
exists only to migrate earlier devices and should not be used by new firmware.
Removal must be announced in release notes and gated by a compatibility policy.

## Robustness requirements

- Never interpolate a received line into Python, a shell, a path, or a log without
  validation/redaction.
- Discard NULs, oversized lines, malformed integers, unsupported identifiers, and
  partial messages without crashing the reader.
- Treat disconnect as a state transition; reconnect must negotiate a fresh session.
- Keep the parser deterministic and covered by malformed-input tests.
- A custom device should fuzz its encoder/decoder and run an eight-hour reconnect
  and event soak test before being declared compatible.
