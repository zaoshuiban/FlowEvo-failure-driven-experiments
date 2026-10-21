# 本地 Linux 部署与真实验收方案

当前主机为 Apple Silicon macOS，未安装 Docker、Colima、Lima、Podman 或 QEMU，检查时可用磁盘约 4.2 GiB。本轮未下载虚拟机镜像，未安装运行时，未执行任何候选源码。下面是可执行部署方案，不是部署通过的记录。建议先将可用磁盘提高到至少 10 GiB，给镜像、虚拟磁盘和结果留出余量；这是本项目预留建议，不是供应商的硬性最低要求。

选用本地 Colima + Docker Linux VM。安装后按官方文档创建独立 VM，建议 2 CPU、2 GiB 内存、20 GiB 虚拟磁盘上限。Colima 的安装与 Docker runtime 使用见 [官方仓库](https://github.com/abiosoft/colima)。实际执行前应核对本机 CLI 支持的参数。

```sh
brew install colima docker
colima start --cpu 2 --memory 2 --disk 20

docker info --format '{{.OSType}}'
docker pull python:3.11-slim
FLOWEVO_IMAGE_ID=$(docker image inspect python:3.11-slim --format '{{.Id}}')
python3 scripts/accept_s12_worker.py --image "$FLOWEVO_IMAGE_ID" --output smoke-results/s12-worker-new.json
```

拉取镜像是部署步骤，须保存实际 Image ID 和 RepoDigest。测试 Worker 仅接受不可变 sha256 Image ID，并禁止运行时自动拉取；初始 Python tag 不能代替最终冻结的镜像身份。不得传入其他项目的镜像或带密钥的自定义镜像。

Worker 只挂载候选源码和已固定的 candidate_worker.py，均只读；不挂载项目目录、评分器、注册表、Docker socket 或密钥。请求通过 stdin 传输，参考答案留在宿主比较器。使用本地 Unix socket Docker endpoint，不连接远程 daemon。

容器设置：无外部网络、只读根文件系统、非 root UID 65534、drop ALL capabilities、no-new-privileges、默认 seccomp、32 个进程上限、256 MiB 内存及相同 swap 上限、1 CPU、32 MiB 临时目录、32 MiB 文件大小上限、64 个文件描述符。父进程提供墙钟超时和强制清理。参考 [Docker 资源与权限文档](https://docs.docker.com/engine/containers/run/) 和 [默认 seccomp 文档](https://docs.docker.com/engine/security/seccomp/)。这些配置是否在本地真实生效，必须以测试结果为准。

真实 probe 包括正常结果、异常分类、无限循环、宿主文件不可见、凭据环境缺席、源码不可写、外部网络不可达、不可提权、进程命名空间、pids/memory cgroup 配置与实际大内存申请失败。全部通过后还要用已审查工程正反例测试完整评价器的合约、伪造验证、非目标拒绝、宿主公开检查及异常回退。

当前 worker_acceptance_final.json 为 BLOCKED，不能拿历史 sandbox_acceptance.json 或 120 项单元测试替代本轮真实验收。
