# PID 14520 runtime delta

Proxy `ec383668b403b8bd42761cb2f1544b891eef1f1569e364e81e8c38bbb19a6110`. Session flushed after normal exit: 16,505,924 bytes; 3305 valid rows and 45 malformed rows excluded without repair.

## Damage continuity

| Frame | Admission | Native position-state SHA-256 | Draw / restore |
|---|---|---|---|
| 13446 | Healthy native tree; 13 records, UV/winding verified | `084bae92931b844481e8cddd2a99c391209df510b89067450021d4ab08074d54` | 0 / 0 |
| 14554 | Private damage tree; 13 records, UV/winding verified | `21a5bd9b630fdc5ef39d5cfce29dcccb49d8069e26a9d82384d83f4a515a0ba1` | 0 / 0 |
| 15780 | Private damage tree; 13 records, UV/winding verified | `39a1c2d81eecb60e493432cc4fe5135583953efff0e64cb007b028b6685d3263` | 0 / 0 |
| 15783 | Private damage tree; 13 records, UV/winding verified | `997e76f349bf2cb0336014f698ff1e93ee8a3e0e9bba519f59337831ccfc417d` | 0 / 0 |

All four admissions submit 1330 private faces. The three explicit race-damage captures contain 24 rows each; every row has current owner context, matching owner, context gate 7 and certified=true. Frame 14178 is healthy; 16180 and 18446 use private native damage trees with updated VB revisions (373/45 and 407/75). VB/IB generations remain current. This supports stable replacement after damage, consistent with the user observation that reflections now persist.

The short impact blink is not localized by these artifacts. No impact failure gate was recorded: race gate logging is bounded/once-claim, and the only logged gates concern initial warmup and non-chassis context. Standard F10 API counts do not count direct native UP submissions, so they are not model-active counters. Three widely spaced captures cannot identify a transient failed admission between them. Do not label a root cause as proven.

## Newly corrected frontend families

| Family | First successful replacement frame | Result |
|---|---|---|
| Tata | 945 | Current owner, exact source records; draw/restore HRESULT 0 |
| KiaSportage | 2522 | Current owner, exact source records; draw/restore HRESULT 0 |
| Simmbugghini | 5336 | Current owner, exact source records; draw/restore HRESULT 0 |
| Mattserati | 6671 | Current owner, exact source records; draw/restore HRESULT 0 |
| IceCream | 7937 | Current owner, exact source records; draw/restore HRESULT 0 |

These are native runtime PASS events, accompanied by user confirmation that the five models display. Forester/WOOLDAND and Ufo are not evidenced as replaced in this session. Other previously working frontend families continue to log successful replacements.

## Smallest next diagnostic

For a transient blink, add bounded state-transition counters/reporting (only a changed rejection gate or damage identity), distinguishing partial same-frame owner/source warmup, mirror revision updates, material/capture readiness, and successful private submission. A new ordinary F10 after impact cannot prove the failure at impact. Keep strict identity checks; collect only one moderate and one further impact.
