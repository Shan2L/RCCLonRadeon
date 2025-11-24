import argparse
import subprocess
import os
from typing import Dict
from datetime import datetime
import shutil


class Logger:

    def __init__(self, path: str):
        self.path = path
        os.makedirs(path, exist_ok=True)
        self.logfile = open(os.path.join(self.path, "log.txt"), "a")

    def log(self, message: str, level: str="info") -> None:
        if level == "info":
            msg = f"{time_str} [INFO] {message}"
        elif level == "warning":
            msg = f"{time_str} [WARN] {message}"
        elif level == "error":
            msg = f"[ERROR] {message}"
        else:
            msg = f"{time_str} [{level.upper()}] {message}"
        print(msg)
        
        self.logfile.write(msg + "\n")
    
    def __del__(self):
        self.logfile.close()


def print_args(args):
    print("================== Arguments ======================= ")
    max_key_length = max(len(str(key)) for key in vars(args).keys())
    for key, value in vars(args).items():
        print(f"{str(key):<{max_key_length}} : {value}")
    print("==================================================== ")
    

def run_bash_command(command: list[str], timeout: int=600, cwd=None, env: Dict = None, shell:bool = False) -> Dict:
    
    logger.log(f"Running command: {' '.join(command)}, with env: {env}")
    ret = subprocess.run(command, capture_output=True, text=True, shell=shell, timeout=timeout, cwd=cwd if cwd else None, env=env if env!=None else None)
    if ret.returncode != 0:
        logger.log(ret.stderr, level="error")
        raise KeyError("Bash command return error")
    else:
        logger.log(ret.stdout)
        return ret


def init_submodules():
    run_bash_command(["git", "submodule", "sync"])
    run_bash_command(["git", "submodule", "update", "--init"])
    logger.log("Git submodules initialized successfully.")


def install_mpi():
    if not os.path.exists(os.path.join(cwd, "mpich-4.3.1.tar.gz")):
        run_bash_command(["wget", "https://www.mpich.org/static/downloads/4.3.1/mpich-4.3.1.tar.gz"])
    if not os.path.exists(os.path.join(cwd, "mpich-4.3.1")):
        run_bash_command(["tar", "-xzvf", "mpich-4.3.1.tar.gz"])
    run_bash_command(["./configure", "--prefix=/usr/local/mpi"], cwd=os.path.join(cwd, "mpich-4.3.1"))
    run_bash_command(["make", "-j", "128"], cwd=os.path.join(cwd, "mpich-4.3.1"))
    run_bash_command(["make", "install"], cwd=os.path.join(cwd, "mpich-4.3.1"))
    logger.log("MPI has been installed to /usr/local/mpi successfully.")
    

def get_patch_list(patch_list_str: str) -> list[str]:
    return [f"{patch_id}.patch" for patch_id in patch_list_str.split(",")] if patch_list_str else []


def main(args):
    init_submodules()

    # build rccl
    if args.build_rccl:
        if os.path.exists(os.path.join(rccl_path, "build")):
            shutil.rmtree(os.path.join(rccl_path, "build"))
            logger.log(f"Removed existing rccl build directory: {os.path.join(rccl_path, 'build')}")


        run_bash_command(["git", "checkout", "."], cwd=os.path.join(cwd, rccl_path))
        patch_list = get_patch_list(args.patch_list)
        if len(patch_list) > 0:
            print("Checking patch files...")
            for patch in patch_list:
                patch_file = os.path.join(patch_dir, patch)
                if os.path.exists(patch_file):
                    logger.log(f"Found patch file: {patch_file}")
                    run_bash_command(["git", "apply", patch_file], cwd=os.path.join(cwd, rccl_path))
                    logger.log(f"Applied patch file: {patch_file}")
                    
                else:
                    logger.log(f"Patch file not found: {patch_file}", level="error")

        logger.log("Start building RCCL")
        if os.path.exists(args.prefix):
            shutil.rmtree(args.prefix, )
            logger.log(f"Removed existing installation directory: {args.prefix}")
        rccl_build_command = ["./install.sh", f"--prefix={args.prefix}", "--install", "-j 128"]
        if args.debug:
            rccl_build_command.append("--debug")
        if args.amdgpu_targets:
            rccl_build_command.append(f"--amdgpu_targets='{args.amdgpu_targets}'")
            
        run_bash_command(rccl_build_command, cwd=rccl_path, timeout=6000)
        logger.log("RCCL build successfully.")


        # cp .so to archive dir
        run_bash_command(["cp", os.path.join(args.prefix, 'lib/librccl.so.1.0'), archive_dir])
        logger.log(f"librccl.so has been copied to {archive_dir}.")

    # build rccl-tests
    if args.build_rccl_tests:
        if os.path.exists(os.path.join(rccltests_path, "build")):
            shutil.rmtree(os.path.join(rccltests_path, "build"))
            logger.log(f"Removed existing rccl-tests build directory: {os.path.join(rccltests_path, 'build')}")

        build_tests_command = ["make"]
        if args.build_tests_with_MPI:
            build_tests_command.append("MPI=1")
            build_tests_command.append("MPI_HOME=/usr/local/mpi")
            build_tests_command.append(f"RCCL_HOME={args.prefix}")
            if not os.path.exists("/usr/local/mpi"):
                install_mpi()

        build_tests_command.extend(["-j", "32"])

        envs = os.environ
        ld_library_path  = envs.get("LD_LIBRARY_PATH", "")
        envs['GPU_TARGETS'] = args.amdgpu_targets
        envs["LD_LIBRARY_PATH"] = f"{args.prefix}/lib:" + ld_library_path
        run_bash_command(build_tests_command, cwd=rccltests_path, timeout=600, env=envs.copy())
        logger.log("Rccl-tests built successfully.")

if __name__ == "__main__":

    now = datetime.now()
    cwd = os.getcwd()
    time_str = now.strftime("%Y-%m-%d-%H_%M_%S")  # 2025-11-21-4_30_45

    args = argparse.ArgumentParser(description="Build RCCL library for Radeon GPUs")
    args.add_argument("--patch_list", type=str, 
                      help="A comma-spereated list of patches to apply, like 01,02,03")
    args.add_argument("--prefix", type=str, 
                      help="Installation prefix", default=f"{cwd}/install")
    args.add_argument("--debug", action="store_true", 
                      help="Build RCCL with debug symbols")
    args.add_argument("--build_rccl", action="store_true", help="Build RCCL library")
    args.add_argument("--build_rccl_tests", action="store_true", help="Build RCCL tests")
    args.add_argument("--build_tests_with_MPI", action="store_true", help="Build RCCL tests with MPI support")
    args.add_argument("--log_dir", type=str, help="Path to store build logs", default=os.getcwd()+"/logs")
    args.add_argument("--archive_dir", type=str, help="Path to store build archives", default=os.getcwd()+"/archives")
    args.add_argument("--amdgpu_targets", type=str, help="Target amdgpu architectures, like gfx1100;gfx1201")
    args.add_argument("--scp_passwd", type=str, help="passwd for scp files")

    args = args.parse_args()

    print_args(args)

    log_dir = os.path.join(args.log_dir, time_str)
    patch_dir = os.path.join(cwd, "patches")
    archive_dir = os.path.join(args.archive_dir, time_str)
    rccl_path = os.path.join(cwd, "3rd_party/rccl")
    rccltests_path = os.path.join(cwd, "3rd_party/rccl-tests")
    os.makedirs(archive_dir, exist_ok=True)

    global logger  # global
    logger = Logger(log_dir)
    
    main(args)
