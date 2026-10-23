# Archive verification

Run from the repository root. Python tests require only Python 3 and Git. Node
format/offline tests require Node 22+ and no installed packages.

| Test | What it establishes |
| --- | --- |
| `python3 tests/check_source_pack.py` | Seven tests: all file/Git/CID hashes and license evidence, all 14 locked tree inventories, byte-identical offline reconstruction twice, permission/notice failures, tree tampering, moving-ref rejection and size-cap failure. Reconstructs only permitted Git objects from the shipped pack; never fetches excluded content. |
| `node tests/check_formats.mjs` | Existing CID vector, DAG-CBOR ordering, 126 catalog identities, WASM/JS CRC cross-check and empty export compatibility. |
| `node tests/check_offline.mjs` | Runs the actual standalone importer, reader and exporters in Node with storage replaced by an in-memory adapter and `fetch` forbidden. Reads all 99 texts, checks a fresh-import JSON round trip and deterministic root, independently parses CAR framing and verifies every block, rejects tampered bytes/trees/commits/licenses/paths/duplicates/false completeness. Tests legacy v1 and coverage changes. |
| `python3 tests/check_server.py` | Existing loopback archive-server CID checks, aliases, inventory and relay behavior. |
| `node tests/check_browser.mjs` | Chromium, Firefox and WebKit through Playwright 1.56.1: actual IndexedDB v1→v2 migration, all 99 offline reads, UI JSON and CAR export, fresh storage import, local-file navigation, persistence after loading the shell again, atomic rollback under injected quota/write failure, and corrupt-bundle rejection. External routes are blocked throughout; the browser is switched offline for import/read/export. |

For the browser tests, run `npm ci` and
`npx playwright install --with-deps chromium firefox webkit` first. To run one
engine, use `ATLAS_BROWSERS=chromium node tests/check_browser.mjs`.

Browser output and screenshots go to ignored `test-results/`; CI uploads them as
`offline-browser-evidence`. CI uses the official Playwright 1.56.1 Noble image
pinned by manifest digest, with its browser libraries preinstalled. Tests reload the application shell from the included
loopback origin. They do not assert that an unsaved hosted page will boot offline,
or that every browser permits IndexedDB under `file://`. Save the HTML and bundle
or serve them from the included local server. Mobile/private-mode quotas and real
IPFS pinning are outside this test scope.

Regenerate `index.html`, CAR, DAG-CBOR, CID and SHA256SUMS and require a clean diff
in CI. These tests verify the reading archive; they do not execute archived
research code, build Lean, certify ownership or validate scientific claims.
