from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

MAX_RANGE_BYTES = 64 * 1024 * 1024


class HttpRangeReader(io.RawIOBase):
    def __init__(self, url: str) -> None:
        request = Request(url, method="HEAD")
        with urlopen(request, timeout=60) as response:
            self.url = response.geturl()
            self.length = int(response.headers["Content-Length"])
            self.etag = response.headers.get("ETag")
        self.position = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            position = offset
        elif whence == io.SEEK_CUR:
            position = self.position + offset
        elif whence == io.SEEK_END:
            position = self.length + offset
        else:
            raise ValueError(f"Unsupported seek mode: {whence}")
        if position < 0:
            raise ValueError("Cannot seek before byte zero")
        self.position = min(position, self.length)
        return self.position

    def read(self, size: int = -1) -> bytes:
        if self.position >= self.length:
            return b""
        remaining = self.length - self.position
        requested = remaining if size < 0 else min(size, remaining)
        if requested > MAX_RANGE_BYTES:
            raise ValueError(f"Refusing remote range larger than {MAX_RANGE_BYTES} bytes")

        end = self.position + requested - 1
        request = Request(self.url, headers={"Range": f"bytes={self.position}-{end}"})
        with urlopen(request, timeout=120) as response:
            if response.status != 206:
                raise OSError(f"Server ignored byte range; status={response.status}")
            data = response.read(requested + 1)
        if len(data) != requested:
            raise OSError(f"Short byte range: expected {requested}, received {len(data)}")
        self.position += len(data)
        return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List a remote ZIP without downloading it")
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--extract-json-dir",
        type=Path,
        help="Optionally extract JSON members only, preserving safe archive paths",
    )
    parser.add_argument(
        "--extract-member",
        action="append",
        default=[],
        help="Exact JSON member to extract; repeat to select more than one",
    )
    return parser.parse_args()


def safe_destination(root: Path, member_name: str) -> Path:
    destination = (root / member_name).resolve()
    resolved_root = root.resolve()
    if resolved_root not in destination.parents:
        raise ValueError(f"Unsafe archive member path: {member_name}")
    return destination


def main() -> int:
    args = parse_args()
    reader = HttpRangeReader(args.url)
    extracted_json: list[str] = []
    with zipfile.ZipFile(reader) as archive:
        entries = [
            {
                "name": info.filename,
                "compressed_bytes": info.compress_size,
                "uncompressed_bytes": info.file_size,
                "crc32": f"{info.CRC:08x}",
                "is_directory": info.is_dir(),
            }
            for info in archive.infolist()
        ]
        if args.extract_json_dir is not None:
            selected_members = set(args.extract_member)
            for info in archive.infolist():
                if info.is_dir() or Path(info.filename).suffix.lower() != ".json":
                    continue
                if selected_members and info.filename not in selected_members:
                    continue
                if info.file_size > MAX_RANGE_BYTES:
                    raise ValueError(f"Refusing oversized JSON member: {info.filename}")
                destination = safe_destination(args.extract_json_dir, info.filename)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(info))
                extracted_json.append(info.filename)
    report = {
        "source_url": args.url,
        "resolved_url_redacted": reader.url.split("?", maxsplit=1)[0],
        "archive_bytes": reader.length,
        "etag": reader.etag,
        "entry_count": len(entries),
        "file_count": sum(not entry["is_directory"] for entry in entries),
        "uncompressed_bytes": sum(entry["uncompressed_bytes"] for entry in entries),
        "extracted_json": extracted_json,
        "entries": entries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "entries"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
