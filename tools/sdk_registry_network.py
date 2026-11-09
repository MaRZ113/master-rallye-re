"""Fail closed before the retail unsigned-byte selectedCar packet narrows an ID.

No wider protocol is claimed. This guards advertisement/transmission, not every
native host-start command. Offline CarID paths and -1 inactive state are intact.
"""
from __future__ import annotations
import struct
import sdk_capacity_native as native

BASE = 0x10000000
WRITER = 0x434450
WRITER_END = 0x434661
SENDER = 0x433dc0
LOGGER = 0x4d0620


def append_network_guard(source, image, extension, *, allocation_size):
    pe = native.registry.parse_pe(source)
    checks = [(WRITER, bytes.fromhex('8a4530884605')),
              (WRITER_END, bytes.fromhex('5f5e8bc35d5b83c420c20c00')),
              (SENDER, bytes.fromhex('8b44240853')),
              (0x433e4a, bytes.fromhex('5f5e5d5bc21000')),
              (LOGGER, bytes.fromhex('5155568b357c7b6f00')),
              (0x4d06d8, bytes.fromhex('5f5e5d59c3'))]
    for address, expected in checks:
        offset = native.registry.va_to_file_offset(pe, address, len(expected))
        if image[offset:offset + len(expected)] != expected:
            raise ValueError('Network guard native owner changed at ' + hex(address))
    padding = bytes((-len(extension)) % 16)
    va = BASE + len(extension) + len(padding)
    code = native.registry._CodeImage(va)

    def state_operand(prefix):
        code.emit(prefix + bytes(4))
        code.imm32.append((len(code.code) - 4, 'state'))

    code.label('packet_guard')
    code.emit(bytes.fromhex('508b453083f8ff'))  # save EAX; full owner CarID, -1 sentinel
    code.je('packet_valid')
    code.emit(b'\x3d' + struct.pack('<I', 254))
    code.ja('packet_block')
    code.label('packet_valid')
    code.emit(b'\xb8\xff\xff\xff\xff')
    state_operand(b'\xa3')
    code.emit(b'\x58')
    code.emit(bytes.fromhex('8a4530884605'))
    code.jump(WRITER + 6)
    code.label('packet_block')
    code.call('diagnostic')
    code.emit(bytes.fromhex('5833db'))  # restore temporary; zero length; original epilogue
    code.jump(WRITER_END)

    code.label('sender_guard')
    code.emit(bytes.fromhex('8b413083f8ff'))
    code.je('sender_length')
    code.emit(b'\x3d' + struct.pack('<I', 254))
    code.ja('sender_block')
    code.label('sender_length')
    code.emit(bytes.fromhex('837c240c00'))
    code.je('sender_return')
    code.emit(bytes.fromhex('8b44240853'))
    code.jump(SENDER + 5)
    code.label('sender_block')
    code.call('diagnostic')
    code.label('sender_return')
    code.emit(bytes.fromhex('33c0c21000'))

    code.label('diagnostic')
    # One native printf-style log per rejected selection. Logger is cdecl;
    # PUSHAD/PUSHFD isolate all its volatile registers and flags from owners.
    code.emit(bytes.fromhex('9c60'))
    state_operand(bytes.fromhex('3b05'))
    code.je('diagnostic_done')
    state_operand(b'\xa3')
    code.emit(b'\x50')
    code.push_literal('message')
    code.call(LOGGER)
    code.emit(bytes.fromhex('83c408'))
    code.label('diagnostic_done')
    code.emit(bytes.fromhex('619dc3'))
    code.label('message')
    code.emit(b'[Vehicle Registry] NETWORK BLOCKED: physical Vehicle ID %u cannot use the retail selectedCar protocol. '
              b'Only IDs 0..254 and inactive -1 are admitted. Offline registry is unaffected; choose a compatible vehicle.\n\0')
    # Align absolute address, not relative helper size, so only the state page
    # is writable; adjacent instructions remain RX and state remains RW/NX.
    while code.va % 4096:
        code.emit(b'\x90')
    code.label('state')
    code.emit(b'\xff\xff\xff\xff' + bytes(4092))
    blob = code.build()
    combined = extension + padding + blob
    if len(combined) > allocation_size:
        raise ValueError('Network guard code/state exceed configured allocation budget')
    entries = {name: va + offset for name, offset in code.labels.items()}
    operations = []
    for address, size, name in [(WRITER, 6, 'packet_guard'), (SENDER, 5, 'sender_guard')]:
        offset = native.registry.va_to_file_offset(pe, address, size)
        operations.append(native.i0._operation('registry_network_' + name, 'vcap2-network', offset,
                          image[offset:offset + size], native.i0._rel32(address, entries[name], 0xe9) + b'\x90' * (size - 5),
                          'Reject unencodable network IDs before byte truncation or backend send', va=address))
    result = native.i0._apply_layer(image, operations)
    return result, combined, dict(operations=operations, entries=entries, payload_va=va, payload_size=len(blob),
        writable_ranges=[{'offset': entries['state'] - BASE, 'size': 4096}],
        status='NETWORK_ADVERTISEMENT_GUARDED', admitted_ids='0..254; -1 inactive sentinel',
        rejected_ids='255 and above, and other negative values', protocol='unchanged selectedCar unsigned-byte field',
        diagnostic='native cdecl logger 0x4D0620; once per rejected selection, reset by valid selection',
        blocked_actions=['selectedCar packet construction', 'all network sender calls while cached selectedCar is unsupported',
                         'zero-length network sender calls'],
        limitations=['Native host-start UI and isolated network lifecycle require owner validation',
                     'No wider protocol, mixed-client catalog negotiation or network support for ID255+'],
        runtime_qualified=False)
