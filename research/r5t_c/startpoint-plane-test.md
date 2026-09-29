# France1 startpoint-box candidate plane test

The values below apply the two stated plane conventions to each of the 11 unit-normal-like float4 windows in the one-point tag100 differential and the eight corners of the first-pool candidate box. The source-to-DX transform and node association remain inferences. Residuals are absolute values. No plane candidate passes the 1e-3 tolerance.

| tag100 offset | alignment mod 16 | |n| baseline | |n| modified | min |n·x+d| | min |n·x-d| |
|---:|---:|---:|---:|---:|---:|
| `0x86B070` | 0 | 1.000000026 | 1.000000038 | 24.889590 | 417.031679 |
| `0x86B150` | 0 | 0.999999935 | 0.999999986 | 16.203604 | 709.053580 |
| `0x86B1C0` | 0 | 0.999999979 | 0.999999938 | 38.641358 | 50.202269 |
| `0x86D5A0` | 0 | 1.000000019 | 1.000000021 | 22.327852 | 291.155520 |
| `0x8702B0` | 0 | 0.999999928 | 1.000000010 | 29.924952 | 524.533595 |
| `0x8745A0` | 0 | 1.000000042 | 0.999999942 | 30.595814 | 473.304860 |
| `0x876750` | 0 | 1.000000030 | 1.000000000 | 29.189525 | 324.032909 |
| `0x86B188` | 8 | 1.000000046 | 0.999999995 | 15.631578 | 691.183091 |
| `0x86B1F8` | 8 | 1.000000049 | 1.000000032 | 34.293256 | 117.054583 |
| `0x86DDB8` | 8 | 0.999999979 | 1.000000082 | 46.130277 | 185.725706 |
| `0x870278` | 8 | 1.000000036 | 0.999999993 | 22.642837 | 131.280716 |

Best residual among all candidate/corner pairs: `15.631578` for `n·x+d=0`, and `50.202269` for `n·x=d`. No corner is within `1e-3`. This does not establish that tag100 has no plane records; it means these candidate windows do not directly represent planes through this point box under the tested transform. The one-point tracer is not a rigid translation, so the plane translation law was not tested.

Machine-readable details: [`startpoint-plane-test.json`](startpoint-plane-test.json). Source GXM SHA-256: `56ebbf03fe681d730e796a40d455562b5f9976d794c710e73d5c9be32e4e86b2`; TXT SHA-256: `71ea372203bcc6e84bfee87e7d2f410e22c1fdcdc5f653c87274100df38c0d43`.
