# Sun Halo Quality

IMPLEMENTED / OFFLINE_VALIDATED; RUNTIME_TESTED=false. `SunHaloDither=1`, `SunDitherStrength=1` (0–2) добавляют постоянный 4×4 ordered pattern с нулевым средним перед 8-bit quantization halo и sun-wide sprite. Он не зависит от кадра/времени: временной noise не используется. Вне support sprite сохраняет нулевую энергию. Dither=0 возвращает прежнюю quantization.

Managed sprite пересоздаётся только при изменении quality settings; на кадрах текстура не перегенерируется. Allocation failure использует существующий fail-closed SunFX путь. Depth-mask, occlusion logic, thresholds и orientation не изменены. Новых render targets нет.

Тесты: deterministic periodic noise, zero mean, nonfinite/zero intensity, sprite contract и штатные SunFX state/lifetime tests. Остаются 8-bit framebuffer и 128px базовый halo; полного устранения banding/мерцания при движении камеры без игры обещать нельзя. Изменения должны сравниваться при неизменном SunGlowIntensity и окклюзии за горой/деревьями.
