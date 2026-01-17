import os
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import soundfile as sf

if TYPE_CHECKING:
    from g726_seek.subtypes import BITS_TYPE


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

    @classmethod
    def convert(
        cls,
        data: np.ndarray,
        output_path: Path | str,
        src_sr: int,
        target_sr: int = 16000,
        bits: "BITS_TYPE" = 2,
        to_mono: bool = True,
    ) -> Path:
        """
        Converts numpy array to G.726 WAV format.

        Args:
            data (np.array): Audio data
            src_sr (int): Source sample rate (required for resampling)
            output_path (Path | str): Output file path
            target_sr (int): Target sample rate (default 16000)
            bits (BITS_TYPE): Compression depth (2, 3, 4, 5)
            to_mono (bool): Whether to force conversion to mono
        """
        import librosa

        from g726_seek.ensure_mono import ensure_mono
        from g726_seek.subtypes import SUBTYPE_MAP

        # 1. Handle channels (Mono Mixing)
        if to_mono:
            data = ensure_mono(data, style="librosa")

        # 2. Handle resampling (if source sr != target sr)
        if src_sr != target_sr:
            # Use librosa's resample function
            # Note: This step is CPU intensive
            data = librosa.resample(data, orig_sr=src_sr, target_sr=target_sr)

        # 3. Write file
        subtype = SUBTYPE_MAP[bits]
        sf.write(output_path, data, target_sr, format="WAV", subtype=subtype)

        return Path(output_path)

    @classmethod
    def convert_from_file(
        cls,
        input_path: Path | str,
        output_path: Path | str,
        *,
        target_sr: int = 16000,
        bits: "BITS_TYPE" = 2,
        to_mono: bool = True,
    ):
        """
        Converts any audio file (MP3, WAV, FLAC...) to G.726 WAV format.

        Args:
            input_path (str): Source file path
            output_path (str): Output file path
            target_sr (int): Target sample rate (default 16000)
            bits (int): Compression depth (2=32kbps, 3=48kbps...)
            to_mono (bool): Whether to force conversion to mono
        """
        import librosa

        from g726_seek.subtypes import SUBTYPE_MAP

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"File not found: {input_path}")

        # 1. Load with librosa
        try:
            # y is audio data (float32), sr is actual sample rate read
            y, _ = librosa.load(input_path, sr=target_sr, mono=to_mono)
        except Exception as e:
            raise RuntimeError(f"Failed to load or resample: {e}")

        # 2. Write to G.726
        subtype = SUBTYPE_MAP[bits]
        sf.write(output_path, y, target_sr, format="WAV", subtype=subtype)

        return output_path
