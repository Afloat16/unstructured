import gc
import hashlib
import json
import statistics
import time
import tracemalloc

from unstructured.cleaners.core import auto_paragraph_grouper

text = "A complete source line.\n" * 300_000
gc.collect()
tracemalloc.start()
output = auto_paragraph_grouper(text)
_, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
digest = hashlib.sha256(output.encode()).hexdigest()
output_length = len(output)
del output

timings = []
for _ in range(5):
    gc.collect()
    start = time.perf_counter()
    result = auto_paragraph_grouper(text)
    timings.append(time.perf_counter() - start)
    assert hashlib.sha256(result.encode()).hexdigest() == digest
    del result

print(json.dumps({
    "input_lines": 300_000,
    "input_chars": len(text),
    "output_chars": output_length,
    "output_sha256": digest,
    "tracemalloc_peak_bytes": peak,
    "median_seconds": statistics.median(timings),
    "sample_max_lines": 2000,
}))
