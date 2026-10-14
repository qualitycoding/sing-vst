#!/usr/bin/env bash
# Spike (C-047, C-048): RVC 81eed5e training resume and inference-weight output. Usage: bash verify.sh <empty dir> > output.txt
set -euo pipefail
W=${1:?dir}; C=81eed5e8f68b6bed1789f682fe78cdd324495afc
git init -q "$W/rvc"; cd "$W/rvc"; git remote add origin https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git
git fetch -q --depth 1 origin "$C"; git checkout -q FETCH_HEAD; echo "== commit $(git rev-parse HEAD)"
echo "== resume: train.py loads the newest D_*/G_*.pth from model_dir, else falls back to the pretrained models"
grep -n 'latest_checkpoint_path(hps.model_dir' train/train.py
grep -n 'except Exception:  #' train/train.py
grep -n 'def latest_checkpoint_path' -A4 train/utils.py
echo "== checkpoints written every save_every_epoch; if_latest=1 overwrites G_2333333.pth / D_2333333.pth"
grep -n 'epoch % hps.save_every_epoch == 0\|format(2333333)\|format(global_step)' train/train.py
echo "== inference weights: savee() writes assets/weights/<name>.pth with half-precision weights and these keys"
grep -n 'ckpt\[key\].half()\|opt\["config"\]\|opt\["sr"\]\|opt\["f0"\]\|opt\["version"\]\|torch.save(opt, "assets/weights/%s.pth" % name)' train/process_ckpt.py
grep -n 'savee(' train/train.py
