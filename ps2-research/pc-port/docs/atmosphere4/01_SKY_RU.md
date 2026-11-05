# Небо: существующий пресет, исправление проекции

IMPLEMENTED / OFFLINE_VALIDATED; RUNTIME_TESTED=false. Новый пресет и новые текстуры не создавались. `CustomSet=Atmosphere2/sets/r_deepforest`, `CustomBase=3`, `CustomSkyUScale=0.5` сохранены.

В exporter существующая панорама кодирует tan(elevation) от горизонта. Нативный цилиндр MR имеет радиус 1000, scale 0.6, фиксированный worldY=-100. В F10 frame-47920-d1-00006618 камераY≈60.0185: горизонт приходится примерно на V=.27. Нижние облака оказываются под видимым горизонтом. UScale=.5 верен: native U охватывает около двух повторов, исходный GT3 экспорт — один полный оборот. Второй слой содержит усреднённый по горизонтали RGB и заметную alpha, поэтому дополнительно скрывает детали первого.

`CustomSkyProjection=1` меняет только UV V в временной копии sky VB: .003+.995*(vertexWorldY-cameraY)/worldRadius. Требуются rigid VIEW и uniform yaw-only WORLD без shear/reflection/perspective; иначе native fallback. Геометрия неба, EXE, высота камеры и файлы текстур не изменяются. Верхний cap с V>=.97 сохраняет авторские UV. ADDRESSV=CLAMP scoped и восстанавливается.

`CustomSkyHaze=0.35` независимо ослабляет alpha второго слоя через scoped TFACTOR, не перекрашивает текстуру. 1 возвращает исходную плотность. Оба параметра LiveTuning. Projection=0/Haze=1 — старый путь. Стоковое небо без CustomSet не затрагивается.

Private preview вне дистрибутива: `.research-output/atmosphere4/sky-projection-private-preview.png`. Это математическая развёртка существующих текстур, не кадр игры и не доказательство устранения видимого дефекта. Полные GT3 панорамы, contact sheet и скриншоты не включены в пакет. Ограничения: остаётся native cylinder tessellation/cap; возможный горизонтальный шов и вид cap оценить в игре с разной высотой FreeCam, FOV и Restart.
