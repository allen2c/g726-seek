# G.726 Random Access Reader

[![PyPI version](https://img.shields.io/pypi/v/g726-seek.svg)](https://pypi.org/project/g726-seek/)
[![Python Version](https://img.shields.io/pypi/pyversions/g726-seek.svg)](https://pypi.org/project/g726-seek/)
[![License](https://img.shields.io/pypi/l/g726-seek.svg)](https://opensource.org/licenses/MIT)

A lightweight Python library designed for **precision seeking** and **zero-waste decoding** of G.726 ADPCM compressed WAV files.

## Key Features

* **O(1) Seeking:** Unlike MP3 or AAC, G.726 allows for sample-accurate seeking without parsing frame headers or processing bit reservoirs.
* **Zero Waste:** Reads and decodes only the requested time slice. No "warm-up" samples or overlapping frames required.
* **High Efficiency:** Wraps `libsndfile` (via `pysoundfile`) for C-level performance.
* **Format Support:** Compatible with standard G.726 WAV containers at various sample rates (e.g., 8kHz, 16kHz) and bit depths (2-bit to 5-bit).

## Use Case

Ideal for applications requiring low-latency access to specific segments of long audio recordings, such as:

* Dataset slicing for machine learning.
* Real-time audio seeking in web services.
* Telephony archive retrieval.
