# (10a) Memory and disk check before training (PK-43).
def _resources():
    global BATCH_SIZE
    rc, out = sh("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits", "/")
    _need(rc, "nvidia-smi", out)
    gpu_name, mem_mib = [x.strip() for x in out.strip().splitlines()[0].split(",")]
    gpu_gib = int(mem_mib) / 1024.0
    ram_gib = int(next(l for l in open("/proc/meminfo") if l.startswith("MemTotal")).split()[1]) / 1048576.0
    free_gib = shutil.disk_usage(ROOT).free / 2 ** 30
    raw_gib = sum(f.stat().st_size for f in Path(RAW).rglob("*") if f.is_file()) / 2 ** 30
    print(f"GPU {gpu_name} {gpu_gib:.1f} GiB; RAM {ram_gib:.1f} GiB; free on {ROOT}: {free_gib:.1f} GiB; recordings {raw_gib:.2f} GiB")
    BATCH_SIZE = 8 if gpu_gib >= 14 else 4
    print(f"batch size {BATCH_SIZE}")
    if ram_gib < 10:
        raise OwnerAction("10a", "less than 10 GiB RAM: choose a High-RAM runtime and run again")
    need = (3 * raw_gib + 8) * (2 if PLATFORM == "kaggle" else 1)
    if free_gib < need:
        if PLATFORM == "kaggle":
            raise OwnerAction("10a", f"only {free_gib:.1f} GiB free, {need:.1f} needed: switch to Colab (`switch-platform`)")
        raise OwnerAction("10a", f"only {free_gib:.1f} GiB free, {need:.1f} needed: free Drive space; the largest deletable items are earlier runs' logs/<exp>/ folders")


guarded("10a", _resources)
