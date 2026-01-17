import os
from pathlib import Path

import numpy as np
import soundfile as sf


class G726Seek:
    """
    Handles G.726 ADPCM WAV file reading, writing and information retrieval.
    """

    @staticmethod
    def get_duration(file_path: Path | str) -> float:
        """
        Gets audio file total duration (seconds).
        Advantage: Only reads header, doesn't load audio data, extremely fast (O(1)).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # SoundFile object only parses Header when opened
        with sf.SoundFile(file_path) as f:
            # frames = total samples, samplerate = sampling rate
            return f.frames / f.samplerate

    @staticmethod
    def read_segment(
        file_path: Path | str,
        start_sec: float,
        duration_sec: float,
    ) -> np.ndarray:
        from g726_seek.read_audio_segment import read_audio_segment

        return read_audio_segment(file_path, start_sec, duration_sec)

    @staticmethod
    def write(
        file_path: Path | str,
        data: np.ndarray,
        *,
        sample_rate: int = 16000,
        bits_per_sample: int = 2,
    ) -> Path:
        """
        Writes numpy array to G.726 format.

        Args:
            file_path (str): Output path (recommend .wav)
            data (np.array): Audio data (float32 or int16)
            sample_rate (int): Sampling rate (e.g. 16000, 8000)
            bits_per_sample (int): Compression depth (2, 3, 4, 5).
                                   2 bits @ 16k = 32kbps (recommended)
                                   3 bits @ 16k = 48kbps
        """
        from g726_seek.subtypes import SUBTYPE_MAP

        # 1. Check if compression depth is valid
        subtype = SUBTYPE_MAP.get(bits_per_sample)
        if not subtype:
            raise ValueError(
                f"Unsupported bits_per_sample: {bits_per_sample}. "
                + f"Please choose one of: {list(SUBTYPE_MAP.keys())}"
            )

        # 2. Write file
        # format='WAV' is container, subtype determines encoding
        sf.write(file_path, data, sample_rate, format="WAV", subtype=subtype)

        return Path(file_path)
