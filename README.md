# Monolithic Atlas — portable local-first corpus app

**Snapshot:** 2026-10-23. **Catalog:** 126 public repositories found in the GitHub-connected `enuminous` inventory. **Mirror completeness:** catalog metadata only; repository source trees are **not** bundled wholesale. Ten central README Git blob IDs have been spot-checked. Core repo annotations are editorial summaries, not copies of source documents.

## Start

1. Open `index.html` directly in a modern browser. No build tools, npm, network or server are required to search the embedded catalog. **For reliable WebCrypto/IndexedDB caching, serve from HTTPS or use the included local server**; some browsers restrict storage on `file://` URLs.
2. Select a repository, then `Fetch & cache source` or `List tree` when internet access is available. These operations fetch via public GitHub URLs and respect GitHub rate and browser CORS policies. Cached source becomes readable offline.
3. Export the **portable JSON bundle** to copy the catalog and cached files elsewhere. A second device can use `Import portable JSON bundle` to validate SHA-256 and store files locally.
4. `Export CAR v1` packages a canonical DAG-CBOR root and raw cached files as content-addressed blocks. Bring it to a local IPFS node using `ipfs dag import monolithic-corpus.car`. Publishing requires a configured node and actual pinning; the Atlas does not automatically advertise CIDs.
5. Optionally run `python3 tools/archive_server.py` and visit `http://127.0.0.1:8765` to enable local HTTP block archival, manual block synchronization and a simple relay bulletin board. The companion is **not a libp2p implementation**.

## Capabilities / actual implementation

| Requested feature | Delivered here | Important boundary |
| --- | --- | --- |
| Single-page, HTML5, immutable snapshot | Standalone HTML with 126 embedded repository metadata records | Full Git histories and source files not pre-mirrored |
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
- **Ownership/licensing remain undetermined** per repository. No blanket relicense is implied by this index; do not republish third-party source without verifying its license and contributors.
- Export archives are *content-verified*, not cryptographically signed for source attribution. SHA-256 or CIDv1 proves only that specific bytes match.
- The research claims and formalization results must be validated independently. Lean formal proof of a mathematical statement is not evidence that nature satisfies its assumptions.

## Formats

- `corpus-index.json`: JSON collection, immutable snapshot and all 126 repo identities.
- `monolithic-corpus-bundle.json`: portable UTF-8 JSON including imported files as Base64 and SHA-256; import verifies each byte string.
- `monolithic-corpus.car`: CAR v1, one DAG-CBOR manifest root (CIDv1 sha2-256 codec 0x71), then zero or more raw source blocks (CIDv1 sha2-256 codec 0x55).
- `monolithic-root.dag-cbor`: the root manifest encoded canonically; exact CID depends on timestamp and current cached contents.
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

## Next steps for a complete mirror

The missing part for literal *entire source corpus* is a reproducible per-repository file/commit capture with licenses, contributor permissions, complete Git trees and content bytes. That should be a separate authorized mirroring job, producing a versioned content-addressed dataset and size manifest. The current static package deliberately does not claim to have done that.

## Opt-in repository-source extraction

For a source snapshot beyond the embedded catalog, run on a machine with Git and GitHub access:

```bash
python3 tools/mirror_corpus.py --plan
python3 tools/mirror_corpus.py --repo EFMW --repo papers --out my_mirror
# Or request the full visible catalog, with protective size caps:
python3 tools/mirror_corpus.py --out my_mirror
```

Each resulting `*.bundle.json` imports directly via **Archive → Import portable JSON**. `mirror-report.json` records commit SHAs, omissions, failures and limits. Defaults cap individual files at 10 MiB, any repository at 100 MiB, and total captured bytes at 500 MiB. To intentionally attempt all committed-tree bytes, use `--unbounded` with sufficient resources; some repositories are large. This copies shallow committed snapshots, not full Git histories, submodule content, Git LFS payloads, or private repos. Review third-party permissions and licenses before sharing derived bundles.
