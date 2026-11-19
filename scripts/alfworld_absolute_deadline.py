"""Small main-thread absolute deadline around the existing HTTP transport.
Partial response bytes are persisted; no automatic resend or provider cancellation claim.
"""
import signal,time,os
from contextlib import contextmanager
from pathlib import Path
from failure_evo.network_transport import _connection

@contextmanager
def absolute_deadline(seconds):
    def expire(signum,frame):raise TimeoutError('ABSOLUTE_REQUEST_DEADLINE')
    previous=signal.getsignal(signal.SIGALRM)
    if signal.getitimer(signal.ITIMER_REAL)[0]:raise RuntimeError('nested absolute deadline')
    signal.signal(signal.SIGALRM,expire);signal.setitimer(signal.ITIMER_REAL,seconds)
    try:yield
    finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)

class Capture:
    def __init__(self,response,path):self.response=response;self.status=response.status;self.path=Path(path)
    def read(self,limit):
        data=bytearray()
        with self.path.open('xb') as out:
            while len(data)<limit:
                block=self.response.read1(min(65536,limit-len(data)))
                if not block:break
                data.extend(block);out.write(block);out.flush();os.fsync(out.fileno())
        return bytes(data)

def capturing_factory(folder):
    def factory(policy,timeout):
        c=_connection(policy,timeout);original=c.getresponse
        def response():return Capture(original(),Path(folder)/'received_body.partial')
        c.getresponse=response
        return c
    return factory
