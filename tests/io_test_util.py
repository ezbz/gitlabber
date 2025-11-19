import os
import sys
import subprocess
from contextlib import contextmanager
from io import StringIO
from typing import List, Optional


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

def execute(args: List[str], timeout: Optional[int] = None) -> str:
    """
    Execute gitlabber command with given arguments
    
    Args:
        args: List of command line arguments
        timeout: Optional timeout in seconds
        
    Returns:
        Command output as string
    """
    cmd = [sys.executable, "-m", "gitlabber"] + args
    env = os.environ.copy()
    
    # Print the command being executed
    print(f"Executing command: {' '.join(cmd)}")
    
    print(f"Using interpreter: {sys.executable}")
    
    result = subprocess.run(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        text=True
    )
    
    # Print stderr if the command failed
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        print(f"STDERR: {result.stderr}")
        
    return result.stdout