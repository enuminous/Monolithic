# Offline source pack: central-efmw-v1

Release date: 2026-10-23. **99 files, 352,723 source bytes.** Two complete committed trees, one partial tree, and 123 other catalog entries with no source bytes in this release.

## Use offline

1. Download the repository ZIP (or copy `index.html` and `source-packs/central-efmw-v1.bundle.json`) while connected. Keep the JSON file as your portable backup.
2. Open the saved HTML. For browsers that restrict `file://` storage, run `python3 tools/archive_server.py` from the saved repository and visit `http://127.0.0.1:8765`. The loopback server needs no internet.
3. In **Archive**, import the JSON bundle. Wait for **Validated and imported 99 files and 3 pinned tree manifests**.
4. In **Corpus atlas**, select one of the three included repositories. Use **List local files**, then choose a document. Source is shown as text and never executed. **Download cached file** saves the full byte sequence; long previews are explicitly marked.
5. Export portable JSON for another device; import it there while disconnected. CAR export is for external IPFS tools, not an in-browser CAR importer.

The HTML alone is a catalog, not the source pack. A hosted page is not installed by a service worker; save it before disconnecting. Browser storage may be denied or evicted. JSON/CAR files are the durable backup, independent of IndexedDB.

## Exact coverage

Each commit below is an immutable Git object ID. “Fully mirrored” counts every tracked leaf at that commit, not Git history, dependencies, Git LFS payloads or submodules. The published-pack column is separate from the current device’s actual coverage.

| Repository | Commit | Pack coverage | Files / tree | Source bytes |
| --- | --- | --- | ---: | ---: |
| [Circus](https://github.com/enuminous/Circus/tree/892f0d5498b5ec0369691f31a058871675e64b43) | `892f0d5498b5ec0369691f31a058871675e64b43` | fully-mirrored | 9 / 9 | 25,010 |
| [Devs2.0](https://github.com/enuminous/Devs2.0/tree/2ec5cfb7cb98e36d7bba01552a74aa4d610e07c3) | `2ec5cfb7cb98e36d7bba01552a74aa4d610e07c3` | metadata-only | 0 / 108 | 0 |
| [EFMW](https://github.com/enuminous/EFMW/tree/cae1b1b9518af9dddc8ab9f09d391645e611847c) | `cae1b1b9518af9dddc8ab9f09d391645e611847c` | metadata-only | 0 / 18 | 0 |
| [EFMW-Axioms](https://github.com/enuminous/EFMW-Axioms/tree/248dcbf323b8ee3f25ccfcf346d29516d77019a1) | `248dcbf323b8ee3f25ccfcf346d29516d77019a1` | metadata-only | 0 / 14 | 0 |
| [EFMW-EXP-001](https://github.com/enuminous/EFMW-EXP-001/tree/65134993069c2dc0c46a60fccd8bcdb2d951cdd3) | `65134993069c2dc0c46a60fccd8bcdb2d951cdd3` | metadata-only | 0 / 48 | 0 |
| [EFMW-Grid](https://github.com/enuminous/EFMW-Grid/tree/2be52f3f72937742f76ad7ba35a837d157e20196) | `2be52f3f72937742f76ad7ba35a837d157e20196` | metadata-only | 0 / 9 | 0 |
| [EFMW-Lagrangian](https://github.com/enuminous/EFMW-Lagrangian/tree/2e392b9fb5bbfa35667cd562787e23cadcc1623f) | `2e392b9fb5bbfa35667cd562787e23cadcc1623f` | metadata-only | 0 / 120 | 0 |
| [EFMW_Post156_Zoo_Audit](https://github.com/enuminous/EFMW_Post156_Zoo_Audit/tree/dc8903f99c5503e2279b3962d960cb4f0bfa622c) | `dc8903f99c5503e2279b3962d960cb4f0bfa622c` | metadata-only | 0 / 107 | 0 |
| [FieldSpace](https://github.com/enuminous/FieldSpace/tree/39e8a7e8acbf20b9a9b8e2afd0985549925ab86c) | `39e8a7e8acbf20b9a9b8e2afd0985549925ab86c` | metadata-only | 0 / 34 | 0 |
| [Monolithic-102-Zoo-Lean4](https://github.com/enuminous/Monolithic-102-Zoo-Lean4/tree/2ee2abd51cbe25aa54fd6c244dc67f72e5a36085) | `2ee2abd51cbe25aa54fd6c244dc67f72e5a36085` | metadata-only | 0 / 177 | 0 |
| [Monolithic-Zoo-Lean4](https://github.com/enuminous/Monolithic-Zoo-Lean4/tree/15dfb335424e77e1458cd77996f23d074dac0d88) | `15dfb335424e77e1458cd77996f23d074dac0d88` | partially-cached | 80 / 82 | 302,722 |
| [Monolithic_102_EFMW](https://github.com/enuminous/Monolithic_102_EFMW/tree/170679d21aa0f570fda505ee3b03864b717be950) | `170679d21aa0f570fda505ee3b03864b717be950` | metadata-only | 0 / 113 | 0 |
| [Oroboros](https://github.com/enuminous/Oroboros/tree/72958ea6f3faaab07ad64ab9db8818362da370bb) | `72958ea6f3faaab07ad64ab9db8818362da370bb` | metadata-only | 0 / 39 | 0 |
| [Zoo-Monster](https://github.com/enuminous/Zoo-Monster/tree/6d75d1280eb03d66f8e12b484ec3c3e38d76909c) | `6d75d1280eb03d66f8e12b484ec3c3e38d76909c` | fully-mirrored | 10 / 10 | 24,991 |

The other 112 catalog entries were not selected for this first pack and remain metadata-only. The 11 selected metadata-only entries above have pinned tree metadata but no redistributed source bytes.

### Included source

- **Circus:** all 9 tracked files, including README, Python source, examples/tests and its CC0 notice.
- **Zoo-Monster:** all 10 tracked files, including README, Python source, examples/tests and its CC0 notice.
- **Monolithic-Zoo-Lean4:** 80 files, including the 46 animal Lean modules, shared and extension models, build manifests, Python scripts, documentation and MIT notice. `UPSTREAM_SOURCES.json` and `extension-sources.json` are excluded because they embed upstream source requiring a separate rights review. Scripts referring to those omitted collections cannot reproduce their full source-dependent verification from this pack alone.

Every included path, exact original byte count, SHA-256, CID, Git blob ID, source URL and license record appears in the [portable bundle](../source-packs/central-efmw-v1.bundle.json). The [report](../source-packs/central-efmw-v1.report.json) lists every omitted path and reason. The [lock](../source-packs/central-efmw-v1.lock.json) fixes commits, full leaf inventories, allowed paths and caps.

## License and provenance boundaries

The two CC0 notices and the MIT copyright/permission notice are included verbatim at their original paths. These records establish the source’s stated terms, not a legal certification of ownership or contributor assignments. The Zoo root license expressly defers to individual upstream notices; this pack therefore withholds its two embedded upstream collections. It does not fetch third-party dependencies or follow repository links. No license is added to the withheld EFMW work, and no blanket relicense of the corpus is implied.

SHA-256 and CIDs establish byte identity. Git SHA-1 is used only to bind those bytes to the existing Git commit/tree/blob identities. Commit objects and tree reconstructions are checked, but signatures and authorship are not authenticated. The format preserves explicit provenance claims without treating them as scientific validation.

## Reproducible output

Use the locked commands in the [main README](../README.md#reviewed-source-pack-and-reproducibility). Creation time is fixed to release-date midnight UTC as a deterministic serialization label, not a claimed observation timestamp. Output ordering, source bytes and metadata are stable; dirty checkout contents and Git checkout filters are ignored because the builder reads Git objects. Caps fail the build rather than silently dropping files. The full reviewed lock SHA-256 travels with each archive manifest on re-export.

Check `source-packs/SHA256SUMS` before transfer. The `.cid` file identifies the canonical `.dag-cbor` root; the `.car` file contains that root plus 99 raw source blocks. Duplicate raw blocks may share a CID. `node tools/export_pack.mjs` uses the existing Atlas importer and exporter to produce these files.

## Capabilities still external

| Capability | Boundary |
| --- | --- |
| IPFS publication/pinning | Run a configured external node, e.g. `ipfs dag import central-efmw-v1.car`; publication and retention are not automatic. |
| libp2p | Configuration only; no embedded peer transport/signaling implementation. |
| UUCP / sneakernet | External transfer of unchanged JSON/CAR files; no browser UUCP daemon. |
| Archive HTTP relay | Optional separate loopback Python process; not libp2p or an authenticated public service. |
| RDF / OWL | Existing metadata exports remain; no inferred ownership or scientific truth. |
| Offline rebuilds of research software | Toolchains, dependency packages, external data and omitted upstream sources remain separate requirements. |
| Browser compatibility | Original standalone HTML and v1 bundle fields retained; storage migration is additive. Browser origin policies, quotas and private modes still apply. |
