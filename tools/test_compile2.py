import os
import subprocess
import tempfile

MSC_ROOT = r"C:\Users\yotam\projects\falcon3\dos_compilers\msc5.1"
SRC_DIR = r"C:\Users\yotam\projects\falcon3\src"
OBJ_DIR = r"C:\Users\yotam\projects\falcon3\obj"

def compile_c(source_name, source_code, flags="/c /Os /Gs"):
    """Compile a C file using MSC 5.1 under DOSBox-X"""
    # Write source to src directory
    src_file = f"{source_name}.c"
    src_path = os.path.join(SRC_DIR, src_file)
    with open(src_path, "w") as f:
        f.write(source_code)
    
    obj_name = f"{source_name}.obj"
    cod_name = f"{source_name}.cod"
    
    config_content = f"""[sdl]
fullscreen=false
[dosbox]
machine=svga_s3
memsize=16
[cpu]
core=normal
cputype=386
cycles=max
[mixer]
nosound=true
[autoexec]
mount c {MSC_ROOT.replace('\\', '\\\\')}
mount d {SRC_DIR.replace('\\', '\\\\')}
mount e {OBJ_DIR.replace('\\', '\\\\')}
c:
path c:\\rbin;c:\\rbinb
set INCLUDE=c:\\include
set LIB=c:\\lib
set PATH=c:\\rbin;c:\\rbinb
d:
rbin\\cl /c /Gs /Fc{source_name} /Ic:\\include {source_name}.c > compile.log
e:
copy d:\\{source_name}.obj e:\\{source_name}.obj
exit
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "dosbox.conf")
        with open(config_path, "w") as f:
            f.write(config_content)
        
        cmd = [
            r"C:\dosbox-x\dosbox-x.exe",
            "-conf", os.path.join(tmpdir, "dosbox.conf"),
            "-exit"
        ]
        
        print("Running DOSBox-X...")
        result = subprocess.run(
            [r"C:\dosbox-x\dosbox-x.exe", "-conf", os.path.join(tmpdir, "dosbox.conf"), "-exit"],
            capture_output=True, text=True, timeout=120, cwd=SRC_DIR
        )
        
        print("returncode:", result.returncode)
        if result.stdout:
            print("stdout:", result.stdout[-500:])
        if result.stderr:
            print("stderr:", result.stderr[-500:])
        
        # Check for .cod file
        cod_path = os.path.join(SRC_DIR, f"{source_name}.cod")
        if os.path.exists(cod_path):
            print(f"SUCCESS: {source_name}.cod created")
            with open(os.path.join(SRC_DIR, f"{source_name}.cod"), "r") as f:
                print(f.read())
            return True
        else:
            print(f"FAILED: {source_name}.cod not created")
            # Check compile.log
            log_path = os.path.join(os.getcwd(), "compile.log")
            if os.path.exists("compile.log"):
                with open("compile.log", "r") as f:
                    print(f.read())
            return False

if __name__ == "__main__":
    # Test with a simple function
    c_code = """
int get_answer() {
    return 42;
}
"""
    success = compile_c("getans", c_code)
    if success:
        print("Compilation successful!")
    else:
        print("Compilation failed!")