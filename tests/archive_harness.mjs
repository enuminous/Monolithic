export {harness,root} from '../tools/atlas_runtime.mjs';
import {readFileSync} from 'node:fs';
export const bundle=JSON.parse(readFileSync(new URL('../source-packs/central-efmw-v1.bundle.json',import.meta.url),'utf8'));
