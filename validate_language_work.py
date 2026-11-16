import gc
import hashlib
import json
import statistics
import sys
import time
import tracemalloc

from unstructured.documents.elements import NarrativeText
from unstructured.partition.common.lang import apply_lang_metadata, detect_languages

detect_languages("This is a complete sentence with enough words to initialize the detector.")
elements = [NarrativeText(f"Record {i}") for i in range(2000)]


def run():
    return list(apply_lang_metadata(elements, languages=["auto"], detect_language_per_element=True))


run()
gc.collect()
tracemalloc.start()
result = run()
_, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
output = json.dumps([e.metadata.languages for e in result], sort_keys=True).encode()
samples = []
for _ in range(5):
    start = time.perf_counter()
    run()
    samples.append(time.perf_counter() - start)
report = {
    "input_elements": len(elements),
    "input_chars": sum(len(e.text) for e in elements),
    "output_sha256": hashlib.sha256(output).hexdigest(),
    "tracemalloc_peak_bytes": peak,
    "median_seconds": statistics.median(samples),
}
with open(sys.argv[1], "w") as output_file:
    json.dump(report, output_file)
print("BENCHMARK", json.dumps(report))
