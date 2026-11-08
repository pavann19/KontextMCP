# Publication scope

The public repository begins with a curated source snapshot on 8 November 2026. Earlier local history is retained privately because it included mutable runtime state.

The runtime SQLite database, audit ledger, execution traces, checkpoint state and local Qdrant storage are excluded. Fresh installations create isolated runtime state using the documented startup and migration commands. No real assessment records are required to run the test fixtures.

Committed validation artifacts are historical local measurements, including synthetic fixture output. They are retained with their captured bytes and hashes; checkout line endings and later source changes can affect source fingerprints. They do not establish hosted CI success, production operation or independent legal review. Source snapshots and checksums in these reports describe their original validation runs.
