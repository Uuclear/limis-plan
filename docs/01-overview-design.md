# 01 概要设计说明书

> 文档编号：MatLIMS-SDD-001  
> 版本：V1.0  
> 日期：2026-05-10  
> 密级：内部公开

---

## 1 引言

### 1.1 编写目的

本概要设计说明书用于指导建设材料检测实验室信息管理系统（MatLIMS）的整体架构设计、模块划分与接口定义，为后续的详细设计、编码实现、测试验收提供技术依据。

本文档面向以下读者：

- 系统架构师：确认技术选型与分层架构可行性
- 后端开发工程师：理解模块边界、数据流与接口契约
- 前端开发工程师：掌握页面结构、状态管理与组件组织方式
- 测试工程师：依据功能清单与性能指标制定测试计划
- 实施运维人员：了解部署拓扑与运行环境要求
- 质量保证人员：对照 CMA/CNAS 要求核验合规设计

### 1.2 背景

建设材料检测实验室是建筑工程质量控制的法定环节。随着 CMA（检验检测机构资质认定）和 CNAS（中国合格评定国家认可委员会）双认证要求的不断提高，传统纸质流转与电子表格管理模式已无法满足：

- 样品数量增长：日均 200 至 1000 样品，人工跟踪易遗漏
- 检测方法多样化：200 余种检测标准方法，涉及水泥、钢材、骨料、混凝土、外加剂、防水材料等类别
- 合规追溯要求：原始记录与报告需保存至少 10 年，支持随时调阅
- 数值修约合规：必须严格遵循 GB/T 8170 数值修约规则，人工计算易出错
- 人员权限管理：20 至 50 名检测人员，涵盖 10 种角色，需细粒度权限控制

MatLIMS 定位于中小型检测实验室（年样品量 5 万至 25 万件），采用模块化单体架构（Modular Monolith），在保持开发效率的同时为未来微服务拆分预留条件。系统支持委托登记、样品收样、检测任务分配、原始记录填报、三级审核（检测、审核、批准）、报告签发与归档、计费记账全流程数字化管理。

### 1.3 术语定义

| 术语 | 英文 | 定义 |
|------|------|------|
| 委托 | Order / Consignment | 客户提交检测需求的业务单据，包含委托单位、样品清单、检测项目、要求完成日期等信息 |
| 样品 | Sample | 被检测的实体物质，具有唯一编号（格式见 2.3 节），贯穿全生命周期追踪 |
| 检测任务 | Test Task | 从样品拆分出的具体检测执行单元，一个样品可对应多个检测任务 |
| 检测项目 | Test Item | 具体的检测指标，如抗压强度、屈服强度、氯离子含量等 |
| 原始记录 | Original Record | 检测过程中产生的第一手数据记录，包含仪器读数、环境条件、计算过程、检测人签名 |
| 数值修约 | Rounding-off | 按 GB/T 8170 标准对检测计算结果进行有效位数处理的过程 |
| 检测报告 | Report | 经三级审核通过后正式出具的文件，包含检测结果与结论 |
| 报告编号 | Report Number | 唯一标识一份报告，格式为 LIMS-年份-月份-序号 |
| 审核 | Review | 对原始记录或报告内容的第二级技术核实 |
| 批准 | Approve | 对报告内容的第三级授权确认 |
| 签发 | Issue | 报告正式生效并归档的操作，触发电子签名与 PDF 生成 |
| CMA | China Metrology Accreditation | 检验检测机构资质认定，中国强制性认证 |
| CNAS | China National Accreditation Service | 中国合格评定国家认可委员会认可 |
| 电子签名 | E-Signature | 密码确认式签名操作，记录操作人、时间戳、签名字段值 |
| 状态机 | State Machine | 定义业务对象（委托、样品、报告等）从创建到归档的流程状态与转换规则 |
| 工作流 | Workflow | 由状态机驱动的自动化流程，以 JSON 格式存储在数据库中 |
| RBAC | Role-Based Access Control | 基于角色的访问控制，本系统扩展为资源级与行级权限 |
| GD/T 8170 | GB/T 8170 | 数值修约规则与极限数值的表示和判定方法 |
| GD/T 27025 | GB/T 27025 | 检测和校准实验室能力的通用要求（等同采用 ISO/IEC 17025） |
| WORM | Write Once Read Many | 只写多次读存储策略，用于审计日志与原始记录防篡改 |
| MinIO | - | 兼容 S3 协议的对象存储服务，用于存储检测附件、报告 PDF 等 |

### 1.4 参考资料

| 编号 | 文档名称 | 来源 |
|------|----------|------|
| 1 | GB/T 8567-2006 计算机软件文档编制规范 | 国家标准 |
| 2 | GB/T 8170-2008 数值修约规则与极限数值的表示和判定 | 国家标准 |
| 3 | GB/T 27025-2019 检测和校准实验室能力的通用要求 | 国家标准 |
| 4 | RB/T 214-2017 检验检测机构资质认定能力评价准则 | 行业标准 |
| 5 | CNAS-CL01:2018 检测和校准实验室能力认可准则 | CNAS |
| 6 | Effective Harnesses for Long-Running Agents | Anthropic Engineering Blog |
| 7 | Harness Engineering: Leveraging Codex in an Agent-First World | OpenAI Index |
| 8 | Clean Architecture | Robert C. Martin |
| 9 | FastAPI 官方文档 | https://fastapi.tiangolo.com |
| 10 | React 官方文档 | https://react.dev |
| 11 | PostgreSQL 16 Documentation | https://www.postgresql.org/docs/16/ |
| 12 | Ant Design 5.0 组件库 | https://ant.design |

---

## 2 总体设计

### 2.1 需求规定

#### 2.1.1 功能清单

系统划分为 12 个核心模块，覆盖检测实验室全部业务场景：

| 模块编号 | 模块名称（中文） | 模块名称（代码） | 核心功能 | 优先级 |
|----------|-----------------|-----------------|----------|--------|
| M01 | 用户与权限管理 | users | 用户 CRUD、角色管理、RBAC 权限分配、行级数据过滤、操作日志 | P0 |
| M02 | 委托与收样 | orders | 委托登记、样品接收、条码打印、委托变更、委托归档 | P0 |
| M03 | 样品管理 | samples | 样品编号生成、状态追踪、留样管理、样品处置、盲样管理 | P0 |
| M04 | 检测任务 | testing | 任务分配、原始记录填报、数值自动修约、超标预警、不合格品处理 | P0 |
| M05 | 报告管理 | reports | 报告生成、三级审核、电子签名、PDF 导出、报告防伪、报告作废 | P0 |
| M06 | 设备与仪器 | instruments | 仪器台账、校准计划、期间核查、仪器使用记录、串口数据采集 | P0 |
| M07 | 标准方法管理 | methods | 检测方法库、检测项目维护、修约规则配置、标准有效性管理 | P0 |
| M08 | 工作流引擎 | workflow | 状态机定义、流程编排、审批流配置、超时提醒、异常处理 | P0 |
| M09 | 质量体系 | quality | 人员能力档案、监督计划、内部审核、纠正预防、文件控制 | P1 |
| M10 | 计费与财务 | billing | 价格矩阵、费用计算、账单管理、离线转账登记、对账核销、发票记录 | P1 |
| M11 | 通知与消息 | notifications | 邮件通知、短信通知、站内消息、模板管理、发送日志 | P1 |
| M12 | 系统基础 | system | 数据字典、系统配置、操作日志审计、定时任务、数据备份 | P0 |

模块优先级说明：
- P0：首期上线必须完成
- P1：二期上线完成

#### 2.1.2 性能指标

| 指标 | 目标值 | 测试方法 |
|------|--------|----------|
| 日均样品处理量 | 200 至 1000 件 | 压力测试脚本模拟 8 小时连续收样 |
| 并发在线用户数 | 20 至 50 人 | Locust 并发模拟 |
| API 响应时间 P95 | ≤ 500 毫秒 | 压测报告统计 |
| API 响应时间 P99 | ≤ 1000 毫秒 | 压测报告统计 |
| 报告 PDF 生成时间 | ≤ 5 秒/份（10 页以内） | 计时统计 |
| 数据保留时间 | 10 年 | 归档策略与迁移测试 |
| 数据库存储年增量 | ≤ 50 GB | 容量规划评估 |
| 系统可用性 | ≥ 99.5%（年度） | 运维监控统计 |
| 电子签名响应时间 | ≤ 1 秒 | 用户操作记录 |
| 条码打印响应时间 | ≤ 2 秒 | 用户操作记录 |

#### 2.1.3 合规要求

| 要求项 | 来源 | 系统实现方式 |
|--------|------|-------------|
| 检测全过程可追溯 | CMA RB/T 214 | 样品全生命周期状态机 + 审计日志 |
| 原始记录不可篡改 | CMA RB/T 214 | WORM 存储 + 审计触发器 + 变更留痕 |
| 人员资质管理 | CNAS-CL01 6.2 | 质量体系模块人员能力档案 |
| 仪器校准溯源 | CNAS-CL01 6.4 | 设备模块校准计划与期间核查 |
| 检测方法有效性 | CNAS-CL01 7.2 | 标准方法库与有效性状态管理 |
| 报告三级审核 | CMA | 报告状态机强制三级审批 |
| 记录保存 10 年 | CMA/CNAS | 归档策略与数据库分区 |

### 2.2 运行环境

#### 2.2.1 部署架构

```
                    客户端层
    ┌──────────────┬──────────────┬──────────────┐
    │  Desktop App │   Web Browser│   Mobile App │
    │  (Electron)  │  (React SPA) │  (Web App)   │
    └──────┬───────┴──────┬───────┴──────┬───────┘
           │              │              │
           ▼              ▼              ▼
    ┌──────────────────────────────────────────┐
    │            Nginx 反向代理                   │
    │  :80 HTTP / :443 HTTPS / :5000 Electron  │
    └──────────────────────┬───────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────┐
    │         应用服务层（单台服务器）              │
    │  ┌────────────────────────────────────┐  │
    │  │ Gunicorn (多进程)                   │  │
    │  │ UvicornWorker x 4                │  │
    │  │ FastAPI Application (ASGI)        │  │
    │  │ :8000                             │  │
    │  └────────────────────────────────────┘  │
    │  ┌──────────────┐  ┌──────────────────┐  │
    │  │ Celery Worker │  │  Celery Beat     │  │
    │  │ 并发: 4       │  │  定时调度         │  │
    │  │ :9000         │  │                  │  │
    │  └──────────────┘  └──────────────────┘  │
    │  ┌────────────────────────────────────┐  │
    │  │ Instrument Agent (独立进程)         │  │
    │  │ Electron + node-serialport         │  │
    │  │ RS-232/RS-485 串口轮询             │  │
    │  └────────────────────────────────────┘  │
    └──────────────────────────────────────────┘
                           │
    ┌──────────────────────┼──────────────────┐
    │         数据存储层                        │
    │  ┌─────────┐ ┌─────┐ ┌───────────────┐ │
    │  │PostgreSQL│ │Redis │ │ MinIO         │ │
    │  │ :5432    │ │:6379 │ │ :9000 (内部)  │ │
    │  └─────────┘ └─────┘ └───────────────┘ │
    └─────────────────────────────────────────┘
```

#### 2.2.2 组件明细

| 组件 | 版本 | 用途 | 安装方式 | 管理方式 |
|------|------|------|----------|----------|
| 操作系统 | Ubuntu 22.04 LTS 或 AlmaLinux 9 | 宿主机 | ISO 安装 | systemd |
| PostgreSQL | 16.x | 主数据库、审计日志 | apt/yum 官方源 | systemd |
| Redis | 7.2 LTS | 缓存、会话、Celery Broker | 官方源 | systemd |
| MinIO | 最新稳定版 | 对象存储（附件、报告） | 官方二进制 | systemd |
| Python | 3.12+ | 后端运行时 | pyenv / 虚拟环境 | systemd |
| FastAPI | 0.115+ | Web 框架 | pip | systemd + Gunicorn |
| Gunicorn | 23.0+ | ASGI 进程管理器 | pip | systemd |
| Uvicorn | 0.32+ | ASGI Worker | pip | - |
| Celery | 5.4+ | 异步任务队列 | pip | systemd |
| Celery Beat | 5.4+ | 定时调度器 | pip | systemd |
| Node.js | 20 LTS | Electron 运行时 | nvm | - |
| Electron | 30+ | 桌面客户端框架 | npm | - |
| Ant Design | 5.x | UI 组件库 | npm | - |
| React | 18.2+ | 前端框架 | npm | - |
| Zustand | 4.5+ | 状态管理 | npm | - |
| ECharts | 5.5+ | 图表库 | npm | - |
| Nginx | 1.24+ | 反向代理 | 官方源 | systemd |

#### 2.2.3 Systemd 服务清单

| 服务名 | 描述 | 端口 | 重启策略 |
|--------|------|------|----------|
| matlims-api | FastAPI 应用（Gunicorn 管理） | 8000 | always |
| matlims-worker | Celery Worker（异步任务） | 9000 | always |
| matlims-beat | Celery Beat（定时调度） | - | always |
| matlims-instrument | 仪器串口采集服务（独立进程） | 8001 | always |
| matlims-nginx | Nginx 反向代理 | 80, 443 | always |
| matlims-minio | MinIO 对象存储 | 9000, 9001 | always |
| postgresql | PostgreSQL 数据库 | 5432 | always |
| redis-server | Redis 缓存服务 | 6379 | always |

所有服务统一通过 `/etc/systemd/system/matlims-*.service` 管理，日志输出到 `journald`，可通过 `journalctl -u matlims-*` 查看。

### 2.3 基本设计概念

#### 2.3.1 样品全生命周期追踪

样品从创建到归档经历以下标准状态流转，每个状态变更记录时间戳与操作人：

```
委托登记 ──→ 收样登记 ──→ 样品分配 ──→ 待检测 ──→ 检测中
    │          │          │          │          │
    │          │          │          │          ▼
    │          │          │          │      检测完成
    │          │          │          │          │
    │          │          │          │          ▼
    │          │          │          │      待审核 ──→ 审核通过 ──→ 待批准
    │          │          │          │          │          │          │
    │          │          │          │          ▼          ▼          ▼
    │          │          │          │      审核退回   批准通过   批准退回
    │          │          │          │                     │
    │          │          │          │                     ▼
    │          │          │          │                  待签发
    │          │          │          │                     │
    │          │          │          │                     ▼
    │          │          │          │                  已签发 ──→ 已归档
    │          │          │          │                     │
    │          │          │          │                     ▼
    │          │          │          │                  已作废（异常分支）
    └──────────┴──────────┴──────────┴────────────────────┘
```

状态机定义存储在 `workflow_definitions` 表中（JSON 格式），代码侧通过 `workflow` 模块统一驱动，不硬编码状态转换逻辑。

样例状态机定义（JSON）：

```json
{
  "entity_type": "sample",
  "states": ["draft", "received", "assigned", "testing", "tested", "reviewing", "review_passed", "review_rejected", "approving", "approved", "approval_rejected", "issuing", "issued", "archived", "voided"],
  "initial_state": "draft",
  "transitions": [
    {"from": "draft", "to": "received", "action": "receive_sample", "roles": ["sample_clerk"]},
    {"from": "received", "to": "assigned", "action": "assign_sample", "roles": ["lab_director"]},
    {"from": "assigned", "to": "testing", "action": "start_testing", "roles": ["tester"]},
    {"from": "testing", "to": "tested", "action": "complete_testing", "roles": ["tester"]},
    {"from": "tested", "to": "reviewing", "action": "submit_review", "roles": ["reviewer"]},
    {"from": "reviewing", "to": "review_passed", "action": "approve_review", "roles": ["reviewer"]},
    {"from": "reviewing", "to": "review_rejected", "action": "reject_review", "roles": ["reviewer"]},
    {"from": "review_passed", "to": "approving", "action": "submit_approval", "roles": ["approver"]},
    {"from": "approving", "to": "approved", "action": "approve_report", "roles": ["approver"]},
    {"from": "approving", "to": "approval_rejected", "action": "reject_approval", "roles": ["approver"]},
    {"from": "approved", "to": "issuing", "action": "submit_issue", "roles": ["authorizer"]},
    {"from": "issuing", "to": "issued", "action": "issue_report", "roles": ["authorizer"]},
    {"from": "issued", "to": "archived", "action": "archive_report", "roles": ["admin"]},
    {"from": "*", "to": "voided", "action": "void_entity", "roles": ["admin", "lab_director"]}
  ],
  "required_signatures": {
    "tested": ["tester"],
    "review_passed": ["reviewer"],
    "approved": ["approver"],
    "issued": ["authorizer"]
  }
}
```

#### 2.3.2 轻量级工作流引擎

工作流引擎不引入外部流程引擎（如 BPMN），而是采用 JSON 格式存储状态定义，由 Python 代码解释执行：

- 状态定义：存储在 `workflow_definitions` 表，包含状态列表、初始状态、转换规则
- 状态实例：存储在 `workflow_instances` 表，记录实体当前状态与历史转换记录
- 权限校验：转换规则中定义允许执行的角色，引擎执行时进行 RBAC 校验
- 签名校验：关键转换节点要求密码确认，记录电子签名到 `e_signatures` 表
- 扩展性：当流程需要调整时，仅修改 JSON 定义并部署新定义，无需更改代码

#### 2.3.3 审计日志设计

采用 PostgreSQL 触发器（Trigger）实现全表审计，确保每一条数据的增删改操作都被记录：

```sql
-- 审计日志表结构（简化示意）
CREATE TABLE audit_log (
    id          BIGSERIAL PRIMARY KEY,
    table_name  VARCHAR(128) NOT NULL,
    operation   VARCHAR(10) NOT NULL,  -- INSERT, UPDATE, DELETE
    old_data    JSONB,
    new_data    JSONB,
    user_id     BIGINT,
    user_name   VARCHAR(64),
    ip_address  INET,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);
```

触发器函数由数据库模板自动生成，覆盖所有业务表。审计日志满足：
- 不可删除：审计日志表仅允许 INSERT，UPDATE 和 DELETE 操作被拒绝
- 关联用户：通过数据库会话变量 `app.user_id` 传递当前用户标识
- 包含旧值与新值：支持完整回溯
- WORM 属性：通过 PostgreSQL 分区与只读表空间实现长期归档

#### 2.3.4 GB/T 8170 数值修约

检测项目结果必须按 GB/T 8170 进行数值修约。系统在两个层次实现：

**Python 层**（原始记录计算时）：

```python
# 修约规则枚举
class RoundingRule(Enum):
    ROUND_HALF_EVEN = "round_half_even"   # 四舍六入五成双
    ROUND_HALF_UP = "round_half_up"       # 四舍五入
    TRUNCATE = "truncate"                # 截断
    ROUND_UP = "round_up"                # 进一法

def round_by_gb8170(value: float, decimal_places: int, rule: RoundingRule) -> float:
    """按 GB/T 8170 修约数值"""
    ...
```

**数据库层**（报表查询与导出时复核）：

```sql
-- PostgreSQL 自定义函数
CREATE OR REPLACE FUNCTION gb_round(value NUMERIC, places INT, rule VARCHAR)
RETURNS NUMERIC AS $$
    -- 实现 GB/T 8170 数值修约逻辑
$$ LANGUAGE plpgsql;
```

修约规则存储在 `method_items.round_rule` 字段中，与检测项目绑定。系统在前端展示、API 返回、报告生成三处均应用修约，确保一致。

#### 2.3.5 编号生成规则

| 编号类型 | 格式 | 示例 | 生成方式 |
|----------|------|------|----------|
| 样品编号 | 年份(2位) + 月份(2位) + 流水号(4位) | 2605-0001 | 数据库序列 |
| 委托编号 | 'WT' + 年份(4位) + 流水号(5位) | WT202600001 | 数据库序列 |
| 报告编号 | 'LIMS' + 年份(4位) + 月份(2位) + 流水号(4位) | LIMS2026050001 | 数据库序列 |
| 任务编号 | 'TASK' + 年份(4位) + 流水号(5位) | TASK202600001 | 数据库序列 |

### 2.4 系统结构

#### 2.4.1 分层架构（Clean Architecture）

```
┌─────────────────────────────────────────────────────────────┐
│                    Frameworks Layer                          │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐            │
│  │FastAPI │  │PostgreSQL│ │  Celery │  │ MinIO  │            │
│  │Router  │  │  Repo    │  │ Runner │  │ Client │            │
│  └────────┘  └────────┘  └────────┘  └────────┘            │
│                     ↓↑ 实现接口 ↓↑                           │
├─────────────────────────────────────────────────────────────┤
│                    Adapters Layer                            │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐            │
│  │ API    │  │ Repo   │  │ Worker │  │ Storage│            │
│  │Routes  │  │Impl    │  │Impl    │  │Impl     │            │
│  │(12模块) │  │(Pg)    │  │(Celery)│  │(MinIO)  │            │
│  └────────┘  └────────┘  └────────┘  └────────┘            │
│                     ↓↑ 依赖倒置 ↓↑                           │
├─────────────────────────────────────────────────────────────┤
│                    Use Cases Layer                           │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐            │
│  │Create  │  │Assign  │  │Test    │  │Sign    │            │
│  │Order   │  │Sample  │  │Sample  │  │Report  │            │
│  │UC      │  │UC      │  │UC      │  │UC      │            │
│  └────────┘  └────────┘  └────────┘  └────────┘            │
│  (12 模块 × ~15 UC = ~180 用例)                              │
│                     ↓↑ 仅依赖内层 ↓↑                          │
├─────────────────────────────────────────────────────────────┤
│                      Domain Layer                            │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐            │
│  │ 实体   │  │ 值对象 │  │ 领域   │  │ 领域   │            │
│  │ Ent-   │  │ VO     │  │ 服务   │  │ 事件   │            │
│  │ ities  │  │        │  │ Service│  │ Events │            │
│  └────────┘  └────────┘  └────────┘  └────────┘            │
│  (纯业务逻辑，零框架依赖)                                    │
└─────────────────────────────────────────────────────────────┘
```

**各层职责**：

| 层级 | 职责 | 依赖方向 | 示例 |
|------|------|----------|------|
| Domain | 定义业务实体、值对象、领域服务、领域事件 | 无外部依赖 | `Sample` 实体、`RoundingResult` 值对象 |
| Use Cases | 编排业务流程，调用领域服务与仓储接口 | 仅依赖 Domain | `CreateOrderUseCase`, `TestSampleUseCase` |
| Adapters | 实现 Use Cases 定义的接口（仓储、服务等） | 依赖 Use Cases + Domain | `PostgresOrderRepo`, `MinFileStorage` |
| Frameworks | 框架集成（API 路由、Worker、数据库） | 依赖所有内层 | FastAPI 路由器、Celery 任务调度 |

#### 2.4.2 模块化分包矩阵

```
lims/
├── src/
│   ├── domain/                    # Domain Layer (纯业务逻辑)
│   │   ├── __init__.py
│   │   ├── entities/              # 业务实体
│   │   │   ├── order.py           # 委托
│   │   │   ├── sample.py          # 样品
│   │   │   ├── test_task.py       # 检测任务
│   │   │   ├── original_record.py # 原始记录
│   │   │   ├── report.py          # 报告
│   │   │   ├── instrument.py      # 仪器
│   │   │   ├── user.py            # 用户
│   │   │   └── ...
│   │   ├── value_objects/         # 值对象
│   │   │   ├── sample_code.py
│   │   │   ├── rounding_result.py
│   │   │   ├── e_signature.py
│   │   │   └── ...
│   │   ├── services/              # 领域服务
│   │   │   ├── rounding_engine.py  # GB/T 8170 修约
│   │   │   ├── code_generator.py   # 编号生成
│   │   │   └── ...
│   │   └── events/                # 领域事件
│   │       ├── sample_received.py
│   │       ├── report_issued.py
│   │       └── ...
│   │
│   ├── use_cases/                 # Use Cases Layer
│   │   ├── orders/
│   │   │   ├── create_order.py
│   │   │   ├── update_order.py
│   │   │   ├── receive_sample.py
│   │   │   └── ...
│   │   ├── samples/
│   │   ├── testing/
│   │   ├── reports/
│   │   ├── ...
│   │   └── base.py               # UseCase 基类
│   │
│   ├── adapters/                  # Adapters Layer
│   │   ├── api/                   # API 路由
│   │   │   ├── v1/
│   │   │   │   ├── orders.py
│   │   │   │   ├── samples.py
│   │   │   │   └── ...
│   │   │   └── middleware/
│   │   ├── repos/                 # 仓储实现
│   │   │   ├── postgres/
│   │   │   │   ├── order_repo.py
│   │   │   │   └── ...
│   │   │   └── interfaces.py      # 仓储接口定义
│   │   ├── workers/               # 异步任务
│   │   │   ├── report_generator.py
│   │   │   ├── notification_sender.py
│   │   │   └── ...
│   │   ├── storage/               # 存储
│   │   │   └── minio_adapter.py
│   │   └── instrument/            # 仪器串口
│   │       └── serial_adapter.py
│   │
│   └── frameworks/                # Frameworks Layer
│       ├── fastapi/
│       │   ├── app.py
│       │   ├── config.py
│       │   └── dependencies.py
│       ├── database/
│       │   ├── postgres.py
│       │   └── redis.py
│       └── logging.py
│
├── tests/
│   ├── domain/
│   ├── use_cases/
│   ├── adapters/
│   └── frameworks/
│
├── migrations/                    # Alembic 数据库迁移
├── scripts/                       # 部署脚本
└── pyproject.toml
```

#### 2.4.3 前端项目结构

```
src/
├── main.jsx                     # Electron 入口
├── app/
│   ├── router.tsx               # Electron + React Router
│   └── store/                   # Zustand Store
│       ├── index.ts
│       ├── orderStore.ts
│       ├── sampleStore.ts
│       ├── authStore.ts
│       └── ...
│
├── features/                    # 按功能特性组织的模块
│   ├── orders/                  # 委托模块
│   │   ├── OrderList.tsx
│   │   ├── OrderDetail.tsx
│   │   ├── OrderForm.tsx
│   │   └── ...
│   ├── samples/                 # 样品模块
│   ├── testing/                 # 检测模块
│   │   ├── RecordForm.tsx       # 原始记录表单
│   │   ├── TestTaskList.tsx
│   │   └── ...
│   ├── reports/                 # 报告模块
│   ├── instruments/             # 设备模块
│   ├── methods/                 # 方法模块
│   ├── quality/                 # 质量体系
│   └── billing/                 # 计费模块
│
├── components/                  # 通用组件
│   ├── layout/                  # 布局
│   ├── forms/                   # 表单组件
│   ├── tables/                  # 表格
│   ├── charts/                  # ECharts 封装
│   └── data-entry/              # 数据录入
│
├── test_forms/                  # 200+ 检测方法对应表单组件
│   ├── cement/                  # 水泥类
│   │   ├── GB-T17671_compressive.tsx    # GB/T 17671 抗压强度
│   │   ├── GB-T17671_flexural.tsx       # GB/T 17671 抗折强度
│   │   └── ...
│   ├── steel/                   # 钢材类
│   ├── aggregate/               # 骨料类
│   ├── concrete/                # 混凝土类
│   └── ...                      # 按标准类别分包
│
├── api/                         # API 请求封装
│   ├── orders.ts
│   ├── samples.ts
│   └── ...
│
└── types/                       # TypeScript 类型定义
    ├── order.ts
    ├── sample.ts
    └── ...
```

### 2.5 功能与程序关系矩阵

| 业务功能 | 所属模块 | 后端 Use Case | API 路由 | 前端页面 | 数据库表 |
|----------|---------|--------------|----------|----------|----------|
| 新建委托 | M02 | CreateOrderUseCase | POST /api/v1/orders | OrderForm.tsx | orders |
| 样品收样 | M02 | ReceiveSampleUseCase | POST /api/v1/samples/receive | SampleReceive.tsx | samples |
| 条形码打印 | M02 | PrintBarcodeUseCase | POST /api/v1/samples/barcode | BarcodePrint.tsx | samples |
| 样品分配 | M03 | AssignSampleUseCase | POST /api/v1/samples/assign | SampleAssign.tsx | samples, test_tasks |
| 任务分配 | M04 | AssignTaskUseCase | POST /api/v1/test-tasks/assign | TaskAssign.tsx | test_tasks |
| 原始记录填报 | M04 | SubmitRecordUseCase | POST /api/v1/records | RecordForm.tsx | original_records, record_data |
| 数值修约 | M04 | RoundResultUseCase | POST /api/v1/records/round | RoundResult.tsx | record_data |
| 仪器数据采集 | M06 | CollectInstrumentDataUseCase | POST /api/v1/instruments/collect | SerialCapture.tsx | instrument_data |
| 提交审核 | M08 | SubmitWorkflowUseCase | POST /api/v1/workflow/submit | WorkflowAction.tsx | workflow_instances |
| 报告生成 | M05 | GenerateReportUseCase | POST /api/v1/reports/generate | ReportPreview.tsx | reports |
| 三级审核 | M05 | ReviewReportUseCase | POST /api/v1/reports/review | ReportReview.tsx | reports, e_signatures |
| 报告签发 | M05 | IssueReportUseCase | POST /api/v1/reports/issue | ReportIssue.tsx | reports, e_signatures |
| PDF 导出 | M05 | ExportPdfUseCase | GET /api/v1/reports/{id}/pdf | ReportExport.tsx | - (MinIO) |
| 价格计算 | M10 | CalculateFeeUseCase | POST /api/v1/billing/calculate | FeeCalculate.tsx | price_matrices, invoices |
| 转账登记 | M10 | RecordPaymentUseCase | POST /api/v1/billing/payments | PaymentRecord.tsx | payments |
| 对账核销 | M10 | ReconcilePaymentUseCase | POST /api/v1/billing/reconcile | PaymentReconcile.tsx | payments |
| 仪器校准提醒 | M06 | CheckCalibrationDueUseCase | GET /api/v1/instruments/calibration-due | CalibrationAlert.tsx | instruments |
| 人员能力管理 | M09 | ManageCompetenceUseCase | CRUD /api/v1/quality/competence | CompetenceMgmt.tsx | personnel_competence |
| 操作日志查询 | M12 | QueryAuditLogUseCase | GET /api/v1/system/audit-logs | AuditLogList.tsx | audit_log |
| 仪表盘 | M12 | DashboardUseCase | GET /api/v1/dashboard | Dashboard.tsx | 多表聚合 |

---

## 3 接口设计

### 3.1 用户接口

#### 3.1.1 REST API 设计规范

所有 API 遵循以下规范：

| 规范项 | 规则 | 示例 |
|--------|------|------|
| URL 版本 | v1 前缀，放在 URL 路径中 | `/api/v1/orders` |
| 资源命名 | 复数名词，小写，连字符分隔 | `/api/v1/test-tasks` |
| 动作命名 | 非 CRUD 操作使用动宾结构 | `/api/v1/reports/export` |
| HTTP 方法 | GET/POST/PUT/PATCH/DELETE | - |
| 请求格式 | JSON (application/json) | - |
| 响应格式 | JSON，统一信封结构 | - |
| 认证 | Bearer JWT Token | - |
| 分页 | `page` + `page_size` 参数 | - |
| 时间格式 | ISO 8601 (UTC) | `2026-05-10T08:30:00Z` |
| 错误码 | HTTP 状态码 + 业务错误码 | `{ "code": "SAMPLE_NOT_FOUND", "message": "..." }` |

#### 3.1.2 统一响应信封

```json
{
  "success": true,
  "data": {
    "id": 1,
    "order_code": "WT202600001",
    "status": "received"
  },
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 156,
    "total_pages": 8
  },
  "meta": {
    "request_id": "req-a1b2c3d4",
    "timestamp": "2026-05-10T08:30:00Z"
  }
}
```

#### 3.1.3 统一错误响应

```json
{
  "success": false,
  "code": "SAMPLE_STATUS_INVALID",
  "message": "样品状态不允许执行此操作，当前状态为 testing",
  "details": {
    "current_state": "testing",
    "required_state": "assigned"
  },
  "meta": {
    "request_id": "req-e5f6g7h8",
    "timestamp": "2026-05-10T09:15:00Z"
  }
}
```

#### 3.1.4 业务错误码体系

| 错误码前缀 | 模块 | 示例 | 描述 |
|-----------|------|------|------|
| `AUTH_` | 认证授权 | `AUTH_TOKEN_EXPIRED` | 认证相关 |
| `ORDER_` | 委托 | `ORDER_NOT_FOUND` | 委托业务 |
| `SAMPLE_` | 样品 | `SAMPLE_STATUS_INVALID` | 样品业务 |
| `TEST_` | 检测 | `TEST_RECORD_DUPLICATE` | 检测业务 |
| `REPORT_` | 报告 | `REPORT_NOT_SIGNED` | 报告业务 |
| `WORKFLOW_` | 工作流 | `WORKFLOW_TRANSITION_DENIED` | 状态转换 |
| `INSTRUMENT_` | 仪器 | `INSTRUMENT_CALIBRATION_EXPIRED` | 仪器业务 |
| `BILLING_` | 计费 | `BILLING_AMOUNT_MISMATCH` | 计费业务 |
| `SYSTEM_` | 系统 | `SYSTEM_UNEXPECTED_ERROR` | 系统错误 |

#### 3.1.5 API 文档生成

FastAPI 自动从代码生成 OpenAPI 3.0 规范文档：

| 路径 | 说明 |
|------|------|
| `/docs` | Swagger UI 交互式文档 |
| `/redoc` | ReDoc 可读文档 |
| `/openapi.json` | OpenAPI 3.0 JSON 规范 |

#### 3.1.6 核心 API 清单

| 模块 | 路由 | 方法 | 说明 | 认证 |
|------|------|------|------|------|
| **认证** | | | | |
| 认证 | `/api/v1/auth/login` | POST | 用户名密码登录 | - |
| 认证 | `/api/v1/auth/logout` | POST | 登出 | JWT |
| 认证 | `/api/v1/auth/refresh` | POST | Token 刷新 | Refresh Token |
| **委托** | | | | |
| 委托 | `/api/v1/orders` | POST | 新建委托 | JWT |
| 委托 | `/api/v1/orders` | GET | 委托列表（分页） | JWT |
| 委托 | `/api/v1/orders/{id}` | GET | 委托详情 | JWT |
| 委托 | `/api/v1/orders/{id}` | PATCH | 更新委托 | JWT |
| 委托 | `/api/v1/orders/{id}/samples` | POST | 委托中添加样品 | JWT |
| 委托 | `/api/v1/orders/{id}/archive` | POST | 归档委托 | JWT |
| **样品** | | | | |
| 样品 | `/api/v1/samples` | GET | 样品列表（分页） | JWT |
| 样品 | `/api/v1/samples/{code}` | GET | 样品详情 | JWT |
| 样品 | `/api/v1/samples/{code}/receive` | POST | 收样 | JWT |
| 样品 | `/api/v1/samples/{code}/barcode` | POST | 生成条码 | JWT |
| 样品 | `/api/v1/samples/{code}/assign` | POST | 分配检测任务 | JWT |
| **检测** | | | | |
| 任务 | `/api/v1/test-tasks` | GET | 任务列表 | JWT |
| 任务 | `/api/v1/test-tasks/{id}` | GET | 任务详情 | JWT |
| 任务 | `/api/v1/test-tasks/{id}/assign` | POST | 分配人员 | JWT |
| 记录 | `/api/v1/test-tasks/{id}/record` | POST | 提交原始记录 | JWT |
| 记录 | `/api/v1/test-tasks/{id}/record` | GET | 获取原始记录 | JWT |
| 修约 | `/api/v1/test-tasks/{id}/round` | POST | 数值修约 | JWT |
| **报告** | | | | |
| 报告 | `/api/v1/reports` | GET | 报告列表 | JWT |
| 报告 | `/api/v1/reports/{id}` | GET | 报告详情 | JWT |
| 报告 | `/api/v1/reports/{id}/generate` | POST | 生成报告草稿 | JWT |
| 报告 | `/api/v1/reports/{id}/review` | POST | 审核（含签名） | JWT + 密码 |
| 报告 | `/api/v1/reports/{id}/approve` | POST | 批准（含签名） | JWT + 密码 |
| 报告 | `/api/v1/reports/{id}/issue` | POST | 签发（含签名） | JWT + 密码 |
| 报告 | `/api/v1/reports/{id}/pdf` | GET | 下载 PDF | JWT |
| **工作流** | | | | |
| 工作流 | `/api/v1/workflow/definitions` | GET | 获取状态机定义 | JWT |
| 工作流 | `/api/v1/workflow/instances` | GET | 工作流实例列表 | JWT |
| 工作流 | `/api/v1/workflow/{entity}/{id}/state` | GET | 查询当前状态 | JWT |
| 工作流 | `/api/v1/workflow/{entity}/{id}/transition` | POST | 执行状态转换 | JWT |
| **设备** | | | | |
| 设备 | `/api/v1/instruments` | GET | 仪器列表 | JWT |
| 设备 | `/api/v1/instruments/{id}` | GET | 仪器详情 | JWT |
| 设备 | `/api/v1/instruments/{id}/calibration` | POST | 登记校准 | JWT |
| 设备 | `/api/v1/instruments/calibration-due` | GET | 校准到期提醒 | JWT |
| **计费** | | | | |
| 计费 | `/api/v1/billing/calculate` | POST | 计算费用 | JWT |
| 计费 | `/api/v1/billing/invoices` | GET | 账单列表 | JWT |
| 计费 | `/api/v1/billing/invoices/{id}` | GET | 账单详情 | JWT |
| 计费 | `/api/v1/billing/payments` | POST | 登记付款 | JWT |
| 计费 | `/api/v1/billing/reconcile` | POST | 对账核销 | JWT |
| **系统** | | | | |
| 审计 | `/api/v1/system/audit-logs` | GET | 审计日志查询 | JWT (admin) |
| 审计 | `/api/v1/system/audit-logs/export` | GET | 导出审计日志 | JWT (admin) |
| 仪表 | `/api/v1/dashboard` | GET | 仪表盘数据 | JWT |
| 字典 | `/api/v1/system/dict/{type}` | GET | 数据字典 | JWT |

### 3.2 外部接口

#### 3.2.1 仪器串口数据采集

| 属性 | 值 |
|------|------|
| 连接方式 | RS-232 / RS-485 |
| 实现框架 | Electron + node-serialport |
| 运行模式 | 独立进程 (`matlims-instrument`)，通过 HTTP API 与后端通信 |
| 通信协议 | 本地 HTTP（127.0.0.1:8001），JSON 载荷 |
| 波特率 | 9600 / 19200 / 38400，由仪器配置指定 |
| 数据格式 | ASCII 字符串或十六进制，由仪器协议决定 |
| 采集方式 | 定时轮询（1s 至 5s，可配置）或仪器主动上报 |
| 数据流向 | 仪器 → 串口 → Instrument Agent → POST /internal/instrument-data → DB |

**Instrument Agent 数据流**：

```
[仪器] ──→ RS-232/RS-485 ──→ [Instrument Agent]
                                     │
                                     │ POST /internal/instrument-data
                                     │ { instrument_id, data, timestamp, quality }
                                     ▼
                              [FastAPI 后端]
                                     │
                                     │ 写入 audit trail
                                     ▼
                              [PostgreSQL]
                              instrument_data 表
```

**仪器协议适配表**（首期支持）：

| 仪器类型 | 协议 | 波特率 | 数据格式 |
|----------|------|--------|----------|
| 万能材料试验机 | 通用 ASCII | 9600 | 数值 + 单位，每行一条 |
| 压力试验机 | 通用 ASCII | 9600 | 峰值 + 时间戳 |
| 电子天平 | OIML / 自定义 | 4800 | 稳定重量值 |
| 混凝土搅拌机 | 无（手动录入） | - | - |

#### 3.2.2 邮件通知

| 属性 | 值 |
|------|------|
| 协议 | SMTP (STARTTLS) |
| 端口 | 587 或 465 (SSL) |
| 模板 | HTML 邮件模板，模板存储在数据库通知模板表 |
| 发送时机 | 任务分配、审核请求、报告签发、校准到期等 |
| 发送方式 | Celery 异步任务 |
| 重试策略 | 3 次重试，间隔 1 分钟、5 分钟、15 分钟 |

#### 3.2.3 短信通知

| 属性 | 值 |
|------|------|
| 接口 | HTTP API（第三方短信服务商） |
| 接入方式 | 通过适配器模式封装，配置服务商凭据在系统配置表 |
| 发送内容 | 审核提醒、报告完成通知等简短消息（≤ 70 字） |
| 发送方式 | Celery 异步任务 |
| 限额控制 | 每人每日 ≤ 10 条，防止短信轰炸 |

#### 3.2.4 MinIO 对象存储

| 属性 | 值 |
|------|------|
| 协议 | S3 兼容 API |
| 端口 | 9000（内部访问） |
| 存储桶 | `lims-attachments`（检测附件）、`lims-reports`（报告 PDF）、`lims-archives`（归档文件） |
| 文件命名 | `{entity_type}/{entity_id}/{timestamp}_{hash}.{ext}` |
| 生命周期 | 3 年内热存储，3-10 年转标准存储，10 年后可选删除 |
| 访问控制 | 服务端签名 URL，有效期 1 小时 |

### 3.3 内部接口（模块间依赖）

模块间通过 Python 接口定义（协议依赖倒置），不直接耦合实现：

```
M01 users (用户与权限)
    ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑
    │ │ │ │ │ │ │ │ │ │ │ │
M02 orders ──→ M03 samples    M02 → M01 (委托创建人权限)
                  │            M02 → M03 (委托关联样品)
                  ↓            M02 → M10 (委托费用计算)
              M04 testing      M03 → M04 (样品拆分为检测任务)
                  │            M04 → M06 (仪器数据采集)
                  ↓            M04 → M07 (检测方法获取项目)
              M05 reports      M04 → M01 (行级权限:仅本人可见)
                  │            M05 → M04 (报告从检测记录生成)
                  ↓            M05 → M01 (电子签名验证)
M06 instruments   M05 → M08 (状态转换:签发)
    │              M05 → M11 (报告完成通知)
    ↓
M07 methods        M06 → M11 (校准到期提醒)
    │              M06 → M09 (仪器校准记录归档质控)
    ↓
M08 workflow       M07 基础模块,无强依赖
    │              M07 → M01 (方法审核权限)
    ↓
M09 quality        M08 基础模块,被 M02/M04/M05 调用
    │              M09 → M01 (人员能力与权限关联)
    ↓
M10 billing        M10 → M02 (计费基于委托)
    │              M10 → M05 (报告签发后触发计费)
    ↓
M11 notifications  M11 基础模块,被多模块调用
                   M11 → M01 (通知发送对象权限)
    ↓
M12 system         M12 基础模块,所有模块依赖
                   M12 → 所有模块 (审计日志、数据字典)
```

**模块依赖汇总表**：

| 被依赖模块 | 依赖模块 | 依赖类型 |
|-----------|----------|----------|
| M01 用户权限 | M02, M03, M04, M05, M06, M07, M09, M10, M11, M12 | 必须 |
| M07 标准方法 | M04 | 必须 |
| M08 工作流 | M02, M04, M05 | 必须 |
| M12 系统基础 | 全部模块 | 必须 |
| M02 委托收样 | M03, M10 | 必须 |
| M03 样品管理 | M04 | 必须 |
| M04 检测任务 | M05, M06, M07 | 必须 |
| M05 报告管理 | M11 | 必须 |
| M06 仪器设备 | M09, M11 | 可选 |
| M09 质量体系 | 无（一期） | - |
| M10 计费财务 | M11 | 可选 |
| M11 通知消息 | 无（被调用方） | - |

---

## 4 运行设计

### 4.1 运行模块组合

系统在生产环境通过以下进程组合运行：

```
┌──────────────────────────────────────────────────────────────┐
│                      单台服务器                              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Nginx (1 进程)                                      │     │
│  │  端口: 80, 443                                     │     │
│  │  资源: 50 MB RAM                                   │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Gunicorn (主进程 + 4 Worker)                        │     │
│  │  端口: 8000 (仅内网)                               │     │
│  │  Worker: UvicornWorker x 4                        │     │
│  │  线程: 每个 Worker 单线程(异步)                     │     │
│  │  资源: 4 × 150 MB = 600 MB RAM                     │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Celery Worker (4 并发)                              │     │
│  │  端口: 9000 (Flower 监控)                          │     │
│  │  池: prefork × 4                                   │     │
│  │  资源: 4 × 200 MB = 800 MB RAM                     │     │
│  │  任务:                                             │     │
│  │    - report.generate: 生成 PDF 报告                │     │
│  │    - notification.send: 发送邮件/短信              │     │
│  │    - barcode.print: 条码打印                       │     │
│  │    - sample.archive: 样品归档                      │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Celery Beat (1 进程)                                │     │
│  │  任务:                                             │     │
│  │    - 每 8 小时: 校准到期检查                       │     │
│  │    - 每日 9:00: 发送到期提醒                       │     │
│  │    - 每日 2:00: 数据库自动备份                     │     │
│  │    - 每 5 分钟: 超时流程检查                       │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Instrument Agent (1 进程, Electron)                  │     │
│  │  端口: 8001 (仅本地)                               │     │
│  │  资源: 100 MB RAM                                  │     │
│  │  串口: RS-232/RS-485 轮询                          │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ PostgreSQL (1 实例)                                 │     │
│  │  端口: 5432                                        │     │
│  │  连接池: pgbouncer (50 连接)                       │     │
│  │  资源: 2 GB RAM (shared_buffers=1GB)               │     │
│  │  WAL: enabled, 归档到 MinIO                        │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Redis (1 实例)                                      │     │
│  │  端口: 6379                                        │     │
│  │  用途: 缓存 + Celery Broker                        │     │
│  │  资源: 512 MB RAM                                  │     │
│  │  持久化: AOF (每秒刷盘)                            │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ MinIO (1 实例)                                      │     │
│  │  端口: 9000 (API) / 9001 (Console)                 │     │
│  │  存储: /data/minio (独立数据盘)                     │     │
│  │  资源: 256 MB RAM                                  │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 运行控制

#### 4.2.1 Systemd 单元文件示例

**Gunicorn 服务** (`/etc/systemd/system/matlims-api.service`):

```ini
[Unit]
Description=MatLIMS FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=matlims
Group=matlims
WorkingDirectory=/opt/matlims/app
Environment=PATH=/opt/matlims/venv/bin
ExecStart=/opt/matlims/venv/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile /var/log/matlims/access.log \
    --error-logfile /var/log/matlims/error.log \
    main:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Celery Worker 服务** (`/etc/systemd/system/matlims-worker.service`):

```ini
[Unit]
Description=MatLIMS Celery Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=matlims
Group=matlims
WorkingDirectory=/opt/matlims/app
Environment=PATH=/opt/matlims/venv/bin
ExecStart=/opt/matlims/venv/bin/celery -A src.worker worker \
    --concurrency=4 \
    --loglevel=info \
    --logfile=/var/log/matlims/celery-worker.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### 4.2.2 启动与停止顺序

**启动顺序**（依赖自底向上）：

```
1. PostgreSQL  (基础数据层)
2. Redis       (缓存与消息队列)
3. MinIO       (对象存储)
4. Gunicorn    (Web 应用)
5. Celery Beat (定时调度)
6. Celery Worker (异步任务)
7. Nginx       (反向代理)
8. Instrument Agent (可选,需要物理串口连接时)
```

**停止顺序**（反向）：

```
1. Nginx       (停止外部访问)
2. Instrument Agent
3. Celery Worker (等待正在执行任务完成)
4. Celery Beat
5. Gunicorn    (等待请求处理完毕)
6. MinIO
7. Redis
8. PostgreSQL  (最后,确保数据写入)
```

#### 4.2.3 健康检查

| 组件 | 检查方式 | 健康端点 | 检查频率 |
|------|----------|----------|----------|
| FastAPI | HTTP GET | `/api/v1/health` | 30 秒 |
| Celery Worker | Flower 监控 + 心跳 | Flower API | 60 秒 |
| PostgreSQL | `pg_isready` | - | 30 秒 |
| Redis | `redis-cli ping` | - | 30 秒 |
| MinIO | HTTP GET | `/minio/health/live` | 30 秒 |
| Nginx | HTTP GET | `/` (返回 200) | 30 秒 |

`/api/v1/health` 返回内容：

```json
{
  "status": "healthy",
  "timestamp": "2026-05-10T08:30:00Z",
  "components": {
    "database": {"status": "up", "latency_ms": 2},
    "redis": {"status": "up", "latency_ms": 1},
    "minio": {"status": "up", "latency_ms": 5}
  },
  "version": "1.0.0"
}
```

### 4.3 运行时间与资源

#### 4.3.1 服务器配置推荐

| 配置级别 | CPU | 内存 | 硬盘 | 适用场景 |
|----------|-----|------|------|----------|
| 标准配置 | 4 核 | 8 GB | 500 GB SSD | 日均 200-500 样品，20 用户 |
| 高配 | 8 核 | 16 GB | 1 TB SSD | 日均 500-1000 样品，50 用户 |

**磁盘空间规划**（标准配置 500 GB）：

| 用途 | 空间 | 说明 |
|------|------|------|
| 操作系统 | 50 GB | Ubuntu/AlmaLinux 系统分区 |
| PostgreSQL | 100 GB | 数据 + 索引 + WAL，年增量约 30 GB |
| MinIO | 300 GB | 附件与报告 PDF |
| 日志 | 50 GB | 应用日志 + Nginx 日志 |
| 预留 | 50 GB | 系统维护与升级 |

#### 4.3.2 资源占用预估

| 进程 | CPU 峰值 | 内存占用 | 磁盘 I/O |
|------|----------|----------|----------|
| Gunicorn (4 workers) | 1.5 核 | 600 MB | 中 |
| Celery Worker (4 workers) | 2 核 | 800 MB | 中 |
| PostgreSQL | 1.5 核 | 2 GB | 高 |
| Redis | 0.5 核 | 512 MB | 低 |
| MinIO | 0.5 核 | 256 MB | 高 |
| Nginx | 0.2 核 | 50 MB | 低 |
| Instrument Agent | 0.3 核 | 100 MB | 低 |
| **总计** | **~6.5 核** | **~4.3 GB** | - |

#### 4.3.3 运行时间表

| 活动 | 时间 | 周期 |
|------|------|------|
| 日常业务 | 08:00 - 17:30 | 周一至周五 |
| 数据库备份 | 02:00 | 每日 |
| 数据库 VACUUM | 03:00 | 每周六 |
| 审计日志归档 | 03:30 | 每月 1 日 |
| 校准到期检查 | 09:00 | 每日 |
| 超时流程检查 | 每 5 分钟 | 持续 |

系统需 7×24 运行，工作日 08:00-17:30 为业务高峰期。非工作日仅执行定时任务。

---

## 5 系统数据结构设计

### 5.1 逻辑结构设计

系统核心业务表共计 **50+ 张**，按模块分类如下：

#### 5.1.1 M01 用户权限（6 表）

| 表名 | 用途 | 主键 | 核心字段 |
|------|------|------|----------|
| `users` | 用户主表 | BIGINT `id` | 用户名、密码哈希、姓名、手机号、邮箱、状态、角色ID、能力资质标记 |
| `roles` | 角色定义 | BIGINT `id` | 角色编码、角色名称、描述 |
| `permissions` | 权限定义 | BIGINT `id` | 权限编码、权限名称、资源类型、操作类型、行级过滤表达式 |
| `role_permissions` | 角色权限关联 | 联合主键 | role_id, permission_id |
| `user_roles` | 用户角色关联 | 联合主键 | user_id, role_id |
| `e_signatures` | 电子签名记录 | BIGINT `id` | 用户ID、操作类型、目标实体、签名字段哈希、时间戳、IP 地址 |

#### 5.1.2 M02 委托收样（5 表）

| 表名 | 用途 | 主键 | 核心字段 |
|------|------|------|----------|
| `orders` | 委托主表 | BIGINT `id` | 委托编号、客户名、联系人、电话、委托日期、要求完成日期、状态、工作流实例ID |
| `order_items` | 委托样品项 | BIGINT `id` | 委托ID、检测标准编号、检测项目ID、数量、要求、备注 |
| `order_attachments` | 委托附件 | BIGINT `id` | 委托ID、MinIO 对象键、文件类型、上传时间 |
| `clients` | 客户档案 | BIGINT `id` | 客户编码、单位名称、统一社会信用代码、联系人、电话、地址、状态 |
| `order_change_logs` | 委托变更日志 | BIGINT `id` | 委托ID、变更内容(JB)、变更人、变更时间 |

#### 5.1.3 M03 样品管理（4 表）

| 表名 | 用途 | 主键 | 核心字段 |
|------|------|------|----------|
| `samples` | 样品主表 | BIGINT `id` | 样品编号、委托ID、样品名称、规格型号、生产厂家、样品状态、接收日期、工作流实例ID |
| `sample_locations` | 样品存放位置 | BIGINT `id` | 样品ID、库房、货架号、存放时间、取回时间 |
| `sample_disposals` | 样品处置记录 | BIGINT `id` | 样品ID、处置方式(退还/留存/废弃)、处置人、处置时间、备注 |
| `sample_blind_codes` | 盲样编号管理 | BIGINT `id` | 原样品ID、盲样编号、映射关系(加密)、创建时间 |

#### 5.1.4 M04 检测任务（6 表）

| 表名 | 用途 | 主键 | 核心字段 |
|------|------|------|----------|
| `test_tasks` | 检测任务主表 | BIGINT `id` | 任务编号、样品ID、检测项目ID、分配人员、计划完成日期、实际完成日期、任务状态 |
| `original_records` | 原始记录主表 | BIGINT `id` | 记录ID、任务ID、检测人、检测日期、环境温湿度、检测依据、审核状态 |
| `record_data` | 检测数据明细 | BIGINT `id` | 原始记录ID、检测指标、原始数值、修约规则、修约结果、单位、计算公式 |
| `record_attachments` | 原始记录附件 | BIGINT `id` | 原始记录ID、MinIO 对象键、文件类型、附件说明 |
| `instrument_records` | 仪器使用记录 | BIGINT `id` | 任务ID、仪器ID、使用前状态、使用后状态、使用时长 |
| `nonconformities` | 不合格品记录 | BIGINT `id` | 任务ID、不合格项目、实测值、标准值、处理意见、处理人 |

#### 5.1.5 M05 报告管理（5 表）

| 表名 | 用途 | 主键 | 核心字段 |
|------|------|------|----------|
| `reports` | 报告主表 | BIGINT `id` | 报告编号、委托ID、样品ID、报告状态、生成日期、签发日期、报告模板ID |
| `report_sections` | 报告章节内容 | BIGINT `id` | 报告ID、章节编号、章节标题、章节内容(HTML)、排序号 |
| `report_signatures` | 报告签名记录 | BIGINT `id` | 报告ID、签名角色(检测/审核/批准/签发)、签名人、签名时间、签名确认方式 |
| `report_distribution` | 报告分发记录 | BIGINT `id` | 报告ID、接收方、分发方式(电子版/纸质)、分发时间、接收人 |
| `report_revisions` | 报告修订记录 | BIGINT `id` | 报告ID、修订原因、修订内容、修订人、修订时间、原版报告ID |

#### 5.1.6 M06 设备仪器（7 表）

| 表名 | 用途 | 主键 | 核心字段 |
|------|------|------|----------|
| `instruments` | 仪器台账 | BIGINT `id` | 仪器编号、名称、型号、生产厂家、精度等级、状态、所在部门、保管人 |
| `instrument_calibrations` | 校准记录 | BIGINT `id` | 仪器ID、校准日期、校准结果、下次校准日期、校准机构、证书编号 |
| `instrument_verifications` | 期间核查记录 | BIGINT `id` | 仪器ID、核查日期、核查结果、核查人、核查方法 |
| `instrument_maintenance` | 维护保养记录 | BIGINT `id` | 仪器ID、维护日期、维护内容、维护人、维护结果 |
| `instrument_usage` | 仪器使用记录 | BIGINT `id` | 仪器ID、使用日期、使用人、用途、使用时长、使用前后状态 |
| `instrument_data` | 仪器采集数据 | BIGINT `id` | 仪器ID、原始数据(JSON)、采集时间、数据质量标记 |
| `instruments_serial_ports` | 串口参数 | BIGINT `id` | 仪器ID、端口号(COM)、波特率、数据位、停止位、校验位 |

#### 5.1.7 M07 标准方法（4 表）

| 表名 | 用途 | 主键 | 核心字段 |
|------|------|------|----------|
| `test_methods` | 检测方法库 | BIGINT `id` | 标准编号、标准名称、发布机构、发布日期、实施日期、有效性状态 |
| `method_items` | 检测项目定义 | BIGINT `id` | 方法ID、项目名称、单位、修约规则、有效位数、限值类型、限值 |
| `method_attachments` | 检测方法附件 | BIGINT `id` | 方法ID、MinIO 对象键、附件类型(PDF标准文本) |
| `method_revisions` | 方法修订记录 | BIGINT `id` | 方法ID、修订内容、修订原因、生效日期 |

#### 5.1.8 M08 工作流引擎（5 表）

| 表名 | 用途 | 主键 | 核心字段 |
|------|------|------|----------|
| `workflow_definitions` | 工作流定义 | BIGINT `id` | 实体类型、状态列表(JSON)、转换规则(JSON)、初始状态、版本号 |
| `workflow_instances` | 工作流实例 | BIGINT `id` | 实体类型、实体ID、当前状态、定义ID、创建时间、完成时间 |
| `workflow_transitions` | 状态转换历史 | BIGINT `id` | 实例ID、源状态、目标状态、操作人、操作时间、签名确认 |
| `workflow_reminders` | 超时提醒 | BIGINT `id` | 实例ID、超时阈值、提醒发送时间、接收人 |
| `workflow_anomalies` | 异常处理记录 | BIGINT `id` | 实例ID、异常类型、异常描述、处理措施、处理人、处理时间 |

#### 5.1.9 M09 质量体系（5 表）

| 表名 | 用途 | 主键 | 核心字段 |
|------|------|------|----------|
| `personnel_competence` | 人员能力档案 | BIGINT `id` | 人员ID、检测方法能力列表、授权范围、授权日期、有效期 |
| `supervision_plans` | 监督计划 | BIGINT `id` | 计划名称、监督对象、监督方法、计划日期、监督人 |
| `internal_audits` | 内部审核 | BIGINT `id` | 审核编号、审核范围、审核日期、审核组长、审核发现、审核结论 |
| `corrective_actions` | 纠正预防措施 | BIGINT `id` | 来源、问题描述、原因分析、纠正措施、责任人、截止日期、状态 |
| `controlled_documents` | 受控文件 | BIGINT `id` | 文件编号、文件名称、版本、发布日期、废止日期、状态 |

#### 5.1.10 M10 计费财务（8 表）

| 表名 | 用途 | 主键 | 核心字段 |
|------|------|------|----------|
| `price_matrices` | 价格矩阵主表 | BIGINT `id` | 矩阵名称、生效日期、失效日期、状态 |
| `price_matrix_items` | 价格矩阵明细 | BIGINT `id` | 矩阵ID、样品类别、检测标准编号、检测项目、单价、折扣率 |
| `invoices` | 账单 | BIGINT `id` | 账单编号、委托ID、客户ID、总金额、开票状态、开票日期 |
| `invoice_items` | 账单明细 | BIGINT `id` | 账单ID、检测项目、数量、单价、金额 |
| `payments` | 付款记录 | BIGINT `id` | 账单ID、付款金额、付款方式(转账/现金)、付款凭证号、付款日期、付款人 |
| `payment_reconciliations` | 对账记录 | BIGINT `id` | 账单ID、匹配金额、对账状态、对账人、对账时间 |
| `payment_receipts` | 收款凭证 | BIGINT `id` | 收款凭证编号、凭证类型(银行回单)、文件路径、上传时间 |
| `credit_notes` | 红字冲销 | BIGINT `id` | 原账单ID、冲销金额、冲销原因、操作人、操作时间 |

#### 5.1.11 M11 通知消息（3 表）

| 表名 | 用途 | 主键 | 核心字段 |
|------|------|------|----------|
| `notification_templates` | 通知模板 | BIGINT `id` | 模板编码、模板名称、类型(email/sms/inbox)、标题模板、内容模板、变量定义 |
| `notification_queues` | 发送队列 | BIGINT `id` | 模板ID、接收人、变量值(Json)、发送状态、发送时间、重试次数 |
| `notification_logs` | 发送日志 | BIGINT `id` | 队列ID、发送结果、响应内容、发送时间 |

#### 5.1.12 M12 系统基础（5 表）

| 表名 | 用途 | 主键 | 核心字段 |
|------|------|------|----------|
| `system_configs` | 系统配置 | BIGINT `id` | 配置键、配置值、配置类型、描述 |
| `data_dictionaries` | 数据字典 | BIGINT `id` | 字典类型、字典值、显示名称、排序号、启用状态 |
| `audit_log` | 审计日志(Triggers写入) | BIGINT `id` | 表名、操作类型、旧数据、新数据、操作人、IP、时间 |
| `backup_records` | 备份记录 | BIGINT `id` | 备份时间、备份类型、文件大小、备份路径、状态 |
| `scheduled_jobs` | 定时任务定义 | BIGINT `id` | 任务名称、Cron表达式、执行类、上次运行时间、下次运行时间 |

### 5.2 物理结构设计

#### 5.2.1 索引策略

| 索引类型 | 适用场景 | 示例 |
|----------|----------|------|
| 主键索引 | 所有表的主键 | `PRIMARY KEY (id)` |
| 唯一索引 | 业务唯一键 | `CREATE UNIQUE INDEX ON orders(order_code)` |
| B树索引 | 常规查询与过滤 | `CREATE INDEX ON samples(status)` |
| 组合索引 | 多条件查询 | `CREATE INDEX ON test_tasks(status, assigned_to)` |
| GIN 索引 | JSONB 查询 | `CREATE INDEX ON audit_log USING GIN(new_data)` |
| 日期范围索引 | 时间范围查询 | `CREATE INDEX ON samples(received_date)` |
| 全文索引 | 文本搜索 | `CREATE INDEX ON clients USING GIN(to_tsvector('simple', name))` |

**核心索引定义清单**：

```sql
-- 委托表
CREATE UNIQUE INDEX uix_orders_code ON orders(order_code);
CREATE INDEX ix_orders_status ON orders(status);
CREATE INDEX ix_orders_client ON orders(client_id);
CREATE INDEX ix_orders_received_date ON orders(received_date);

-- 样品表
CREATE UNIQUE INDEX uix_samples_code ON samples(sample_code);
CREATE INDEX ix_samples_order ON samples(order_id);
CREATE INDEX ix_samples_status ON samples(status);

-- 检测任务
CREATE UNIQUE INDEX uix_tasks_code ON test_tasks(task_code);
CREATE INDEX ix_tasks_sample ON test_tasks(sample_id);
CREATE INDEX ix_tasks_status_assignee ON test_tasks(status, assigned_to);

-- 报告
CREATE UNIQUE INDEX uix_reports_code ON reports(report_code);
CREATE INDEX ix_reports_order ON reports(order_id);
CREATE INDEX ix_reports_status ON reports(status);
CREATE INDEX ix_reports_issued_date ON reports(issued_date);

-- 审计日志
CREATE INDEX ix_audit_log_table ON audit_log(table_name);
CREATE INDEX ix_audit_log_user ON audit_log(user_id);
CREATE INDEX ix_audit_log_time ON audit_log(executed_at);
CREATE INDEX ix_audit_log_data ON audit_log USING GIN(new_data);

-- 用户权限
CREATE UNIQUE INDEX uix_users_username ON users(username);
CREATE INDEX ix_users_role ON users(role_id);
```

#### 5.2.2 审计触发器设计

```sql
-- 审计日志触发器函数（通用）
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        table_name,
        operation,
        old_data,
        new_data,
        user_id,
        user_name,
        ip_address
    ) VALUES (
        TG_TABLE_NAME,
        TG_OP,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD)::jsonb END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW)::jsonb END,
        current_setting('app.user_id', true)::bigint,
        current_setting('app.user_name', true),
        current_setting('app.ip_address', true)::inet
    );

    IF TG_OP = 'DELETE' THEN RETURN OLD;
    ELSE RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

对所有审计日志相关的表（`audit_log`），额外设置保护触发器：

```sql
-- 防止审计日志被修改或删除
CREATE OR REPLACE FUNCTION protect_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION '审计日志不可修改或删除';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_protect_audit_log
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION protect_audit_log();
```

#### 5.2.3 分区策略

超过 100 万行的表采用分区策略：

| 表名 | 分区策略 | 分区键 | 分区间隔 |
|------|----------|--------|----------|
| `audit_log` | 范围分区 | `executed_at` | 按月 |
| `record_data` | 范围分区 | `created_at` | 按年 |
| `workflow_transitions` | 范围分区 | `transitioned_at` | 按年 |

```sql
-- 审计日志按月分区示例
CREATE TABLE audit_log (
    id          BIGSERIAL,
    table_name  VARCHAR(128),
    operation   VARCHAR(10),
    old_data    JSONB,
    new_data    JSONB,
    user_id     BIGINT,
    executed_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (executed_at);

CREATE TABLE audit_log_2026_01 PARTITION OF audit_log
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE audit_log_2026_02 PARTITION OF audit_log
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
-- 自动分区创建由定时任务 pg_partman 管理
```

#### 5.2.4 WORM 存储实现

原始记录在归档后变为只读，实现方式：

1. `original_records.is_archived = true` 标记归档完成
2. 数据库触发器拦截 `UPDATE` 和 `DELETE` 操作
3. 归档后记录同步写入 MinIO 作为 PDF 附件长期保存

```sql
CREATE OR REPLACE FUNCTION protect_archived_record()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.is_archived = true THEN
        RAISE EXCEPTION '已归档的原始记录不允许修改或删除';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_protect_archived_record
    BEFORE UPDATE OR DELETE ON original_records
    FOR EACH ROW EXECUTE FUNCTION protect_archived_record();
```

### 5.3 数据结构与程序关系

```
程序模块               访问的表                       访问类型
─────────────────────────────────────────────────────────────────
M01 users              users, roles,                 CRU
                       permissions, role_permissions,
                       user_roles, e_signatures

M02 orders             orders, order_items,          CRUD
                       order_attachments, clients,
                       order_change_logs

M03 samples            samples, sample_locations,    CRUD
                       sample_disposals, sample_blind_codes

M04 testing            test_tasks, original_records, CRU
                       record_data, record_attachments,
                       instrument_records, nonconformities

M05 reports            reports, report_sections,     CRU
                       report_signatures,
                       report_distribution, report_revisions

M06 instruments        instruments, instrument_      CRUD
                       calibrations, instrument_
                       verifications, instrument_
                       maintenance, instrument_usage,
                       instrument_data, instruments_
                       serial_ports

M07 methods            test_methods, method_items,   CR
                       method_attachments

M08 workflow           workflow_definitions,         CR
                       workflow_instances, workflow_
                       transitions, workflow_
                       reminders, workflow_anomalies

M09 quality            personnel_competence,         CRUD
                       supervision_plans, internal_
                       audits, corrective_actions,
                       controlled_documents

M10 billing            price_matrices, price_matrix_ CRU
                       items, invoices, invoice_items,
                       payments, payment_reconcilia-
                       tions, payment_receipts,
                       credit_notes

M11 notifications      notification_templates,       CRU
                       notification_queues, noti-
                       fication_logs

M12 system             system_configs, data_dicts,   CR
                       audit_log, backup_records,
                       scheduled_jobs
```

**访问类型说明**：C=Create, R=Read, U=Update, D=Delete

**多模块共享表**：

| 表名 | 访问模块 | 说明 |
|------|----------|------|
| `users` | 全部 | 用户基础信息 |
| `roles` | M01, M08, M09 | 角色定义，用于权限校验与能力关联 |
| `permissions` | M01, M08 | 权限定义与行级过滤 |
| `e_signatures` | M04, M05 | 检测签名与报告签名 |
| `audit_log` | M01, M12 | 审计日志查询 |
| `data_dictionaries` | 全部 | 全局字典 |
| `workflow_instances` | M02, M03, M04, M05 | 各实体工作流状态 |

---

## 6 系统出错处理设计

### 6.1 出错信息表

#### 6.1.1 系统级错误

| 错误码 | 错误信息 | HTTP 状态 | 触发场景 | 处理方式 |
|--------|----------|-----------|----------|----------|
| 50001 | 系统内部错误，请联系管理员 | 500 | 未预期异常 | 记录日志，返回通用错误，通知运维 |
| 50002 | 数据库连接失败 | 503 | PostgreSQL 不可达 | 自动重试 3 次，失败后返回 503 |
| 50003 | Redis 连接失败 | 503 | Redis 不可达 | 降级到无缓存模式，记录告警 |
| 50004 | 存储服务不可用 | 503 | MinIO 不可达 | 阻止文件上传操作，记录告警 |
| 50005 | 请求超时 | 504 | API 处理超过 30 秒 | 终止请求，记录慢查询日志 |
| 40001 | 请求参数错误 | 400 | Pydantic 校验失败 | 返回字段级错误信息 |
| 40002 | 请求体格式错误 | 400 | 非 JSON 请求体 | 返回格式错误信息 |

#### 6.1.2 认证授权错误

| 错误码 | 错误信息 | HTTP 状态 | 触发场景 | 处理方式 |
|--------|----------|-----------|----------|----------|
| 10001 | 未提供认证令牌 | 401 | 请求缺少 Authorization 头 | 返回登录页面链接 |
| 10002 | 认证令牌已过期 | 401 | JWT Token 超时 | 返回刷新令牌指引 |
| 10003 | 认证令牌无效 | 401 | Token 签名错误或篡改 | 要求重新登录 |
| 10004 | 密码错误，剩余 {n} 次机会 | 403 | 密码验证失败 | 计数器递减，5 次后锁定 |
| 10005 | 账户已锁定，请 {time} 后重试 | 403 | 连续失败 5 次 | 锁定 30 分钟，记录安全日志 |
| 10006 | 权限不足 | 403 | 无对应资源权限 | 返回权限不足提示 |
| 10007 | 无权访问该数据行 | 403 | 行级权限过滤无结果 | 视为数据不存在 |

#### 6.1.3 业务流程错误

| 错误码 | 错误信息 | HTTP 状态 | 触发场景 | 处理方式 |
|--------|----------|-----------|----------|----------|
| 20001 | 委托编号已存在 | 409 | 重复的委托编号 | 提示检查数据 |
| 20002 | 委托状态不允许此操作 | 409 | 已归档委托尝试修改 | 提示当前状态 |
| 30001 | 样品状态不允许此操作 | 409 | 状态机转换校验失败 | 提示当前状态与允许操作 |
| 30002 | 样品编号已分配 | 409 | 重复的样品编号 | 生成新编号 |
| 40001 | 检测记录已提交 | 409 | 已提交的原始记录不允许修改 | 走报告修订流程 |
| 40002 | 仪器校准已过期 | 400 | 使用过期仪器录入数据 | 告警并允许继续(需说明) |
| 50001 | 报告已签发，不可修改 | 409 | 修改已签发报告 | 走报告修订流程 |
| 50002 | 电子签名验证失败 | 400 | 签名密码不匹配 | 提示重新输入 |
| 60001 | 工作流程转换非法 | 400 | 状态转换不在定义中 | 提示合法转换路径 |
| 80001 | 账单已核销，不可修改 | 409 | 修改已核销账单 | 提示走冲销流程 |

#### 6.1.4 前端错误展示

前端按错误类型采用不同展示策略：

| 错误类型 | 展示方式 | 组件 |
|----------|----------|------|
| 表单校验错误 | 字段级红框提示 | Ant Design Form.Item |
| 业务错误（4xx） | Message 错误提示 | Ant Design message.error |
| 系统错误（5xx） | Result 错误页面 | Ant Design Result |
| 网络断开 | Alert 全局告警 | Ant Design Alert (顶部固定) |

### 6.2 补救措施

#### 6.2.1 密码锁定机制

| 参数 | 值 | 说明 |
|------|-----|------|
| 最大失败次数 | 5 次 | 连续 5 次密码错误触发锁定 |
| 锁定时间 | 30 分钟 | 锁定后等待 30 分钟自动解锁 |
| 锁定存储 | Redis Key | `lims:lock:user:{user_id}` |
| 失败计数器 | Redis Key | `lims:fail:{user_id}`，TTL 5 分钟 |
| 解锁方式 | 自动定时解锁，或管理员手动解锁 | - |
| 安全告警 | 邮件通知 | 第 3 次失败时发送告警邮件给管理员 |

#### 6.2.2 数据备份策略

| 备份类型 | 频率 | 工具 | 保留时间 | 存储位置 |
|----------|------|------|----------|----------|
| 全量备份 | 每周日 02:00 | `pg_dump` | 12 个月 | 本地磁盘 + MinIO |
| 增量备份（WAL归档） | 每 10 分钟 | `pg_walog` | 30 天 | MinIO |
| 实时复制 | 持续 | PostgreSQL Streaming Replication | - | 备用服务器（如有） |
| MinIO 同步 | 每 6 小时 | MinIO Client (`mc mirror`) | 12 个月 | 异地备份服务器（如有） |

**备份验证**：
- 每周执行一次备份恢复验证，将备份恢复到测试数据库并运行校验脚本
- 验证内容包括：表完整性、数据行数对比、关键业务记录抽检

#### 6.2.3 故障恢复

| 故障场景 | 恢复步骤 | 预计恢复时间 |
|----------|----------|-------------|
| PostgreSQL 崩溃 | 1. 停止所有应用服务；2. 检查 PG 日志定位故障；3. 重启 PG；4. 验证数据一致性；5. 重启应用 | 5-15 分钟 |
| Redis 崩溃 | 1. 重启 Redis；2. AOF 自动恢复；3. 客户端自动重连 | 1-3 分钟 |
| Gunicorn 崩溃 | 1. Systemd 自动重启；2. 检查错误日志 | < 30 秒 |
| Nginx 崩溃 | 1. Systemd 自动重启 | < 10 秒 |
| 磁盘满 | 1. 清理过期日志（保留 3 天）；2. 清理旧备份；3. 如仍不足，扩充磁盘 | 30 分钟 |
| 数据误删除 | 1. 从 WAL 恢复到误删除前时间点；2. 对比数据差异；3. 手动补录缺失数据 | 1-4 小时 |
| 全机房断电 | 1. 启动 UPS（30 分钟缓冲）；2. 电力恢复后按 4.2 节顺序启动服务；3. 验证数据一致性 | 1-2 小时 |

### 6.3 系统维护设计

#### 6.3.1 日志管理

| 日志类型 | 输出位置 | 格式 | 保留时间 | 轮转策略 |
|----------|----------|------|----------|----------|
| 应用日志 | `/var/log/matlims/` | JSON | 90 天 | logrotate, 每日 |
| 访问日志 | `/var/log/matlims/access.log` | CLF | 30 天 | logrotate, 每日 |
| 错误日志 | `/var/log/matlims/error.log` | JSON | 180 天 | logrotate, 每日 |
| Celery 日志 | `/var/log/matlims/celery-*.log` | TEXT | 30 天 | logrotate, 每周 |
| Nginx 日志 | `/var/log/nginx/` | CLF | 30 天 | logrotate, 每日 |
| PG 日志 | `/var/log/postgresql/` | TEXT | 90 天 | logrotate, 每周 |
| 审计日志 | `audit_log` 表 (DB内) | JSONB | 10 年 | 按月分区 |

logrotate 配置示例（`/etc/logrotate.d/matlims`）：

```
/var/log/matlims/*.log {
    daily
    rotate 90
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

#### 6.3.2 数据库维护

| 维护任务 | 执行方式 | 频率 | 说明 |
|----------|----------|------|------|
| VACUUM ANALYZE | Celery Beat | 每周六 03:00 | 回收死元组 + 更新统计信息 |
| VACUUM FULL | 手动执行 | 按需（年度） | 需要锁表，维护窗口执行 |
| REINDEX | Celery Beat | 每季度 | 重建索引 |
| 过期数据清理 | Celery Beat | 每月 1 日 03:00 | 清理 90 天前的 session 与通知队列 |
| 分区表管理 | pg_partman | 每日 | 自动创建下月分区 |
| 统计信息更新 | PostgreSQL Auto-Analyze | 持续 | autovacuum 触发 |
| 慢查询分析 | pg_stat_statements | 每周 | 识别性能瓶颈 |

#### 6.3.3 监控指标

| 指标类型 | 监控项 | 告警阈值 | 告警方式 |
|----------|--------|----------|----------|
| 系统资源 | CPU 使用率 | > 80% 持续 5 分钟 | 邮件 + 站内消息 |
| 系统资源 | 内存使用率 | > 85% | 邮件 + 站内消息 |
| 系统资源 | 磁盘使用率 | > 80% | 邮件 |
| 系统资源 | 磁盘使用率 | > 90% | 邮件(紧急) |
| 数据库 | 连接数 | > 40 (共 50) | 邮件 |
| 数据库 | 慢查询数 | > 10/分钟 | 邮件 |
| 数据库 | 复制延迟 | > 60 秒 | 邮件 |
| 应用 | P95 响应时间 | > 1000ms 持续 5 分钟 | 邮件 |
| 应用 | 500 错误率 | > 1% | 邮件 |
| 队列 | Celery 积压 | > 100 件 | 邮件 |
| 安全 | 登录失败 | > 10 次/分钟 | 邮件(紧急) |
| 业务 | 校准到期 | ≤ 7 天 | 站内消息 |

#### 6.3.4 版本升级

| 步骤 | 操作 | 回退方案 |
|------|------|----------|
| 1 | 备份数据库 | 恢复备份 |
| 2 | 停止应用服务 | 重新启动旧版本 |
| 3 | 执行数据库迁移（Alembic） | 运行 downgrade 脚本 |
| 4 | 部署新代码 | 回退到旧代码版本 |
| 5 | 启动应用服务 | - |
| 6 | 运行冒烟测试 | - |
| 7 | 验证关键业务流程 | - |
| 8 | 开放外部访问 | - |

升级过程预计 5-15 分钟停机窗口，安排在非工作时间（周五 19:00 或周末）执行。

---

> **文档变更记录**
>
> | 版本 | 日期 | 修改内容 | 修改人 |
> |------|------|----------|--------|
> | V1.0 | 2026-05-10 | 初始版本发布 | - |
