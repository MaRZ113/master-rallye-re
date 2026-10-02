# Master Rallye Observatory

## Обычный запуск

Из корня `master-rallye-re-general`:

```powershell
python tools/runtime/mr_observe.py
```

Или запустите `tools/runtime/MRallye-Observatory.cmd`. Нужен Python 3.11+;
launcher в репозитории использует `py -3`, Python-скрипт можно запустить через
свой обычный `python`. Сторонняя terminal UI библиотека не нужна.

Используйте **disposable retail install** с pristine EXE. Программа сама находит
MRallye, проверяет размер и SHA256. При одном подходящем процессе PID вводить
не нужно; при нескольких появится выбор. Demo и изменённые EXE отклоняются.
Если игра не запущена: `[C]` запоминает путь к копии retail, `[L]` запускает её,
`[W]` повторяет проверку после ручного запуска. Игра не запускается сама при
открытии меню Observatory. Путь хранится в игнорируемом
`research-output/general-re/runtime-config.json`, не в Git.

| Действие | Как использовать |
|---|---|
| `[1]` Broker Editor | открыть окно; существующее окно повторно не открывается |
| `[2]` Snapshot | штатный Debug→Dump, ожидание нового полного блока, сохранение пары |
| `[3]` Snapshot with label | то же, с вашей меткой |
| `[4]` Latest | последний валидный snapshot, в том числе без запущенной игры |
| `[5]` Diff last two | две последние валидные пары без ввода путей |
| `[6]` Diff files | явный выбор двух JSON |
| `[7]` Capture folder | открыть единую папку результатов |
| `[8]` Flow Builder | только открытие окна |
| `[9]` Status | процесс, hash, окна, Debug buffer, история captures |

Для автоматического открытия Broker нужен известный native menu
`Game → Reset / Exit`. Если он выключен, включите `Menues/Enabled=True`
**в disposable копии** по прежней процедуре R-DEV или сначала вручную откройте
Broker. Observatory сам не меняет конфигурацию игры. Не выбирайте в редакторах
Edit/Remove/Commit/Save/Build/Clear: эти операции в инструмент не включены.

Открытие Broker может зарегистрировать `__NO_SAVE` и `__NO_CHANGE` в списке
SaveFile — это известное изменение метаданных. Snapshot отправляет только
**локальный Broker Editor WM_COMMAND 2**, соответствующий Debug→Dump; адресат
проверяется по PID, EXE hash, заголовку и шестипунктовому menu. Main-window ID 2
для этой операции не используется. Открытие Flow/Broker переиспользует проверенный
`dev_command_trigger.py`; его прежний CLI с dry-run и confirmation остаётся доступен.

## Snapshot действительно новый

Перед Dump читается baseline Debug buffer. После единственного штатного Dump
запроса инструмент ждёт полный блок, начинающийся **после baseline**; старый
блок из буфера не выдаётся за новый. Даже одинаковый по содержимому новый Dump
допустим, если подтверждено новое смещение. При realloc адрес может измениться;
используется содержимое/offset, а не закреплённый указатель.

При сбросе/уплотнении буфера, неполном Dump, изменении HWND или timeout запрос
не повторяется автоматически. Ошибка timeout не означает, что игра не обработает
уже отправленный запрос. Можно заново выполнить capture после стабилизации.
Ручной fallback:

```powershell
python tools/runtime/mr_observe.py capture frontend --manual-dump
```

После baseline нажмите в Broker `Debug → Dump`, затем Enter в консоли.

## Файлы и история

Одна папка:

```text
research-output/general-re/broker-observatory/captures/
  2026-10-02/
    20261002-221530_frontend.json
    20261002-221530_frontend.dump.bin
```

Имя/дата назначаются автоматически; исходная метка сохраняется внутри JSON.
При совпадении имени добавляется суффикс, старые данные не перезаписываются.
Перед публикацией проверяются parser/schema/hash; temporary/reservation файлы
не считаются captures. История вычисляется по metadata, проверяет оба файла,
размер и hash raw sidecar. Неполная или повреждённая пара не становится latest.
Ранние пары прямо в корне captures также учитываются без переписывания.
Жёсткое завершение процесса может оставить orphan/reservation — они исключены
из истории. Два файла не являются одной атомарной операцией ОС.

## Короткие команды

```powershell
python tools/runtime/mr_observe.py status
python tools/runtime/mr_observe.py capture race-grid
python tools/runtime/mr_observe.py show --last
python tools/runtime/mr_observe.py show --previous
python tools/runtime/mr_observe.py diff --last
python tools/runtime/mr_observe.py diff --last --preset race
python tools/runtime/mr_observe.py diff --last --preset vehicle
python tools/runtime/mr_observe.py diff --last --preset frontend --ignore-revision-only
python tools/runtime/mr_observe.py persistence-report --save-mode playerstate
python tools/runtime/mr_observe.py persistence-report --save-file PlayerState --scope GLOBAL
```

Глобальные `--pid`, `--exe`, `--install-root`, `--capture-root`, `--config`
идут **перед** subcommand. Обычно они не нужны. Capture root ограничен
`research-output` текущего worktree. В local config сохраняются абсолютные пути;
при ручной правке относительные пути разрешаются относительно рабочего каталога.

Presets `race`, `vehicle`, `frontend`, `route` — только фильтры имён, без новых
геймплейных выводов. `persistence` показывает изменения метаданных. Полный diff
остаётся default. `--ignore-revision-only` скрывает только изменения, где revision
— единственное изменённое поле; изменения values/flags/scope/SaveFile сохраняются.

Persistence report группирует **выведенные** строки по точному SaveFile, считает
типы, scopes, save bits, revisions и показывает примеры путей. Он не эмулирует
все правила native save: Game требует ещё group match, whole-Game saver исключает
sentinels, XmlData зависит от class serializer. Фильтр `--save-mode game` здесь
означает Game-bit eligibility, а не гарантию попадания в конкретный файл.

## Launcher рядом с игрой

Один раз настройте путь через `[C]`, затем:

```powershell
python tools/runtime/mr_observe.py setup-launcher
```

Будет создан новый user-local
`research-output/general-re/MRallye-Observatory.cmd`. Его можно **вручную**
скопировать рядом с disposable игрой. Он содержит пути к текущим Python/script,
открывает то же меню и использует remembered config. Перегенерируйте после
перемещения repo/Python. Существующий launcher не перезаписывается.
Machine-specific пути не добавляются в Git.

Standalone EXE в будущем можно собрать локально (например, PyInstaller one-folder
с этими тремя Python-модулями). Такая упаковка не сделана в R-BROKER1: сначала
нужен человеческий Windows smoke test, затем воспроизводимая проверка bundle.

## Статус доказательств

Предыдущий passive reader уже проверен человеком: большие Dumps, realloc,
несколько блоков и XmlData continuation. Новая цепочка discovery→open→автоматический
Dump→paired capture проверена синтетическими тестами и статическим разбором,
**но ещё не подтверждена новым runtime-тестом**.

Нет injection, WriteProcessMemory, patch EXE, suspend/debugger modification,
команд Save/Commit/Build или автоматической игры. Process access — query/read;
команды окон — только два reviewed openers и original Broker Dump. Raw capture
содержит собственные данные игры и остаётся игнорируемым исследовательским output.

Результаты RE: [Broker](../research/general-re/broker-core/findings.md),
[XML](../research/general-re/xml-core/findings.md),
[persistence](../research/general-re/persistence/findings.md).
Human persistence tests: [U1–U4](../research/general-re/persistence/runtime-validation-plan.md).

Низкоуровневый `tools/runtime/broker_observatory.py` сохранён: parse, summarize,
diff, passive capture и новый persistence-report. Primary frontend импортирует
его parser/schema/diff/reader вместо независимой реализации.
