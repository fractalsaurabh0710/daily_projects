"""A Bloom filter built from scratch on the standard library.

A Bloom filter answers "have I seen this?" with one of two answers:
"definitely not", or "probably yes". It never stores the keys themselves --
only bits -- so membership costs about 10 bits per item instead of the item.

The part worth the write-up is that the error rate is *designed* rather than
discovered. Given how many items you expect (n) and the false-positive rate
you will tolerate (p), the optimal bit count and number of hash functions
fall straight out of two closed-form formulas:

    m = -n * ln(p) / (ln 2)^2        bits
    k = (m / n) * ln 2               hash functions

The test at the bottom fills a filter to capacity and checks that the
measured false-positive rate actually lands near the rate it promised.
"""

from __future__ import annotations

import hashlib
import math
import random
import string


class BloomFilter:
    """A fixed-capacity Bloom filter. Items go in; they never come out."""

    def __init__(self, capacity: int, error_rate: float = 0.01) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if not 0.0 < error_rate < 1.0:
            raise ValueError("error_rate must be strictly between 0 and 1")

        self.capacity = capacity
        self.error_rate = error_rate
        self.num_bits = max(
            1, math.ceil(-capacity * math.log(error_rate) / math.log(2) ** 2)
        )
        self.num_hashes = max(1, round(self.num_bits / capacity * math.log(2)))
        self._bits = bytearray((self.num_bits + 7) // 8)
        self.count = 0

    # -- hashing ---------------------------------------------------------

    @staticmethod
    def _encode(item: object) -> bytes:
        return item if isinstance(item, bytes) else str(item).encode("utf-8")

    def _positions(self, item: object):
        """Kirsch-Mitzenmacher: build k hashes out of two independent ones.

        One 128-bit digest is split in half and the halves combined as
        h1 + i*h2. Forcing h2 odd keeps the stride coprime with any
        power-of-two-ish table, so the positions spread out instead of
        collapsing onto a short cycle.
        """
        digest = hashlib.blake2b(self._encode(item), digest_size=16).digest()
        h1 = int.from_bytes(digest[:8], "big")
        h2 = int.from_bytes(digest[8:], "big") | 1
        for i in range(self.num_hashes):
            yield (h1 + i * h2) % self.num_bits

    # -- core operations -------------------------------------------------

    def add(self, item: object) -> None:
        for pos in self._positions(item):
            self._bits[pos >> 3] |= 1 << (pos & 7)
        self.count += 1

    def __contains__(self, item: object) -> bool:
        return all(
            self._bits[pos >> 3] >> (pos & 7) & 1 for pos in self._positions(item)
        )

    def __len__(self) -> int:
        return self.count

    # -- introspection ---------------------------------------------------

    @property
    def bits_per_item(self) -> float:
        return self.num_bits / self.capacity

    @property
    def fill_ratio(self) -> float:
        """Fraction of bits currently set."""
        return sum(byte.bit_count() for byte in self._bits) / self.num_bits

    def current_error_rate(self) -> float:
        """Predicted false-positive rate at the present fill level."""
        return self.fill_ratio**self.num_hashes

    def __repr__(self) -> str:
        return (
            f"BloomFilter(capacity={self.capacity}, error_rate={self.error_rate}, "
            f"bits={self.num_bits}, hashes={self.num_hashes}, items={self.count})"
        )


def _random_word(rng: random.Random, length: int = 12) -> str:
    return "".join(rng.choice(string.ascii_lowercase) for _ in range(length))


def _test() -> None:
    rng = random.Random(20260929)

    # Sizing: ~9.6 bits and 7 hashes per item is the textbook answer for 1%.
    bf = BloomFilter(capacity=10_000, error_rate=0.01)
    assert 9.0 < bf.bits_per_item < 10.5, bf.bits_per_item
    assert bf.num_hashes == 7, bf.num_hashes

    members = {_random_word(rng) for _ in range(bf.capacity)}
    for word in members:
        bf.add(word)

    # No false negatives, ever. This is the filter's one hard guarantee.
    assert all(word in bf for word in members)

    # About half the bits should be set at optimal sizing.
    assert 0.4 < bf.fill_ratio < 0.6, bf.fill_ratio

    # False positives: measured rate should sit near the promised one.
    strangers = [w for w in (_random_word(rng) for _ in range(50_000)) if w not in members]
    hits = sum(1 for w in strangers if w in bf)
    measured = hits / len(strangers)
    assert measured < 0.02, f"measured {measured:.4%}, wanted ~1%"

    # A filter with room to spare should be far below its design rate.
    roomy = BloomFilter(capacity=10_000, error_rate=0.01)
    for word in list(members)[:1_000]:
        roomy.add(word)
    assert roomy.current_error_rate() < bf.current_error_rate()

    print(bf)
    print(f"  bits/item     : {bf.bits_per_item:.2f}")
    print(f"  bits set      : {bf.fill_ratio:.1%}")
    print(f"  promised FP   : {bf.error_rate:.2%}")
    print(f"  predicted FP  : {bf.current_error_rate():.2%}")
    print(f"  measured FP   : {measured:.2%}  ({hits} of {len(strangers)})")
    print(f"  false negs    : 0 of {len(members)}")
    print(f"  memory        : {bf.num_bits // 8:,} bytes vs "
          f"{sum(len(w) for w in members):,} bytes of raw keys")
    print("all tests passed")


if __name__ == "__main__":
    _test()
