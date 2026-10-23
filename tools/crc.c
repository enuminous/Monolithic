#include <stdint.h>
// Lightweight CRC-32 browser demo; not a cryptographic integrity primitive.

__attribute__((export_name("crc32"))) uint32_t crc32(uint32_t ptr, uint32_t len) {
  uint32_t c=0xffffffff;
  if(ptr+len>65536) return 0;
  const uint8_t* mem=(const uint8_t*)(uintptr_t)0;
  for(uint32_t i=0;i<len;i++){
    c^=mem[ptr+i];
    for(uint32_t j=0;j<8;j++)c=(c>>1)^((c&1u)?0xEDB88320u:0);
  }
  return c^0xffffffffu;
}
// memory export from clang linker; the compiler uses its own linear memory.
