"""
ZipStreamer — HTTP range-request ZIP streaming for IRS TEOS XML files.

Streams individual XML files out of monthly IRS ZIP archives without
downloading the full file (typically 99–500 MB). Uses two range requests
per entry: one for the local file header, one for the compressed data.

Promoted and hardened from tools/irs_990_bulk_loader/test_zip_range.py.
"""

import asyncio
import logging
import struct
import zlib
from typing import AsyncIterator

import aiohttp

logger = logging.getLogger(__name__)

# ZIP signatures
_EOCD_SIG    = b"PK\x05\x06"
_CD_SIG      = b"PK\x01\x02"
_LFH_SIG     = b"PK\x03\x04"
_ZIP64_EXTRA = 0x0001          # ZIP64 extended information extra field ID

# Maximum EOCD comment size (ZIP spec)
_EOCD_SEARCH_SIZE = 65536 + 22


class ZipStreamer:
    """
    Async iterator that yields (filename, xml_bytes) tuples for every .xml
    entry in a remote ZIP file, using HTTP range requests only.

    Usage:
        async with aiohttp.ClientSession() as session:
            streamer = ZipStreamer(url, session, concurrency=3)
            async for filename, xml_bytes in streamer.stream_xml_entries():
                process(xml_bytes)
    """

    def __init__(
        self,
        url: str,
        session: aiohttp.ClientSession,
        concurrency: int = 3,
        max_retries: int = 3,
    ):
        self.url = url
        self.session = session
        self._sem = asyncio.Semaphore(concurrency)
        self.max_retries = max_retries
        self._total_size: int = 0
        self._entries: list[dict] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def get_entry_count(self) -> int:
        """Return number of XML entries in the ZIP (reads central directory once)."""
        if not self._entries:
            await self._load_central_directory()
        return len(self._entries)

    async def stream_xml_entries(self) -> AsyncIterator[tuple[str, bytes]]:
        """
        Async generator that yields (filename, xml_bytes) for every .xml
        entry in the ZIP, respecting the concurrency semaphore.
        """
        if not self._entries:
            await self._load_central_directory()

        for entry in self._entries:
            async with self._sem:
                try:
                    xml_bytes = await self._download_entry(entry)
                    yield entry["name"], xml_bytes
                except Exception as e:
                    logger.warning(f"Failed to download {entry['name']}: {e}")

    # ------------------------------------------------------------------
    # Central directory
    # ------------------------------------------------------------------

    async def _load_central_directory(self) -> None:
        """Fetch and parse the ZIP central directory via range requests."""
        self._total_size = await self._get_file_size()
        logger.debug(f"ZIP size: {self._total_size:,} bytes")

        # 1. Fetch tail to locate EOCD
        tail_size = min(_EOCD_SEARCH_SIZE, self._total_size)
        tail = await self._range_fetch(self._total_size - tail_size, self._total_size - 1)

        eocd_pos = tail.rfind(_EOCD_SIG)
        if eocd_pos == -1:
            raise ValueError(f"EOCD signature not found in {self.url}")
        eocd = tail[eocd_pos:]

        cd_size   = struct.unpack_from("<I", eocd, 12)[0]
        cd_offset = struct.unpack_from("<I", eocd, 16)[0]

        # Handle ZIP64 (sentinel values 0xFFFFFFFF)
        if cd_size == 0xFFFFFFFF or cd_offset == 0xFFFFFFFF:
            cd_size, cd_offset = self._parse_zip64_eocd(tail, eocd_pos)

        logger.debug(f"Central directory: {cd_size:,} bytes at offset {cd_offset:,}")

        # 2. Fetch central directory
        cd_data = await self._range_fetch(cd_offset, cd_offset + cd_size - 1)

        # 3. Parse entries
        self._entries = self._parse_central_directory(cd_data)
        logger.info(f"Found {len(self._entries):,} XML entries in {self.url.split('/')[-1]}")

    def _parse_zip64_eocd(self, tail: bytes, eocd_pos: int) -> tuple[int, int]:
        """Locate and parse ZIP64 End-of-Central-Directory Locator + Record."""
        # ZIP64 EOCD Locator is 20 bytes before the EOCD record
        loc_pos = eocd_pos - 20
        if loc_pos < 0 or tail[loc_pos:loc_pos+4] != b"PK\x06\x07":
            raise ValueError("ZIP64 EOCD locator not found")
        zip64_eocd_offset = struct.unpack_from("<Q", tail, loc_pos + 8)[0]

        # Fetch ZIP64 EOCD record (56 bytes)
        # It may be outside our tail — need an extra range request
        # For simplicity, try within tail first
        tail_base = self._total_size - len(tail)
        rel_offset = zip64_eocd_offset - tail_base
        if 0 <= rel_offset < len(tail) - 56:
            z64 = tail[rel_offset:]
        else:
            # Out of tail — fetch separately (rare)
            import asyncio
            z64 = asyncio.get_event_loop().run_until_complete(
                self._range_fetch(zip64_eocd_offset, zip64_eocd_offset + 55)
            )

        if z64[:4] != b"PK\x06\x06":
            raise ValueError("ZIP64 EOCD record signature not found")

        cd_size   = struct.unpack_from("<Q", z64, 40)[0]
        cd_offset = struct.unpack_from("<Q", z64, 48)[0]
        return cd_size, cd_offset

    def _parse_central_directory(self, cd_data: bytes) -> list[dict]:
        """Parse binary central directory data into a list of entry dicts."""
        entries = []
        pos = 0
        while pos < len(cd_data):
            if cd_data[pos:pos+4] != _CD_SIG:
                break

            compress_method   = struct.unpack_from("<H", cd_data, pos + 10)[0]
            compressed_size   = struct.unpack_from("<I", cd_data, pos + 20)[0]
            uncompressed_size = struct.unpack_from("<I", cd_data, pos + 24)[0]
            fname_len         = struct.unpack_from("<H", cd_data, pos + 28)[0]
            extra_len         = struct.unpack_from("<H", cd_data, pos + 30)[0]
            comment_len       = struct.unpack_from("<H", cd_data, pos + 32)[0]
            local_hdr_offset  = struct.unpack_from("<I", cd_data, pos + 42)[0]
            fname = cd_data[pos+46 : pos+46+fname_len].decode("utf-8", errors="replace")

            # Resolve ZIP64 extended sizes if sentinel values present
            extra_data = cd_data[pos+46+fname_len : pos+46+fname_len+extra_len]
            if (compressed_size == 0xFFFFFFFF or uncompressed_size == 0xFFFFFFFF
                    or local_hdr_offset == 0xFFFFFFFF):
                compressed_size, uncompressed_size, local_hdr_offset = (
                    self._resolve_zip64_extra(
                        extra_data,
                        compressed_size,
                        uncompressed_size,
                        local_hdr_offset,
                    )
                )

            if fname.lower().endswith(".xml"):
                entries.append({
                    "name":             fname,
                    "compress_method":  compress_method,
                    "compressed_size":  compressed_size,
                    "uncompressed_size": uncompressed_size,
                    "local_hdr_offset": local_hdr_offset,
                })

            pos += 46 + fname_len + extra_len + comment_len

        return entries

    @staticmethod
    def _resolve_zip64_extra(
        extra_data: bytes,
        compressed_size: int,
        uncompressed_size: int,
        local_hdr_offset: int,
    ) -> tuple[int, int, int]:
        """Parse ZIP64 extra field to get 64-bit sizes/offsets."""
        i = 0
        while i + 4 <= len(extra_data):
            field_id   = struct.unpack_from("<H", extra_data, i)[0]
            field_size = struct.unpack_from("<H", extra_data, i + 2)[0]
            field_data = extra_data[i+4 : i+4+field_size]
            if field_id == _ZIP64_EXTRA:
                offset = 0
                if uncompressed_size == 0xFFFFFFFF and offset + 8 <= len(field_data):
                    uncompressed_size = struct.unpack_from("<Q", field_data, offset)[0]
                    offset += 8
                if compressed_size == 0xFFFFFFFF and offset + 8 <= len(field_data):
                    compressed_size = struct.unpack_from("<Q", field_data, offset)[0]
                    offset += 8
                if local_hdr_offset == 0xFFFFFFFF and offset + 8 <= len(field_data):
                    local_hdr_offset = struct.unpack_from("<Q", field_data, offset)[0]
                break
            i += 4 + field_size
        return compressed_size, uncompressed_size, local_hdr_offset

    # ------------------------------------------------------------------
    # File download
    # ------------------------------------------------------------------

    async def _download_entry(self, entry: dict) -> bytes:
        """Download and decompress a single ZIP entry via range requests."""
        # Read local file header (first 30 bytes) to find actual data offset
        lh = await self._range_fetch(entry["local_hdr_offset"],
                                      entry["local_hdr_offset"] + 29)
        if lh[:4] != _LFH_SIG:
            raise ValueError(f"Local file header signature missing for {entry['name']}")

        fname_len = struct.unpack_from("<H", lh, 26)[0]
        extra_len = struct.unpack_from("<H", lh, 28)[0]
        data_start = entry["local_hdr_offset"] + 30 + fname_len + extra_len
        data_end   = data_start + entry["compressed_size"] - 1

        compressed = await self._range_fetch(data_start, data_end)

        if entry["compress_method"] == 8:    # deflate
            return zlib.decompress(compressed, -15)
        return compressed                    # stored (method 0)

    # ------------------------------------------------------------------
    # HTTP primitives
    # ------------------------------------------------------------------

    async def _get_file_size(self) -> int:
        for attempt in range(self.max_retries):
            try:
                async with self.session.head(self.url) as resp:
                    resp.raise_for_status()
                    return int(resp.headers["Content-Length"])
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        return 0  # unreachable

    async def _range_fetch(self, start: int, end: int) -> bytes:
        headers = {"Range": f"bytes={start}-{end}"}
        for attempt in range(self.max_retries):
            try:
                async with self.session.get(self.url, headers=headers) as resp:
                    if resp.status not in (200, 206):
                        raise aiohttp.ClientResponseError(
                            resp.request_info, resp.history, status=resp.status
                        )
                    return await resp.read()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == self.max_retries - 1:
                    raise
                wait = 2 ** attempt
                logger.debug(f"Range fetch retry {attempt+1}/{self.max_retries} "
                             f"(bytes {start}-{end}): {e} — waiting {wait}s")
                await asyncio.sleep(wait)
        return b""  # unreachable
