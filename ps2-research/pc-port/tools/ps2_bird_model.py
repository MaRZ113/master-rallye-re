"""COURSE-ALIVE2 reference model of the PS2 gaAnimals_BirdManager (SLES_509.06), float32, one call = one game tick.

Built on the AMBIENT2 primitives of `ps2-research/tools/bird_runtime.py` (Schrage RNG with the low-24-bit output, FlyBird
init/step, nearest marker search, bank switcher) and the manager order recovered in this phase (docs/course-alive2):

    tick(camera):                                   # one dispatch 21f088; manager before its birds (tick queue order)
      manager 1af330, only if BOTH MarkerList pointers resolve (FlightList and MillList of the course scene):
        observer = camera position (camera manager 201350 entry 0, +c0..c8)
        1afa20 burst      U(0.1,1) <  (clock += 0.003) * 0.1  ->  clock = 0, n = min(R(0,RndFly), free)
                          n > 0: spawn marker (nearest, cached +-5 window, + R(0,3), clamped), strict
                          MinFly^2 < XZ^2 < MaxFly^2  ->  n entities popped from the free BACK, carrier = marker XYZ,
                          each inserted at the FRONT of the pending queue
        1b0238 retire     flying bird with MaxFly^2 < XZ^2  ->  owners cleared, back to the free BACK
        1afc88/1afdd8     ground (Miller) vector: always empty (its producers 1af770/1aff58 have no reference in the ELF)
        1affe0 convert    pending BACK (FIFO): FlyBird ctor + ImageBankSwitcher, 1b0a40 init (6 RNG draws, camera)
        1b0508 copy       carrier translation -> en2d translation of every flying bird
      birds, in entity (pool) order: FlyBird 1b0e68 (1-2 RNG draws), ImageBankSwitcher 1b17e8 (key 0..2, every 5 ticks)

The renderer (337a98/330530) draws each flying bird's en2d at the en2d translation with the PSB frame of its current key.
`world_quad` gives the PS2 world-space vertices for a camera.
"""
from __future__ import annotations

import math
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PORT.parent / 'tools'))
import bird_runtime as br  # noqa: E402

f32, add, sub, mul, div = br.f32, br.add, br.sub, br.mul, br.div
POOL = 16                 # constructor +34; no producer of the Broker key Animals/MaxBirds exists in the ELF or PackFS
SEED = 12345              # constructor seed of the global RNG (1d5de0); its in-race state is shared and unknown
SCALE = f32(0.1)          # 1af460: en2d uniform scale


@dataclass
class CourseBirds:
    flight: list            # FlightList XYZ (float32), source order; None when the course has no FlightList
    mill_present: bool      # MillList exists in the course scene (its points are only used by dead ground code)
    min_fly: float
    max_fly: float
    rnd_fly: int            # clamped to <=10 by 1af0b0

    @property
    def gate(self):
        return self.flight is not None and self.mill_present


@dataclass
class Entity:
    carrier: tuple = (0., 0., 0.)
    en2d: tuple = (0., 0., 0.)
    bird: br.FlyBird | None = None
    switch: br.BankSwitcher | None = None
    visible: bool = False


@dataclass
class Manager:
    course: CourseBirds
    rng: br.RandomStream = field(default_factory=lambda: br.RandomStream(SEED))
    clock: float = 0.
    cache: int = -1
    observer: tuple = (0., 0., 0.)
    entities: list = field(default_factory=lambda: [Entity() for _ in range(POOL)])
    free: list = field(default_factory=lambda: list(range(POOL)))
    flying: list = field(default_factory=list)
    pending: list = field(default_factory=list)
    ticks: int = 0

    def _xz2(self, p):
        dx = sub(p[0], self.observer[0]); dz = sub(p[2], self.observer[2])
        return add(add(mul(dx, dx), 0.), mul(dz, dz))

    def burst(self):
        pts = self.course.flight
        if not self.free or pts is None or not pts:
            return
        u = self.rng.real(f32(.1), 1.)
        self.clock = add(self.clock, f32(.003))
        if not u < mul(self.clock, f32(.1)):
            return
        self.clock = 0.
        n = min(self.rng.integer(0, self.course.rnd_fly), len(self.free))
        if n <= 0:
            return
        base = br.nearest_marker(pts, self.observer, self.cache)
        self.cache = base
        idx = min(len(pts) - 1, max(0, base + self.rng.integer(0, 3)))
        p = pts[idx]
        dx = sub(p[0], self.observer[0]); dz = sub(p[2], self.observer[2]); dy = sub(p[1], p[1])
        d2 = add(add(mul(dx, dx), mul(dy, dy)), mul(dz, dz))
        if not (mul(self.course.min_fly, self.course.min_fly) < d2 < mul(self.course.max_fly, self.course.max_fly)):
            return
        for _ in range(n):
            e = self.free.pop()
            self.entities[e].carrier = p
            self.pending.insert(0, e)

    def retire(self):
        limit = mul(self.course.max_fly, self.course.max_fly)
        i = 0
        while i < len(self.flying):
            e = self.flying[i]
            if limit < self._xz2(self.entities[e].carrier):
                ent = self.entities[e]
                ent.bird = ent.switch = None
                ent.visible = False
                ent.carrier = (0., 0., 0.)          # 263038 identity carrier
                self.free.append(e)
                del self.flying[i]
            else:
                i += 1

    def convert(self, camera):
        if not self.pending:
            return
        e = self.pending.pop()
        ent = self.entities[e]
        ent.bird = br.FlyBird(ent.carrier)
        ent.visible = True
        ent.switch = br.BankSwitcher()
        ent.bird.initialize(camera, self.rng)
        ent.carrier = ent.bird.origin
        self.flying.append(e)

    def tick(self, camera):
        camera = br.xyz(camera)
        self.ticks += 1
        if self.course.gate:
            self.observer = camera
            self.burst()
            self.retire()
            self.convert(camera)
            for e in self.flying:
                self.entities[e].en2d = self.entities[e].carrier
        for ent in self.entities:          # entity (pool) order
            if ent.bird is not None:
                ent.carrier = ent.bird.step(self.rng)
                ent.switch.step()

    def snapshot(self):
        return [(e, self.entities[e].en2d, self.entities[e].switch.frame) for e in sorted(self.flying)]


def billboard(side, look):
    """330530 on the PS2 view matrix built by 3387c8/36fc18 (DAT_00435e88=1): view row2 = (side.z, up.z, look.z).
    F=(row2.x,0,row2.z) (x=1 if both ~0), U=(0,1,0), R=(F.z,0,-F.x); rows scaled by the en2d scale 0.1."""
    fx, fz = f32(side[2]), f32(look[2])
    eps = f32(1.1920929e-6)
    if -eps <= fx <= eps and -eps <= fz <= eps:
        fx = 1.
    return (mul(fz, SCALE), 0., mul(-fx, SCALE)), (0., SCALE, 0.)


def world_vertex(translation, rows, lx, ly):
    r, u = rows
    return tuple(add(add(mul(f32(lx), r[i]), mul(f32(ly), u[i])), translation[i]) for i in range(3))


def frame_local(vx, vy):
    """337a98: local x = -0.5 + vx, local y = 0.5 - vy (command offset 0)."""
    return add(f32(-.5), f32(vx)), sub(f32(.5), f32(vy))


def camera_basis(look, up):
    """36fc18: side = normalize(look x up) (DAT_00435e88=1: not negated)."""
    s = (sub(mul(look[1], up[2]), mul(look[2], up[1])), sub(mul(look[2], up[0]), mul(look[0], up[2])),
         sub(mul(look[0], up[1]), mul(look[1], up[0])))
    n2 = add(add(mul(s[0], s[0]), mul(s[1], s[1])), mul(s[2], s[2]))
    if n2 <= f32(1.1920929e-07):
        return (0., 0., 0.)
    r = div(1., f32(math.sqrt(n2)))
    return tuple(mul(x, r) for x in s)


def f32bits(x):
    return struct.pack('<f', x)
