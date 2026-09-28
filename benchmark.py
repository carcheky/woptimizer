import sys
import os
import time
import io
import psutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.abspath("src"))

def run_benchmark():
    t0 = time.perf_counter()
    from woptimizer.services.process_service import ProcessService
    from woptimizer.services.pack_service import PackService
    from woptimizer.services.gaming_service import GamingService
    t_import = (time.perf_counter() - t0) * 1000

    ps = ProcessService()
    pack_s = PackService()
    gs = GamingService(ps, pack_s)

    t1 = time.perf_counter()
    procs = ps.get_running_processes()
    t_scan = (time.perf_counter() - t1) * 1000

    current_proc = psutil.Process(os.getpid())
    ram_mb = current_proc.memory_info().rss / (1024 * 1024)

    print("=== BENCHMARK WOPTIMIZER ===")
    print(f"Tiempo de Import/Init:   {t_import:.2f} ms")
    print(f"Tiempo de Escaneo:       {t_scan:.2f} ms ({len(procs)} procesos analizados)")
    print(f"Consumo de RAM (RSS):    {ram_mb:.2f} MB")
    print("============================")
    
    return {
        "import_ms": round(t_import, 2),
        "scan_ms": round(t_scan, 2),
        "procs_count": len(procs),
        "ram_mb": round(ram_mb, 2)
    }

if __name__ == "__main__":
    run_benchmark()
