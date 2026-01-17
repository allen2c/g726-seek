import os
from pathlib import Path
from typing import Literal, TypeAlias

import numpy as np
import soundfile as sf

BITS_TYPE: TypeAlias = Literal[2, 3, 4, 5]

SUBTYPE_CACHE: dict[BITS_TYPE, str] = {}


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
        bits_per_sample: BITS_TYPE = 2,
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

        # 1. Check if compression depth is valid
        subtype = G726Seek.resolve_best_subtype(bits_per_sample)
        if not subtype:
            raise ValueError(
                f"Unsupported bits_per_sample: {bits_per_sample}. "
                + f"Please choose one of: {list(SUBTYPE_CACHE.keys())}"
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

        # 1. Handle channels (Mono Mixing)
        if to_mono:
            data = ensure_mono(data, style="librosa")

        # 2. Handle resampling (if source sr != target sr)
        if src_sr != target_sr:
            # Use librosa's resample function
            # Note: This step is CPU intensive
            data = librosa.resample(data, orig_sr=src_sr, target_sr=target_sr)

        # 3. Write file
        subtype = G726Seek.resolve_best_subtype(bits)
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

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"File not found: {input_path}")

        # 1. Load with librosa
        try:
            # y is audio data (float32), sr is actual sample rate read
            y, _ = librosa.load(input_path, sr=target_sr, mono=to_mono)
        except Exception as e:
            raise RuntimeError(f"Failed to load or resample: {e}")

        # 2. Write to G.726
        subtype = G726Seek.resolve_best_subtype(bits)
        sf.write(output_path, y, target_sr, format="WAV", subtype=subtype)

        return output_path

    @staticmethod
    def resolve_best_subtype(bits: BITS_TYPE) -> str:
        """
        動態尋找當前作業系統支援的最佳 Subtype。
        優先級：標準 G726 -> NMS 變體 -> G721 (僅4bit) -> IMA ADPCM (保底)
        """
        if bits in SUBTYPE_CACHE:
            return SUBTYPE_CACHE[bits]

        # 取得當前系統支援的所有 WAV Subtypes
        available = sf.available_subtypes("WAV")

        # 定義優先順序候選名單 (Priority List)
        candidates = []
        if bits == 2:
            # 32kbps @ 16k
            candidates = ["G726_16", "NMS_ADPCM_16"]
        elif bits == 3:
            # 48kbps @ 16k
            candidates = ["G726_24", "NMS_ADPCM_24"]
        elif bits == 4:
            # 64kbps @ 16k
            candidates = ["G726_32", "G721_32", "NMS_ADPCM_32", "IMA_ADPCM"]
        elif bits == 5:
            # 80kbps @ 16k
            candidates = ["G726_40", "NMS_ADPCM_40"]

        # 遍歷候選名單，選出系統支援的第一個
        selected = None
        for c in candidates:
            if c in available:
                selected = c
                break

        # 特殊處理：如果 2-bit/3-bit 都不支援，是否要 fallback 到 4-bit IMA_ADPCM?
        # 為了保證 write 不會 crash，我們做最後的保底
        if selected is None:
            if "IMA_ADPCM" in available:
                print(f"警告: 系統不支援 {bits}-bit G.726，降級使用 4-bit IMA_ADPCM。")
                selected = "IMA_ADPCM"
            else:
                # 幾乎不可能發生，除非 libsndfile 壞了
                raise RuntimeError("嚴重錯誤: 您的系統不支援任何 ADPCM 壓縮格式。")

        SUBTYPE_CACHE[bits] = selected
        return selected
