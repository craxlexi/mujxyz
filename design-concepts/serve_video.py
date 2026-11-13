"""Serve the design previews with byte-range support for scroll-scrubbed video."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        self.byte_range = None
        path = Path(self.translate_path(self.path))
        header = self.headers.get("Range", "")
        if not header.startswith("bytes=") or not path.is_file():
            return super().send_head()

        try:
            start_text, end_text = header[6:].split("-", 1)
            size = path.stat().st_size
            start = int(start_text) if start_text else max(0, size - int(end_text))
            end = min(size - 1, int(end_text)) if end_text else size - 1
            if start < 0 or start > end or start >= size:
                raise ValueError
        except (ValueError, TypeError):
            self.send_error(416, "Invalid byte range")
            return None

        file = path.open("rb")
        self.byte_range = start, end
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(str(path)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        return file

    def copyfile(self, source, outputfile):
        if self.byte_range is None:
            return super().copyfile(source, outputfile)
        start, end = self.byte_range
        source.seek(start)
        remaining = end - start + 1
        while remaining:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    path = Path(__file__).resolve().parent
    from functools import partial

    handler = partial(RangeHandler, directory=str(path))
    print(f"Open http://localhost:{args.port}/photo-turn.html?theme=dark")
    ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()
