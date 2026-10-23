# Monolithic Atlas — portable local-first corpus app

**Snapshot:** 2026-10-23. **Catalog:** 126 public repositories. **Published offline pack:** 99 files / 352,723 source bytes from three exact commits: two complete committed trees and one partial tree. The remaining **123 catalog entries are metadata-only in this release**. The standalone HTML still embeds only the catalog; import the separate pack to make its source readable offline.

[Offline pack and exact coverage](docs/OFFLINE_ARCHIVE.md) · [Portable JSON](source-packs/central-efmw-v1.bundle.json) · [CAR v1](source-packs/central-efmw-v1.car) · [File inventory and exclusions](source-packs/central-efmw-v1.report.json) · [Integrity checks](source-packs/SHA256SUMS)

| Repository | Source available offline after import | License evidence retained |
| --- | --- | --- |
| Circus | 9/9 tracked files, complete pinned tree | CC0-1.0 notice |
| Zoo-Monster | 10/10 tracked files, complete pinned tree | CC0-1.0 notice |
| Monolithic-Zoo-Lean4 | 80/82 tracked files, partial | MIT notice; two embedded upstream collections withheld |

“Complete” means every tracked leaf at the stated commit, not Git history, toolchains, dependencies, submodules or an empirically validated research result.

## Start

1. Open `index.html` directly in a modern browser. No build tools, npm, network or server are required to search the embedded catalog. **For reliable WebCrypto/IndexedDB caching, serve from HTTPS or use the included local server**; some browsers restrict storage on `file://` URLs.
2. Save `source-packs/central-efmw-v1.bundle.json` with the application before disconnecting. In **Archive → Import a portable JSON bundle**, choose that file. Select **Circus**, **Zoo-Monster**, or **Monolithic-Zoo-Lean4**, then **List local files → Open cached**. The importer verifies SHA-256, CIDs, Git commit/tree/blob bindings and retained license notices. **Download cached file** retrieves the complete original bytes. Optional **Fetch & cache source** and **List remote tree** still require internet access.
3. Export the **portable JSON bundle** to copy the catalog and cached files elsewhere. A second device can use `Import portable JSON bundle` to validate SHA-256 and store files locally.
4. `Export CAR v1` packages a canonical DAG-CBOR root and raw cached files as content-addressed blocks. Bring it to a local IPFS node using `ipfs dag import monolithic-corpus.car`. Publishing requires a configured node and actual pinning; the Atlas does not automatically advertise CIDs.
5. Optionally run `python3 tools/archive_server.py` and visit `http://127.0.0.1:8765` to enable local HTTP block archival, manual block synchronization and a simple relay bulletin board. The companion is **not a libp2p implementation**.

## Capabilities / actual implementation

| Requested feature | Delivered here | Important boundary |
| --- | --- | --- |
| Single-page, HTML5, immutable snapshot | Standalone HTML with 126 embedded repository metadata records | Separate source pack must be imported; full histories and remaining sources are not included |
| LocalStorage / offline | Saved UI settings in localStorage; files in IndexedDB | Browser quotas and private-mode behavior vary |
| URL args / sharing | `?repo=EFMW&tab=atlas&file=README.md&q=Lean` | URL shares selection, not cached bytes |
| DAG-CBOR / IPLD / IPFS | Canonical encoder, SHA-256 CIDv1, CAR v1 export, IPFS gateway link | IPFS not automatically pinned; no CID-based retrieval daemon |
| RDF / OWL | JSON-LD and RDF Turtle describing repository metadata and classes | No inferred scientific facts or equivalences |
| Relay / archive server | Optional loopback HTTP block store with CID verification and message relay | Requires separate Python process and trusted local network |
| libp2p | Peer multiaddr configuration + documented integration boundary | A full js-libp2p stack and signaling relay are **not** embedded |
| UUCP / sneakernet | Download files, local import/export, UUCP CLI recipe | UUCP itself operates outside the browser |
| Animated SVG / WebGL / shaders | Inline SVG network animation; optional ambient fragment shader | Decorative, not a physical simulation |
| GIF / MPEG / audio | Local media import and native HTML5 playback | Playback depends on browser codec support |
| TTS | Built-in Web Speech API / speechSynthesis | Device voices and speech permissions vary |
| Wikidata / OSM / OEIS / LMFDB | User-triggered external search links; optional local Wikidata QID | No bulk scraping or automatic identity inference |
| WASM extracted | Tiny WASM CRC-32 demo with JS cross-check | CRC-32 demonstration only, not a cryptographic security guarantee |

## Evidence / provenance

- `corpus-index.json` records source identity, default branches, rough GitHub-reported repository sizes, domain grouping, and README blob IDs for checked central repositories.
- Inferred topical groupings are UI aids, not scientific classifications.
- **Ownership and contributor permissions require separate verification.** The selected pack records observed license notices. No blanket relicense is implied by this index; do not republish third-party source without verifying its license and contributors.
- Export archives are *content-verified*, not cryptographically signed for source attribution. SHA-256 or CIDv1 proves only that specific bytes match.
- The research claims and formalization results must be validated independently. Lean formal proof of a mathematical statement is not evidence that nature satisfies its assumptions.

## Formats

- `corpus-index.json`: JSON collection, immutable snapshot and all 126 repo identities.
- `monolithic-corpus-bundle.json`: portable UTF-8 JSON including imported files as Base64 and SHA-256; import verifies each byte string.
- `monolithic-corpus.car`: CAR v1, one DAG-CBOR manifest root (CIDv1 sha2-256 codec 0x71), then zero or more raw source blocks (CIDv1 sha2-256 codec 0x55).
- `monolithic-root.dag-cbor`: the root manifest encoded canonically; exact CID depends on snapshot metadata and current cached contents.
- `monolithic-corpus.jsonld` / `.ttl`: metadata-only RDF/OWL exports.

To regenerate after source edits:

```bash
python3 tools/build.py
```

The bundled `tools/crc.wasm` was built with:

```bash
clang --target=wasm32 -O2 -nostdlib -Wl,--no-entry -Wl,--export=crc32 -Wl,--export-memory -Wl,--initial-memory=131072 -o tools/crc.wasm tools/crc.c
python3 tools/build.py
```

## Security

- The archive server is intentionally unauthenticated and binds to loopback by default. Do **not** expose it on a public interface.
- The app uses `textContent` to show fetched text, and **never executes fetched HTML or JavaScript**. Media is displayed via browser-native elements.
- Remote source fetching and third-party portals require explicit clicks. No analytics or tracker is included.
- Source hashes are content identifiers, not identity signatures. Back up the JSON/CAR exports for durable offline preservation.

## Reviewed source pack and reproducibility

The original snapshotter now has a **locked, rights-gated mode**. Its lock records all 14 reviewed central repository commits and their complete leaf inventories. Only the three repositories in the table contribute source bytes. Other repositories are withheld where an applicable redistribution grant was not established; an account name does not prove ownership. The lock uses an explicit per-path allowlist, retained notices and fixed byte caps. Unknown source, Git LFS pointers, symlinks and submodules cannot silently enter this pack.

```bash
# Rebuild using existing local Git objects, without fetching:
python3 tools/mirror_corpus.py --lock source-packs/central-efmw-v1.lock.json --source-root /path/to/checkouts --out source-packs
# Or explicitly fetch only the locked commits into local object stores:
python3 tools/mirror_corpus.py --lock source-packs/central-efmw-v1.lock.json --fetch --out source-packs
python3 tools/build.py
node tools/export_pack.mjs
sha256sum -c source-packs/SHA256SUMS
```

GitHub unavailability may prevent reacquiring a commit. The offline reconstruction test rebuilds the pack byte-for-byte from the permitted Git objects already contained in the published bundle. No excluded source bytes are needed.

The v1 JSON and CAR/DAG-CBOR formats are preserved with additive `provenance` and `archives` fields. Old JSON bundles still import. IndexedDB upgrades preserve existing files; validated multi-file imports commit atomically. Local coverage is derived from actual matching bytes. Published-pack coverage is displayed separately, so a new device is never labeled fully mirrored before import. This is a reading archive: Lean and Python execution environments are not bundled.

## Verification

```bash
python3 tests/check_source_pack.py
node tests/check_formats.mjs
node tests/check_offline.mjs
python3 tests/check_server.py
# Optional development-only browser dependencies; runtime HTML has none:
npm ci
npx playwright install --with-deps chromium firefox webkit
node tests/check_browser.mjs
```

[Automated workflow](.github/workflows/archive.yml) checks deterministic reconstruction, hashes, source identity, license retention, malformed imports, coverage transitions, CAR framing and all 99 offline text reads. Browser checks exercise real IndexedDB migration, disconnected import/read/export, import into a fresh storage partition, persistence after reloading the local shell, quota rollback and tamper rejection. No external request is allowed during those browser tests. See [test scope](tests/readme.md) for precise boundaries.

## Next steps for a complete mirror

Establish per-source rights for the withheld repositories and embedded upstream collections, then extend the reviewed lock with additional exact commits and explicit paths. Rebuild and test each new pack. This release does not claim to archive the whole research corpus.

## Opt-in repository-source extraction

For a source snapshot beyond the embedded catalog, run on a machine with Git and GitHub access:

```bash
python3 tools/mirror_corpus.py --plan
python3 tools/mirror_corpus.py --repo EFMW --repo papers --out my_mirror
# Or request the full visible catalog, with protective size caps:
python3 tools/mirror_corpus.py --out my_mirror
```

Each resulting `*.bundle.json` imports directly via **Archive → Import portable JSON**. `mirror-report.json` records commit SHAs, omissions, failures and limits. Defaults cap individual files at 10 MiB, any repository at 100 MiB, and total captured bytes at 500 MiB. To intentionally attempt all committed-tree bytes, use `--unbounded` with sufficient resources; some repositories are large. This copies shallow committed snapshots, not full Git histories, submodule content, Git LFS payloads, or private repos. This older opt-in extraction mode is for personal capture and does not perform the reviewed lock’s permission gate. Review third-party permissions and licenses before sharing its derived bundles; use `--lock` for the reproducible published pack.
