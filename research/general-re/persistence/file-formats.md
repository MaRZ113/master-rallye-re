# Output format and paths

Game, Options and PlayerState Broker persistence uses **XML**, not a newly
discovered binary save struct. `0052EFB0` builds a Game root, containing Broker
Value children from `005FE460/005FE580`; other Game-save side paths can serialize
their own engine data.

Typed Value writers emit Name, Type and value/class data. `005FE580` appends
SaveOptions and SavePlayerState booleans. XmlData uses class-specific ToXml;
StringList uses its list conversion. Scope, revision and SaveFile are **not
serialized entry fields** on this generic path. Game bit is assigned by load
policy; SaveFile is assigned by the filename job; scope becomes GLOBAL.

Normal logical names resolve under the backend data root to:

- `DataGame/options.xml`
- `DataGame/PlayerState.xml`
- whole Game: `DataGame/<registered-logical-name>.xml`, plus GameParticles path.

Existing output backup adds `#` to the complete filename. Developer SaveAs can
choose another DataGame basename and can change live grouping for Game mode.
Backend root is not assumed universally identical to the process image directory
under every possible developer configuration.

Native whitespace/float formatting, StringList escaping and every object schema
are not promised byte-stable. The metadata inventory records source hashes and
types without copying proprietary Value payloads. The Observatory JSON is an
analysis snapshot, **not a native loadable save file**.
