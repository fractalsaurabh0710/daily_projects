"""Minimal PNG reader/writer on the standard library (zlib + struct).

Images are (width, height, channels, rows) where rows is a list of bytearrays.
Reads 8-bit grayscale / RGB / RGBA, non-interlaced, all five scanline filters.
Writes grayscale or RGB. That is all a grain-on-a-mat photo needs.
"""
import struct
import zlib

SIG = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 6: 4}


def _chunk(tag, data):
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))


def write_png(path, width, height, channels, rows):
    ctype = {1: 0, 3: 2}[channels]
    raw = b"".join(b"\x00" + bytes(r) for r in rows)  # filter 0 on every row
    ihdr = struct.pack(">IIBBBBB", width, height, 8, ctype, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(SIG + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(raw, 6)) + _chunk(b"IEND", b""))


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != SIG:
        raise ValueError("not a PNG")
    pos, idat, hdr = 8, [], None
    while pos < len(data):
        n, tag = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if tag == b"IHDR":
            hdr = struct.unpack(">IIBBBBB", body)
        elif tag == b"IDAT":
            idat.append(body)
        pos += 12 + n
    w, h, depth, ctype, _, _, interlace = hdr
    if depth != 8 or ctype not in CHANNELS or interlace:
        raise ValueError("only 8-bit non-interlaced gray/RGB/RGBA supported")
    ch = CHANNELS[ctype]
    stride = w * ch
    raw = zlib.decompress(b"".join(idat))
    rows, prev = [], bytearray(stride)
    for y in range(h):
        base = y * (stride + 1)
        ft, line = raw[base], bytearray(raw[base + 1:base + 1 + stride])
        for i in range(stride):
            a = line[i - ch] if i >= ch else 0
            b, c = prev[i], (prev[i - ch] if i >= ch else 0)
            if ft == 1:
                line[i] = (line[i] + a) & 255
            elif ft == 2:
                line[i] = (line[i] + b) & 255
            elif ft == 3:
                line[i] = (line[i] + ((a + b) >> 1)) & 255
            elif ft == 4:
                line[i] = (line[i] + _paeth(a, b, c)) & 255
        rows.append(line)
        prev = line
    return w, h, ch, rows


def to_gray(img):
    """Collapse to one luminance channel (Rec. 601 weights); alpha is ignored."""
    w, h, ch, rows = img
    if ch == 1:
        return w, h, 1, rows
    out = [bytearray((299 * r[i] + 587 * r[i + 1] + 114 * r[i + 2]) // 1000
                     for i in range(0, w * ch, ch)) for r in rows]
    return w, h, 1, out


if __name__ == "__main__":
    import os, random, tempfile
    rng = random.Random(7)
    tmp = tempfile.mkdtemp()
    for ch in (1, 3):
        rows = [bytearray(rng.randrange(256) for _ in range(37 * ch)) for _ in range(23)]
        p = os.path.join(tmp, f"t{ch}.png")
        write_png(p, 37, 23, ch, rows)
        w, h, c, back = read_png(p)
        assert (w, h, c) == (37, 23, ch) and [bytes(r) for r in back] == [bytes(r) for r in rows]
    # Every filter type, hand-encoded, must decode to the same pixels.
    rows = [bytearray(rng.randrange(256) for _ in range(10)) for _ in range(5)]
    enc, prev = b"", bytearray(10)
    for ft, r in enumerate(rows):
        out = bytearray()
        for i in range(10):
            a = r[i - 1] if i else 0
            b, c = prev[i], (prev[i - 1] if i else 0)
            pred = (0, a, b, (a + b) >> 1, _paeth(a, b, c))[ft]
            out.append((r[i] - pred) & 255)
        enc += bytes([ft]) + bytes(out)
        prev = r
    ihdr = struct.pack(">IIBBBBB", 10, 5, 8, 0, 0, 0, 0)
    p = os.path.join(tmp, "f.png")
    open(p, "wb").write(SIG + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(enc)) + _chunk(b"IEND", b""))
    assert [bytes(r) for r in read_png(p)[3]] == [bytes(r) for r in rows]
    print("pngio: all tests passed")
