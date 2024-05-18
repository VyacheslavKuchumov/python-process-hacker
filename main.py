try:
    import psutil
except:
    import os
    os.system("pip install psutil")
    import psutil

try:
    import GPUtil
except:
    import os
    os.system("pip install GPUtil")
    import GPUtil

import time

try:
    from pynvml import (
        nvmlInit, nvmlShutdown, nvmlDeviceGetHandleByIndex, 
        nvmlDeviceGetGraphicsRunningProcesses, nvmlDeviceGetUtilizationRates
    )
except:
    import os
    os.system("pip install pynvml")
    from pynvml import (
        nvmlInit, nvmlShutdown, nvmlDeviceGetHandleByIndex, 
        nvmlDeviceGetGraphicsRunningProcesses, nvmlDeviceGetUtilizationRates
    )

def get_process_info(process: psutil.Process):
    try:
        full_path = process.exe()
        cpu_usage = process.cpu_percent(interval=0.1) / psutil.cpu_count()
        ram_usage = process.memory_info().rss / (1024 * 1024)  # in MB
        return full_path, cpu_usage, ram_usage
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None, None, None

def calculate_cpu_usage(start_cpu_times, end_cpu_times, interval, num_cpus):
    user_time = end_cpu_times.user - start_cpu_times.user
    system_time = end_cpu_times.system - start_cpu_times.system
    total_time = user_time + system_time
    return (total_time / (interval * num_cpus)) * 100

def get_gpu_usage_by_process(pid):
    try:
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            handle = nvmlDeviceGetHandleByIndex(gpu.id)
            processes = nvmlDeviceGetGraphicsRunningProcesses(handle)
            for process in processes:
                if process.pid == pid:
                    utilization = nvmlDeviceGetUtilizationRates(handle)
                    return utilization.gpu  # GPU utilization in percentage
        return 0.0
    except:
        pass

def get_system_info():
    nvmlInit()
    cpu_usage = psutil.cpu_percent(interval=1.0)
    ram_usage = psutil.virtual_memory().percent
    overall_gpu_usage = 0.0
    gpus = GPUtil.getGPUs()
    if gpus:
        for gpu in gpus:
            handle = nvmlDeviceGetHandleByIndex(gpu.id)
            overall_gpu_usage += nvmlDeviceGetUtilizationRates(handle).gpu
        overall_gpu_usage /= len(gpus)  # Average GPU usage across all GPUs
    nvmlShutdown()
    return cpu_usage, ram_usage, overall_gpu_usage

def main():
    while True:
        process_info_list = []
        
        cpu_usage = psutil.cpu_percent(interval=1.0)

        if cpu_usage < 30:
            time.sleep(300)
            continue
        
        print("CPU Usage is greater than 30%!")
        print("CPU Usage:", cpu_usage)

        try:
            nvmlInit()
        except:
            pass
        # Iterate over all running processes
        for process in psutil.process_iter(attrs=['pid', 'name']):
            pid = process.info['pid']
            process_name = process.info['name']
            full_path, cpu_usage, ram_usage = get_process_info(process)
            gpu_usage = get_gpu_usage_by_process(pid)
            if full_path is not None:
                process_info_list.append({
                    'pid': pid,
                    'name': process_name,
                    'full_path': full_path,
                    'cpu_usage': cpu_usage,
                    'ram_usage': ram_usage,
                    'gpu_usage': gpu_usage
                })
        
        try:
            nvmlShutdown()
        except:
            pass

        # Get system information
        system_cpu_usage, system_ram_usage, system_gpu_usage = get_system_info()
        print(f"Overall CPU Usage: {system_cpu_usage}%")
        print(f"Overall RAM Usage: {system_ram_usage}%")
        if system_gpu_usage is not None:
            print(f"Overall GPU Usage: {system_gpu_usage}%")
        else:
            print("No GPU found or GPU usage information is not available.")

        import pandas as pd
        data = pd.DataFrame(process_info_list)
        print(data.sort_values(by="cpu_usage", ascending=False))

if __name__ == "__main__":
    main()
