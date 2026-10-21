import os,socket
assert not os.path.exists("/opt/flowevo-benchmark-20261019/.deepseek-key")
assert not any("KEY" in k or "PASSWORD" in k for k in os.environ)
s=socket.socket();s.settimeout(1)
try:
 s.connect(("1.1.1.1",443))
 raise AssertionError("network accessible")
except OSError:
 pass
print("isolated")
