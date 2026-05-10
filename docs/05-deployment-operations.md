# 部署与运维规范

> **文档编号**: OPL-DEP-05  
> **版本**: 1.0  
> **最后更新**: 2026-05-10  
> **部署模式**: On-Premise / Systemd 原生进程部署（生产环境不使用容器）

---

## 目录

1. [部署架构概述](#1-部署架构概述)
2. [服务器硬件规格](#2-服务器硬件规格)
3. [各组件部署详细说明](#3-各组件部署详细说明)
4. [监控体系](#4-监控体系)
5. [备份与恢复](#5-备份与恢复)
6. [系统初始化清单](#6-系统初始化清单)
7. [CI/CD 流程](#7-cicd-流程)

---

## 1. 部署架构概述

### 1.1 系统组件图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        内网 (192.168.1.0/24)                        │
│                                                                       │
│  ┌──────────┐    ┌──────────────────────────────────────────────┐    │
│  │  客户端   │    │              LIMS 应用服务器                   │    │
│  │  桌面端   │───▶│  8C16G / Ubuntu 22.04 LTS / 500GB SSD       │    │
│  │ Electron │    │                                              │    │
│  └──────────┘    │  ┌─────────┐                                 │    │
│                  │  │  Nginx  │◀── HTTPS :443 (反向代理)         │    │
│  ┌──────────┐    │  │ :80/443 │                                 │    │
│  │  浏览器   │───▶│  └────┬────┘                                 │    │
│  │  Web SPA  │    │       │ 转发内部请求                           │    │
│  └──────────┘    │       ▼                                       │    │
│                  │  ┌──────────────┐   ┌──────────────────────┐   │    │
│                  │  │  Gunicorn +  │   │   Celery Worker       │   │    │
│                  │  │  Uvicorn     │──▶│   (异步任务处理)       │   │    │
│                  │  │  :8000(内部) │   │   Redis Broker/Bus    │   │    │
│                  │  └──────┬───────┘   └───────┬──────────────┘   │    │
│                  │         │                    │                   │    │
│                  │         ▼                    ▼                   │    │
│                  │  ┌──────────────┐   ┌──────────────────────┐   │    │
│                  │  │   FastAPI    │   │   Celery Beat         │   │    │
│                  │  │   应用逻辑    │──▶│   (定时任务调度)       │   │    │
│                  │  └──────┬───────┘   └──────────────────────┘   │    │
│                  │         │                                       │    │
│                  │     ┌───┴─────────┬──────────┐                 │    │
│                  │     ▼             ▼          ▼                 │    │
│                  │  ┌──────┐  ┌─────────┐  ┌─────────┐          │    │
│                  │  │PostgreSQL│ │ Redis   │  │ MinIO   │          │    │
│                  │  │ :5432  │  │ :6379   │  │ :9000   │          │    │
│                  │  ├──────┤  ├─────────┤  ├─────────┤          │    │
│                  │  │ 数据  │  │ 缓存/队列│  │ 对象存储 │          │    │
│                  │  │ 库   │  │         │  │         │          │    │
│                  │  └──────┘  └─────────┘  └─────────┘          │    │
│                  └──────────────────────────────────────────────┘    │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                    监控与日志基础设施                          │    │
│  │  Node Exporter  │  PostgreSQL Exporter  │  Filebeat          │    │
│  │  Prometheus(内置)│  Redis Exporter       │  MinIO Exporter    │    │
│  └──────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流向图

```
                    外部请求流                     内部数据流
                    ──────────                     ──────────

  浏览器/客户端 ──HTTPS──▶ Nginx ──Proxy──▶ Gunicorn ──▶ FastAPI
                                                          │
                                            ┌─────────────┼─────────────┐
                                            ▼             ▼             ▼
                                      ┌─────────┐  ┌─────────┐  ┌─────────┐
                                      │PostgreSQL│  │ Redis   │  │ MinIO   │
                                      │  读写    │  │ 缓存/锁 │  │ I/O     │
                                      └─────────┘  └────┬────┘  └─────────┘
                                                         │
                                        异步任务 enqueue │
                                                         ▼
                                                  ┌─────────────┐
                                                  │ Celery Broker│
                                                  │   (Redis)    │
                                                  └──────┬──────┘
                                                         │
                                                         ▼
                                                  ┌─────────────┐
                                                  │Celery Worker│
                                                  │  仪器数据采集 │
                                                  │  报告生成     │
                                                  │  数据归档     │
                                                  └─────────────┘

                    指标采集流                     日志采集流
                    ──────────                     ──────────

  ┌─────────┐ ┌─────────┐ ┌─────────┐      ┌─────────┐  ┌─────────┐
 │Node Exp. │ │PG Exp.  │ │RedisExp │      │Filebeat │──│Logstash │
  └────┬────┘ └────┬────┘ └────┬────┘      └────┬────┘  └────┬────┘
       ▼            ▼           ▼                 ▼           ▼
  ┌─────────────────────┐                 ┌─────────────────────┐
  │     Prometheus       │                 │   Elasticsearch     │
  │    (时序指标存储)     │                 │    (日志全文索引)    │
  └─────────┬───────────┘                 └─────────┬───────────┘
            ▼                                        ▼
  ┌─────────────────────┐                 ┌─────────────────────┐
  │       Grafana       │                 │       Kibana        │
  │    (仪表板可视化)     │                 │   (日志搜索与告警)   │
  └─────────────────────┘                 └─────────────────────┘
```

### 1.3 进程依赖顺序

系统启动必须遵循以下顺序, 确保下游组件就绪后上游才启动:

```
1. PostgreSQL  ──▶  2. Redis  ──▶  3. MinIO  ──▶  4. 后端 Gunicorn
                                                       │
                    ┌──────────────────────────────────┤
                    ▼                                  ▼
                5. Celery Beat                      6. Celery Worker
                                                       │
                    ┌──────────────────────────────────┘
                    │
                    ▼
                7. Nginx (前端 SPA + API 代理)
```

各 systemd unit 通过 `After=` 和 `Requires=` 指令保证此顺序, 详见下文各小节.

---

## 2. 服务器硬件规格

### 2.1 推荐配置

| 项目 | 规格 |
|---|---|
| CPU | 8 核 (推荐 Intel Xeon E-2300 系列或 AMD EPYC 7003 系列) |
| 内存 | 16 GB DDR4 ECC |
| 系统盘 | 500 GB NVMe SSD (推荐 Samsung 980 PRO / Intel DC P4510) |
| 网卡 | 双千兆以太网 (内网/管理网分离) |
| 操作系统 | Ubuntu 22.04 LTS (64-bit, 最小化安装) |
| 文件系统 | ext4 (系统分区), 数据盘可单独 LVM 挂载至 `/data` |

### 2.2 各组件资源分配

| 组件 | 内存上限 | CPU 配额 (systemd) | 磁盘占用 (估算) |
|---|---|---|---|
| **PostgreSQL 16** | 4 GB (shared_buffers 1GB + OS 缓存) | 25% (2C) | WAL + 数据: ~50GB 起步 |
| **Redis 7** | 512 MB | 6.25% (0.5C) | AOF + RDB: ~1GB |
| **Gunicorn + Uvicorn** | 4 GB | 37.5% (3C) | 代码 + venv: ~2GB |
| **MinIO** | 2 GB | 12.5% (1C) | 对象数据 + WAL: ~100GB 起步 |
| **Celery Worker** | 2 GB | 25% (2C) | 临时文件: ~5GB |
| **Nginx** | 256 MB | 6.25% (0.5C) | 日志 + 静态文件: ~5GB |
| **操作系统与监控** | ≈4 GB (预留) | 剩余配额 | 系统 + 日志 + 监控: ~30GB |
| **总计** | **16 GB** | **8C** | **~200GB (含裕量)** |

> **注意**: 内存上限通过 systemd `MemoryMax=` 控制, 防止单个组件 OOM 影响全局. CPU 配额通过 `CPUQuota=` 软限制, 允许空闲时段借用.

### 2.3 网络拓扑与防火墙策略

#### 2.3.1 内网分区

```
┌────────────────────────────────────────────────────────────┐
│                    DMZ (可选, 对外网暴露)                    │
│  Nginx :443 (HTTPS)                                       │
└───────────────────┬────────────────────────────────────────┘
                    │ iptables FORWARD (仅允许 443 入站)
┌───────────────────▼────────────────────────────────────────┐
│                    应用层 (App Zone)                         │
│  Nginx → Gunicorn(:8000) → Celery                          │
│  内部回环通信, 不对外暴露                                    │
└───────────────────┬────────────────────────────────────────┘
                    │ iptables FORWARD (仅允许应用层访问)
┌───────────────────▼────────────────────────────────────────┐
│                    数据层 (Data Zone)                        │
│  PostgreSQL(:5432), Redis(:6379), MinIO(:9000, :9001)     │
│  仅监听 127.0.0.1, 不绑定公网                              │
└────────────────────────────────────────────────────────────┘
```

#### 2.3.2 防火墙规则 (ufw / iptables)

```
# 入站规则
ufw default deny incoming
ufw allow 22/tcp       # SSH (建议限内网 IP)
ufw allow 443/tcp      # HTTPS
ufw allow 9001/tcp     # MinIO Console (限内网)

# 禁止外部直接访问数据端口
ufw deny 5432/tcp      # PostgreSQL (仅 localhost)
ufw deny 6379/tcp      # Redis (仅 localhost)
ufw deny 9000/tcp      # MinIO API (仅 localhost/应用层)

# 出站: 默认允许
ufw default allow outgoing
```

所有数据层服务绑定地址统一设置为 `127.0.0.1`, 从网络层面杜绝越权访问.

---

## 3. 各组件部署详细说明

### 3.1 PostgreSQL 16

#### 3.1.1 安装

```bash
# 添加官方 APT 源
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.sh
sudo apt update
sudo apt install -y postgresql-16 postgresql-client-16
```

#### 3.1.2 postgresql.conf 关键配置

编辑 `/etc/postgresql/16/main/postgresql.conf`:

```ini
# ── 连接 ──
listen_addresses = 'localhost'
port = 5432
max_connections = 40                # Gunicorn workers + Celery + 管理连接

# ── 内存 (总内存 16GB, 分配 4GB 给 PG) ──
shared_buffers = 1GB                # 建议为总内存的 1/4 ~ 1/8
effective_cache_size = 6GB           # OS 缓存 + shared_buffers (总内存的 ~3/4)
work_mem = 32MB                      # 每连接排序/哈希内存 (max_connections * work_mem 不得超可用内存)
maintenance_work_mem = 512MB         # VACUUM / CREATE INDEX 时可用
huge_pages = try

# ── WAL 与检查点 ──
wal_level = replica                  # 支持 PITR 恢复
max_wal_size = 2GB
min_wal_size = 512MB
checkpoint_completion_target = 0.9

# ── 日志 ──
log_destination = 'stderr'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-16-%Y%m%d.log'
log_min_duration_statement = 500     # 记录执行超过 500ms 的 SQL
log_statement = 'ddl'                # 记录 DDL 操作
log_line_prefix = '%m [%p] %q%u@%d ' # 时间戳 PID 用户 数据库
log_timezone = 'Asia/Shanghai'

# ── 时区 ──
timezone = 'Asia/Shanghai'

# ── 性能 ──
random_page_cost = 1.1               # SSD 优化 (HDD 默认 4.0)
effective_io_concurrency = 200       # SSD 优化
default_statistics_target = 100
```

#### 3.1.3 pg_hba.conf 配置

编辑 `/etc/postgresql/16/main/pg_hba.conf`:

```ini
# TYPE  DATABASE        USER            ADDRESS                 METHOD
# 本地管理连接
local   all             postgres                                peer
local   all             all                                     peer

# IPv4 本地连接 (应用通过 localhost 访问)
host    all             lims_db_user    127.0.0.1/32            scram-sha-256

# 禁止远程直连 (仅允许本机)
# 如需从其他服务器访问, 在此添加精确 IP
```

#### 3.1.4 systemd unit 文件

PostgreSQL 16 的官方包已自带 `/lib/systemd/system/postgresql@.service`, 无需手动创建. 确认启用:

```bash
sudo systemctl enable postgresql@16-main
sudo systemctl start postgresql@16-main
```

#### 3.1.5 初始化脚本

创建脚本 `/opt/lims/scripts/init-database.sh`:

```bash
#!/bin/bash
set -euo pipefail

DB_NAME="lims_production"
DB_USER="lims_db_user"
DB_PASSWORD="${LIMS_DB_PASSWORD:-$(openssl rand -base64 24)}"

echo "→ 创建数据库用户..."
sudo -u postgres psql <<EOF
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE ROLE ${DB_USER} WITH LOGIN PASSWORD '${DB_PASSWORD}';
  END IF;
END
\$\$;

CREATE DATABASE ${DB_NAME} WITH OWNER ${DB_USER} ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8' TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
EOF

echo "→ 数据库初始化完成"
echo "→ 请将以下凭据写入 /opt/lims/.env:"
echo "  DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@127.0.0.1:5432/${DB_NAME}"

# 将密码写入安全文件 (仅 root 可读)
echo "${DB_PASSWORD}" > /opt/lims/.db_password
chmod 600 /opt/lims/.db_password
```

执行初始化:

```bash
sudo chmod +x /opt/lims/scripts/init-database.sh
sudo LIMS_DB_PASSWORD='YourSecurePassword' /opt/lims/scripts/init-database.sh
```

---

### 3.2 Redis 7

#### 3.2.1 安装

```bash
sudo add-apt-repository -y ppa:redislabs/redis
sudo apt update
sudo apt install -y redis-server
```

#### 3.2.2 redis.conf 配置

编辑 `/etc/redis/redis.conf`:

```ini
# ── 网络 ──
bind 127.0.0.1
port 6379
protected-mode yes
tcp-backlog 511
timeout 300                              # 客户端空闲超时 (秒)
tcp-keepalive 60

# ── 安全 ──
requirepass ${REDIS_PASSWORD}             # 替换为强密码
rename-command FLUSHDB ""                 # 禁用危险命令
rename-command FLUSHALL ""
rename-command DEBUG ""

# ── 内存 ──
maxmemory 512mb
maxmemory-policy allkeys-lru              # LRU 淘汰策略 (缓存场景)
# 若用作 Celery broker 且不丢弃任务:
# maxmemory-policy noeviction

# ── 持久化 ──
save 900 1                                # 900s 内至少 1 次写入则 RDB
save 300 10
save 60 10000

appendonly yes                            # 启用 AOF
appendfilename "appendonly.aof"
appendfsync everysec                      # 每秒 fsync (性能与可靠性权衡)
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# ── 日志 ──
loglevel notice
logfile /var/log/redis/redis-server.log
# syslog-enabled yes
# syslog-ident redis

# ── 慢查询日志 ──
slowlog-log-slower-than 10000             # 10ms 以上记录
slowlog-max-len 128

# ── 惰性删除与内存碎片整理 ──
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
activedefrag yes
```

#### 3.2.3 systemd unit

官方包自带 `/lib/systemd/system/redis-server.service`, 确认配置:

```bash
sudo systemctl enable redis-server
sudo systemctl restart redis-server

# 验证
redis-cli -a ${REDIS_PASSWORD} ping
```

---

### 3.3 MinIO

#### 3.3.1 二进制部署

```bash
# 下载 MinIO 服务器
sudo curl -Lo /usr/local/bin/minio https://dl.min.io/server/minio/release/linux-amd64/minio
sudo chmod +x /usr/local/bin/minio

# 下载 MinIO 客户端 (mc)
sudo curl -Lo /usr/local/bin/mc https://dl.min.io/client/mc/release/linux-amd64/mc
sudo chmod +x /usr/local/bin/mc

# 创建数据目录
sudo mkdir -p /data/minio
sudo chown minio-user:minio-user /data/minio
```

#### 3.3.2 创建独立用户

```bash
sudo useradd -r -s /sbin/nologin -M minio-user
sudo mkdir -p /etc/minio
```

#### 3.3.3 systemd unit 文件

创建 `/etc/systemd/system/minio.service`:

```ini
[Unit]
Description=MinIO Object Storage
Documentation=https://docs.min.io
Wants=network-online.target
After=network-online.target

AssertFileIsExecutable=/usr/local/bin/minio

[Service]
WorkingDirectory=/data/minio

User=minio-user
Group=minio-user

EnvironmentFile=-/etc/default/minio

ExecStartPre=/bin/bash -c 'if [ -z "${MINIO_ROOT_USER}" ]; then echo "MINIO_ROOT_USER not set"; exit 1; fi'

ExecStart=/usr/local/bin/minio server \
  /data/minio \
  --console-address ":9001" \
  --address ":9000" \
  --certs-dir /etc/minio/certs

Restart=always
RestartSec=5
LimitNOFILE=1048576
LimitNPROC=65536
TimeoutStopSec=infinity
SendSIGKILL=no

# 资源限制
MemoryMax=2G
CPUQuota=150%

# 安全
ProtectSystem=full
PrivateTmp=yes
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
```

环境变量文件 `/etc/default/minio`:

```bash
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=YourMinioSecurePassword123!
MINIO_VOLUMES="/data/minio"
MINIO_OPTS="--console-address :9001"
# 可选: 启用 TLS
# MINIO_CERTS_DIR="/etc/minio/certs"
```

#### 3.3.4 桶配置与访问策略

启用后通过 mc 初始化桶:

```bash
# 配置 mc 别名
mc alias set limio http://127.0.0.1:9000 minioadmin YourMinioSecurePassword123!

# 创建桶
mc mb limio/raw-data          # 原始仪器数据 (不可变, 合规留存)
mc mb limio/reports           # 检测报告 (PDF/Excel)
mc mb limio/attachments       # 附件文件 (图片, 签名等)
mc mb limio/backups           # 数据库导出备份

# 设置对象锁定 (raw-data 桶用于合规保存, WORM)
mc version enable limio/raw-data
mc object-lock enable limio/raw-data

# 设置生命周期策略 (reports 桶: 1 年后转 IA 存储, 3 年后删除)
mc ilm add --expiry-days 1095 limio/reports
mc ilm add --transition-days 365 --storage-class STANDARD_IA limio/reports

# 设置桶策略 (应用通过 IAM 角色访问, 不公开)
# 所有桶默认禁止公共读写
```

#### 3.3.5 服务管理

```bash
sudo systemctl daemon-reload
sudo systemctl enable minio
sudo systemctl start minio
sudo systemctl status minio
```

---

### 3.4 后端 (FastAPI + Gunicorn + UvicornWorker)

#### 3.4.1 Python 环境与 virtualenv

```bash
# 系统依赖
sudo apt install -y python3.11 python3.11-venv python3.11-dev build-essential libpq-dev

# 创建应用目录
sudo mkdir -p /opt/lims
sudo useradd -r -s /sbin/nologin lims

# 创建虚拟环境
sudo python3.11 -m venv /opt/lims/venv
sudo chown -R lims:lims /opt/lims

# 进入虚拟环境并安装依赖
source /opt/lims/venv/bin/activate
pip install --upgrade pip

# 安装项目依赖 (根据实际 requirements.txt)
pip install fastapi uvicorn gunicorn uvicorn[standard] \
  asyncpg sqlalchemy alembic pydantic pydantic-settings \
  celery redis python-multipart httpx \
  prometheus-client python-json-logger

# 部署应用代码
cp -r /path/to/lims-backend /opt/lims/app
```

#### 3.4.2 gunicorn.conf.py

创建 `/opt/lims/gunicorn.conf.py`:

```python
import multiprocessing
import os

# ── 服务器绑定 ──
bind = "127.0.0.1:8000"
backlog = 2048

# ── Worker 配置 ──
worker_class = "uvicorn.workers.UvicornWorker"
workers = multiprocessing.cpu_count() * 2 + 1  # 8C → 17 workers (可按需手动下调)
# 建议在生产环境设置固定值, 避免启动波动
workers = int(os.environ.get("GUNICORN_WORKERS", 4))
threads = 2

# ── 超时与保持 ──
timeout = 120                  # 请求超时 (秒)
graceful_timeout = 30          # 优雅重启等待
keepalive = 5

# ── 预加载 ──
preload_app = True             # 共享内存, 减少 worker 内存占用

# ── 日志 ──
accesslog = "/var/log/lims/gunicorn-access.log"
errorlog = "/var/log/lims/gunicorn-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s %(L)s'

# ── 进程名 ──
proc_name = "lims-backend"
pidfile = "/run/lims/gunicorn.pid"

# ── Worker 临时目录 ──
worker_tmp_dir = "/dev/shm"    # 使用 tmpfs, 避免慢盘影响 heartbeat

# ── Hook 函数 ──
def on_starting(server):
    """服务启动前: 确保运行目录存在"""
    os.makedirs("/run/lims", exist_ok=True)
    os.makedirs("/var/log/lims", exist_ok=True)

def post_fork(server, worker):
    """Worker fork 后: 记录 PID"""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def worker_int(worker):
    """收到 SIGINT: 清理资源"""
    worker.log.info("worker received INT or QUIT signal")
```

> **注意**: `workers = 4` 是 8C16G 下的保守值, 每个 UvicornWorker 约 200-300MB 内存. 若内存充足可调至 6-8.

#### 3.4.3 systemd unit 文件

创建 `/etc/systemd/system/lims-backend.service`:

```ini
[Unit]
Description=LIMS Backend API (FastAPI + Gunicorn)
Documentation=https://docs.example.com/lims
After=network.target postgresql@16-main.service redis-server.service minio.service
Requires=postgresql@16-main.service redis-server.service minio.service

[Service]
Type=notify
User=lims
Group=lims
WorkingDirectory=/opt/lims/app
EnvironmentFile=/opt/lims/.env

ExecStart=/opt/lims/venv/bin/gunicorn \
  -c /opt/lims/gunicorn.conf.py \
  lims.main:app

ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID

Restart=always
RestartSec=10

# 运行时目录
RuntimeDirectory=lims
RuntimeDirectoryMode=0755

# 日志目录
LogsDirectory=lims
LogsDirectoryMode=0755

# 资源限制
MemoryMax=4G
CPUQuota=300%

# 安全加固
ProtectSystem=strict
ReadWritePaths=/var/log/lims /run/lims /opt/lims/app
PrivateTmp=yes
NoNewPrivileges=yes
ProtectHome=yes

# 环境变量路径
Environment="PATH=/opt/lims/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"

[Install]
WantedBy=multi-user.target
```

#### 3.4.4 .env 环境变量模板

创建 `/opt/lims/.env` (权限 600, 仅 lims 用户可读):

```bash
# ── 数据库 ──
DATABASE_URL=postgresql+asyncpg://lims_db_user:PASSWORD@127.0.0.1:5432/lims_production

# ── Redis ──
REDIS_URL=redis://:PASSWORD@127.0.0.1:6379/0

# ── Celery ──
CELERY_BROKER_URL=redis://:PASSWORD@127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://:PASSWORD@127.0.0.1:6379/2

# ── MinIO ──
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=YourMinioSecurePassword123!
MINIO_SECURE=false

# ── 应用 ──
SECRET_KEY=your-super-secret-key-change-in-production
ENVIRONMENT=production
LOG_LEVEL=info
ENABLE_METRICS=true

# ── Gunicorn ──
GUNICORN_WORKERS=4

# ── 认证 ──
JWT_SECRET_KEY=your-jwt-secret-key-change
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
```

```bash
chmod 600 /opt/lims/.env
chown lims:lims /opt/lims/.env
```

---

### 3.5 Celery Worker

#### 3.5.1 systemd unit 文件

创建 `/etc/systemd/system/lims-celery.service`:

```ini
[Unit]
Description=LIMS Celery Worker (异步任务处理)
Documentation=https://docs.example.com/lims
After=network.target redis-server.service lims-backend.service
Requires=redis-server.service

[Service]
Type=simple
User=lims
Group=lims
WorkingDirectory=/opt/lims/app
EnvironmentFile=/opt/lims/.env

ExecStart=/opt/lims/venv/bin/celery \
  --app=lims.celery_app.celery \
  worker \
  --loglevel=info \
  --concurrency=4 \
  --pool=prefork \
  --logfile=/var/log/lims/celery-worker.log \
  --pidfile=/run/lims/celery-worker.pid \
  --max-tasks-per-child=1000

ExecStop=/bin/kill -s TERM $MAINPID

Restart=always
RestartSec=10
StartLimitBurst=5
StartLimitIntervalSec=300

# 资源限制
MemoryMax=2G
CPUQuota=200%

# 安全
ProtectSystem=strict
ReadWritePaths=/var/log/lims /run/lims /data/minio/raw-data
PrivateTmp=yes
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
```

> **参数说明**:
> - `--concurrency=4`: 并发进程数, 建议与分配给 Celery 的 CPU 核数一致
> - `--pool=prefork`: 多进程池, 适合 CPU 密集型任务 (数据解析、报告生成). 若以 I/O 密集型为主可改为 `--pool=gevent`
> - `--max-tasks-per-child=1000`: 每 worker 处理 1000 个任务后重启, 防止内存泄漏

#### 3.5.2 Celery 配置

创建 `/opt/lims/app/lims/celery_config.py`:

```python
from datetime import timedelta

# ── Broker 与 Backend ──
broker_url = "redis://:PASSWORD@127.0.0.1:6379/1"
result_backend = "redis://:PASSWORD@127.0.0.1:6379/2"

# ── 序列化 ──
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

# ── 时区 ──
timezone = "Asia/Shanghai"
enable_utc = True

# ── 任务执行 ──
task_acks_late = True                  # 任务完成后才 ACK, 防止 worker 崩溃时任务丢失
task_reject_on_worker_lost = True     # Worker 断开时拒绝任务, 等待重新入队
worker_prefetch_multiplier = 1         # 每次只预取 1 个任务, 避免长任务阻塞

# ── 重试 ──
task_default_retry_delay = 60          # 默认重试间隔 (秒)
task_max_retries = 5                   # 最大重试次数
task_acks_on_failure_or_timeout = False  # 失败任务不自动 ACK, 允许重试

# ── 超时 ──
task_soft_time_limit = 600             # 软超时: 10 分钟后抛出 SoftTimeLimitExceeded
task_time_limit = 900                  # 硬超时: 15 分钟后强制终止

# ── 结果过期 ──
result_expires = 86400                 # 24 小时后清理结果

# ── 速率限制 (防止仪器接口被压垮) ──
task_annotations = {
    "lims.tasks.instrument_collect": {"rate_limit": "10/m"},
    "lims.tasks.report_generate": {"rate_limit": "5/m"},
}
```

---

### 3.6 Celery Beat (定时任务)

#### 3.6.1 systemd unit 文件

创建 `/etc/systemd/system/lims-celerybeat.service`:

```ini
[Unit]
Description=LIMS Celery Beat (定时任务调度器)
Documentation=https://docs.example.com/lims
After=network.target redis-server.service
Requires=redis-server.service

[Service]
Type=simple
User=lims
Group=lims
WorkingDirectory=/opt/lims/app
EnvironmentFile=/opt/lims/.env

ExecStart=/opt/lims/venv/bin/celery \
  --app=lims.celery_app.celery \
  beat \
  --loglevel=info \
  --logfile=/var/log/lims/celery-beat.log \
  --pidfile=/run/lims/celery-beat.pid \
  --scheduler celery.beat:PersistentScheduler

ExecStop=/bin/kill -s TERM $MAINPID

Restart=always
RestartSec=10

# 资源限制
MemoryMax=256M
CPUQuota=25%

# 安全
ProtectSystem=strict
ReadWritePaths=/var/log/lims /run/lims /opt/lims/app
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

#### 3.6.2 定时任务清单

任务定义在 Beat 调度配置中 (也可通过 Django-Celery-Beat / 数据库动态配置):

```python
# lims/celery_beat_schedule.py
from datetime import timedelta

beat_schedule = {
    # ── 校准到期预警: 每天 08:00 ──
    "calibration-expiry-alert": {
        "task": "lims.tasks.calibration.check_expiry",
        "schedule": timedelta(days=1),
        "options": {"expires": 3600},
    },

    # ── 数据归档: 每周日 02:00 ──
    "weekly-data-archive": {
        "task": "lims.tasks.data.archive_completed",
        "schedule": timedelta(weeks=1),
        "options": {"expires": 7200},
    },

    # ── 数据库备份: 每日 03:00 ──
    "daily-backup": {
        "task": "lims.tasks.backup.run_full_backup",
        "schedule": timedelta(days=1),
        "options": {"expires": 3600},
    },

    # ── 统计报告: 每月 1 日 06:00 ──
    "monthly-statistics": {
        "task": "lims.tasks.statistics.generate_monthly_report",
        "schedule": timedelta(days=30),
        "options": {"expires": 7200},
    },

    # ── 过期数据清理: 每月 15 日 04:00 ──
    "monthly-cleanup": {
        "task": "lims.tasks.cleanup.remove_expired_records",
        "schedule": timedelta(days=30),
        "options": {"expires": 7200},
    },

    # ── 健康检查心跳: 每 5 分钟 ──
    "health-check-heartbeat": {
        "task": "lims.tasks.health.check_services",
        "schedule": timedelta(minutes=5),
        "options": {"expires": 600},
    },
}
```

**任务清单说明**:

| 任务名 | 调度频率 | 用途 | 执行时长估算 |
|---|---|---|---|
| calibration-expiry-alert | 每日 08:00 | 扫描即将到期的仪器校准记录, 发送预警 | < 30s |
| weekly-data-archive | 每周日 02:00 | 将已完成超过 90 天的检测数据归档至 MinIA | 5-15min |
| daily-backup | 每日 03:00 | pg_dump 全量备份 + MinIO 同步 | 10-30min |
| monthly-statistics | 每月 1 日 06:00 | 汇总生成月度统计报告 (样品量、合格率等) | 2-5min |
| monthly-cleanup | 每月 15 日 04:00 | 清理过期的临时文件和会话数据 | 1-3min |
| health-check-heartbeat | 每 5 分钟 | 检查所有依赖服务连通性 | < 5s |

---

### 3.7 Nginx (前端 SPA + API 反向代理)

#### 3.7.1 安装

```bash
sudo apt install -y nginx
```

#### 3.7.2 nginx.conf 完整配置

创建 `/etc/nginx/sites-available/lims`:

```nginx
# ── 上游后端 ──
upstream lims_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# ── HTTP → HTTPS 重定向 ──
server {
    listen 80;
    server_name lims.example.com;

    # Let's Encrypt ACME 挑战路径 (不重定向)
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# ── HTTPS 主服务 ──
server {
    listen 443 ssl http2;
    server_name lims.example.com;

    # ── SSL 证书 ──
    ssl_certificate /etc/letsencrypt/live/lims.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lims.example.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/lims.example.com/chain.pem;

    # SSL 优化配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    # 安全头
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self';" always;

    # ── 日志 ──
    access_log /var/log/nginx/lims-access.log combined;
    error_log /var/log/nginx/lims-error.log warn;

    # ── 前端 SPA 静态文件 ──
    root /opt/lims/frontend/dist;
    index index.html;

    # ── Gzip 压缩 ──
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_min_length 256;
    gzip_types
        text/plain
        text/css
        text/javascript
        application/json
        application/javascript
        application/x-javascript
        application/xml
        application/xml+rss
        image/svg+xml
        font/truetype
        font/opentype;

    # ── 静态文件缓存 ──
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location /favicon.ico {
        expires 30d;
        add_header Cache-Control "public, no-transform";
        access_log off;
    }

    # ── SPA 路由: 所有非 API 请求返回 index.html ──
    location / {
        try_files $uri $uri/ /index.html;

        # HTML 文件不缓存
        location = /index.html {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            expires 0;
        }
    }

    # ── API 反向代理 ──
    location /api/ {
        proxy_pass http://lims_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        # 超时与缓冲
        proxy_connect_timeout 10s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;

        # 大文件上传支持 (如附件上传)
        client_max_body_size 100M;
    }

    # ── WebSocket 代理 (实时通知) ──
    location /ws/ {
        proxy_pass http://lims_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400s;  # 保持长连接
    }

    # ── Prometheus Metrics (限内网访问) ──
    location /metrics {
        proxy_pass http://lims_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # 仅允许内网或 Prometheus 服务器
        allow 127.0.0.1;
        allow 192.168.1.0/24;
        deny all;
    }

    # ── 健康检查端点 ──
    location /health {
        proxy_pass http://lims_backend;
        proxy_set_header Host $host;
        access_log off;
    }

    # ── 禁止访问隐藏文件 ──
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

#### 3.7.3 启用站点与 SSL 证书

```bash
# 启用站点
sudo ln -sf /etc/nginx/sites-available/lims /etc/nginx/sites-enabled/lims
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 申请 Let's Encrypt 证书 (若内网部署, 使用自签名证书)
# sudo apt install -y certbot python3-certbot-nginx
# sudo certbot --nginx -d lims.example.com

# 或使用自签名证书 (内网无 DNS 场景)
# sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
#   -keyout /etc/ssl/private/lims.key \
#   -out /etc/ssl/certs/lims.crt \
#   -subj "/CN=lims.example.com"

# 重载 Nginx
sudo systemctl reload nginx
```

---

### 3.8 Electron 桌面端

#### 3.8.1 打包配置 (electron-builder)

`electron-builder.json`:

```json
{
  "appId": "com.lims.desktop",
  "productName": "LIMS 桌面客户端",
  "copyright": "Copyright © 2026",
  "directories": {
    "output": "release"
  },
  "files": [
    "dist/**/*",
    "main/**/*",
    "node_modules/**/*",
    "package.json"
  ],
  "extraResources": [
    {
      "from": "resources/serial-drivers",
      "to": "serial-drivers",
      "filter": ["**/*"]
    }
  ],
  "linux": {
    "target": [
      {
        "target": "AppImage",
        "arch": ["x86_64"]
      },
      {
        "target": "deb",
        "arch": ["x86_64"]
      }
    ],
    "category": "Utility",
    "icon": "build/icons",
    "desktop": {
      "Name": "LIMS 桌面客户端",
      "Comment": "实验室信息管理系统桌面客户端",
      "Terminal": false,
      "Type": "Application",
      "Categories": "Utility;"
    }
  },
  "win": {
    "target": [
      {
        "target": "nsis",
        "arch": ["x64"]
      }
    ],
    "icon": "build/icons/icon.ico",
    "requestedExecutionLevel": "asInvoker"
  },
  "nsis": {
    "oneClick": false,
    "perMachine": true,
    "allowToChangeInstallationDirectory": true,
    "createDesktopShortcut": true,
    "createStartMenuShortcut": true,
    "shortcutName": "LIMS 客户端"
  },
  "publish": {
    "provider": "generic",
    "url": "http://192.168.1.100:8080/updates",
    "channel": "latest"
  }
}
```

#### 3.8.2 自动更新 (连接本地服务器)

主进程中配置:

```typescript
import { autoUpdater } from "electron-updater";

// 生产环境连接内网更新服务器
autoUpdater.setFeedURL({
  provider: "generic",
  url: "http://192.168.1.100:8080/updates",
});

autoUpdater.autoDownload = true;
autoUpdater.autoInstallOnAppQuit = true;

// 检查更新 (静默, 每 2 小时一次)
setInterval(() => {
  autoUpdater.checkForUpdatesAndNotify();
}, 2 * 60 * 60 * 1000);

// 事件监听
autoUpdater.on("update-available", (info) => {
  console.log("更新可用:", info.version);
});

autoUpdater.on("update-downloaded", () => {
  autoUpdater.quitAndInstall();
});
```

更新服务器 (Nginx 静态目录):

```nginx
# /etc/nginx/conf.d/lims-updates.conf
server {
    listen 8080;
    server_name 127.0.0.1;

    location /updates/ {
        alias /opt/lims/updates/;
        autoindex on;
        add_header Cache-Control "no-cache";
        add_header Access-Control-Allow-Origin "*";
    }
}
```

#### 3.8.3 串口权限处理 (node-serialport)

Linux 端串口设备 (天平、仪器接口) 需要 `dialout` 组权限:

```bash
# 创建规则, 允许 lims 用户使用串口
sudo usermod -aG dialout $USER

# udev 规则 (固定设备权限)
sudo tee /etc/udev/rules.d/99-lims-serial.rules <<'EOF'
# 天平 USB-Serial 适配器
SUBSYSTEM=="tty", ATTRS{idVendor}=="067b", ATTRS{idProduct}=="2303", GROUP="dialout", MODE="0660", SYMLINK+="lims/analytical-balance"
# 仪器 RS485 接口
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", GROUP="dialout", MODE="0660", SYMLINK+="lims/instrument-rs485"
EOF

# 重载 udev
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Electron 打包时包含 serialport 原生模块:

```json
{
  "build": {
    "npmRebuild": true,
    "nodeGypRebuild": true,
    "nativeRebuilder": "prebuild-install"
  }
}
```

#### 3.8.4 Windows/Linux 差异化打包

构建脚本 `package.json`:

```json
{
  "scripts": {
    "build:linux": "electron-builder --linux",
    "build:win": "electron-builder --win",
    "build:all": "electron-builder --linux --win"
  }
}
```

Windows 端串口使用 `node-serialport` 的预编译二进制, 注意:
- Windows 需要安装 VC++ Redistributable
- 串口端口名格式为 `COM1`, `COM2` 等 (Linux 为 `/dev/ttyUSB0`)
- 建议在主进程中检测平台, 动态生成可用端口列表:

```typescript
import { SerialPort } from "serialport";

function listAvailablePorts(): Promise<string[]> {
  return SerialPort.list().then((ports) => {
    if (process.platform === "win32") {
      // Windows: 过滤 COM 端口
      return ports
        .filter((p) => p.path.startsWith("COM"))
        .map((p) => p.path);
    }
    // Linux: 过滤 ttyUSB/ttyACM
    return ports
      .filter((p) => p.path.match(/^\/dev\/tty(USB|ACM)/))
      .map((p) => p.path);
  });
}
```

---

## 4. 监控体系

### 4.1 Prometheus 指标采集

#### 4.1.1 Prometheus Server 安装

```bash
# 创建用户
sudo useradd --no-create-home --shell /bin/false prometheus
sudo mkdir -p /etc/prometheus /var/lib/prometheus
sudo chown prometheus:prometheus /etc/prometheus /var/lib/prometheus

# 下载二进制
wget https://github.com/prometheus/prometheus/releases/download/v2.51.0/prometheus-2.51.0.linux-amd64.tar.gz
tar xzf prometheus-2.51.0.linux-amd64.tar.gz
sudo cp prometheus-2.51.0.linux-amd64/prometheus /usr/local/bin/
sudo cp prometheus-2.51.0.linux-amd64/promtool /usr/local/bin/
sudo chown prometheus:prometheus /usr/local/bin/prometheus /usr/local/bin/promtool

# 配置文件
sudo tee /etc/prometheus/prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # ── 节点指标 ──
  - job_name: "node"
    static_configs:
      - targets: ["localhost:9100"]

  # ── PostgreSQL ──
  - job_name: "postgresql"
    static_configs:
      - targets: ["localhost:9187"]

  # ── Redis ──
  - job_name: "redis"
    static_configs:
      - targets: ["localhost:9121"]

  # ── MinIO ──
  - job_name: "minio"
    metrics_path: /minio/v2/metrics/cluster
    static_configs:
      - targets: ["localhost:9000"]

  # ── LIMS 后端应用指标 ──
  - job_name: "lims-backend"
    metrics_path: /metrics
    static_configs:
      - targets: ["localhost:8000"]
    scrape_interval: 10s
EOF

sudo chown prometheus:prometheus /etc/prometheus/prometheus.yml
```

#### 4.1.2 后端 Metrics 端点

在 FastAPI 中集成 prometheus-client:

```python
# lims/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.requests import Request
from starlette.responses import Response
import time

# ── 自定义业务指标 ──
samples_created_total = Counter(
    "lims_samples_created_total",
    "Total number of samples created",
    ["sample_type"]
)

tests_completed_total = Counter(
    "lims_tests_completed_total",
    "Total number of tests completed",
    ["test_type", "status"]  # status: pass / fail / pending
)

celery_tasks_active = Gauge(
    "lims_celery_tasks_active",
    "Number of active Celery tasks",
    ["task_name"]
)

celery_tasks_timed_out_total = Counter(
    "lims_celery_tasks_timed_out_total",
    "Total number of Celery tasks that timed out",
    ["task_name"]
)

instrument_connections = Gauge(
    "lims_instrument_connections",
    "Number of active instrument connections",
    ["instrument_type"]
)

report_generation_duration = Histogram(
    "lims_report_generation_duration_seconds",
    "Report generation time in seconds",
    ["report_type"],
    buckets=[0.5, 1, 2, 5, 10, 30, 60]
)

api_request_duration = Histogram(
    "lims_api_request_duration_seconds",
    "API request duration",
    ["method", "endpoint", "status_code"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10]
)

# ── Metrics 端点 ──
async def metrics_endpoint(request: Request):
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

注册到 FastAPI:

```python
# lims/main.py
from fastapi import FastAPI
from lims.metrics import metrics_endpoint

app = FastAPI()
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])
```

#### 4.1.3 Exporters 安装

**Node Exporter** (系统指标):

```bash
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xzf node_exporter-1.7.0.linux-amd64.tar.gz
sudo cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
```

systemd unit `/etc/systemd/system/node-exporter.service`:

```ini
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
User=prometheus
Group=prometheus
ExecStart=/usr/local/bin/node_exporter \
  --collector.textfile.directory=/var/lib/prometheus/node-textfile
Restart=always

[Install]
WantedBy=multi-user.target
```

**PostgreSQL Exporter**:

```bash
wget https://github.com/prometheus-community/postgres_exporter/releases/download/v0.15.0/postgres_exporter-0.15.0.linux-amd64.tar.gz
tar xzf postgres_exporter-0.15.0.linux-amd64.tar.gz
sudo cp postgres_exporter-0.15.0.linux-amd64/postgres_exporter /usr/local/bin/
```

systemd unit `/etc/systemd/system/postgres-exporter.service`:

```ini
[Unit]
Description=Prometheus PostgreSQL Exporter
After=postgresql@16-main.service

[Service]
User=prometheus
Group=prometheus
Environment=DATA_SOURCE_NAME="postgresql://lims_monitor:PASSWORD@127.0.0.1:5432/lims_production?sslmode=disable"
ExecStart=/usr/local/bin/postgres_exporter --web.listen-address=:9187
Restart=always

[Install]
WantedBy=multi-user.target
```

> 需在 PostgreSQL 中创建只读监控用户:
> ```sql
> CREATE ROLE lims_monitor WITH LOGIN PASSWORD 'PASSWORD';
> GRANT pg_monitor TO lims_monitor;
> GRANT CONNECT ON DATABASE lims_production TO lims_monitor;
> ```

**Redis Exporter**:

```bash
wget https://github.com/oliver006/redis_exporter/releases/download/v1.58.0/redis_exporter-v1.58.0.linux-amd64.tar.gz
tar xzf redis_exporter-v1.58.0.linux-amd64.tar.gz
sudo cp redis_exporter-v1.58.0.linux-amd64/redis_exporter /usr/local/bin/
```

systemd unit `/etc/systemd/system/redis-exporter.service`:

```ini
[Unit]
Description=Prometheus Redis Exporter
After=redis-server.service

[Service]
User=prometheus
Group=prometheus
ExecStart=/usr/local/bin/redis_exporter \
  --redis.addr=redis://127.0.0.1:6379 \
  --redis.password=REDIS_PASSWORD \
  --web.listen-address=:9121
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 4.1.4 Prometheus systemd unit

```ini
[Unit]
Description=Prometheus Server
Documentation=https://prometheus.io/docs/
After=network.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus/ \
  --storage.tsdb.retention.time=30d \
  --storage.tsdb.retention.size=10GB \
  --web.listen-address=0.0.0.0:9090 \
  --web.enable-lifecycle
Restart=always

# 资源限制
MemoryMax=1G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

### 4.2 Grafana 仪表板

#### 4.2.1 安装

```bash
sudo apt install -y apt-transport-https software-properties-common
wget -q -O - https://apt.grafana.com/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/grafana.gpg
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install -y grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

#### 4.2.2 仪表板规划

建议导入或创建以下仪表板:

| 仪表板名称 | Prometheus 查询示例 | 关键面板 |
|---|---|---|
| **系统资源总览** | `node_cpu_seconds_total`, `node_memory_*`, `node_disk_*`, `node_network_*` | CPU 使用率、内存使用、磁盘 IOPS、网络吞吐 |
| **PostgreSQL 性能** | `pg_stat_database_tup_fetched`, `pg_stat_activity_count`, `pg_stat_bgwriter_*` | 慢查询数、连接池使用率、QPS、缓存命中率 |
| **Redis 性能** | `redis_connected_clients`, `redis_memory_used_bytes`, `redis_commands_processed_total`, `redis_keyspace_hits_total` | 连接数、内存使用、命中率、命令延迟 |
| **LIMS 应用性能** | `lims_api_request_duration_seconds`, `lims_celery_tasks_active`, `lims_samples_created_total` | 请求 P99 延迟、错误率 (5xx%)、吞吐量 (RPS)、活跃任务 |
| **业务指标** | `lims_samples_created_total`, `lims_tests_completed_total`, `lims_celery_tasks_timed_out_total` | 日样品量、检测完成率、超时任务、仪器在线数 |
| **MinIO 存储** | `minio_disk_usage_bytes`, `minio_bucket_objects_total` | 存储用量、桶对象数、API 请求延迟 |
| **Celery 任务队列** | `celery_queue_length`, `celery_task_success_total`, `celery_task_runtime` | 队列堆积、任务成功/失败率、P95 执行时间 |

#### 4.2.3 业务指标查询示例

```promql
# 日样品量 (今日 00:00 至今)
increase(lims_samples_created_total[24h])

# 检测完成率 (过去 1 小时)
sum(rate(lims_tests_completed_total{status="pass"}[1h]))
/
sum(rate(lims_tests_completed_total[1h]))
* 100

# 超时任务告警
increase(lims_celery_tasks_timed_out_total[1h]) > 0

# API P99 延迟
histogram_quantile(0.99, sum(rate(lims_api_request_duration_seconds_bucket[5m])) by (le, endpoint))

# API 错误率
sum(rate(lims_api_request_duration_seconds_count{status_code=~"5.."}[5m]))
/
sum(rate(lims_api_request_duration_seconds_count[5m]))
* 100
```

#### 4.2.4 告警规则

`/etc/prometheus/alerts/lims_alerts.yml`:

```yaml
groups:
  - name: lims_alerts
    rules:
      # ── 系统 ──
      - alert: HighMemoryUsage
        expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100 < 15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率超过 85%"
          description: "当前可用内存: {{ $value | humanize }}%"

      - alert: DiskSpaceRunningLow
        expr: node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} * 100 < 10
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "磁盘可用空间低于 10%"

      # ── 数据库 ──
      - alert: PostgreSQLConnectionPoolExhausted
        expr: pg_stat_activity_count / pg_settings_max_connections * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL 连接池使用率超过 80%"

      - alert: SlowQueriesIncreasing
        expr: rate(pg_stat_database_tup_fetched[5m]) > 10000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL 慢查询持续增加"

      # ── 应用 ──
      - alert: HighErrorRate
        expr: sum(rate(lims_api_request_duration_seconds_count{status_code=~"5.."}[5m])) / sum(rate(lims_api_request_duration_seconds_count[5m])) * 100 > 5
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "API 错误率超过 5%"

      - alert: CeleryTaskTimeoutSpike
        expr: increase(lims_celery_tasks_timed_out_total[10m]) > 5
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "10 分钟内超过 5 个任务超时"

      # ── 备份 ──
      - alert: BackupNotCompleted
        expr: time() - lims_last_backup_timestamp > 172800
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "最近一次备份超过 48 小时"
```

### 4.3 ELK 日志

#### 4.3.1 日志格式规范 (JSON Structured Logging)

后端使用 `python-json-logger` 输出结构化日志:

```python
# lims/logging_config.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(message)s %(lineno)d %(process)d %(threadName)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    },
    "handlers": {
        "json_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/lims/app.log",
            "maxBytes": 100 * 1024 * 1024,  # 100MB
            "backupCount": 10,
            "formatter": "json",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["json_file"],
    },
}
```

日志输出示例:

```json
{
  "asctime": "2026-05-10T14:23:01+0800",
  "name": "lims.api.samples",
  "levelname": "INFO",
  "module": "samples",
  "funcName": "create_sample",
  "message": "Sample created successfully",
  "lineno": 42,
  "process": 12345,
  "threadName": "ThreadPoolExecutor-0_0",
  "sample_id": "SMP-2026-0510-0001",
  "sample_type": "raw_material",
  "user_id": "usr_8d7f6a",
  "request_id": "req_a1b2c3d4",
  "duration_ms": 128.5
}
```

**日志字段规范**:

| 字段 | 说明 | 必填 |
|---|---|---|
| `asctime` | ISO 8601 时间戳 (含时区) | 是 |
| `name` | Logger 名称 (模块路径) | 是 |
| `levelname` | 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL) | 是 |
| `message` | 日志消息 (英文, 动宾结构) | 是 |
| `module` / `funcName` | 代码位置 | 是 |
| `request_id` | 请求追踪 ID (Middleware 注入) | 是 |
| `user_id` | 操作用户 ID (业务操作必填) | 视场景 |
| `duration_ms` | 操作耗时 (毫秒) | 是 (接口/任务) |
| `error` | 异常堆栈 (ERROR 级别) | ERROR 时必填 |

#### 4.3.2 Filebeat 日志采集

安装 Filebeat:

```bash
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /etc/apt/keyrings/elastic.gpg
echo "deb [signed-by=/etc/apt/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt update
sudo apt install -y filebeat
```

配置 `/etc/filebeat/filebeat.yml`:

```yaml
filebeat.inputs:
  # ── 应用日志 ──
  - type: filestream
    id: lims-app-logs
    enabled: true
    paths:
      - /var/log/lims/app.log
    json.keys_under_root: true
    json.add_error_key: true
    json.message_key: message
    tags: ["lims", "application"]

  # ── Gunicorn 访问日志 ──
  - type: filestream
    id: gunicorn-access
    enabled: true
    paths:
      - /var/log/lims/gunicorn-access.log
    tags: ["lims", "gunicorn", "access"]

  # ── Gunicorn 错误日志 ──
  - type: filestream
    id: gunicorn-error
    enabled: true
    paths:
      - /var/log/lims/gunicorn-error.log
    tags: ["lims", "gunicorn", "error"]

  # ── Celery Worker 日志 ──
  - type: filestream
    id: celery-worker
    enabled: true
    paths:
      - /var/log/lims/celery-worker.log
    tags: ["lims", "celery", "worker"]

  # ── Celery Beat 日志 ──
  - type: filestream
    id: celery-beat
    enabled: true
    paths:
      - /var/log/lims/celery-beat.log
    tags: ["lims", "celery", "beat"]

  # ── Nginx 访问日志 ──
  - type: filestream
    id: nginx-access
    enabled: true
    paths:
      - /var/log/nginx/lims-access.log
    tags: ["nginx", "access"]

  # ── Nginx 错误日志 ──
  - type: filestream
    id: nginx-error
    enabled: true
    paths:
      - /var/log/nginx/lims-error.log
    tags: ["nginx", "error"]

  # ── PostgreSQL 慢查询日志 ──
  - type: filestream
    id: postgresql-slow
    enabled: true
    paths:
      - /var/log/postgresql/*.log
    tags: ["postgresql", "queries"]
    multiline.pattern: '^\d{4}-\d{2}-\d{2}'
    multiline.negate: true
    multiline.match: after

  # ── Redis 日志 ──
  - type: filestream
    id: redis-log
    enabled: true
    paths:
      - /var/log/redis/redis-server.log
    tags: ["redis"]

# ── 输出到 Logstash ──
output.logstash:
  hosts: ["127.0.0.1:5044"]

# ── 处理 ──
processors:
  - add_host_metadata:
      when.not.contains.tags: forwarded
  - add_cloud_metadata: ~
  - add_docker_metadata: ~
```

#### 4.3.3 Logstash 处理

`/etc/logstash/conf.d/lims.conf`:

```
input {
  beats {
    port => 5044
  }
}

filter {
  # ── 解析 Nginx 访问日志 ──
  if "nginx" in [tags] and "access" in [tags] {
    grok {
      match => { "message" => "%{COMBINEDAPACHELOG}" }
    }
    date {
      match => ["timestamp", "dd/MMM/yyyy:HH:mm:ss Z"]
    }
    geoip {
      source => "clientip"
      target => "geoip"
    }
  }

  # ── 解析 PostgreSQL 慢查询 ──
  if "postgresql" in [tags] {
    grok {
      match => { "message" => "%{NUMBER:duration_ms}ms" }
    }
    if [duration_ms] {
      mutate { convert => { "duration_ms" => "float" } }
    }
  }

  # ── 标记 LIMS 相关业务日志 ──
  if "lims" in [tags] {
    mutate {
      add_field => {
        "[@metadata][target_index]" => "lims-%{+YYYY.MM.dd}"
      }
    }
  } else if "nginx" in [tags] {
    mutate {
      add_field => {
        "[@metadata][target_index]" => "nginx-%{+YYYY.MM.dd}"
      }
    }
  } else if "postgresql" in [tags] {
    mutate {
      add_field => {
        "[@metadata][target_index]" => "postgresql-%{+YYYY.MM.dd}"
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["http://127.0.0.1:9200"]
    index => "%{[@metadata][target_index]}"
  }
}
```

#### 4.3.4 Elasticsearch 安装

```bash
sudo apt install -y elasticsearch
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch

# 验证
curl -X GET "localhost:9200/_cluster/health?pretty"
```

关键配置 `/etc/elasticsearch/elasticsearch.yml`:

```yaml
cluster.name: lims-logging
node.name: node-1
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
network.host: 127.0.0.1
http.port: 9200
discovery.type: single-node
xpack.security.enabled: true
```

#### 4.3.5 Kibana 配置

```bash
sudo apt install -y kibana
sudo systemctl enable kibana
sudo systemctl start kibana

# 通过 Nginx 反向代理, 仅内网访问
```

Kibana 建议配置:
- **Index Patterns**: `lims-*`, `nginx-*`, `postgresql-*`
- **Saved Dashboards**:
  - 日志检索 (按时间、级别、模块筛选)
  - 错误追踪 (按 `error.stack_trace` 分组)
  - 用户操作审计 (按 `user_id` 聚合)
- **Alerting**: ERROR 级别日志数量突增告警

#### 4.3.6 日志保留策略

```
# Elasticsearch ILM (Index Lifecycle Management)
PUT _ilm/policy/lims_logs
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": { "max_size": "10GB", "max_age": "7d" }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "shrink": { "number_of_shards": 1 },
          "readonly": {}
        }
      },
      "delete": {
        "min_age": "90d",
        "actions": { "delete": {} }
      }
    }
  }
}
```

日志保留 **90 天自动删除**. 合规需求可对接外部归档.

---

## 5. 备份与恢复

### 5.1 PostgreSQL 备份

#### 5.1.1 全量备份 (pg_dump)

```bash
#!/bin/bash
# /opt/lims/scripts/backup-postgres.sh
set -euo pipefail

BACKUP_DIR="/data/backups/postgresql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/lims_production_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=30

mkdir -p "${BACKUP_DIR}"

echo "[${TIMESTAMP}] 开始 PostgreSQL 全量备份..."

sudo -u postgres pg_dump \
  --format=custom \
  --compress=9 \
  --verbose \
  --file="${BACKUP_FILE}" \
  lims_production

# 验证备份文件完整性
if pg_restore --list "${BACKUP_FILE}" > /dev/null 2>&1; then
  echo "[${TIMESTAMP}] 备份验证通过: $(du -h "${BACKUP_FILE}" | cut -f1)"
else
  echo "[${TIMESTAMP}] 备份验证失败!" >&2
  exit 1
fi

# 清理超过保留天数的备份
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete
echo "[${TIMESTAMP}] 已清理 ${RETENTION_DAYS} 天前的备份"

# 同步到异地 (可选, 另一台服务器或 NFS 挂载点)
# rsync -avz "${BACKUP_FILE}" backup-server:/data/lims-backups/postgresql/
```

添加 cron 任务 (Celery Beat 定时任务触发):

```bash
# 每日 03:00 执行
0 3 * * * /opt/lims/scripts/backup-postgres.sh >> /var/log/lims/backup-postgres.log 2>&1
```

#### 5.1.2 WAL Archiving (PITR 支持)

`postgresql.conf`:

```ini
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /data/backups/postgresql/wal/%f && cp %p /data/backups/postgresql/wal/%f'
archive_timeout = 300                  # 5 分钟内强制切换 WAL 段
```

创建归档目录:

```bash
sudo mkdir -p /data/backups/postgresql/wal
sudo chown postgres:postgres /data/backups/postgresql/wal
sudo chmod 700 /data/backups/postgresql/wal
```

#### 5.1.3 WAL 清理脚本

```bash
#!/bin/bash
# /opt/lims/scripts/cleanup-wal.sh
# 清理超过 7 天的 WAL 文件

WAL_DIR="/data/backups/postgresql/wal"
RETENTION_DAYS=7

find "${WAL_DIR}" -type f -mtime +${RETENTION_DAYS} -delete
echo "[$(date)] WAL 文件已清理 (保留 ${RETENTION_DAYS} 天)"
```

### 5.2 MinIO 备份 (mc mirror)

```bash
#!/bin/bash
# /opt/lims/scripts/backup-minio.sh
set -euo pipefail

BACKUP_DIR="/data/backups/minio"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "[${TIMESTAMP}] 开始 MinIO 备份..."

# 配置 mc 别名 (若首次运行)
mc alias set local http://127.0.0.1:9000 minioadmin YourMinioSecurePassword123! 2>/dev/null || true
mc alias set backup file:///data/backups/minio/ 2>/dev/null || true

# 镜像同步所有桶
for bucket in raw-data reports attachments; do
  echo "→ 同步桶: ${bucket}"
  mc mirror --overwrite --remove \
    local/"${bucket}" \
    backup/"${bucket}" 2>&1 | tail -5
done

# 生成备份清单
BACKUP_LOG="${BACKUP_DIR}/_backup_log_${TIMESTAMP}.txt"
mc du --recursive backup/ > "${BACKUP_LOG}"
echo "[${TIMESTAMP}] 备份完成, 清单: ${BACKUP_LOG}"
```

### 5.3 备份策略

#### 5.3.1 备份类型与频率

| 备份类型 | 频率 | 内容 | 保留周期 | 存储位置 |
|---|---|---|---|---|
| PostgreSQL 全量 | 每日 03:00 | pg_dump custom 格式, 全库 | 30 天 | 本地 `/data/backups/postgresql/` |
| PostgreSQL WAL | 持续归档 | WAL 段文件 | 7 天 | 本地 `/data/backups/postgresql/wal/` |
| MinIO 对象 | 每日 03:30 | mc mirror 全量同步 | 永久 (镜像) | 本地 `/data/backups/minio/` |
| 配置文件 | 每次变更后 | /etc/nginx, /etc/systemd, /opt/lims/.env | 版本化 (Git) | Git 仓库 |

#### 5.3.2 异地备份 (推荐)

| 目标 | 方式 | 频率 |
|---|---|---|
| 备份服务器 (同机房) | rsync over SSH | 每日 05:00 |
| 外部存储 (不同机房) | MinIO replication 或 rclone sync | 每周一次 |
| 离线磁带/USB | 手动导出 | 每月一次 |

```bash
# rsync 异地备份
rsync -avz --delete \
  /data/backups/ \
  backup-user@192.168.2.100:/data/lims-backups/
```

#### 5.3.3 备份大小估算

| 组件 | 日增量 | 30 天总量 |
|---|---|---|
| PostgreSQL (pg_dump 压缩) | ~100MB | ~3GB |
| PostgreSQL WAL | ~50MB | ~1.5GB (7 天) |
| MinIO (raw-data) | 取决于样品量, ~500MB/天 | ~15GB |
| 总计 | ~650MB/天 | ~20GB |

### 5.4 恢复演练流程

#### 5.4.1 PostgreSQL 恢复

```bash
# ── 场景 1: 全量恢复 ──
# 1. 停止应用, 禁止写入
sudo systemctl stop lims-backend lims-celery lims-celerybeat

# 2. 删除现有数据库
sudo -u postgres psql -c "DROP DATABASE lims_production;"

# 3. 从最新备份恢复
LATEST=$(ls -t /data/backups/postgresql/lims_production_*.sql.gz | head -1)
sudo -u postgres pg_restore \
  --jobs=4 \
  --verbose \
  --dbname=lims_production \
  --create \
  "${LATEST}"

# 4. 恢复数据后重启应用
sudo systemctl start lims-backend lims-celery lims-celerybeat

# ── 场景 2: PITR (恢复到某一时间点) ──
# 1. 停止 PostgreSQL
sudo systemctl stop postgresql@16-main

# 2. 清空数据目录
sudo rm -rf /var/lib/postgresql/16/main/*

# 3. 从全量备份恢复基础
sudo -u postgres pg_restore \
  --dbname=lims_production \
  --create \
  /data/backups/postgresql/lims_production_20260509_030000.sql.gz

# 4. 配置恢复目标
sudo tee /var/lib/postgresql/16/main/recovery.signal <<EOF
restore_command = 'cp /data/backups/postgresql/wal/%f %p'
recovery_target_time = '2026-05-10 12:00:00+08'
recovery_target_action = promote
EOF

# 5. 启动 PostgreSQL 进入恢复模式
sudo systemctl start postgresql@16-main

# 6. 检查恢复结果, 然后重启应用
```

#### 5.4.2 MinIO 恢复

```bash
# 从异地备份恢复
mc mirror --overwrite backup-fileserver/lims-backups/minio/ local/

# 验证恢复
for bucket in raw-data reports attachments; do
  echo "桶: ${bucket}"
  mc ls local/"${bucket}" | wc -l
done
```

#### 5.4.3 恢复演练计划

| 演练项目 | 频率 | 负责人 | 验收标准 |
|---|---|---|---|
| PostgreSQL 全量恢复 | 每季度 | DBA / DevOps | 数据完整性校验通过, RTO < 30min |
| PITR 恢复 | 每半年 | DBA | 恢复至指定时间点, 数据无丢失, RTO < 60min |
| MinIO 对象恢复 | 每季度 | DevOps | 对象可正常访问, 校验和一致 |
| 全系统恢复 (灾难) | 每年 | IT 全体 | 从裸机恢复到业务可用, RTO < 4h |

> **RTO** (Recovery Time Objective): 恢复时间目标 < 4 小时  
> **RPO** (Recovery Point Objective): 恢复点目标 < 24 小时

---

## 6. 系统初始化清单

### 6.1 预置数据

#### 6.1.1 角色与权限矩阵

创建管理脚本 `/opt/lims/app/lims/scripts/seed_data.py`:

```python
"""系统初始化: 角色, 权限, 超级用户, 检测标准"""
from sqlalchemy.ext.asyncio import AsyncSession

ROLES = [
    {
        "name": "超级管理员",
        "code": "super_admin",
        "description": "系统最高权限, 管理所有功能与用户",
        "permissions": ["*"],  # 所有权限
    },
    {
        "name": "实验室主管",
        "code": "lab_manager",
        "description": "管理实验室日常运营, 审核报告",
        "permissions": [
            "samples:*",
            "tests:*",
            "reports:*",
            "instruments:*",
            "users:read",
            "users:update",
            "statistics:*",
        ],
    },
    {
        "name": "质检员",
        "code": "inspector",
        "description": "执行检测, 录入数据, 查看报告",
        "permissions": [
            "samples:read",
            "samples:update",
            "tests:create",
            "tests:read",
            "tests:update",
            "reports:read",
            "instruments:read",
        ],
    },
    {
        "name": "样品管理员",
        "code": "sample_manager",
        "description": "样品接收、登记、分发",
        "permissions": [
            "samples:*",
            "tests:read",
            "reports:read",
        ],
    },
    {
        "name": "报告审核员",
        "code": "report_reviewer",
        "description": "审核和签发检测报告",
        "permissions": [
            "samples:read",
            "tests:read",
            "reports:read",
            "reports:approve",
            "reports:sign",
        ],
    },
    {
        "name": "设备管理员",
        "code": "equipment_admin",
        "description": "仪器管理, 校准, 维护",
        "permissions": [
            "instruments:*",
            "calibrations:*",
            "samples:read",
        ],
    },
    {
        "name": "数据录入员",
        "code": "data_entry",
        "description": "检测结果录入",
        "permissions": [
            "samples:read",
            "tests:read",
            "tests:update",
        ],
    },
    {
        "name": "客户查看者",
        "code": "client_viewer",
        "description": "客户账号, 仅查看自己的样品和报告",
        "permissions": [
            "samples:read:self",
            "reports:read:self",
        ],
    },
    {
        "name": "质量管理员",
        "code": "quality_admin",
        "description": "质量体系管理, 审核跟踪, 偏差处理",
        "permissions": [
            "samples:read",
            "tests:read",
            "reports:read",
            "audits:*",
            "deviations:*",
            "statistics:*",
        ],
    },
    {
        "name": "只读查看者",
        "code": "readonly_viewer",
        "description": "全局只读, 不执行任何修改",
        "permissions": [
            "samples:read",
            "tests:read",
            "reports:read",
            "instruments:read",
            "statistics:read",
        ],
    },
]

SUPER_USER = {
    "username": "admin",
    "email": "admin@lims.example.com",
    "full_name": "系统管理员",
    "role_code": "super_admin",
    "is_active": True,
}

async def seed_database(db: AsyncSession):
    """执行种子数据插入"""
    # 插入角色
    for role_data in ROLES:
        existing = await db.execute(
            select(Role).where(Role.code == role_data["code"])
        )
        if not existing.scalar_one_or_none():
            role = Role(**role_data)
            db.add(role)

    # 创建超级用户
    existing = await db.execute(
        select(User).where(User.username == SUPER_USER["username"])
    )
    if not existing.scalar_one_or_none():
        user = User(
            username=SUPER_USER["username"],
            email=SUPER_USER["email"],
            full_name=SUPER_USER["full_name"],
            hashed_password=get_password_hash("Admin@2026!"),  # 首次登录必须修改
            role_code=SUPER_USER["role_code"],
            is_active=SUPER_USER["is_active"],
            must_change_password=True,
        )
        db.add(user)
    
    await db.commit()
```

执行:

```bash
cd /opt/lims/app
source /opt/lims/venv/bin/activate
python -m lims.scripts.seed_data
```

#### 6.1.2 检测标准初始数据

检测标准作为参考数据, 建议通过 SQL 或 CSV 导入:

```csv
standard_code,name,method,version,effective_date,status
GB/T 5009.1-2023,食品中铅含量测定,石墨炉原子吸收法,2023,2023-06-01,active
GB/T 5009.12-2017,食品中铅含量测定,ICP-MS法,2017,2017-10-01,active
ISO 17025-2017,检测和校准实验室能力,通用要求,2017,2019-02-01,active
GB/T 27404-2008,实验室质量控制规范,食品理化检测,2008,2008-10-01,active
```

### 6.2 数据库迁移 (Alembic)

```bash
cd /opt/lims/app
source /opt/lims/venv/bin/activate

# 运行所有迁移
alembic upgrade head

# 验证
alembic current
```

迁移目录结构:

```
/opt/lims/app/lims/alembic/
├── env.py
├── script.py.mako
├── versions/
│   ├── 001_initial_schema.py          # 初始表结构
│   ├── 002_add_roles_and_permissions.py
│   ├── 003_add_instruments.py
│   ├── 004_add_sample_workflow.py
│   └── ...
```

**迁移策略**:
- 每次部署前 `alembic upgrade head` 自动执行
- 回滚使用 `alembic downgrade -1`
- 所有迁移文件纳入版本控制, 不可修改已执行的迁移
- 大型数据迁移 (超过 10 万行) 拆分为独立脚本, 分批执行

### 6.3 健康检查脚本

`/opt/lims/scripts/health-check.sh`:

```bash
#!/bin/bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

check() {
  local name=$1
  local cmd=$2
  if eval "$cmd" > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} ${name}"
    ((PASS++))
  else
    echo -e "${RED}❌${NC} ${name}"
    ((FAIL++))
  fi
}

echo "═══════════════════════════════════════════════════════"
echo "  LIMS 健康检查 ($(date '+%Y-%m-%d %H:%M:%S'))"
echo "═══════════════════════════════════════════════════════"
echo ""

# ── 系统服务 ──
check "PostgreSQL 16"        "systemctl is-active postgresql@16-main"
check "Redis 7"              "redis-cli -a ${REDIS_PASSWORD:-} ping | grep -q PONG"
check "MinIO"                "curl -sf http://127.0.0.1:9000/minio/health/live"
check "Nginx"                "systemctl is-active nginx"
check "LIMS Backend"         "systemctl is-active lims-backend"
check "Celery Worker"        "systemctl is-active lims-celery"
check "Celery Beat"          "systemctl is-active lims-celerybeat"

echo ""

# ── API 健康 ──
check "API /health"          "curl -sf http://127.0.0.1:8000/health | grep -q ok"
check "API /metrics"         "curl -sf http://127.0.0.1:8000/metrics | grep -q prometheus"

echo ""

# ── 数据库连接 ──
check "PostgreSQL 连接"       "sudo -u postgres psql -d lims_production -c 'SELECT 1;' > /dev/null"
check "Redis 连接"           "redis-cli -a ${REDIS_PASSWORD:-} ping | grep -q PONG"

echo ""

# ── 磁盘空间 ──
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -lt 80 ]; then
  echo -e "${GREEN}✅${NC} 磁盘使用率: ${DISK_USAGE}%"
  ((PASS++))
else
  echo -e "${YELLOW}⚠️ ${NC}  磁盘使用率: ${DISK_USAGE}% (建议 < 80%)"
  ((FAIL++))
fi

DISK_DATA=$(df /data 2>/dev/null | awk 'NR==2 {print $5}' | tr -d '%')
if [ -n "$DISK_DATA" ]; then
  if [ "$DISK_DATA" -lt 85 ]; then
    echo -e "${GREEN}✅${NC} 数据盘使用率: ${DISK_DATA}%"
    ((PASS++))
  else
    echo -e "${YELLOW}⚠️ ${NC}  数据盘使用率: ${DISK_DATA}%"
    ((FAIL++))
  fi
fi

echo ""

# ── 内存 ──
MEM_AVAIL=$(free -m | awk '/Mem:/ {printf "%.0f", $7/$2*100}')
if [ "$MEM_AVAIL" -gt 20 ]; then
  echo -e "${GREEN}✅${NC} 内存可用率: ${MEM_AVAIL}%"
  ((PASS++))
else
  echo -e "${YELLOW}⚠️ ${NC}  内存可用率: ${MEM_AVAIL}%"
  ((FAIL++))
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  通过: ${PASS}  失败/警告: ${FAIL}"
echo "═══════════════════════════════════════════════════════"

exit $FAIL
```

将此脚本添加为 crontab 每 5 分钟执行一次, 输出到日志并集成告警.

### 6.4 冒烟测试

`/opt/lims/scripts/smoke-test.sh`:

```bash
#!/bin/bash
set -euo pipefail

BASE_URL="http://127.0.0.1:8000"
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

PASS=0
FAIL=0

test_api() {
  local name=$1
  local method=$2
  local path=$3
  local expected=$4
  local extra_args="${5:-}"

  local status_code
  status_code=$(curl -s -o /dev/null -w "%{http_code}" \
    -X "${method}" \
    "${BASE_URL}${path}" \
    ${extra_args})

  if [ "${status_code}" = "${expected}" ]; then
    echo -e "${GREEN}✅${NC} ${name} (HTTP ${status_code})"
    ((PASS++))
  else
    echo -e "${RED}❌${NC} ${name} (期望 ${expected}, 实际 ${status_code})"
    ((FAIL++))
  fi
}

echo "═══════════════════════════════════════════════════════"
echo "  LIMS 冒烟测试 ($(date '+%Y-%m-%d %H:%M:%S'))"
echo "═══════════════════════════════════════════════════════"
echo ""

# ── 基础端点 (无需认证) ──
test_api "健康检查"     "GET" "/health" "200"
test_api "Metrics"      "GET" "/metrics" "200"
test_api "API 文档"     "GET" "/docs" "200"
test_api "OpenAPI JSON" "GET" "/openapi.json" "200"

# ── 需要认证的端点 ──
TOKEN=$(curl -s -X POST "${BASE_URL}/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@2026!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

AUTH_HEADER="-H 'Authorization: Bearer ${TOKEN}'"

test_api "获取用户列表"  "GET" "/api/v1/users?page=1&size=10" "200" "$AUTH_HEADER"
test_api "获取样品列表"  "GET" "/api/v1/samples?page=1&size=10" "200" "$AUTH_HEADER"
test_api "获取检测标准"  "GET" "/api/v1/standards" "200" "$AUTH_HEADER"

# ── 写入操作 ──
test_api "创建测试样品"  "POST" "/api/v1/samples" "201" \
  "$AUTH_HEADER -H 'Content-Type: application/json' -d '{\"name\":\"SmokeTest-001\",\"type\":\"raw_material\"}'"

echo ""

# ── Celery 任务触发测试 ──
TASK_ID=$(curl -s -X POST "${BASE_URL}/api/v1/tasks/test" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")

sleep 3
TASK_STATUS=$(curl -s -X GET "${BASE_URL}/api/v1/tasks/${TASK_ID}/status" \
  -H "Authorization: Bearer ${TOKEN}")

echo -n "Celery 任务执行: "
if echo "${TASK_STATUS}" | grep -q "SUCCESS"; then
  echo -e "${GREEN}✅${NC} Celery Worker 正常"
  ((PASS++))
else
  echo -e "${RED}❌${NC} Celery Worker 异常: ${TASK_STATUS}"
  ((FAIL++))
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  通过: ${PASS}  失败: ${FAIL}"
echo "═══════════════════════════════════════════════════════"

exit $FAIL
```

---

## 7. CI/CD 流程

### 7.1 流程概述

采用 **GitLab CI** 或 **Jenkins Pipeline**, 三阶段流水线:

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Commit  │────▶│  构建    │────▶│  测试    │────▶│  部署    │
│  Push    │     │  Build   │     │  Test    │     │  Deploy  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                     │                │                │
                依赖安装          单元测试           灰度/全量
                代码打包          集成测试           健康检查
                镜像/包构建        Lint/规范          冒烟测试
```

### 7.2 GitLab CI 配置

`.gitlab-ci.yml`:

```yaml
stages:
  - build
  - test
  - deploy

variables:
  PYTHON_VERSION: "3.11"
  APP_DIR: "/opt/lims/app"

# ── 缓存 ──
.cache-python:
  cache:
    key: "${CI_COMMIT_REF_SLUG}-python"
    paths:
      - .venv/
      - pip-cache/

# ════════════════════════ 构建阶段 ════════════════════════

build:backend:
  stage: build
  image: python:${PYTHON_VERSION}-slim
  extends: .cache-python
  script:
    - python -m venv .venv
    - source .venv/bin/activate
    - pip install --cache-dir pip-cache -r requirements.txt
    - pip install --cache-dir pip-cache -r requirements-dev.txt
    # 预编译字节码, 加速部署
    - python -m compileall lims/
  artifacts:
    paths:
      - .venv/
      - build/
    expire_in: 1 hour
  tags:
    - lims-runner

build:frontend:
  stage: build
  image: node:20-alpine
  cache:
    key: "${CI_COMMIT_REF_SLUG}-npm"
    paths:
      - node_modules/
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 hour
  tags:
    - lims-runner

# ════════════════════════ 测试阶段 ════════════════════════

test:unit:
  stage: test
  image: python:${PYTHON_VERSION}-slim
  extends: .cache-python
  services:
    - postgres:16-alpine
    - redis:7-alpine
  variables:
    POSTGRES_DB: lims_test
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_pass
    DATABASE_URL: "postgresql+asyncpg://test_user:test_pass@postgres:5432/lims_test"
    REDIS_URL: "redis://redis:6379/0"
  script:
    - source .venv/bin/activate
    - alembic upgrade head
    - pytest tests/unit/ -v --junitxml=report-unit.xml --cov=lims --cov-report=xml
  artifacts:
    reports:
      junit: report-unit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    when: always
  tags:
    - lims-runner

test:integration:
  stage: test
  image: python:${PYTHON_VERSION}-slim
  extends: .cache-python
  services:
    - postgres:16-alpine
    - redis:7-alpine
  variables:
    POSTGRES_DB: lims_test
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_pass
    DATABASE_URL: "postgresql+asyncpg://test_user:test_pass@postgres:5432/lims_test"
    REDIS_URL: "redis://redis:6379/0"
  script:
    - source .venv/bin/activate
    - alembic upgrade head
    - pytest tests/integration/ -v --junitxml=report-integration.xml
  artifacts:
    reports:
      junit: report-integration.xml
    when: always
  tags:
    - lims-runner

test:lint:
  stage: test
  image: python:${PYTHON_VERSION}-slim
  extends: .cache-python
  script:
    - source .venv/bin/activate
    - ruff check lims/ tests/
    - ruff format --check lims/ tests/
    - mypy lims/
  allow_failure: true  # Lint 不阻断流水线, 但标记警告
  tags:
    - lims-runner

# ════════════════════════ 部署阶段 ════════════════════════

deploy:staging:
  stage: deploy
  image: alpine:latest
  when: manual  # 手动触发
  only:
    - develop
    - /^release\/.*$/
  script:
    - apk add openssh-client
    - eval $(ssh-agent -s)
    - echo "$DEPLOY_SSH_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh && chmod 700 ~/.ssh
    - ssh-keyscan $STAGING_HOST >> ~/.ssh/known_hosts
    # SSH 到目标服务器执行部署
    - |
      ssh $STAGING_USER@$STAGING_HOST <<'REMOTE_SCRIPT'
        set -euo pipefail
        cd /opt/lims/app
        # 拉取最新代码
        git pull origin ${CI_COMMIT_REF_NAME}
        # 激活虚拟环境并更新依赖
        source /opt/lims/venv/bin/activate
        pip install -r requirements.txt
        # 数据库迁移
        alembic upgrade head
        # 重新加载后端 (优雅重启)
        sudo systemctl reload lims-backend
        # 等待重启完成
        sleep 5
        # 健康检查
        curl -sf http://127.0.0.1:8000/health || exit 1
        echo "✅ Staging 部署成功"
      REMOTE_SCRIPT
  environment:
    name: staging
  tags:
    - lims-runner

deploy:production:
  stage: deploy
  image: alpine:latest
  when: manual
  only:
    - main
  script:
    - apk add openssh-client curl jq
    - eval $(ssh-agent -s)
    - echo "$DEPLOY_SSH_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh && chmod 700 ~/.ssh
    - ssh-keyscan $PROD_HOST >> ~/.ssh/known_hosts
    - |
      ssh $PROD_USER@$PROD_HOST <<'REMOTE_SCRIPT'
        set -euo pipefail

        echo "═ 开始生产部署 $(date) ═"

        # ── 阶段 1: 备份 ──
        echo "→ 阶段 1/5: 备份..."
        /opt/lims/scripts/backup-postgres.sh
        /opt/lims/scripts/backup-minio.sh

        # ── 阶段 2: 拉取代码 ──
        echo "→ 阶段 2/5: 拉取代码..."
        cd /opt/lims/app
        git fetch origin main
        git checkout ${CI_COMMIT_SHA}

        # ── 阶段 3: 更新依赖 ──
        echo "→ 阶段 3/5: 更新依赖..."
        source /opt/lims/venv/bin/activate
        pip install -r requirements.txt --quiet

        # ── 阶段 4: 数据库迁移 ──
        echo "→ 阶段 4/5: 数据库迁移..."
        alembic upgrade head

        # ── 阶段 5: 灰度重启 ──
        echo "→ 阶段 5/5: 灰度重启服务..."

        # 5a. 逐批重启 Gunicorn workers (零停机)
        sudo systemctl reload lims-backend
        sleep 10

        # 5b. 健康验证
        for i in $(seq 1 5); do
          HEALTH=$(curl -sf http://127.0.0.1:8000/health 2>&1 || echo "error")
          if echo "$HEALTH" | grep -q "ok"; then
            echo "✅ 健康检查通过 (第 ${i} 次)"
            break
          fi
          echo "⏳ 等待服务就绪... (${i}/5)"
          sleep 3
        done

        # 5c. 确认健康通过后, 重启 Celery
        sudo systemctl restart lims-celery
        sudo systemctl restart lims-celerybeat

        # ── 部署后冒烟测试 ──
        echo "→ 运行冒烟测试..."
        /opt/lims/scripts/smoke-test.sh || {
          echo "❌ 冒烟测试失败, 执行回滚..."
          cd /opt/lims/app
          git checkout $(git rev-parse HEAD~1)
          alembic downgrade -1
          sudo systemctl restart lims-backend
          sudo systemctl restart lims-celery
          sudo systemctl restart lims-celerybeat
          echo "回滚完成"
          exit 1
        }

        echo "═ 生产部署完成 $(date) ═"
      REMOTE_SCRIPT
  environment:
    name: production
  tags:
    - lims-runner
```

### 7.3 灰度发布策略

#### 7.3.1 策略概述

采用 **逐批发布 + 自动回滚** 策略:

```
Phase 1: 10% 流量 (1个 worker) ── 观察 5 分钟 ── 无异常 →
Phase 2: 50% 流量 (2个 worker) ── 观察 5 分钟 ── 无异常 →
Phase 3: 100% 流量 (全部 worker)
```

#### 7.3.2 Gradual Rollout 脚本

```bash
#!/bin/bash
# /opt/lims/scripts/gradual-deploy.sh
set -euo pipefail

echo "═══ 灰度发布开始 ═══"

TOTAL_WORKERS=${GUNICORN_WORKERS:-4}
STAGE1_WORKERS=1
STAGE2_WORKERS=$(( TOTAL_WORKERS / 2 ))
HEALTH_ENDPOINT="http://127.0.0.1:8000/health"
OBSERVE_SECONDS=300  # 5 分钟观察期

# ── Phase 1: 10% 流量 ──
echo ""
echo "→ Phase 1: 启动 ${STAGE1_WORKERS} workers (≈ 10% 流量)"
sudo systemctl reload lims-backend
# 暂时手动调整 worker 数量的方法:
# 在 gunicorn.conf.py 中设置固定 workers 数, 然后 reload

sleep "${OBSERVE_SECONDS}"

# 检查指标
ERROR_RATE=$(curl -s "http://127.0.0.1:9090/api/v1/query" \
  --data-urlencode 'query=sum(rate(lims_api_request_duration_seconds_count{status_code=~"5.."}[5m]))/sum(rate(lims_api_request_duration_seconds_count[5m]))*100' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['result'][0]['value'][1] if d['data']['result'] else 0)")

if (( $(echo "${ERROR_RATE} > 5" | bc -l) )); then
  echo "❌ Phase 1 错误率过高: ${ERROR_RATE}%, 中止发布"
  exit 1
fi

echo "✅ Phase 1 通过 (错误率: ${ERROR_RATE}%)"

# ── Phase 2: 50% 流量 ──
echo ""
echo "→ Phase 2: 启动 ${STAGE2_WORKERS} workers (≈ 50% 流量)"
# 调整 worker 配置后 reload
sed -i "s/^GUNICORN_WORKERS=.*/GUNICORN_WORKERS=${STAGE2_WORKERS}/" /opt/lims/.env
sudo systemctl reload lims-backend

sleep "${OBSERVE_SECONDS}"

ERROR_RATE=$(curl -s "http://127.0.0.1:9090/api/v1/query" \
  --data-urlencode 'query=sum(rate(lims_api_request_duration_duration_seconds_count{status_code=~"5.."}[5m]))/sum(rate(lims_api_request_duration_seconds_count[5m]))*100' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['result'][0]['value'][1] if d['data']['result'] else 0)")

if (( $(echo "${ERROR_RATE} > 5" | bc -l) )); then
  echo "❌ Phase 2 错误率过高: ${ERROR_RATE}%, 回退到 Phase 1"
  sed -i "s/^GUNICORN_WORKERS=.*/GUNICORN_WORKERS=${STAGE1_WORKERS}/" /opt/lims/.env
  sudo systemctl reload lims-backend
  exit 1
fi

echo "✅ Phase 2 通过 (错误率: ${ERROR_RATE}%)"

# ── Phase 3: 全量 ──
echo ""
echo "→ Phase 3: 全量启动 ${TOTAL_WORKERS} workers"
sed -i "s/^GUNICORN_WORKERS=.*/GUNICORN_WORKERS=${TOTAL_WORKERS}/" /opt/lims/.env
sudo systemctl reload lims-backend

sleep 60

# 最终冒烟验证
/opt/lims/scripts/smoke-test.sh || {
  echo "❌ 冒烟测试失败, 回退..."
  sed -i "s/^GUNICORN_WORKERS=.*/GUNICORN_WORKERS=${STAGE2_WORKERS}/" /opt/lims/.env
  sudo systemctl reload lims-backend
  exit 1
}

echo ""
echo "═══ 灰度发布完成 ═══"
```

#### 7.3.3 回滚流程

当部署失败或验证不通过时:

```bash
#!/bin/bash
# /opt/lims/scripts/rollback.sh
set -euo pipefail

echo "═══ 开始回滚 ═══"

# 1. 恢复到上一个 Git 提交
cd /opt/lims/app
PREVIOUS_SHA=$(git rev-parse HEAD~1)
git checkout ${PREVIOUS_SHA}
echo "→ 代码回退至 ${PREVIOUS_SHA}"

# 2. 恢复数据库 (降级)
source /opt/lims/venv/bin/activate
alembic downgrade -1
echo "→ 数据库已降级"

# 3. 重启服务
sudo systemctl restart lims-backend
sudo systemctl restart lims-celery
sudo systemctl restart lims-celerybeat

# 4. 验证
sleep 5
/opt/lims/scripts/health-check.sh
/opt/lims/scripts/smoke-test.sh

echo "═══ 回滚完成 ═══"
```

### 7.4 Jenkins Pipeline 替代方案

对于偏好 Jenkins 的团队, 等效 Jenkinsfile:

```groovy
pipeline {
    agent { label 'lims-runner' }

    environment {
        PYTHON_VERSION = '3.11'
        APP_DIR = '/opt/lims/app'
    }

    stages {
        stage('Build') {
            parallel {
                stage('Backend') {
                    steps {
                        sh '''
                            python${PYTHON_VERSION} -m venv .venv
                            source .venv/bin/activate
                            pip install -r requirements.txt
                        '''
                    }
                }
                stage('Frontend') {
                    steps {
                        sh '''
                            npm ci
                            npm run build
                        '''
                    }
                }
            }
        }

        stage('Test') {
            parallel {
                stage('Unit') {
                    steps {
                        sh '''
                            source .venv/bin/activate
                            alembic upgrade head
                            pytest tests/unit/ -v --junitxml=report-unit.xml
                        '''
                    }
                    post {
                        always {
                            junit 'report-unit.xml'
                        }
                    }
                }
                stage('Integration') {
                    steps {
                        sh '''
                            source .venv/bin/activate
                            pytest tests/integration/ -v --junitxml=report-integration.xml
                        '''
                    }
                    post {
                        always {
                            junit 'report-integration.xml'
                        }
                    }
                }
                stage('Lint') {
                    steps {
                        sh '''
                            source .venv/bin/activate
                            ruff check lims/ tests/
                            ruff format --check lims/ tests/
                        '''
                    }
                }
            }
        }

        stage('Deploy Staging') {
            when {
                branch 'develop'
            }
            steps {
                input message: '部署到 Staging?'
                sh '''
                    ssh staging-server <<'EOF'
                        cd /opt/lims/app && git pull
                        source /opt/lims/venv/bin/activate && pip install -r requirements.txt
                        alembic upgrade head
                        sudo systemctl reload lims-backend
                        /opt/lims/scripts/smoke-test.sh
                    EOF
                '''
            }
        }

        stage('Deploy Production') {
            when {
                branch 'main'
            }
            steps {
                input message: '确认部署到 Production?'
                sh '''
                    ssh prod-server <<'EOF'
                        set -eu
                        cd /opt/lims/app && git pull origin main
                        source /opt/lims/venv/bin/activate && pip install -r requirements.txt
                        alembic upgrade head
                        sudo systemctl reload lims-backend
                        sleep 5
                        /opt/lims/scripts/smoke-test.sh
                    EOF
                '''
            }
        }
    }

    post {
        success {
            slackSend(channel: '#lims-deploy', color: 'good', message: "部署成功: ${env.BUILD_NUMBER}")
        }
        failure {
            slackSend(channel: '#lims-deploy', color: 'danger', message: "部署失败: ${env.BUILD_NUMBER}")
        }
    }
}
```

---

## 附录

### A. 端口汇总

| 服务 | 端口 | 协议 | 绑定地址 | 说明 |
|---|---|---|---|---|
| Nginx | 80 | HTTP | 0.0.0.0 | HTTP → HTTPS 重定向 |
| Nginx | 443 | HTTPS | 0.0.0.0 | 主服务入口 |
| Gunicorn | 8000 | HTTP | 127.0.0.1 | 内部 (仅 Nginx 反向代理) |
| PostgreSQL | 5432 | TCP | 127.0.0.1 | 数据库 |
| Redis | 6379 | TCP | 127.0.0.1 | 缓存/消息队列 |
| MinIO API | 9000 | HTTP/HTTPS | 127.0.0.1 | 对象存储 (内部) |
| MinIO Console | 9001 | HTTP | 0.0.0.0 | 管理控制台 |
| Prometheus | 9090 | HTTP | 0.0.0.0 | 指标查询/Web UI |
| Grafana | 3000 | HTTP | 127.0.0.1 | 仪表板 (Nginx 代理) |
| Node Exporter | 9100 | HTTP | 127.0.0.1 | 系统指标 |
| PG Exporter | 9187 | HTTP | 127.0.0.1 | PostgreSQL 指标 |
| Redis Exporter | 9121 | HTTP | 127.0.0.1 | Redis 指标 |
| Elasticsearch | 9200 | HTTP | 127.0.0.1 | 日志索引 |
| Logstash | 5044 | TCP | 127.0.0.1 | Filebeat 输入 |
| Kibana | 5601 | HTTP | 127.0.0.1 | 日志可视化 |
| 更新服务器 | 8080 | HTTP | 127.0.0.1 | Electron 自动更新 |

### B. systemd Unit 汇总

| Unit 文件 | 服务名 | 启动顺序 | 重启策略 |
|---|---|---|---|
| `postgresql@16-main.service` | PostgreSQL 16 | 1 | always, 10s |
| `redis-server.service` | Redis 7 | 2 | always, 10s |
| `minio.service` | MinIO | 3 | always, 5s |
| `lims-backend.service` | Gunicorn + API | 4 (依赖 1,2,3) | always, 10s |
| `lims-celery.service` | Celery Worker | 4 (依赖 2) | always, 10s |
| `lims-celerybeat.service` | Celery Beat | 4 (依赖 2) | always, 10s |
| `nginx.service` | Nginx | 7 (依赖 4) | always |
| `prometheus.service` | Prometheus | 并行 | always |
| `grafana-server.service` | Grafana | 并行 | always |
| `node-exporter.service` | Node Exporter | 并行 | always |
| `postgres-exporter.service` | PG Exporter | 并行 (依赖 PG) | always |
| `redis-exporter.service` | Redis Exporter | 并行 (依赖 Redis) | always |

### C. 文件目录结构

```
/opt/lims/
├── .env                        # 环境变量 (权限 600)
├── .db_password                # 数据库密码 (仅 root, 权限 600)
├── venv/                       # Python 虚拟环境
├── app/                        # FastAPI 应用代码
│   ├── lims/
│   │   ├── main.py
│   │   ├── celery_app.py
│   │   ├── celery_config.py
│   │   ├── metrics.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── tasks/
│   │   └── alembic/
│   └── requirements.txt
├── frontend/
│   └── dist/                   # Vue/React 构建产物
├── scripts/
│   ├── init-database.sh        # 数据库初始化
│   ├── backup-postgres.sh      # PG 备份
│   ├── backup-minio.sh         # MinIO 备份
│   ├── cleanup-wal.sh          # WAL 清理
│   ├── health-check.sh         # 健康检查
│   ├── smoke-test.sh           # 冒烟测试
│   ├── gradual-deploy.sh       # 灰度发布
│   └── rollback.sh             # 回滚
├── gunicorn.conf.py            # Gunicorn 配置
├── updates/                    # Electron 更新文件
│   ├── latest.yml
│   └── LIMS.Desktop-1.0.0.AppImage
│   └── LIMS-Desktop-Setup-1.0.0.exe

/data/
├── minio/                      # MinIO 数据
│   ├── raw-data/
│   ├── reports/
│   ├── attachments/
│   └── backups/
└── backups/
    ├── postgresql/            # PG 备份 (含 WAL)
    │   ├── lims_production_*.sql.gz
    │   └── wal/
    └── minio/                 # MinIO 镜像备份

/var/log/lims/
├── app.log                    # 应用 JSON 日志
├── gunicorn-access.log
├── gunicorn-error.log
├── celery-worker.log
└── celery-beat.log
```

---

> **文档维护说明**: 本文件为部署与运维核心规范. 配置变更需同步更新本文档和版本控制系统. 任何偏离本文档的部署行为需经技术评审.
