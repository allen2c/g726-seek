# Defines bit depth to subtype mapping table
# Key: Bits per sample
# Value: libsndfile subtype string
SUBTYPE_MAP = {
    2: "G726_16",  # 2 bits (16k sr -> 32kbps)
    3: "G726_24",  # 3 bits (16k sr -> 48kbps)
    4: "G726_32",  # 4 bits (16k sr -> 64kbps)
    5: "G726_40",  # 5 bits (16k sr -> 80kbps)
}
