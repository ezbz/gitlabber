import os
import sys
import subprocess
import sys
from contextlib import contextmanager
from io import StringIO


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

def execute(args, timeout=3):
    cmd = [sys.executable, '-m', 'gitlabber']
    cmd.extend(args)
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, env=os.environ.copy()) as process:
        outs, err = process.communicate(timeout=timeout)    
        process.wait()
        return outs.decode('utf-8')