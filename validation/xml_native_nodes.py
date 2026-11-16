"""Measure native parser retention in a fresh process, without storing output text."""

import hashlib
import json
import os
import resource
import sys
import tempfile
import time

from unstructured.partition.xml import get_leaf_elements

kind, count = sys.argv[1], int(sys.argv[2])
record = b"<item>value</item>" if kind == "elements" else b"<!-- comment --> <?pi value?> "
block = record * 1000
with tempfile.NamedTemporaryFile(suffix=".xml") as source:
    source.write(b"<root>")
    for _ in range(count // 1000):
        source.write(block)
    source.write(b"</root>")
    source.flush()

    before_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    digest = hashlib.sha256()
    emitted = 0
    start = time.perf_counter()
    for text in get_leaf_elements(source.name, None, None, None):
        digest.update(text.encode())
        digest.update(b"\0")
        emitted += 1
    elapsed = time.perf_counter() - start
    peak_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps({
        "kind": kind, "records": count, "file_bytes": os.path.getsize(source.name),
        "initial_peak_kb": before_kb, "peak_kb": peak_kb,
        "added_peak_kb": peak_kb - before_kb,
        "seconds": elapsed, "output_count": emitted, "output_sha256": digest.hexdigest(),
    }))
