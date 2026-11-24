set -e
source venv/bin/activate
export HF_HOME=$PWD/.hf_cache
date; echo "== Wan2.1 T5"
hf download Wan-AI/Wan2.1-T2V-1.3B models_t5_umt5-xxl-enc-bf16.pth --local-dir models/Wan-AI/Wan2.1-T2V-1.3B
date; echo "== Wan2.2 I2V A14B experts"
hf download Wan-AI/Wan2.2-I2V-A14B --include "high_noise_model/*" --include "low_noise_model/*" --local-dir models/Wan-AI/Wan2.2-I2V-A14B
date; echo "ALL DONE"
