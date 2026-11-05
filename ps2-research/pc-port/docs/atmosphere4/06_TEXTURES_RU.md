# Размытые скалы и грунт

OFFLINE_VALIDATED аудит, не новая отрисовка. `analysis/textures.json` содержит 518 текстур и 3313 material/draw UV-density диапазонов France1/Turkey2/Turkey3, PC extracted и установленный PS2-loose. Ошибок разбора 0. В этой выборке max dimension=128; wrapper содержит один BGRA image level, это не доказательство отсутствия runtime mip generation.

UV density рассчитана по площади геометрических/UV треугольников в texels/source-unit. Не следует сравнивать её как texels/metre без world scale; repeated small texture на больших скалах не становится детальнее от anisotropy. В F10 effective stage0 включает MINFILTER=3, MAGFILTER=2, MAXANISOTROPY=16: AF уже работает. MIPFILTER=1 и LOD bias .1 наблюдаются, но причина/умысел не подтверждены. Подмена этого значения без controlled game A/B не объявляется исправлением ошибки. Renderer filtering не менялся.

Совместимый enhancement-пакет: отдельный overlay с авторскими/лицензированными high-res .dxt, теми же material names, UV tiling, BGRA/alpha semantics и header format; keep opaque/alpha-test cutoff и tile edges. Создавать через существующий SDK texture authoring, проверить parser/hash/dimensions, alpha coverage и mipchain upload в изолированной копии, затем matched camera game A/B. Оригинальные Data.sma/DataGx не перезаписывать. x2/x4 resize сам по себе не восстанавливает детали; автоматический такой пакет не выдаётся за реставрацию.

PS2-loose каталог может содержать fallback PC texture files: варианты обозначены по локальному корню, не приписаны всему оригинальному PS2 диску. Неизменённые ассеты и подробные source hashes обеспечивают обратимость. Ошибка рендера, достаточная для безопасного изменения фильтрации, в доступных данных не установлена.
