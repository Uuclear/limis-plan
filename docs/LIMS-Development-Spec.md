# 建设材料检测 LIMS 技术开发方案（合订本）

> **项目名称**: MatLIMS | **版本**: V2.0 | **日期**: 2026-05-10 | **标准**: GB/T 8567-2006

---

# 第一部分: 概要设计

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

---

# 第二部分: 详细设计

# 02 详细设计说明书

> 本文档依据 GB/T 8567-2006《计算机软件文档编制规范》中"详细设计说明书"模板编写。
> 对应架构决策见 [01-architecture.md](./01-architecture.md)。

---

## 目录

- [3 程序系统的设计说明](#3-程序系统的设计说明)
  - [3.1 程序1: 用户与认证模块](#31-程序1-用户与认证模块)
  - [3.2 程序2: 样品管理类](#32-程序2-样品管理类)
  - [3.3 程序3: 检测管理模块](#33-程序3-检测管理模块)
  - [3.4 程序4: 报告管理模块](#34-程序4-报告管理模块)
  - [3.5 程序5: 原始记录模块](#35-程序5-原始记录模块)
  - [3.6 程序6: 设备管理模块](#36-程序6-设备管理模块)
  - [3.7 程序7: 标准方法库模块](#37-程序7-标准方法库模块)
  - [3.8 程序8: 工作流引擎模块](#38-程序8-工作流引擎模块)
  - [3.9 程序9: 计费管理模块](#39-程序9-计费管理模块)
  - [3.10 程序10: 质量管控模块](#3a-程序10-质量管控模块)
  - [3.11 程序11: 统计报表模块](#3b-程序11-统计报表模块)
  - [3.12 程序12: 系统配置模块](#3c-程序12-系统配置模块)

---

## 3 程序系统的设计说明

### 全局约定

| 条目 | 约定 |
|---|---|
| 架构风格 | Clean Architecture (Domain → Use Cases → Adapters → Frameworks) |
| 前端框架 | React 18 + TypeScript + Zustand + React Query |
| 后端框架 | Python FastAPI + SQLAlchemy 2.0 + Alembic |
| 数据库 | PostgreSQL 15+ |
| 工作流引擎 | 轻量状态机 (JSON 定义持久化至 workflow_definitions 表) |
| 报告生成 | HTML 模板 + WeasyPrint 转 PDF |
| 电子签名 | 密码二次确认 (密码哈希校验) |
| 检测表单 | 硬编码 React 组件 (200+ 检测方法) |
| 串口通信 | Electron + node-serialport (RS-232/RS-485) |
| ID 策略 | ULID (排序友好, URL-safe Base32) |
| 时间戳 | UTC, 数据库 TIMESTAMPTZ, API 层 ISO 8601 |
| 修约规则 | GB/T 8170-2008 数值修约规则 |
| 金额精度 | DECIMAL(12,2), ROUND_HALF_UP |

---

## 3.1 程序1: 用户与认证模块

### 3.1.1 程序描述

**目的**: 管理系统用户的注册、认证、授权与会话,为全系统提供安全访问控制。

**特性**:
- JWT 无状态认证 (Access Token 15分钟 + Refresh Token 7天)
- RBAC 权限模型 (用户 → 角色 → 权限)
- 密码锁定策略: 连续 5 次失败锁定 30 分钟
- 支持双因素认证 (TOTP)
- 完整的登录审计日志

### 3.1.2 功能 (IPO)

**Input**:
- 用户名/密码 (登录)
- 用户信息 (创建用户)
- 角色权限配置 (RBAC 设置)
- TOTP secret (双因素认证)

**Process**:
1. 密码使用 bcrypt (cost=12) 哈希存储
2. 登录时校验密码哈希,失败计数器 +1,超阈值则设置 locked_until
3. 登录成功生成 JWT (Access: 15分钟, Refresh: 7天)
4. RBAC 中间件从 JWT 提取角色,查询 role_permissions 表校验权限
5. TOTP 验证使用 pyotp 库,时间窗口 30 秒

**Output**:
- JWT Token 对 (access_token, refresh_token)
- 权限校验结果 (allow/deny)
- 审计日志记录 (login_success, login_failure, password_change, account_lock)

### 3.1.3 性能

| 指标 | 要求 |
|---|---|
| 精度 | 密码哈希 bcrypt cost=12, 碰撞概率 < 10^-18 |
| 灵活性 | RBAC 支持运行时动态配置,无需重启 |
| 时间特性 | 登录响应 < 500ms, JWT 校验 < 10ms, 权限校验 < 20ms |
| 并发 | 支持 1000 并发登录请求 |

### 3.1.4 输入项

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | 登录用户名 |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt 哈希值 |
| `real_name` | VARCHAR(50) | NOT NULL | 真实姓名 |
| `email` | VARCHAR(100) | UNIQUE, NULLABLE | 邮箱地址 |
| `phone` | VARCHAR(20) | NULLABLE | 手机号 |
| `department_id` | ULID | FK → departments.id | 所属部门 |
| `locked_until` | TIMESTAMPTZ | NULLABLE | 账户锁定截止时间 |
| `login_fail_count` | SMALLINT | DEFAULT 0 | 连续登录失败次数 |
| `totp_secret` | VARCHAR(32) | NULLABLE | TOTP 密钥 |
| `is_active` | BOOLEAN | DEFAULT true | 是否启用 |

### 3.1.5 输出项

| 字段名 | 类型 | 说明 |
|---|---|---|
| `access_token` | VARCHAR(512) | JWT, 15分钟有效 |
| `refresh_token` | VARCHAR(512) | JWT, 7天有效 |
| `token_type` | VARCHAR(10) | 固定值 "Bearer" |
| `expires_in` | INTEGER | Access Token 过期秒数 (900) |
| `user_info` | JSON | 用户基本信息 + 权限列表 |
| `audit_log` | JSON | 审计事件记录 |

### 3.1.6 算法

**密码锁定算法**:
```
FUNCTION check_login_attempt(username, password):
    user = SELECT * FROM users WHERE username = :username
    IF user IS NULL:
        RETURN "USER_NOT_FOUND"

    IF user.locked_until IS NOT NULL AND user.locked_until > NOW():
        RETURN "ACCOUNT_LOCKED"

    IF bcrypt.verify(password, user.password_hash):
        UPDATE users SET login_fail_count = 0, locked_until = NULL
                         WHERE id = user.id
        tokens = generate_jwt(user)
        LOG_AUDIT(user.id, 'LOGIN_SUCCESS')
        RETURN tokens
    ELSE:
        fail_count = user.login_fail_count + 1
        IF fail_count >= 5:
            locked_until = NOW() + INTERVAL '30 minutes'
            LOG_AUDIT(user.id, 'ACCOUNT_LOCKED')
        ELSE:
            locked_until = NULL
        UPDATE users SET login_fail_count = fail_count,
                          locked_until = locked_until
                          WHERE id = user.id
        LOG_AUDIT(user.id, 'LOGIN_FAILURE', fail_count)
        RETURN "INVALID_CREDENTIALS"
```

**JWT Payload**:
```json
{
  "sub": "<user_id_ulid>",
  "roles": ["tester", "reviewer"],
  "permissions": ["sample:read", "test:execute", "report:read"],
  "exp": 1700000000,
  "iat": 1699999100,
  "jti": "<uuid>"
}
```

### 3.1.7 流程逻辑

```
+-------------------+
|  用户提交登录请求  |
+--------+----------+
         |
         v
+-------------------+     +----------------+
|  查询用户记录      |---->| 用户不存在?    | --YES--> 返回 401
+--------+----------+     +----------------+
         | NO
         v
+-------------------+     +----------------+
|  检查锁定状态      |---->| 已锁定?        | --YES--> 返回 423
+--------+----------+     +----------------+
         | NO
         v
+-------------------+     +----------------+     +---------------+
|  校验密码哈希      |---->| 密码正确?      | --NO-->| fail_count++ |
+--------+----------+     +----------------+     +------+--------+
         | YES                                        |
         |                          +-----------------+
         v                          v
+-------------------+     +------------------+
|  TOTP 已启用?      |     | fail_count >= 5? |
+--------+----------+     +--------+---------+
    YES|      | NO              YES|     | NO
       |      |                    |     v
       |      |              +------------------+    +------------------+
       |      v              | 设置锁定30分钟     |    | 重置计数为0      |
       |  +-----------+      +---------+--------+    +--------+---------+
       |  | TOTP校验  |                |                      |
       |  +-----+-----+                v                      v
       |  YES|  | NO           返回错误信息              生成JWT
       |     |  +-----> 返回 401                    +-----+------+
       |     |                                      |            |
       |     +----------------------------------------------+
       |                                                    |
       v                                                    v
+-------------------+                              +------------------+
| (TOTP未启用)直接   |                              | 写入审计日志      |
| 生成JWT            |                              +--------+---------+
+-------------------+                                       |
                                                            v
                                                     +------------------+
                                                     | 返回 token 对    |
                                                     +------------------+
```

### 3.1.8 接口

**上层模块调用**: 所有业务模块通过 `@require_permission("xxx")` 装饰器调用本模块的权限校验能力

**下层子模块**:
- `password_hasher`: bcrypt 封装
- `jwt_manager`: JWT 生成与验证
- `audit_logger`: 审计日志写入
- `totp_validator`: TOTP 校验

**API 端点**:

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/v1/auth/login` | 用户登录 | 公开 |
| POST | `/api/v1/auth/refresh` | 刷新 Token | 公开 |
| POST | `/api/v1/auth/logout` | 登出 | 已认证 |
| POST | `/api/v1/auth/totp/enable` | 启用 TOTP | 已认证 |
| POST | `/api/v1/auth/totp/verify` | 验证 TOTP | 已认证 |
| GET | `/api/v1/users` | 用户列表 | user:list |
| POST | `/api/v1/users` | 创建用户 | user:create |
| PUT | `/api/v1/users/{id}` | 更新用户 | user:update |
| POST | `/api/v1/users/{id}/unlock` | 解锁账户 | user:unlock |
| GET | `/api/v1/roles` | 角色列表 | role:list |
| POST | `/api/v1/roles` | 创建角色 | role:create |
| POST | `/api/v1/roles/{id}/permissions` | 分配权限 | role:update |

**数据结构 (数据库表)**:

```sql
CREATE TABLE users (
    id            ULID PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    real_name     VARCHAR(50) NOT NULL,
    email         VARCHAR(100) UNIQUE,
    phone         VARCHAR(20),
    department_id ULID REFERENCES departments(id),
    is_active     BOOLEAN DEFAULT true,
    locked_until  TIMESTAMPTZ,
    login_fail_count SMALLINT DEFAULT 0,
    totp_secret   VARCHAR(32),
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE roles (
    id          ULID PRIMARY KEY,
    name        VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_system   BOOLEAN DEFAULT false,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE role_permissions (
    role_id     ULID REFERENCES roles(id) ON DELETE CASCADE,
    permission  VARCHAR(100) NOT NULL,
    PRIMARY KEY (role_id, permission)
);

CREATE TABLE user_roles (
    user_id     ULID REFERENCES users(id) ON DELETE CASCADE,
    role_id     ULID REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE audit_logs (
    id          BIGSERIAL PRIMARY KEY,
    user_id     ULID REFERENCES users(id),
    action      VARCHAR(50) NOT NULL,
    resource    VARCHAR(100),
    resource_id VARCHAR(30),
    details     JSONB,
    ip_address  INET,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at DESC);
```

---

## 3.2 程序2: 样品管理类

### 3.2.1 程序描述

**目的**: 管理样品从委托登记到销毁的全生命周期,包括收样确认、条码生成、样品流转与状态跟踪。

**特性**:
- 委托信息登记 (客户、项目、样品来源)
- 自动/手动生成样品编号 (规则可配置)
- 条码/二维码打印 (支持标签打印机)
- 样品流转记录 (每一步操作可追溯)
- 样品状态跟踪 (待检/检测中/已检毕/已归档/已销毁)

### 3.2.2 功能 (IPO)

**Input**:
- 委托申请信息 (客户ID、项目信息、样品列表)
- 样品信息 (名称、规格、数量、状态、检测项目)
- 样品流转操作 (签收、交接、归还、废弃)
- 条码打印请求

**Process**:
1. 接收委托申请,校验必填字段,生成委托单号 (格式: WT-YYYYMMDD-NNNN)
2. 为每个样品生成唯一编号 (格式: YP-{category_prefix}-{YYYYMMDD}-NNNN)
3. 生成 Code128 条码 + QR 码,包含样品编号、委托日期、检测项目摘要
4. 样品状态变更触发工作流引擎状态转换
5. 每次流转操作写入 sample_transitions 表 (操作人、时间、备注)

**Output**:
- 委托单 (含委托编号)
- 样品条码 (PDF/PNG)
- 样品流转日志
- 样品状态汇总

### 3.2.3 性能

| 指标 | 要求 |
|---|---|
| 精度 | 样品编号全局唯一, 使用 SEQUENCE 保证不重复 |
| 灵活性 | 编号规则可通过 sys_config 表配置前缀/日期格式/序列长度 |
| 时间特性 | 委托单创建 < 200ms, 条码生成 < 100ms/个 |
| 容量 | 单委托可包含 100 个样品, 年管理量 50,000+ 样品 |

### 3.2.4 输入项

**委托登记表 (entrustments)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 委托单 ID |
| `entrust_no` | VARCHAR(30) | UNIQUE, NOT NULL | 委托编号 (WT-YYYYMMDD-NNNN) |
| `client_id` | ULID | FK → clients.id | 客户 |
| `project_name` | VARCHAR(200) | NOT NULL | 项目名称 |
| `project_code` | VARCHAR(50) | NULLABLE | 项目编号 |
| `contact_person` | VARCHAR(50) | NOT NULL | 联系人 |
| `contact_phone` | VARCHAR(20) | NOT NULL | 联系电话 |
| `sample_source` | VARCHAR(50) | NOT NULL | 样品来源 (送样/抽样/其他) |
| `sampling_location` | VARCHAR(200) | NULLABLE | 抽样地点 |
| `sampling_date` | DATE | NULLABLE | 抽样日期 |
| `received_date` | DATE | DEFAULT CURRENT_DATE | 收样日期 |
| `required_date` | DATE | NOT NULL | 要求完成日期 |
| `test_purpose` | TEXT | NULLABLE | 检测目的说明 |
| `workflow_state` | VARCHAR(30) | DEFAULT 'draft' | 工作流状态 |
| `status` | VARCHAR(30) | DEFAULT 'draft' | 状态 |
| `notes` | TEXT | NULLABLE | 备注 |
| `created_by` | ULID | FK → users.id | 创建人 |

**样品表 (samples)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 样品 ID |
| `sample_no` | VARCHAR(30) | UNIQUE, NOT NULL | 样品编号 |
| `entrust_id` | ULID | FK → entrustments.id | 所属委托 |
| `name` | VARCHAR(100) | NOT NULL | 样品名称 |
| `category` | VARCHAR(50) | NOT NULL | 样品类别 |
| `specification` | VARCHAR(100) | NULLABLE | 规格型号 |
| `quantity` | DECIMAL(10,2) | NOT NULL | 数量 |
| `unit` | VARCHAR(10) | NOT NULL | 单位 |
| `manufacturer` | VARCHAR(100) | NULLABLE | 生产厂家 |
| `production_date` | DATE | NULLABLE | 生产日期 |
| `appearance` | TEXT | NULLABLE | 外观描述 |
| `storage_condition` | VARCHAR(50) | NULLABLE | 存储条件 |
| `status` | VARCHAR(30) | DEFAULT 'pending_test' | 状态 |
| `location` | VARCHAR(50) | NULLABLE | 当前存放位置 |
| `retention_days` | INTEGER | DEFAULT 180 | 保留天数 |
| `dispose_date` | TIMESTAMPTZ | NULLABLE | 计划销毁日期 |

### 3.2.5 输出项

| 字段名 | 类型 | 说明 |
|---|---|---|
| `entrustment` | JSON | 委托单完整信息 |
| `samples` | JSON[] | 样品列表 (含条码数据) |
| `barcode_data` | STRING | Base64 编码的条码图片 |
| `qr_data` | STRING | QR 码内容 (JSON 字符串) |
| `transitions` | JSON[] | 流转记录 |
| `workflow_state` | JSON | 当前工作流状态 |

### 3.2.6 算法

**样品编号生成**:
```
FUNCTION generate_sample_no(category, received_date):
    prefix_map = {
        '混凝土': 'HT', '钢筋': 'GJ', '沥青': 'LQ', '土工': 'TG',
        '水泥': 'SN', '砂石': 'SS', '外加剂': 'WJJ'
    }
    category_prefix = prefix_map.get(category, 'QT')
    date_str = FORMAT(received_date, 'YYYYMMDD')
    seq = NEXTVAL('sample_seq_' + category_prefix)
    seq_str = LPAD(CAST(seq AS TEXT), 4, '0')
    RETURN 'YP-' + category_prefix + '-' + date_str + '-' + seq_str
```

**委托编号生成**:
```
FUNCTION generate_entrust_no(received_date):
    date_str = FORMAT(received_date, 'YYYYMMDD')
    seq = NEXTVAL('entrust_seq')
    seq_str = LPAD(CAST(seq AS TEXT), 4, '0')
    RETURN 'WT-' + date_str + '-' + seq_str
```

### 3.2.7 流程逻辑

```
+------------------+
|  创建委托单       |
+--------+---------+
         |
         v
+------------------+     +--------------------+
|  生成委托编号     |     | WT-日期-序列号     |
+--------+---------+     +--------------------+
         |
         v
+------------------+
|  录入样品信息     | (名称、规格、数量、检测项目)
+--------+---------+
         |
         v
+------------------+     +--------------------------+
|  为每个样品生成   |     | YP-类别前缀-日期-序列号 |
|  样品编号         |     +--------------------------+
+--------+---------+
         |
         v
+------------------+
|  收样确认         | (状态→received)
+--------+---------+
         |
         v
+------------------+     +--------------------+
|  打印条码标签     |---->| Code128 / QR 码   |
+--------+---------+     +--------------------+
         |
         v
+------------------+
|  样品入库         | (记录存放位置)
+--------+---------+
         |
         v
+------------------+     +------------------------------+
|  流转操作         |     | 签收/交接/归还/废弃/检测中/  |
|  (状态机驱动)    |---->| 检测完成/归档                 |
+--------+---------+     +------------------------------+
         |
         v
+------------------+
|  写入流转日志     |
+--------+---------+
         |
         v (保留期满)
+------------------+     +--------------------+
|  审批后销毁       |---->| 记录销毁日期      |
+------------------+     +--------------------+
```

### 3.2.8 接口

**上层模块调用**:
- 检测管理模块: 通过 `GET /api/v1/samples/{id}` 获取样品详情,触发样品状态变更
- 报告管理模块: 通过 `GET /api/v1/samples?entrust_id=xxx` 获取委托下所有样品
- 计费管理模块: 通过 `GET /api/v1/samples/{id}/test_items` 获取检测项目用于计价

**下层子模块**:
- `sample_numbering`: 编号生成器 (基于 PostgreSQL SEQUENCE)
- `barcode_generator`: python-barcode 封装,生成 Code128 + QR 码
- `transition_tracker`: 流转记录器
- `workflow_trigger`: 触发工作流状态转换

**API 端点**:

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/v1/entrustments` | 创建委托单 | entrustment:create |
| GET | `/api/v1/entrustments` | 委托列表 (可分页/搜索) | entrustment:list |
| GET | `/api/v1/entrustments/{id}` | 委托详情 | entrustment:read |
| PUT | `/api/v1/entrustments/{id}` | 更新委托 | entrustment:update |
| POST | `/api/v1/samples` | 登记样品 | sample:create |
| GET | `/api/v1/samples/{id}` | 样品详情 | sample:read |
| PUT | `/api/v1/samples/{id}/status` | 变更状态 | sample:update |
| POST | `/api/v1/samples/{id}/transition` | 流转记录 | sample:transition |
| POST | `/api/v1/samples/{id}/barcode` | 生成条码图片 | sample:barcode |
| GET | `/api/v1/samples/{id}/transitions` | 流转日志 | sample:read |
| POST | `/api/v1/samples/{id}/dispose` | 样品销毁 | sample:dispose |

**数据结构**:

```sql
CREATE TABLE entrustments (
    id              ULID PRIMARY KEY,
    entrust_no      VARCHAR(30) UNIQUE NOT NULL,
    client_id       ULID REFERENCES clients(id),
    project_name    VARCHAR(200) NOT NULL,
    project_code    VARCHAR(50),
    contact_person  VARCHAR(50) NOT NULL,
    contact_phone   VARCHAR(20) NOT NULL,
    sample_source   VARCHAR(50) NOT NULL,
    sampling_location VARCHAR(200),
    sampling_date   DATE,
    received_date   DATE DEFAULT CURRENT_DATE,
    required_date   DATE NOT NULL,
    test_purpose    TEXT,
    workflow_state  VARCHAR(30) DEFAULT 'draft',
    status          VARCHAR(30) DEFAULT 'draft',
    notes           TEXT,
    created_by      ULID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE samples (
    id              ULID PRIMARY KEY,
    sample_no       VARCHAR(30) UNIQUE NOT NULL,
    entrust_id      ULID REFERENCES entrustments(id),
    name            VARCHAR(100) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    specification   VARCHAR(100),
    quantity        DECIMAL(10,2) NOT NULL,
    unit            VARCHAR(10) NOT NULL,
    manufacturer    VARCHAR(100),
    production_date DATE,
    appearance      TEXT,
    storage_condition VARCHAR(50),
    status          VARCHAR(30) DEFAULT 'pending_test',
    location        VARCHAR(50),
    retention_days  INTEGER DEFAULT 180,
    dispose_date    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sample_transitions (
    id          BIGSERIAL PRIMARY KEY,
    sample_id   ULID REFERENCES samples(id),
    from_status VARCHAR(30),
    to_status   VARCHAR(30) NOT NULL,
    action      VARCHAR(50) NOT NULL,
    operator_id ULID REFERENCES users(id),
    notes       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE SEQUENCE entrust_seq START 1;
CREATE SEQUENCE sample_seq_HT START 1;
CREATE SEQUENCE sample_seq_GJ START 1;
CREATE SEQUENCE sample_seq_LQ START 1;
CREATE SEQUENCE sample_seq_TG START 1;
CREATE SEQUENCE sample_seq_SN START 1;
CREATE SEQUENCE sample_seq_SS START 1;
CREATE SEQUENCE sample_seq_WJJ START 1;
CREATE SEQUENCE sample_seq_QT START 1;

CREATE INDEX idx_entrustments_client ON entrustments(client_id);
CREATE INDEX idx_entrustments_status ON entrustments(status, created_at DESC);
CREATE INDEX idx_samples_entrust ON samples(entrust_id);
CREATE INDEX idx_samples_status ON samples(status);
CREATE INDEX idx_sample_transitions_sample ON sample_transitions(sample_id, created_at DESC);
```

---

## 3.3 程序3: 检测管理模块

### 3.3.1 程序描述

**目的**: 管理检测任务的分配、执行、数据录入与原始记录,是实验室业务的核心环节。

**特性**:
- 检测任务分配 (检测员、审核员)
- 检测任务执行 (按检测方法逐项录入)
- 原始记录填写 (硬编码 React 表单)
- 自动计算 (公式引擎)
- 数据修约 (GB/T 8170)
- 检测环境记录 (温湿度)

### 3.3.2 功能 (IPO)

**Input**:
- 检测任务 (来自样品关联的检测项目)
- 检测数据 (实测值, 环境条件, 仪器使用记录)
- 检测人/审核人指派

**Process**:
1. 按检测方法加载对应的 React 表单组件
2. 检测员逐项录入实测数据,系统自动计算衍生值
3. 计算过程应用 GB/T 8170 修约规则
4. 校验数据合理性 (范围检查, 逻辑校验)
5. 生成原始记录 (含检测人电子签名)
6. 提交后触发审核流程

**Output**:
- 原始记录 (JSON 结构化数据 + 计算结果)
- 检测任务状态变更
- 审核待办通知

### 3.3.3 性能

| 指标 | 要求 |
|---|---|
| 精度 | 浮点计算使用 Decimal, 修约按 GB/T 8170 执行 |
| 灵活性 | 表单组件按检测方法动态加载, 支持自定义公式 |
| 时间特性 | 表单加载 < 500ms, 自动计算 < 50ms, 提交 < 200ms |

### 3.3.4 输入项

**检测任务表 (test_tasks)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 任务 ID |
| `sample_id` | ULID | FK → samples.id | 关联样品 |
| `test_method_id` | ULID | FK → test_methods.id | 检测方法 |
| `test_items` | JSONB | NOT NULL | 需要检测的项目列表 |
| `assigned_to` | ULID | FK → users.id | 分配给检测员 |
| `reviewer_id` | ULID | FK → users.id | 审核员 |
| `environment` | JSONB | | 环境条件 (温度、湿度) |
| `equipment_used` | JSONB | | 使用的仪器列表 |
| `status` | VARCHAR(30) | DEFAULT 'pending' | 任务状态 |
| `priority` | VARCHAR(10) | DEFAULT 'normal' | 优先级 |
| `deadline` | DATE | | 完成期限 |

**检测数据表 (test_records)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 记录 ID |
| `test_task_id` | ULID | FK → test_tasks.id, UNIQUE | 关联任务 |
| `test_data` | JSONB | NOT NULL | 检测数据 (结构化) |
| `calculated_data` | JSONB | | 自动计算结果 |
| `result` | VARCHAR(30) | | 结论 (pass/fail/pending) |
| `conclusion_notes` | TEXT | | 结论说明 |
| `tester_signature` | JSONB | | 检测人签名 |
| `reviewer_signature` | JSONB | | 审核人签名 |
| `tested_at` | TIMESTAMPTZ | | 检测完成时间 |
| `reviewed_at` | TIMESTAMPTZ | | 审核时间 |

### 3.3.5 输出项

| 字段名 | 类型 | 说明 |
|---|---|---|
| `test_record` | JSON | 完整原始记录数据 |
| `calculated_items` | JSON[] | 计算结果列表 (每项含原始值、公式、修约值) |
| `result_summary` | JSON | 结果摘要 |
| `validation_errors` | JSON[] | 数据校验错误 |

### 3.3.6 算法

**GB/T 8170 修约 (四舍六入五成双)**:
```
FUNCTION round_gbt8170(value: Decimal, precision: int) -> Decimal:
    quantize_exp = Decimal(10) ** (-precision)
    RETURN value.quantize(quantize_exp, rounding=ROUND_HALF_EVEN)
```

**示例**:
- 3.14159 修约到 2 位 → 3.14
- 2.675 修约到 2 位 → 2.68 (5 前 7 为奇,进 1)
- 2.685 修约到 2 位 → 2.68 (5 前 8 为偶,舍去)
- 1.0505 修约到 2 位 → 1.05 (5 后还有数字,进 1)

**混凝土抗压强度计算**:
```
FUNCTION calculate_compressive_strength(raw_data):
    F = raw_data.max_load_kN          -- 破坏荷载 (kN)
    A = raw_data.cross_section_mm2    -- 承压面积 (mm²)
    fc_raw = (F * 1000) / A           -- MPa
    fc = round_gbt8170(fc_raw, 1)     -- 修约至 0.1 MPa
    RETURN {
        'fc_raw': fc_raw,
        'fc': fc,
        'is_qualified': fc >= raw_data.design_strength
    }
```

### 3.3.7 流程逻辑

```
+------------------+
|  任务分配         | (检测员、审核员)
+--------+---------+
         |
         v
+------------------+
|  检测员接单       |
+--------+---------+
         |
         v
+------------------+     +-------------------+
|  加载检测表单     |---->| React 组件        |
|  (按检测方法)    |     | (硬编码, 200+)    |
+--------+---------+     +-------------------+
         |
         v
+------------------+     +----------------------------+
|  录入环境条件     |---->| 温度、湿度、大气压         |
+--------+---------+     +----------------------------+
         |
         v
+------------------+     +----------------------------+
|  录入实测数据     |---->| 逐项输入, 带单位和限值     |
|  (onChange事件)  |     |                            |
+--------+---------+     +----------------------------+
         |
         v
+------------------+     +-------------------+
|  自动计算         |---->| 公式引擎          |
|                   |     | GB/T 8170 修约    |
+--------+---------+     | 即时显示结果       |
         |               +-------------------+
         v
+------------------+
|  合理性校验       | (范围检查、逻辑校验)
+--------+---------+
         |
    +----+----+
    v         v
  通过      不通过 --> 高亮错误字段, 提示修正
    |
    v
+------------------+
|  电子签名         | (密码二次确认)
+--------+---------+
         |
         v
+------------------+
|  提交原始记录     | (status→submitted)
+--------+---------+
         |
         v
+------------------+     +-------------------+
|  触发审核流程     |---->| 审核员待办通知    |
+------------------+     +-------------------+
```

### 3.3.8 接口

**上层模块调用**:
- 报告管理模块: 通过 `GET /api/v1/test-records?sample_id=xxx` 获取检测数据
- 样品管理模块: 通过更新 samples.status 变更样品检测状态

**下层子模块**:
- `formula_engine`: 公式解析与计算引擎 (Python)
- `rounding_service`: GB/T 8170 修约规则
- `validation_service`: 数据合理性校验
- `esig_service`: 电子签名
- `form_loader`: 检测方法表单组件加载器

**API 端点**:

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| GET | `/api/v1/test-tasks` | 任务列表 | test_task:list |
| GET | `/api/v1/test-tasks/{id}` | 任务详情 | test_task:read |
| POST | `/api/v1/test-tasks/assign` | 分配任务 | test_task:assign |
| POST | `/api/v1/test-tasks/{id}/start` | 开始检测 | test:execute |
| GET | `/api/v1/test-tasks/{id}/form` | 获取检测表单 schema | test:execute |
| PUT | `/api/v1/test-tasks/{id}/data` | 保存检测数据 | test:execute |
| POST | `/api/v1/test-tasks/{id}/submit` | 提交原始记录 | test:submit |
| GET | `/api/v1/test-records/{id}` | 原始记录详情 | test_record:read |
| POST | `/api/v1/test-records/{id}/sign` | 电子签名 | test:sign |
| POST | `/api/v1/test-records/{id}/approve` | 审核通过 | test:review |
| POST | `/api/v1/test-records/{id}/reject` | 审核退回 | test:review |

**数据结构**:

```sql
CREATE TABLE test_tasks (
    id              ULID PRIMARY KEY,
    sample_id       ULID REFERENCES samples(id),
    test_method_id  ULID REFERENCES test_methods(id),
    test_items      JSONB NOT NULL,
    assigned_to     ULID REFERENCES users(id),
    reviewer_id     ULID REFERENCES users(id),
    environment     JSONB,
    equipment_used  JSONB,
    status          VARCHAR(30) DEFAULT 'pending',
    priority        VARCHAR(10) DEFAULT 'normal',
    deadline        DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE test_records (
    id              ULID PRIMARY KEY,
    test_task_id    ULID REFERENCES test_tasks(id) UNIQUE,
    test_data       JSONB NOT NULL,
    calculated_data JSONB,
    result          VARCHAR(30),
    conclusion_notes TEXT,
    tester_signature JSONB,
    reviewer_signature JSONB,
    tested_at       TIMESTAMPTZ,
    reviewed_at     TIMESTAMPTZ,
    created_by      ULID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_test_tasks_status ON test_tasks(status, assigned_to);
CREATE INDEX idx_test_tasks_sample ON test_tasks(sample_id);
CREATE INDEX idx_test_tasks_deadline ON test_tasks(status, deadline)
    WHERE deadline IS NOT NULL;
CREATE INDEX idx_test_records_result ON test_records(result);
```

---

## 3.4 程序4: 报告管理模块

### 3.4.1 程序描述

**目的**: 根据检测原始记录自动生成检测报告,支持 HTML 模板渲染、PDF 转换、CMA/CNAS 标识嵌入与三级审核流程。

**特性**:
- HTML 模板引擎 (Jinja2)
- WeasyPrint PDF 生成
- CMA/CNAS 标识自动嵌入 (按资质范围)
- 三级审核: 编制 → 审核 → 批准
- 报告编号自动生成
- 报告版本控制 (退回重出时版本号递增)

### 3.4.2 功能 (IPO)

**Input**:
- 委托/样品/检测数据 (聚合)
- 报告模板 (Jinja2 HTML)
- 审核人电子签名
- CMA/CNAS 标识配置

**Process**:
1. 聚合委托、样品、检测数据至报告上下文
2. 按检测方法类别选择对应报告模板
3. Jinja2 渲染 HTML 报告
4. WeasyPrint 将 HTML 转 PDF (支持中文字体)
5. 叠加 CMA/CNAS 标识 (条件渲染)
6. 三级审核流程,每级需电子签名
7. 批准后报告定稿,不可修改

**Output**:
- 检测报告 (PDF)
- 报告编号
- 审核记录

### 3.4.3 性能

| 指标 | 要求 |
|---|---|
| 精度 | PDF 输出矢量质量, 中文字体无乱码 |
| 灵活性 | 模板支持按客户/项目定制, 条件渲染 CMA/CNAS |
| 时间特性 | 报告渲染 < 3s, PDF 生成 < 2s, 批量生成 < 30s/10 份 |

### 3.4.4 输入项

**报告模板表 (report_templates)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 模板 ID |
| `name` | VARCHAR(100) | NOT NULL | 模板名称 |
| `category` | VARCHAR(50) | NOT NULL | 对应检测方法类别 |
| `html_template` | TEXT | NOT NULL | Jinja2 模板内容 |
| `css` | TEXT | | 报告专用 CSS 样式 |
| `is_default` | BOOLEAN | DEFAULT false | 是否为默认模板 |
| `is_active` | BOOLEAN | DEFAULT true | 是否启用 |

**报告表 (reports)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 报告 ID |
| `report_no` | VARCHAR(30) | UNIQUE | 报告编号 (BG-YYYY-NNNNN) |
| `entrust_id` | ULID | FK → entrustments.id | 关联委托 |
| `template_id` | ULID | FK → report_templates.id | 使用模板 |
| `html_content` | TEXT | | 渲染后的 HTML |
| `pdf_file` | VARCHAR(500) | | PDF 文件路径/URL |
| `version` | SMALLINT | DEFAULT 1 | 版本号 |
| `status` | VARCHAR(30) | DEFAULT 'draft' | 状态 |
| `cma_mark` | BOOLEAN | DEFAULT false | 是否含 CMA 标识 |
| `cnas_mark` | BOOLEAN | DEFAULT false | 是否含 CNAS 标识 |
| `issuer_id` | ULID | FK → users.id | 编制人 |
| `reviewer_id` | ULID | FK → users.id | 审核人 |
| `approver_id` | ULID | FK → users.id | 批准人 |
| `issue_date` | DATE | | 签发日期 |

### 3.4.5 输出项

| 字段名 | 类型 | 说明 |
|---|---|---|
| `report_pdf` | BINARY | PDF 文件流 |
| `report_no` | VARCHAR | 报告编号 |
| `approval_chain` | JSON | 审核链信息 (三级签名) |
| `render_log` | JSON | 渲染日志 (模板变量、用时) |

### 3.4.6 算法

**报告编号生成**:
```
FUNCTION generate_report_no(issued_date):
    year = FORMAT(issued_date, 'YYYY')
    seq = NEXTVAL('report_seq')
    seq_str = LPAD(CAST(seq AS TEXT), 5, '0')
    RETURN 'BG-' + year + '-' + seq_str
```

**HTML 渲染与 PDF 生成**:
```
FUNCTION render_report(entrust_id, template_id):
    context = aggregate_report_context(entrust_id)
        -- 聚合: entrustment + samples + test_records
        -- 聚合: client info, lab info, test_method details
    template = load_jinja2_template(template_id)
    html = template.render(context)
    pdf = weasyprint.HTML(string=html).write_pdf(
        stylesheets=[base_css, report_css]
    )
    IF context.has_cma_qualification:
        pdf = overlay_cma_mark(pdf, config.cma_image)
    IF context.has_cnas_qualification:
        pdf = overlay_cnas_mark(pdf, config.cnas_image)
    RETURN html, pdf
```

### 3.4.7 流程逻辑

```
+------------------+
|  选择委托         |
+--------+---------+
         |
         v
+------------------+     +----------------------+
|  选择/分配模板    |---->| 按检测类别匹配模板   |
+--------+---------+     +----------------------+
         |
         v
+------------------+
|  聚合数据         |
|  (委托+样品       |
|   +检测记录)      |
+--------+---------+
         |
         v
+------------------+
| Jinja2 渲染       |
| HTML 报告         |
+--------+---------+
         |
         v
+------------------+
| WeasyPrint        |
| HTML → PDF        |
+--------+---------+
         |
         v
+------------------+     +----------------------+
| 叠加 CMA/CNAS     |---->| 资质范围校验         |
+--------+---------+     +----------------------+
         |
         v
+------------------+
|  编制人签名       | (一级)
+--------+---------+
         |
         v
+------------------+     +----------------+
|  审核人审核       |---->| 退回?         | --YES--> 修改重出
+--------+---------+     +----------------+
         | NO
         v
+------------------+     +----------------+
|  批准人批准       |---->| 退回?         | --YES--> 退回编制
+--------+---------+     +----------------+
         | NO
         v
+------------------+
|  报告定稿         | (status→approved, 不可改)
+--------+---------+
         |
         v
+------------------+     +----------------------+
|  生成编号         |---->| BG-YYYY-NNNNN       |
+------------------+     +----------------------+
```

### 3.4.8 接口

**上层模块调用**:
- 计费管理模块: 通过报告状态 (approved) 触发计费
- 原始记录模块: 通过报告审核状态控制原始记录锁定

**下层子模块**:
- `template_engine`: Jinja2 模板渲染
- `pdf_generator`: WeasyPrint 封装
- `watermark_service`: CMA/CNAS 标识叠加 (Pillow/PyPDF2)
- `approval_workflow`: 三级审核流程

**API 端点**:

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/v1/reports/generate` | 生成报告 | report:generate |
| GET | `/api/v1/reports/{id}` | 报告详情 | report:read |
| GET | `/api/v1/reports/{id}/pdf` | 下载 PDF | report:read |
| GET | `/api/v1/reports/{id}/preview` | 在线预览 HTML | report:read |
| POST | `/api/v1/reports/{id}/sign-issue` | 编制人签名 | report:issue |
| POST | `/api/v1/reports/{id}/review` | 审核 | report:review |
| POST | `/api/v1/reports/{id}/approve` | 批准 | report:approve |
| POST | `/api/v1/reports/{id}/reissue` | 退回重出 | report:update |
| GET | `/api/v1/reports` | 报告列表 | report:list |
| GET | `/api/v1/report-templates` | 模板列表 | template:read |
| POST | `/api/v1/reports/batch` | 批量生成 (Celery) | report:generate |

**数据结构**:

```sql
CREATE TABLE report_templates (
    id          ULID PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    category    VARCHAR(50) NOT NULL,
    html_template TEXT NOT NULL,
    css         TEXT,
    is_default  BOOLEAN DEFAULT false,
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE reports (
    id              ULID PRIMARY KEY,
    report_no       VARCHAR(30) UNIQUE,
    entrust_id      ULID REFERENCES entrustments(id),
    template_id     ULID REFERENCES report_templates(id),
    html_content    TEXT,
    pdf_file        VARCHAR(500),
    version         SMALLINT DEFAULT 1,
    status          VARCHAR(30) DEFAULT 'draft',
    cma_mark        BOOLEAN DEFAULT false,
    cnas_mark       BOOLEAN DEFAULT false,
    issuer_id       ULID REFERENCES users(id),
    issuer_signature JSONB,
    reviewer_id     ULID REFERENCES users(id),
    reviewer_signature JSONB,
    approver_id     ULID REFERENCES users(id),
    approver_signature JSONB,
    reviewed_at     TIMESTAMPTZ,
    approved_at     TIMESTAMPTZ,
    issue_date      DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE SEQUENCE report_seq START 1;

CREATE TABLE report_approval_log (
    id          BIGSERIAL PRIMARY KEY,
    report_id   ULID REFERENCES reports(id),
    action      VARCHAR(30) NOT NULL,  -- issue/review/approve/reject
    actor_id    ULID REFERENCES users(id),
    comments    TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reports_entrust ON reports(entrust_id);
CREATE INDEX idx_reports_status ON reports(status, created_at DESC);
```

---

## 3.5 程序5: 原始记录模块

### 3.5.1 程序描述

**目的**: 提供检测原始记录的填写、计算、修约、校验、签名与导出功能,采用硬编码 React 表单组件实现。

**特性**:
- 200+ 检测方法的硬编码 React 表单
- 自动计算 (公式引擎)
- GB/T 8170 数值修约
- 数据校验 (范围、逻辑、必填)
- 电子签名 (密码确认)
- 打印与 PDF 导出

### 3.5.2 功能 (IPO)

**Input**:
- 检测方法标识
- 实测数据 (逐项录入)
- 环境条件 (温湿度)
- 使用仪器信息

**Process**:
1. 按检测方法 ID 加载对应 React 表单组件
2. 表单渲染后显示检测标准、步骤说明
3. 检测员录入实测数据, onChange 触发自动计算
4. 计算结果即时显示,自动修约
5. 提交前全量校验
6. 电子签名后锁定记录
7. 支持打印 (A4 排版) 与 PDF 导出

**Output**:
- 结构化原始记录 (JSON)
- 原始记录打印版 (PDF)
- 校验报告

### 3.5.3 性能

| 指标 | 要求 |
|---|---|
| 精度 | Decimal 精度 10 位, 修约按 GB/T 8170 执行 |
| 灵活性 | 200+ 方法独立组件, 公共逻辑抽离为 hooks/utils |
| 时间特性 | 表单渲染 < 1s, 实时计算 < 10ms, 提交 < 500ms |

### 3.5.4 输入项

**原始记录数据 (JSONB, 存储于 test_records.test_data)**:

| 字段名 | 类型 | 说明 |
|---|---|---|
| `method_code` | STRING | 检测方法编号 |
| `environment` | JSON | {"temperature": 23.5, "humidity": 55} |
| `equipment` | JSON[] | [{"id": "xxx", "calibration_expiry": "..."}] |
| `raw_values` | JSON | 实测值 (按项目键值对) |
| `calculated_values` | JSON | 计算结果 |
| `attachments` | STRING[] | 附件文件路径 |

**前端表单组件目录结构**:
```
src/features/test-forms/
  ├── components/
  │   ├── CompressiveStrengthForm.tsx      (混凝土抗压强度)
  │   ├── TensileStrengthForm.tsx          (钢筋拉伸)
  │   ├── PenetrationForm.tsx              (沥青针入度)
  │   └── ... (200+ 方法)
  ├── hooks/
  │   ├── useTestData.ts                   (通用数据管理)
  │   ├── useAutoCalculate.ts              (自动计算 hook)
  │   └── useFormValidation.ts             (校验 hook)
  ├── utils/
  │   ├── rounding.ts                      (GB/T 8170 修约)
  │   ├── formulas.ts                      (常用公式)
  │   └── validators.ts                    (校验规则)
  └── types.ts
```

### 3.5.5 输出项

| 字段名 | 类型 | 说明 |
|---|---|---|
| `record_json` | JSON | 完整结构化数据 |
| `print_html` | HTML | 打印版 HTML |
| `print_pdf` | BINARY | PDF 导出 |
| `validation_report` | JSON | 校验结果 (通过/失败列表) |
| `signature_hash` | STRING | 电子签名哈希 |

### 3.5.6 算法

**前端 GB/T 8170 修约 (TypeScript, 使用 decimal.js)**:
```typescript
import Decimal from 'decimal.js';

function roundGbt8170(value: string | number, precision: number): string {
    const d = new Decimal(value);
    const quantizeStr = '1E-' + precision;
    // ROUND_HALF_EVEN = 四舍六入五成双
    return d.toDecimalPlaces(precision, Decimal.ROUND_HALF_EVEN).toString();
}
```

**前端自动计算 Hook 伪代码**:
```typescript
function useAutoCalculate(formula: string, context: Record<string, number>): number[] {
    const [results, setResults] = useState<CalcResult[]>([]);

    const calculate = useCallback(() => {
        const tree = parseFormula(formula);
        const rawValue = evaluateTree(tree, context);
        const precision = getPrecisionFromMetadata(formula);
        const rounded = roundGbt8170(rawValue, precision);
        setResults([{ raw: rawValue, rounded, formula }]);
    }, [formula, context]);

    useEffect(() => calculate(), [calculate]);
    return results;
}
```

### 3.5.7 流程逻辑

```
+------------------+
|  打开原始记录     |
+--------+---------+
         |
         v
+------------------+     +----------------------+
|  加载表单组件     |---->| 按方法ID map组件     |
|  (按检测方法)    |     +----------------------+
+--------+---------+
         |
         v
+------------------+
|  填写环境条件     | (温湿度等)
+--------+---------+
         |
         v
+------------------+     +----------------------+
|  录入实测值       |---->| 逐项输入, 带单位/限值|
|  (onChange事件)  |     +----------------------+
+--------+---------+
         |
         v
+------------------+     +----------------------+
|  自动计算         |---->| 公式引擎             |
|                   |     | GB/T 8170 即时修约   |
+--------+---------+     +----------------------+
         |
         v
+------------------+
|  实时显示结果     | (计算值, 修约值, 判定)
+--------+---------+
         |
         v
        === 数据录入完毕 ===
         |
         v
+------------------+
|  提交前校验       | (必填/范围/逻辑一致性)
+--------+---------+
         |
    +----+----+
    v         v
  通过      不通过 --> 高亮错误字段
    |
    v
+------------------+
|  电子签名         | (密码确认)
+--------+---------+
         |
         v
+------------------+
|  锁定记录         | (status→submitted)
+--------+---------+
         |
         v
+------------------+
|  打印/导出 (可选) |
+------------------+
```

### 3.5.8 接口

**上层模块调用**:
- 检测管理模块: 调用原始记录的保存、提交、签名 API
- 报告管理模块: 通过 `GET /api/v1/test-records/{id}` 读取已签名的原始记录

**下层子模块**:
- `formula_executor`: 前端公式计算 (TS)
- `rounding_util`: GB/T 8170 前端实现 (decimal.js)
- `form_validation`: Zod/React Hook Form 校验
- `print_service`: 打印版 HTML 生成

**API 端点**:

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| GET | `/api/v1/test-records/{id}` | 获取原始记录 | test_record:read |
| PUT | `/api/v1/test-records/{id}/data` | 保存检测数据 | test_record:update |
| POST | `/api/v1/test-records/{id}/sign` | 电子签名 | test_record:sign |
| POST | `/api/v1/test-records/{id}/lock` | 锁定记录 | test_record:lock |
| GET | `/api/v1/test-records/{id}/print` | 获取打印版 HTML | test_record:read |
| GET | `/api/v1/test-records/{id}/pdf` | 导出 PDF | test_record:read |
| POST | `/api/v1/test-records/{id}/unlock` | 解锁 (需授权) | test_record:unlock |

**数据结构**:
test_records 表已在 3.3 模块定义, 本模块复用。

```sql
CREATE INDEX idx_test_records_task ON test_records(test_task_id);
CREATE INDEX idx_test_records_result ON test_records(result);
```

---

## 3.6 程序6: 设备管理模块

### 3.6.1 程序描述

**目的**: 管理实验室仪器设备的全生命周期,包括采购、入账、校准、维护维修、期间核查、转移与报废。

**特性**:
- 设备台账管理 (基础信息、技术参数)
- 采购与验收流程
- 校准计划与记录 (周期性)
- 维护保养记录
- 维修登记
- 报废审批
- 期间核查管理

### 3.6.2 功能 (IPO)

**Input**:
- 设备采购申请 (名称、型号、供应商、预算)
- 设备验收记录 (技术指标、合格证)
- 校准记录 (校准值、偏差、下次校准日期)
- 维修记录 (故障描述、维修内容、费用)
- 报废申请 (报废原因、残值)

**Process**:
1. 设备采购申请审批通过后创建台账记录
2. 自动生成设备编号 (EQ-类别-YYYY-NNNN)
3. 基于设备校准周期自动生成校准计划
4. 校准到期前 30 天/7 天发送提醒
5. 维修/保养记录关联至设备台账
6. 报废需逐级审批, 审批后状态变更

**Output**:
- 设备台账 (完整生命周期记录)
- 校准计划与提醒
- 设备状态看板 (正常/校准中/维修中/停用/报废)
- 统计报表 (设备使用率、校准合格率)

### 3.6.3 性能

| 指标 | 要求 |
|---|---|
| 精度 | 设备编号全局唯一, 财务数据精确到 0.01 元 |
| 灵活性 | 校准周期、提醒策略可通过配置调整 |
| 时间特性 | 台账查询 < 300ms, 提醒任务每日凌晨执行 |

### 3.6.4 输入项

**设备表 (equipments)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 设备 ID |
| `equipment_no` | VARCHAR(30) | UNIQUE, NOT NULL | 设备编号 |
| `name` | VARCHAR(100) | NOT NULL | 设备名称 |
| `category` | VARCHAR(50) | NOT NULL | 类别 (力学/化学/环境) |
| `model` | VARCHAR(50) | NOT NULL | 型号规格 |
| `manufacturer` | VARCHAR(100) | | 厂家 |
| `serial_number` | VARCHAR(50) | | 出厂编号 |
| `supplier_id` | ULID | FK → suppliers.id | 供应商 |
| `purchase_price` | DECIMAL(12,2) | | 采购价格 |
| `purchase_date` | DATE | | 采购日期 |
| `acceptance_date` | DATE | | 验收日期 |
| `location` | VARCHAR(100) | | 存放位置 |
| `custodian_id` | ULID | FK → users.id | 保管人 |
| `status` | VARCHAR(30) | DEFAULT 'draft' | 状态 |
| `calibration_cycle_months` | INTEGER | | 校准周期 (月) |
| `last_calibration_date` | DATE | | 上次校准日期 |
| `next_calibration_date` | DATE | | 下次校准日期 |
| `calibration_org` | VARCHAR(100) | | 校准机构 |
| `certificate_no` | VARCHAR(50) | | 校准证书编号 |

### 3.6.5 输出项

| 字段名 | 类型 | 说明 |
|---|---|---|
| `equipment` | JSON | 设备完整信息 (含关联记录) |
| `calibration_schedule` | JSON[] | 校准计划列表 |
| `due_alerts` | JSON[] | 即将到期的校准/保养提醒 |
| `lifecycle_log` | JSON[] | 全生命周期事件时间线 |

### 3.6.6 算法

**下次校准日期计算**:
```
FUNCTION calculate_next_calibration(equipment):
    IF equipment.calibration_cycle_months IS NULL:
        RETURN NULL

    base_date = COALESCE(equipment.last_calibration_date,
                         equipment.acceptance_date)
    IF base_date IS NULL:
        RETURN NULL

    next_date = base_date + (equipment.calibration_cycle_months * '1 month')

    -- 如遇周末顺延至下一工作日
    dow = EXTRACT(DOW FROM next_date)
    IF dow = 6:  -- 周六
        next_date = next_date + INTERVAL '2 days'
    ELSIF dow = 0:  -- 周日
        next_date = next_date + INTERVAL '1 day'

    RETURN next_date
```

**设备使用率计算**:
```
FUNCTION calculate_utilization_rate(equipment_id, start_date, end_date):
    total_days = end_date - start_date
    test_tasks = SELECT COUNT(*) FROM test_tasks tt
                 JOIN test_records tr ON tr.test_task_id = tt.id
                 WHERE tt.equipment_used @> [{equipment_id}]
                 AND tt.created_at BETWEEN start_date AND end_date

    -- 假设每次检测任务平均占用 4 小时
    used_hours = test_tasks * 4
    total_hours = total_days * 8  -- 8 小时工作日
    utilization = ROUND((used_hours / total_hours) * 100, 2)
    RETURN LEAST(utilization, 100)
```

### 3.6.7 流程逻辑

```
+------------------+
|  采购申请         |
+--------+---------+
         |
         v
+------------------+
|  审批流程         | (预算/技术)
+--------+---------+
         |
         v
+------------------+
|  采购执行         |
+--------+---------+
         |
         v
+------------------+     +----------------------+
|  到货验收         |---->| 技术指标、合格证    |
+--------+---------+     +----------------------+
         |
         v
+------------------+     +----------------------+
|  设备入库         |---->| EQ-编号, 首次校准   |
|  (创建台账)       |     +----------------------+
+--------+---------+
         |
         v
        === 正常使用阶段 ===
         |
    +----+----+-------+
    v    v    v       v
  +--+ +----+ +----+ +----+
  |校| |保养| |维修| |核查|
  |准| |    | |    | |    |
  +--+ +----+ +----+ +----+
    |    |    |       |
    v    v    v       v
  记录  记录  记录   记录
  更新  更新  更新   更新
  日历        状态
         |
         v (到报废条件)
+------------------+
|  报废申请         |
+--------+---------+
         |
         v
+------------------+
|  审批 (残值评估)  |
+--------+---------+
         |
         v
+------------------+
|  报废执行         |
|  status=scrapped  |
+------------------+
```

### 3.6.8 接口

**上层模块调用**:
- 检测管理模块: 通过 `GET /api/v1/equipments?status=active` 获取可用设备
- 检测执行时记录使用的设备 (test_records 中的 equipment_used)
- 统计报表模块: 通过设备使用记录计算利用率

**下层子模块**:
- `equipment_numbering`: 设备编号生成器
- `calibration_scheduler`: 校准计划调度器 (Celery Periodic Task)
- `utilization_calculator`: 使用率计算
- `alert_service`: 到期提醒

**API 端点**:

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/v1/equipments` | 创建设备台账 | equipment:create |
| GET | `/api/v1/equipments` | 设备列表 | equipment:list |
| GET | `/api/v1/equipments/{id}` | 设备详情 | equipment:read |
| PUT | `/api/v1/equipments/{id}` | 更新设备信息 | equipment:update |
| POST | `/api/v1/equipments/{id}/calibration` | 记录校准 | equipment:calibrate |
| POST | `/api/v1/equipments/{id}/maintenance` | 记录保养 | equipment:maintain |
| POST | `/api/v1/equipments/{id}/repair` | 记录维修 | equipment:repair |
| POST | `/api/v1/equipments/{id}/check` | 期间核查 | equipment:check |
| POST | `/api/v1/equipments/{id}/scrap` | 报废申请 | equipment:scrap |
| GET | `/api/v1/equipments/{id}/lifecycle` | 生命周期记录 | equipment:read |
| GET | `/api/v1/equipments/due-calibration` | 即将到期设备 | equipment:list |
| GET | `/api/v1/equipments/{id}/utilization` | 使用率统计 | equipment:read |

**数据结构**:

```sql
CREATE TABLE equipments (
    id                      ULID PRIMARY KEY,
    equipment_no            VARCHAR(30) UNIQUE NOT NULL,
    name                    VARCHAR(100) NOT NULL,
    category                VARCHAR(50) NOT NULL,
    model                   VARCHAR(50) NOT NULL,
    manufacturer            VARCHAR(100),
    serial_number           VARCHAR(50),
    supplier_id             ULID REFERENCES suppliers(id),
    purchase_price          DECIMAL(12,2),
    purchase_date           DATE,
    acceptance_date         DATE,
    location                VARCHAR(100),
    custodian_id            ULID REFERENCES users(id),
    status                  VARCHAR(30) DEFAULT 'draft',
    calibration_cycle_months INTEGER,
    last_calibration_date   DATE,
    next_calibration_date   DATE,
    calibration_org         VARCHAR(100),
    certificate_no          VARCHAR(50),
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE equipment_calibrations (
    id              ULID PRIMARY KEY,
    equipment_id    ULID REFERENCES equipments(id),
    calibration_date DATE NOT NULL,
    next_date       DATE,
    result          VARCHAR(30) NOT NULL,  -- pass/fail/limited
    calibration_org VARCHAR(100),
    certificate_no  VARCHAR(50),
    certificate_file VARCHAR(500),
    data            JSONB,
    operator_id     ULID REFERENCES users(id),
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE equipment_maintenance_log (
    id              BIGSERIAL PRIMARY KEY,
    equipment_id    ULID REFERENCES equipments(id),
    type            VARCHAR(30) NOT NULL,  -- maintenance/repair/check
    description     TEXT NOT NULL,
    cost            DECIMAL(10,2),
    provider        VARCHAR(100),
    operator_id     ULID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_equipments_status ON equipments(status, category);
CREATE INDEX idx_equipments_calibration ON equipments(next_calibration_date)
    WHERE next_calibration_date IS NOT NULL;
CREATE INDEX idx_equipments_category ON equipments(category);
```

---

## 3.7 程序7: 标准方法库模块

### 3.7.1 程序描述

**目的**: 管理实验室使用的检测方法标准,支持 GB/T、JTG、TB、SL 等标准体系,提供方法版本控制与参数配置。

**特性**:
- 标准分类管理 (GB/T、JTG、TB、SL、ISO、ASTM)
- 方法版本控制 (新标准生效后旧版本历史留存)
- 方法参数配置 (检测项目、公式、修约精度、合格判定)
- 资质范围绑定 (CMA/CNAS 附表)
- 方法替代/失效标记

### 3.7.2 功能 (IPO)

**Input**:
- 标准方法信息 (标准号、名称、发布机构、实施日期)
- 方法版本 (版本号、变更说明、替代关系)
- 配置参数 (检测项目列表、计算公式、修约规则、判定条件)

**Process**:
1. 录入标准方法,校验标准号格式 (如 GB/T 50081-2019)
2. 方法版本变更时,保留旧版本并标记 superseded_by
3. 配置检测项目的公式、修约精度、合格判定标准
4. 绑定 CMA/CNAS 资质范围 (方法是否在附表内)
5. 标准更新提醒 (监控标准发布机构变更)

**Output**:
- 完整的标准方法库
- 方法版本历史
- 资质方法清单 (CMA/CNAS 附表)

### 3.7.3 性能

| 指标 | 要求 |
|---|---|
| 精度 | 标准号唯一标识, 版本号区分同一标准不同年度 |
| 灵活性 | 方法参数可配置, 支持不同修约精度与判定标准 |
| 时间特性 | 方法查询 < 200ms, 版本切换 < 100ms |

### 3.7.4 输入项

**标准方法表 (test_methods)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 方法 ID |
| `method_code` | VARCHAR(50) | NOT NULL | 方法编号 (自定义) |
| `standard_no` | VARCHAR(50) | NOT NULL | 标准号 (如 GB/T 50081-2019) |
| `standard_name` | VARCHAR(200) | NOT NULL | 标准名称 |
| `standard_type` | VARCHAR(20) | NOT NULL | 类型 (GB/T/JTG/TB/SL/ISO/ASTM) |
| `version` | VARCHAR(20) | DEFAULT 'current' | 版本状态 |
| `publish_date` | DATE | | 发布日期 |
| `effective_date` | DATE | NOT NULL | 实施日期 |
| `replacement_for` | ULID | FK → test_methods.id | 替代的方法 |
| `replaced_by` | ULID | FK → test_methods.id | 被替代至 |
| `category` | VARCHAR(50) | NOT NULL | 检测类别 |
| `parameters` | JSONB | NOT NULL | 检测项目参数配置 |
| `cma_qualified` | BOOLEAN | DEFAULT false | 是否有 CMA 资质 |
| `cnas_qualified` | BOOLEAN | DEFAULT false | 是否有 CNAS 资质 |
| `status` | VARCHAR(20) | DEFAULT 'active' | 状态 (active/superseded/withdrawn) |

**parameters JSONB 结构**:
```json
{
  "test_items": [
    {
      "item_code": "fc",
      "item_name": "抗压强度",
      "unit": "MPa",
      "formula": "(max_load * 1000) / area",
      "precision": 1,
      "rounding_rule": "gbt8170",
      "pass_condition": ">= design_strength",
      "required_fields": ["max_load", "area", "design_strength"]
    }
  ],
  "equipment_requirements": ["压力试验机"],
  "environment_requirements": {
    "temperature": {"min": 20, "max": 25},
    "humidity": {"min": null, "max": null}
  },
  "form_component": "CompressiveStrengthForm"
}
```

### 3.7.5 输出项

| 字段名 | 类型 | 说明 |
|---|---|---|
| `method` | JSON | 完整方法信息 (含参数配置) |
| `version_history` | JSON[] | 版本变更历史 |
| `qualified_methods` | JSON[] | CMA/CNAS 资质方法清单 |
| `active_methods` | JSON[] | 当前有效方法列表 |

### 3.7.6 算法

**标准号解析**:
```
FUNCTION parse_standard_no(standard_no):
    """
    解析标准号格式, 提取类型、序号、年份
    示例: "GB/T 50081-2019" → type="GB/T", number="50081", year="2019"
    """
    pattern = r'^([A-Z/]+)\s+(\d+)\s*-(\d{4})$'
    match = REGEX_MATCH(standard_no, pattern)
    IF NOT match:
        RAISE ValidationError("标准号格式错误")
    RETURN {
        'type': match[1],
        'number': match[2],
        'year': match[3]
    }
```

**版本替代链查询 (递归 CTE)**:
```sql
WITH RECURSIVE version_chain AS (
    SELECT id, standard_no, version, replacement_for, replaced_by,
           ARRAY[id] AS chain, 1 AS depth
    FROM test_methods
    WHERE id = :start_id

    UNION ALL

    SELECT tm.id, tm.standard_no, tm.version, tm.replacement_for,
           tm.replaced_by, vc.chain || tm.id, vc.depth + 1
    FROM test_methods tm
    JOIN version_chain vc ON tm.id = vc.replaced_by
)
SELECT * FROM version_chain ORDER BY depth;
```

### 3.7.7 流程逻辑

```
+------------------+
|  录入标准方法     |
+--------+---------+
         |
         v
+------------------+
|  解析标准号       | (校验格式)
+--------+---------+
         |
    +----+----+
    v         v
格式正确   格式错误 --> 报错提示
    |
    v
+------------------+     +----------------------+
|  检查同标准号     |---->| 同标准号存在?       |
|  是否已有         |     +----------------------+
+--------+---------+
         |
    +----+----+
    v         v
 NO         YES
    |         |
    |         v
    |    +------------------+
    |    | 旧版本标记        |
    |    | superseded        |
    |    | 建立替代关系      |
    |    +--------+----------+
    |             |
    v             v
+------------------+
|  配置方法参数     | (检测项目、公式、修约)
+--------+---------+
         |
         v
+------------------+
|  绑定资质范围     | (CMA/CNAS)
+--------+---------+
         |
         v
+------------------+
|  发布生效         | (status=active)
+------------------+
         |
         v
        === 日常使用 (检测方法选择) ===
         |
         v (标准更新时)
+------------------+
|  标准升级         |
|  新版本录入       |
|  旧版本归档       |
+------------------+
```

### 3.7.8 接口

**上层模块调用**:
- 检测管理模块: 通过 `GET /api/v1/test-methods/{id}` 获取检测方法参数,驱动表单渲染
- 报告管理模块: 通过 `GET /api/v1/test-methods?cma_qualified=true` 获取资质方法
- 样品管理模块: 方法选择器

**下层子模块**:
- `standard_parser`: 标准号解析
- `method_loader`: 方法配置读取 (含版本解析)
- `qualification_checker`: 资质范围校验

**API 端点**:

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/v1/test-methods` | 录入方法 | method:create |
| GET | `/api/v1/test-methods` | 方法列表 (可筛选) | method:list |
| GET | `/api/v1/test-methods/{id}` | 方法详情 | method:read |
| PUT | `/api/v1/test-methods/{id}` | 更新方法 | method:update |
| POST | `/api/v1/test-methods/{id}/supersede` | 标记替代 | method:update |
| GET | `/api/v1/test-methods/{id}/versions` | 版本历史 | method:read |
| GET | `/api/v1/test-methods/qualified` | 资质方法清单 | method:list |
| GET | `/api/v1/test-methods/categories` | 检测类别列表 | method:list |
| GET | `/api/v1/test-methods/{id}/form-schema` | 获取表单 schema | method:read |

**数据结构**:

```sql
CREATE TABLE test_methods (
    id              ULID PRIMARY KEY,
    method_code     VARCHAR(50) NOT NULL,
    standard_no     VARCHAR(50) NOT NULL,
    standard_name   VARCHAR(200) NOT NULL,
    standard_type   VARCHAR(20) NOT NULL,
    version         VARCHAR(20) DEFAULT 'current',
    publish_date    DATE,
    effective_date  DATE NOT NULL,
    replacement_for ULID REFERENCES test_methods(id),
    replaced_by     ULID REFERENCES test_methods(id),
    category        VARCHAR(50) NOT NULL,
    parameters      JSONB NOT NULL,
    cma_qualified   BOOLEAN DEFAULT false,
    cnas_qualified  BOOLEAN DEFAULT false,
    status          VARCHAR(20) DEFAULT 'active',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_test_methods_standard ON test_methods(standard_no);
CREATE INDEX idx_test_methods_category ON test_methods(category, status);
CREATE INDEX idx_test_methods_qualified ON test_methods(cma_qualified, cnas_qualified)
    WHERE status = 'active';
CREATE INDEX idx_test_methods_effective ON test_methods(effective_date DESC);
```

---

## 3.8 程序8: 工作流引擎模块

### 3.8.1 程序描述

**目的**: 提供轻量级状态机引擎,驱动样品流转、委托处理、报告审核等业务状态转换,所有变更可审计。

**特性**:
- JSON 定义的状态机 (持久化至数据库)
- 状态转换条件判断 (角色、字段值、时间)
- 自动触发 (状态变更后自动调用下游)
- 完整的状态变更审计日志
- 支持并行分支与条件分支

### 3.8.2 功能 (IPO)

**Input**:
- 工作流定义 (JSON: states, transitions, conditions)
- 状态转换请求 (entity_type, entity_id, action)
- 当前上下文 (用户角色、数据值)

**Process**:
1. 加载实体对应的工作流定义
2. 读取实体当前状态
3. 匹配可用转换 (当前状态 + action)
4. 校验转换条件 (if 配置了条件)
5. 执行状态转换
6. 执行 post_action (通知、回调、自动操作)
7. 写入审计日志

**Output**:
- 新状态
- 转换结果 (success/error + 原因)
- 审计日志

### 3.8.3 性能

| 指标 | 要求 |
|---|---|
| 精度 | 原子操作 (数据库事务), 状态保证一致性 |
| 灵活性 | 工作流定义热加载, 修改即生效, 无需重启 |
| 时间特性 | 单次状态转换 < 100ms, 含条件校验 < 200ms |

### 3.8.4 输入项

**工作流定义表 (workflow_definitions)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 定义 ID |
| `entity_type` | VARCHAR(50) | UNIQUE | 实体类型 (entrustment/sample/report) |
| `definition` | JSONB | NOT NULL | 状态机定义 |
| `version` | SMALLINT | DEFAULT 1 | 版本号 |
| `is_active` | BOOLEAN | DEFAULT true | 是否启用 |

**definition JSONB 结构示例**:
```json
{
  "initial_state": "draft",
  "states": {
    "draft": {"label": "草稿"},
    "pending_review": {"label": "待审核"},
    "approved": {"label": "已批准"},
    "rejected": {"label": "已退回"},
    "archived": {"label": "已归档"}
  },
  "transitions": [
    {
      "from": "draft",
      "to": "pending_review",
      "action": "submit",
      "label": "提交审核",
      "condition": "user.role in ['tester', 'engineer']",
      "required_fields": ["sample_count", "test_items"],
      "post_action": {"type": "notify", "role": "reviewer"}
    },
    {
      "from": "pending_review",
      "to": "approved",
      "action": "approve",
      "label": "审核通过",
      "condition": "user.role in ['reviewer', 'manager']",
      "post_action": {"type": "notify", "role": "issuer"}
    },
    {
      "from": "pending_review",
      "to": "rejected",
      "action": "reject",
      "label": "退回修改",
      "condition": "user.role in ['reviewer', 'manager']",
      "required_fields": ["rejection_reason"],
      "post_action": {"type": "notify", "role": "issuer"}
    }
  ]
}
```

**状态审计表 (workflow_audit_log)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | BIGSERIAL | PK | 日志 ID |
| `workflow_id` | ULID | FK → workflow_definitions.id | 工作流定义 |
| `entity_type` | VARCHAR(50) | NOT NULL | 实体类型 |
| `entity_id` | ULID | NOT NULL | 实体 ID |
| `from_state` | VARCHAR(50) | | 原状态 |
| `to_state` | VARCHAR(50) | NOT NULL | 新状态 |
| `action` | VARCHAR(50) | NOT NULL | 触发动作 |
| `actor_id` | ULID | FK → users.id | 操作人 |
| `context` | JSONB | | 转换上下文 |
| `condition_result` | JSONB | | 条件执行结果 |

### 3.8.5 输出项

| 字段名 | 类型 | 说明 |
|---|---|---|
| `new_state` | STRING | 转换后的状态 |
| `transition` | JSON | 执行的转换定义 |
| `audit_entry` | JSON | 审计日志记录 |
| `notifications` | JSON[] | 触发的通知列表 |

### 3.8.6 算法

**状态转换引擎**:
```
FUNCTION transition(entity_type, entity_id, action, user_id, context):
    workflow_def = load_workflow_definition(entity_type)
    entity = load_entity(entity_type, entity_id)
    current_state = entity.workflow_state

    -- 查找匹配的转换
    transition = FIND t IN workflow_def.transitions
        WHERE t.from == current_state AND t.action == action

    IF NOT transition:
        RAISE InvalidTransitionError(
            "No transition '" + action + "' from '" + current_state + "'")

    -- 校验条件
    IF transition.condition:
        ctx = {'user': get_user(user_id), 'entity': entity, 'context': context}
        IF NOT evaluate_condition(transition.condition, ctx):
            RAISE ConditionNotMetError("Condition not met for '" + action + "'")

    -- 校验必填字段
    IF transition.required_fields:
        FOR field IN transition.required_fields:
            IF context[field] IS EMPTY:
                RAISE ValidationError("Required field: " + field)

    -- 执行转换 (事务)
    BEGIN TRANSACTION
        entity.workflow_state = transition.to

        -- 执行后操作
        IF transition.post_action:
            execute_post_action(transition.post_action, entity)

        -- 写入审计
        INSERT INTO workflow_audit_log (
            workflow_id, entity_type, entity_id,
            from_state, to_state, action, actor_id, context
        )

        -- 更新实体状态字段
        UPDATE entity SET status = transition.to
    COMMIT

    RETURN {
        'new_state': transition.to,
        'transition': transition,
        'notifications': sent_notifications
    }
```

**支持的条件表达式运算符**:
- 比较: `==`, `!=`, `>`, `<`, `>=`, `<=`
- 集合: `in`, `not in`
- 逻辑: `and`, `or`, `not`
- 对象域: `user.role`, `entity.status`, `context.field_name`

### 3.8.7 流程逻辑

```
+------------------+
| 接收转换请求      | (entity, action)
+--------+---------+
         |
         v
+------------------+
| 加载工作流定义    | (JSON, 从缓存)
+--------+---------+
         |
         v
+------------------+
| 读取当前状态      |
+--------+---------+
         |
         v
+------------------+     +------------------+
| 匹配转换规则      |---->| 转换存在?        | --NO--> 返回错误
+--------+---------+     +------------------+
         | YES
         v
+------------------+     +------------------+
| 校验条件          |---->| 条件满足?        | --NO--> 返回错误
+--------+---------+     +------------------+
         | YES
         v
+------------------+     +------------------+
| 校验必填字段      |---->| 字段齐全?        | --NO--> 返回错误
+--------+---------+     +------------------+
         | YES
         v
+------------------+
| BEGIN TX         |
|  更新状态         |
|  执行后操作       |
|  写审计日志       |
| COMMIT           |
+--------+---------+
         |
         v
+------------------+
| 发送通知          | (post_action)
+--------+---------+
         |
         v
+------------------+
| 返回新状态        |
+------------------+
```

### 3.8.8 接口

**上层模块调用**: 所有业务模块通过 `transition(entity_type, entity_id, action, user_id, context)` 触发状态变更

**下层子模块**:
- `condition_evaluator`: 条件表达式解析 (安全的 AST 解析, 不使用 eval)
- `post_action_executor`: 后操作执行 (通知、回调)
- `workflow_loader`: 工作流定义加载 (Redis 缓存 5 分钟 TTL)
- `audit_writer`: 审计日志写入

**API 端点**:

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| GET | `/api/v1/workflows` | 工作流定义列表 | workflow:list |
| GET | `/api/v1/workflows/{entity_type}` | 实体工作流定义 | workflow:read |
| PUT | `/api/v1/workflows/{entity_type}` | 更新工作流定义 | workflow:admin |
| POST | `/api/v1/workflows/{entity_type}/transition` | 触发状态转换 | 按业务权限 |
| GET | `/api/v1/workflows/{entity_type}/{entity_id}/state` | 查询当前状态 | entity:read |
| GET | `/api/v1/workflows/{entity_type}/{entity_id}/available` | 可用转换列表 | entity:read |
| GET | `/api/v1/workflows/{entity_type}/{entity_id}/audit` | 审计日志 | entity:read |

**数据结构**:

```sql
CREATE TABLE workflow_definitions (
    id          ULID PRIMARY KEY,
    entity_type VARCHAR(50) UNIQUE NOT NULL,
    definition  JSONB NOT NULL,
    version     SMALLINT DEFAULT 1,
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE workflow_audit_log (
    id              BIGSERIAL PRIMARY KEY,
    workflow_id     ULID REFERENCES workflow_definitions(id),
    entity_type     VARCHAR(50) NOT NULL,
    entity_id       ULID NOT NULL,
    from_state      VARCHAR(50),
    to_state        VARCHAR(50) NOT NULL,
    action          VARCHAR(50) NOT NULL,
    actor_id        ULID REFERENCES users(id),
    context         JSONB,
    condition_result JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_workflow_audit_entity ON workflow_audit_log(entity_type, entity_id);
CREATE INDEX idx_workflow_audit_actor ON workflow_audit_log(actor_id, created_at DESC);
CREATE INDEX idx_workflow_audit_action ON workflow_audit_log(action, created_at DESC);
```

---

## 3.9 程序9: 计费管理模块

### 3.9.1 程序描述

**目的**: 管理实验室的计费、合同、账单、发票与收款流程,支持多维度价格矩阵与自动算价。

**特性**:
- 价格矩阵 (按检测方法、客户等级、数量阶梯)
- 自动算价 (委托单提交时自动计算)
- 合同管理 (框架协议、单价协议)
- 账单生成与确认
- 发票申请与跟踪
- 收款登记与对账

### 3.9.2 功能 (IPO)

**Input**:
- 价格规则 (方法 × 客户等级 × 数量阶梯)
- 合同信息 (框架协议、有效期、折扣)
- 委托单 (含检测项目)
- 收款记录

**Process**:
1. 委托单创建时,匹配价格矩阵
2. 按检测项目逐项查价,计算金额
3. 应用合同折扣 (如有)
4. 生成账单 (未确认状态)
5. 客户确认后生成发票申请
6. 收款登记,自动核销账单

**Output**:
- 费用明细 (逐项计价)
- 账单 (含总额、折扣、净额)
- 发票记录
- 收款台账

### 3.9.3 性能

| 指标 | 要求 |
|---|---|
| 精度 | 金额精确到 0.01 元, 使用 DECIMAL(12,2) |
| 灵活性 | 价格规则可配置, 支持临时调价 |
| 时间特性 | 自动算价 < 100ms/委托, 批量账单 < 2s |

### 3.9.4 输入项

**价格矩阵表 (price_rules)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 规则 ID |
| `test_method_id` | ULID | FK → test_methods.id | 检测方法 |
| `client_level` | VARCHAR(30) | | 客户等级 (A/B/C/标准) |
| `min_quantity` | INTEGER | DEFAULT 0 | 最小数量 |
| `max_quantity` | INTEGER | NULLABLE | 最大数量 (NULL=无限) |
| `unit_price` | DECIMAL(10,2) | NOT NULL | 单价 (元) |
| `effective_date` | DATE | NOT NULL | 生效日期 |
| `expiry_date` | DATE | NULLABLE | 失效日期 |

**账单表 (bills)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 账单 ID |
| `bill_no` | VARCHAR(30) | UNIQUE | 账单编号 (ZD-YYYYMMDD-NNNN) |
| `client_id` | ULID | FK → clients.id | 客户 |
| `entrust_id` | ULID | FK → entrustments.id | 关联委托 |
| `contract_id` | ULID | FK → contracts.id | 关联合同 |
| `items` | JSONB | NOT NULL | 费用明细 |
| `subtotal` | DECIMAL(12,2) | | 小计 |
| `discount_rate` | DECIMAL(5,2) | DEFAULT 100 | 折扣率 (%) |
| `discount_amount` | DECIMAL(12,2) | | 折扣金额 |
| `total_amount` | DECIMAL(12,2) | NOT NULL | 应付金额 |
| `paid_amount` | DECIMAL(12,2) | DEFAULT 0 | 已付金额 |
| `status` | VARCHAR(30) | DEFAULT 'draft' | 状态 |
| `due_date` | DATE | | 到期日期 |
| `invoice_no` | VARCHAR(50) | | 发票号码 |
| `invoice_date` | DATE | | 开票日期 |
| `paid_at` | TIMESTAMPTZ | | 付清时间 |

### 3.9.5 输出项

| 字段名 | 类型 | 说明 |
|---|---|---|
| `bill` | JSON | 完整账单信息 |
| `bill_items` | JSON[] | 费用明细列表 |
| `summary` | JSON | 金额汇总 (小计、折扣、净额、已付) |
| `payment_status` | JSON | 付款状态 (已付/未付/部分付清) |

### 3.9.6 算法

**自动算价**:
```
FUNCTION calculate_bill(entrustment):
    client = get_client(entrustment.client_id)
    contract = get_active_contract(client.id)
    bill_items = []

    FOR sample IN entrustment.samples:
        FOR test_item IN sample.test_items:
            price = lookup_price(
                method_id = test_item.method_id,
                client_level = client.level,
                quantity = test_item.quantity
            )

            amount = price * test_item.quantity
            bill_items.append({
                'sample_no': sample.sample_no,
                'test_item': test_item.name,
                'unit_price': price,
                'quantity': test_item.quantity,
                'amount': amount
            })

    subtotal = SUM(item.amount for item in bill_items)

    -- 应用合同折扣
    IF contract AND contract.discount_rate:
        discount_rate = contract.discount_rate
    ELSE:
        discount_rate = 100  -- 无折扣

    discount = ROUND(subtotal * (100 - discount_rate) / 100, 2)
    total = ROUND(subtotal - discount, 2)

    RETURN {
        'items': bill_items,
        'subtotal': subtotal,
        'discount_rate': discount_rate,
        'discount_amount': discount,
        'total': total
    }
```

**价格查找 (数量阶梯匹配)**:
```sql
SELECT unit_price FROM price_rules
WHERE test_method_id = :method_id
  AND (client_level IS NULL OR client_level = :client_level)
  AND :quantity >= min_quantity
  AND (:quantity <= max_quantity OR max_quantity IS NULL)
  AND effective_date <= CURRENT_DATE
  AND (expiry_date IS NULL OR expiry_date >= CURRENT_DATE)
ORDER BY min_quantity DESC  -- 取最精确的阶梯
LIMIT 1;
```

### 3.9.7 流程逻辑

```
+------------------+
|  委托单创建       |
+--------+---------+
         |
         v
+------------------+
|  自动算价         | (匹配价格矩阵)
+--------+---------+
         |
         v
+------------------+
|  匹配合同折扣     | (可选)
+--------+---------+
         |
         v
+------------------+
|  生成账单         | (status=draft)
+--------+---------+
         |
         v
+------------------+     +------------------+
|  确认账单         |---->| 客户确认?       | --NO--> 修改重发
+--------+---------+     +------------------+
         | YES
         v
+------------------+
|  status=confirmed |
+--------+---------+
         |
         v
+------------------+
|  发票申请         |
+--------+---------+
         |
         v
+------------------+
|  开具发票         | (记录发票号)
+--------+---------+
         |
         v
+------------------+
|  收款登记         |
+--------+---------+
         |
         v
+------------------+     +------------------+
|  自动核销         |---->| paid=total?     |
+--------+---------+     +--------+---------+
         |                YES|        | NO
         v                   v         v
  更新余额              已付清       部分付清
         |
         v
+------------------+
|  对账报表         |
+------------------+
```

### 3.9.8 接口

**上层模块调用**:
- 样品管理模块: 委托单状态变更时触发计费
- 报告管理模块: 报告批准后确认计费
- 统计报表模块: 营收统计

**下层子模块**:
- `price_matcher`: 价格匹配引擎
- `bill_calculator`: 算价引擎
- `discount_applier`: 折扣计算
- `invoice_tracker`: 发票跟踪
- `payment_reconciler`: 收款核销

**API 端点**:

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| GET | `/api/v1/price-rules` | 价格规则列表 | price_rule:list |
| POST | `/api/v1/price-rules` | 创建价格规则 | price_rule:create |
| PUT | `/api/v1/price-rules/{id}` | 更新价格规则 | price_rule:update |
| POST | `/api/v1/bills/calculate` | 试算费用 | bill:calculate |
| POST | `/api/v1/bills` | 创建账单 | bill:create |
| GET | `/api/v1/bills` | 账单列表 | bill:list |
| GET | `/api/v1/bills/{id}` | 账单详情 | bill:read |
| POST | `/api/v1/bills/{id}/confirm` | 确认账单 | bill:confirm |
| POST | `/api/v1/bills/{id}/invoice` | 申请发票 | bill:invoice |
| POST | `/api/v1/bills/{id}/payment` | 收款登记 | bill:payment |
| GET | `/api/v1/contracts` | 合同列表 | contract:list |
| POST | `/api/v1/contracts` | 创建合同 | contract:create |
| GET | `/api/v1/contracts/{id}` | 合同详情 | contract:read |

**数据结构**:

```sql
CREATE TABLE price_rules (
    id              ULID PRIMARY KEY,
    test_method_id  ULID REFERENCES test_methods(id),
    client_level    VARCHAR(30),
    min_quantity    INTEGER DEFAULT 0,
    max_quantity    INTEGER,
    unit_price      DECIMAL(10,2) NOT NULL,
    effective_date  DATE NOT NULL,
    expiry_date     DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE contracts (
    id              ULID PRIMARY KEY,
    contract_no     VARCHAR(30) UNIQUE NOT NULL,
    client_id       ULID REFERENCES clients(id),
    title           VARCHAR(200) NOT NULL,
    type            VARCHAR(30) NOT NULL,  -- framework/project
    discount_rate   DECIMAL(5,2) DEFAULT 100,
    start_date      DATE NOT NULL,
    end_date        DATE,
    status          VARCHAR(20) DEFAULT 'active',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bills (
    id              ULID PRIMARY KEY,
    bill_no         VARCHAR(30) UNIQUE NOT NULL,
    client_id       ULID REFERENCES clients(id),
    entrust_id      ULID REFERENCES entrustments(id),
    contract_id     ULID REFERENCES contracts(id),
    items           JSONB NOT NULL,
    subtotal        DECIMAL(12,2),
    discount_rate   DECIMAL(5,2) DEFAULT 100,
    discount_amount DECIMAL(12,2),
    total_amount    DECIMAL(12,2) NOT NULL,
    paid_amount     DECIMAL(12,2) DEFAULT 0,
    status          VARCHAR(30) DEFAULT 'draft',
    invoice_no      VARCHAR(50),
    invoice_date    DATE,
    due_date        DATE,
    paid_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payments (
    id              ULID PRIMARY KEY,
    bill_id         ULID REFERENCES bills(id),
    amount          DECIMAL(12,2) NOT NULL,
    payment_method  VARCHAR(30),  -- transfer/check/cash
    payment_date    DATE NOT NULL,
    reference_no    VARCHAR(50),
    operator_id     ULID REFERENCES users(id),
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_price_rules_lookup ON price_rules(
    test_method_id, client_level, min_quantity, effective_date
) WHERE expiry_date IS NULL OR expiry_date >= CURRENT_DATE;

CREATE INDEX idx_bills_client ON bills(client_id, status);
CREATE INDEX idx_bills_entrust ON bills(entrust_id);
CREATE INDEX idx_bills_status ON bills(status, due_date);
CREATE INDEX idx_payments_bill ON payments(bill_id, payment_date);
```

---

## 3.10 程序10: 质量管控模块

### 3.10.1 程序描述

**目的**: 管理实验室质量管理体系,包括不符合工作处理、纠正措施、内部审核、能力验证与质量指标监控。

**特性**:
- 不符合工作报告 (NCR)
- 纠正与预防措施 (CAPA)
- 内部审核计划与执行
- 能力验证/实验室间比对
- 质量指标看板
- 纠正措施跟踪

### 3.10.2 功能 (IPO)

**Input**:
- 不符合工作描述 (发现人、发现时间、不符合描述)
- 原因分析 (根本原因)
- 纠正措施 (措施内容、责任人、期限)
- 内审计划 (范围、审核员、时间)
- 能力验证结果 (参加项目、结果、z 值)

**Process**:
1. 不符合工作登记,触发审批流程
2. 原因分析 (5Why / 鱼骨图)
3. 制定纠正措施,分配责任人
4. 措施执行,验证有效性
5. 关闭不符合项
6. 内审计划执行,发现问题登记
7. 能力验证结果录入, z 值判定

**Output**:
- 不符合工作报告
- CAPA 跟踪记录
- 内审报告
- 能力验证报告
- 质量指标统计

### 3.10.3 性能

| 指标 | 要求 |
|---|---|
| 精度 | z 值精确到 0.01, 判定按 ISO 13528 执行 |
| 灵活性 | NCR/CAPA 流程可配置, 支持多级审批 |
| 时间特性 | NCR 创建 < 300ms, z 值计算 < 50ms |

### 3.10.4 输入项

**不符合工作表 (nonconformities)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 不符合工作 ID |
| `ncr_no` | VARCHAR(30) | UNIQUE, NOT NULL | 不符合编号 (NCR-YYYY-NNNN) |
| `type` | VARCHAR(30) | NOT NULL | 类型 (过程/结果/设备/体系) |
| `source` | VARCHAR(30) | NOT NULL | 来源 (内审/外审/日常/客户投诉) |
| `description` | TEXT | NOT NULL | 不符合描述 |
| `severity` | VARCHAR(20) | | 严重度 (轻微/一般/严重) |
| `discovered_by` | ULID | FK → users.id | 发现人 |
| `discovered_date` | DATE | DEFAULT CURRENT_DATE | 发现日期 |
| `root_cause` | TEXT | | 根本原因分析 |
| `correction` | TEXT | | 纠正措施 |
| `corrective_action` | TEXT | | 纠正措施 (预防再发) |
| `responsible_id` | ULID | FK → users.id | 责任人 |
| `due_date` | DATE | | 完成期限 |
| `verification_result` | TEXT | | 验证结果 |
| `status` | VARCHAR(30) | DEFAULT 'open' | 状态 |
| `closed_date` | DATE | | 关闭日期 |
| `closed_by` | ULID | FK → users.id | 关闭人 |

**能力验证表 (proficiency_tests)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 能力验证 ID |
| `pt_no` | VARCHAR(30) | UNIQUE | 编号 |
| `organizer` | VARCHAR(100) | NOT NULL | 组织者 |
| `test_item` | VARCHAR(100) | NOT NULL | 检测项目 |
| `test_method` | VARCHAR(50) | | 检测方法 |
| `laboratory_result` | DECIMAL(12,4) | | 实验室结果 |
| `assigned_value` | DECIMAL(12,4) | | 指定值 |
| `standard_deviation` | DECIMAL(12,4) | | 标准偏差 |
| `z_score` | DECIMAL(5,2) | | z 值 (自动计算) |
| `evaluation` | VARCHAR(20) | | 判定 (满意/可疑/不满意) |
| `report_date` | DATE | | 报告日期 |

**内部审核表 (internal_audits)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 内审 ID |
| `audit_no` | VARCHAR(30) | UNIQUE, NOT NULL | 内审编号 |
| `title` | VARCHAR(200) | NOT NULL | 内审名称 |
| `scope` | TEXT | | 审核范围 |
| `planned_date` | DATE | | 计划日期 |
| `actual_date` | DATE | | 实际日期 |
| `auditor_id` | ULID | FK → users.id | 审核员 |
| `findings` | JSONB | | 审核发现 |
| `status` | VARCHAR(30) | DEFAULT 'planned' | 状态 |
| `report_file` | VARCHAR(500) | | 报告文件路径 |

### 3.10.5 输出项

| 字段名 | 类型 | 说明 |
|---|---|---|
| `ncr` | JSON | 不符合工作完整记录 |
| `capa_log` | JSON[] | CAPA 执行记录 |
| `pt_evaluation` | JSON | 能力验证评价 |
| `quality_metrics` | JSON | 质量指标统计 |

### 3.10.6 算法

**z 值计算 (ISO 13528)**:
```
FUNCTION calculate_z_score(lab_result, assigned_value, std_dev):
    """
    z = (x - X) / σ

    |z| <= 2.0:  满意 (Satisfactory)
    2.0 < |z| < 3.0:  可疑 (Questionable)
    |z| >= 3.0:  不满意 (Unsatisfactory)
    """
    IF std_dev <= 0:
        RAISE ValidationError("标准偏差必须大于0")

    z = (lab_result - assigned_value) / std_dev
    z_rounded = round_gbt8170(Decimal(str(z)), 2)

    IF ABS(z_rounded) <= 2.0:
        evaluation = 'satisfactory'
    ELIF ABS(z_rounded) < 3.0:
        evaluation = 'questionable'
    ELSE:
        evaluation = 'unsatisfactory'

    RETURN {
        'z_score': z_rounded,
        'evaluation': evaluation
    }
```

**质量指标聚合**:
```
FUNCTION calculate_quality_metrics(period_start, period_end):
    RETURN {
        'ncr_count': count_ncre(
            start=period_start, end=period_end),
        'ncr_open_count': count_ncr(status='open'),
        'ncr_avg_closure_days': avg_days_to_close_ncr(),
        'capa_completion_rate': pct_capa_completed(),
        'internal_audit_findings': count_audit_findings(),
        'pt_satisfactory_rate': pct_pt_satisfactory(),
        'report_error_rate': pct_reports_reissued(),
        'sample_qualification_rate': pct_samples_qualified()
    }
```

**NCR 编号生成**:
```
FUNCTION generate_ncr_no(discovered_date):
    year = FORMAT(discovered_date, 'YYYY')
    seq = NEXTVAL('ncr_seq')
    seq_str = LPAD(CAST(seq AS TEXT), 4, '0')
    RETURN 'NCR-' + year + '-' + seq_str
```

### 3.10.7 流程逻辑

```
+------------------+
| 发现不符合工作    |
+--------+---------+
         |
         v
+------------------+
| 登记 NCR         | (生成编号)
+--------+---------+
         |
         v
+------------------+
| 初步评估         | (严重度分级)
+--------+---------+
         |
         v
+------------------+
| 原因分析         | (5Why / 鱼骨图)
+--------+---------+
         |
         v
+------------------+
| 制定纠正措施      | (指定责任人、期限)
+--------+---------+
         |
         v
+------------------+
| 措施执行         | (跟踪进度)
+--------+---------+
         |
         v
+------------------+     +------------------+
| 验证有效性        |---->| 有效?           | --NO--> 继续整改
+--------+---------+     +------------------+
         | YES
         v
+------------------+
| 关闭 NCR         | (status=closed)
+--------+---------+
         |
         v
+------------------+
| 归档并统计        |
+------------------+

能力验证流程 (并行):
+------------------+
| 参加能力验证      |
+--------+---------+
         |
         v
+------------------+
| 录入结果 + 指定值 | + 标准差
+--------+---------+
         |
         v
+------------------+
| 计算 z 值         | (ISO 13528)
+--------+---------+
         |
         v
+------------------+     +------------------+
| 结果判定          |---->| |z| >= 3?       | --YES--> 启动 NCR
+--------+---------+     +------------------+
         | NO
         v
+------------------+
| 记录归档         |
+------------------+
```

### 3.10.8 接口

**上层模块调用**:
- 报告管理模块: 报告退回/错误检测时登记不符合工作
- 统计报表模块: 质量指标统计
- 检测管理模块: 能力验证检测任务

**下层子模块**:
- `z_score_calculator`: z 值计算
- `ncr_numbering`: NCR 编号生成
- `capa_tracker`: CAPA 跟踪
- `quality_dashboard`: 质量指标聚合

**API 端点**:

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/v1/nonconformities` | 登记不符合工作 | ncr:create |
| GET | `/api/v1/nonconformities` | NCR 列表 | ncr:list |
| GET | `/api/v1/nonconformities/{id}` | NCR 详情 | ncr:read |
| PUT | `/api/v1/nonconformities/{id}` | 更新 NCR | ncr:update |
| POST | `/api/v1/nonconformities/{id}/capa` | 制定纠正措施 | ncr:capa |
| POST | `/api/v1/nonconformities/{id}/verify` | 验证有效性 | ncr:verify |
| POST | `/api/v1/nonconformities/{id}/close` | 关闭 NCR | ncr:close |
| POST | `/api/v1/proficiency-tests` | 录入能力验证 | pt:create |
| GET | `/api/v1/proficiency-tests` | 能力验证列表 | pt:list |
| GET | `/api/v1/proficiency-tests/{id}` | 详情 | pt:read |
| GET | `/api/v1/internal-audits` | 内审计划列表 | audit:list |
| POST | `/api/v1/internal-audits` | 创建内审 | audit:create |
| GET | `/api/v1/quality/metrics` | 质量指标 | quality:read |

**数据结构**:

```sql
CREATE SEQUENCE ncr_seq START 1;

CREATE TABLE nonconformities (
    id              ULID PRIMARY KEY,
    ncr_no          VARCHAR(30) UNIQUE NOT NULL,
    type            VARCHAR(30) NOT NULL,
    source          VARCHAR(30) NOT NULL,
    description     TEXT NOT NULL,
    severity        VARCHAR(20),
    discovered_by   ULID REFERENCES users(id),
    discovered_date DATE DEFAULT CURRENT_DATE,
    root_cause      TEXT,
    correction      TEXT,
    corrective_action TEXT,
    responsible_id  ULID REFERENCES users(id),
    due_date        DATE,
    verification_result TEXT,
    status          VARCHAR(30) DEFAULT 'open',
    closed_date     DATE,
    closed_by       ULID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE proficiency_tests (
    id              ULID PRIMARY KEY,
    pt_no           VARCHAR(30) UNIQUE NOT NULL,
    organizer       VARCHAR(100) NOT NULL,
    test_item       VARCHAR(100) NOT NULL,
    test_method     VARCHAR(50),
    laboratory_result DECIMAL(12,4),
    assigned_value  DECIMAL(12,4),
    standard_deviation DECIMAL(12,4),
    z_score         DECIMAL(5,2),
    evaluation      VARCHAR(20),
    report_date     DATE,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE internal_audits (
    id              ULID PRIMARY KEY,
    audit_no        VARCHAR(30) UNIQUE NOT NULL,
    title           VARCHAR(200) NOT NULL,
    scope           TEXT,
    planned_date    DATE,
    actual_date     DATE,
    auditor_id      ULID REFERENCES users(id),
    findings        JSONB,
    status          VARCHAR(30) DEFAULT 'planned',
    report_file     VARCHAR(500),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ncr_status ON nonconformities(status, due_date);
CREATE INDEX idx_ncr_discovered ON nonconformities(discovered_date DESC);
CREATE INDEX idx_pt_evaluation ON proficiency_tests(evaluation);
CREATE INDEX idx_audit_status ON internal_audits(status, planned_date);
```

---

## 3.11 程序11: 统计报表模块

### 3.11.1 程序描述

**目的**: 提供实验室运营数据的多维度统计分析,以 ECharts 可视化展示,支持样品量、合格率、报告周期、设备利用率、收入等关键指标的统计。

**特性**:
- 样品量统计 (按日/周/月/季度/年, 按类别)
- 合格率统计 (按方法、按检测员)
- 周转时间 (TAT - Turnaround Time) 统计
- 设备使用率统计
- 收入统计
- ECharts 图表渲染 (柱状图、折线图、饼图、雷达图)

### 3.11.2 功能 (IPO)

**Input**:
- 统计维度 (时间范围、分组字段、聚合函数)
- 过滤条件 (类别、状态、检测员、客户)
- 图表类型 (柱状图、折线图、饼图、雷达图)

**Process**:
1. 接收统计请求,构建 SQL 聚合查询
2. 从 PostgreSQL 执行聚合查询
3. 转换为 ECharts 数据格式 (series, xAxis, yAxis)
4. 返回统计结果
5. 支持 Excel 导出

**Output**:
- ECharts 数据格式 (JSON)
- 数据表格 (CSV/Excel)
- 统计摘要

### 3.11.3 性能

| 指标 | 要求 |
|---|---|
| 精度 | 聚合计算精度 0.01%, 金额精确到 0.01 元 |
| 灵活性 | 支持按任意维度组合筛选和分组 |
| 时间特性 | 常规查询 < 2s, 年度汇总 < 5s |

### 3.11.4 输入项

**统计请求参数**:

| 参数名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `metric` | STRING | REQUIRED | 指标类型 |
| `start_date` | DATE | REQUIRED | 起始日期 |
| `end_date` | DATE | REQUIRED | 结束日期 |
| `group_by` | STRING[] | OPTIONAL | 分组字段 |
| `filters` | JSON | OPTIONAL | 过滤条件 |
| `chart_type` | STRING | OPTIONAL | 图表类型 (bar/line/pie/radar) |

**metric 枚举**:

| 值 | 说明 |
|---|---|
| `sample_count` | 样品量统计 |
| `pass_rate` | 合格率统计 |
| `tat` | 周转时间统计 |
| `utilization` | 设备使用率 |
| `revenue` | 收入统计 |
| `dashboard` | 仪表板汇总数据 |

### 3.11.5 输出项

| 字段名 | 类型 | 说明 |
|---|---|---|
| `chart_option` | JSON | ECharts option 对象 |
| `table_data` | JSON[] | 表格数据 |
| `summary` | JSON | 统计摘要 (总数、平均、最大、最小) |

### 3.11.6 算法

**周转时间 (TAT) 统计**:
```
FUNCTION calculate_tat(start_date, end_date):
    """
    TAT = 报告批准日期 - 收样日期 (工作日)
    统计: 平均TAT、中位数TAT、P95、P99
    """
    results = SELECT
        e.id as entrust_id,
        e.received_date,
        r.approved_at as issue_date,
        business_days(e.received_date, r.approved_at::date) as tat_days
    FROM entrustments e
    JOIN reports r ON r.entrust_id = e.id
    WHERE e.received_date >= start_date
      AND e.received_date <= end_date
      AND r.status = 'approved'

    tat_values = [r.tat_days for r in results]

    RETURN {
        'avg': mean(tat_values),
        'median': median(tat_values),
        'p95': percentile(tat_values, 95),
        'p99': percentile(tat_values, 99),
        'max': max(tat_values),
        'min': min(tat_values),
        'count': len(tat_values)
    }
```

**工作日计算 (排除周末)**:
```
FUNCTION business_days(start_date, end_date):
    IF start_date > end_date:
        RETURN 0

    days = 0
    current = start_date

    WHILE current < end_date:
        IF current.weekday() < 5:  -- 周一到周五
            days += 1
        current += timedelta(days=1)

    RETURN days
```

**ECharts 数据格式转换**:
```
FUNCTION to_echarts_bar(data, x_field, y_field):
    RETURN {
        'title': {'text': '统计图表'},
        'tooltip': {'trigger': 'axis'},
        'xAxis': {'type': 'category', 'data': [r[x_field] for r in data]},
        'yAxis': {'type': 'value'},
        'series': [{
            'type': 'bar',
            'data': [r[y_field] for r in data]
        }]
    }
```

### 3.11.7 流程逻辑

```
+------------------+
|  选择统计指标     |
|  (样品量/合格率   |
|   TAT/利用率/     |
|   收入)           |
+--------+---------+
         |
         v
+------------------+
|  设置时间范围     |
|  过滤条件         |
+--------+---------+
         |
         v
+------------------+
|  构建聚合 SQL     | (GROUP BY, HAVING)
+--------+---------+
         |
         v
+------------------+
|  执行查询         | (PostgreSQL)
+--------+---------+
         |
         v
+------------------+
|  转换数据格式     | (→ ECharts)
+--------+---------+
         |
         v
+------------------+     +----------------------+
|  渲染图表         |---->| ECharts 柱/折/饼图  |
|  (前端)          |     +----------------------+
+--------+---------+
         |
         v
+------------------+
|  导出 (可选)      | (Excel/CSV)
+------------------+
```

### 3.11.8 接口

**上层模块调用**:
- 首页 Dashboard: 调用关键指标 API 展示概览
- 管理决策: 多维度报表分析

**下层子模块**:
- `query_builder`: SQL 聚合查询构建器
- `chart_formatter`: ECharts 数据格式转换
- `export_service`: Excel/CSV 导出
- `cache_manager`: 统计结果缓存 (Redis 5 分钟 TTL)

**API 端点**:

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| GET | `/api/v1/reports/stats/samples` | 样品量统计 | stats:read |
| GET | `/api/v1/reports/stats/pass-rate` | 合格率统计 | stats:read |
| GET | `/api/v1/reports/stats/tat` | TAT 统计 | stats:read |
| GET | `/api/v1/reports/stats/utilization` | 设备利用率 | stats:read |
| GET | `/api/v1/reports/stats/revenue` | 收入统计 | stats:read |
| GET | `/api/v1/reports/stats/dashboard` | 仪表板数据 | stats:read |
| GET | `/api/v1/reports/stats/export` | 导出 Excel | stats:export |

**数据结构 (物化视图 + 缓存)**:

```sql
-- 每日统计物化视图 (定时刷新)
CREATE MATERIALIZED VIEW mv_daily_stats AS
SELECT
    e.received_date::date as stat_date,
    COUNT(DISTINCT e.id) as entrust_count,
    COUNT(DISTINCT s.id) as sample_count,
    COUNT(DISTINCT s.id) FILTER (
        WHERE s.status = 'completed'
    ) as completed_sample_count,
    COUNT(DISTINCT s.id) FILTER (
        WHERE s.status = 'pending_test'
    ) as pending_sample_count,
    COUNT(DISTINCT tr.id) FILTER (
        WHERE tr.result = 'pass'
    ) as pass_count,
    COUNT(DISTINCT tr.id) FILTER (
        WHERE tr.result = 'fail'
    ) as fail_count
FROM entrustments e
LEFT JOIN samples s ON s.entrust_id = e.id
LEFT JOIN test_tasks tt ON tt.sample_id = s.id
LEFT JOIN test_records tr ON tr.test_task_id = tt.id
GROUP BY e.received_date::date;

-- 统计结果缓存表
CREATE TABLE stats_cache (
    id          BIGSERIAL PRIMARY KEY,
    metric_key  VARCHAR(100) NOT NULL,
    filters_hash VARCHAR(64) NOT NULL,
    result      JSONB NOT NULL,
    cached_at   TIMESTAMPTZ DEFAULT NOW(),
    expires_at  TIMESTAMPTZ
);

CREATE UNIQUE INDEX idx_mv_daily_stats_date ON mv_daily_stats(stat_date);
CREATE INDEX idx_stats_cache_lookup ON stats_cache(metric_key, filters_hash)
    WHERE expires_at > NOW();
```

---

## 3.12 程序12: 系统配置模块

### 3.12.1 程序描述

**目的**: 管理系统级配置参数、数据字典、操作日志、通知模板,为全系统提供可配置的基础设施支撑。

**特性**:
- 数据字典管理 (枚举值、下拉选项)
- 系统参数配置 (键值对, 热加载)
- 操作日志审计 (全模块操作记录)
- 通知模板管理 (邮件、短信、站内消息)
- 系统参数版本控制

### 3.12.2 功能 (IPO)

**Input**:
- 字典条目 (字典类型、键、值、排序)
- 系统参数 (键、值、描述、类型)
- 通知模板 (类型、主题、内容、变量)

**Process**:
1. 字典配置变更时,刷新 Redis 缓存
2. 系统参数读取带缓存 (Redis 5 分钟 TTL)
3. 操作日志异步写入 (通过 FastAPI 中间件)
4. 通知发送时加载对应模板,渲染变量
5. 参数变更写入审计日志

**Output**:
- 字典列表 (按类型分组)
- 参数值 (缓存/直读)
- 通知渲染结果
- 操作日志 (审计)

### 3.12.3 性能

| 指标 | 要求 |
|---|---|
| 精度 | 参数值类型安全, 按定义的类型校验 |
| 灵活性 | 热加载, 参数变更 5 秒内全局生效 |
| 时间特性 | 字典查询 < 10ms (缓存命中), 参数读取 < 15ms |

### 3.12.4 输入项

**数据字典表 (sys_dict_type + sys_dict_data)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 字典类型 ID |
| `dict_type` | VARCHAR(50) | UNIQUE, NOT NULL | 字典类型编码 |
| `dict_name` | VARCHAR(100) | NOT NULL | 字典类型名称 |
| `description` | TEXT | | 描述 |
| `is_system` | BOOLEAN | DEFAULT false | 是否系统内置 |

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 字典数据 ID |
| `dict_type_id` | ULID | FK → sys_dict_type.id | 所属字典类型 |
| `dict_label` | VARCHAR(100) | NOT NULL | 显示标签 |
| `dict_value` | VARCHAR(100) | NOT NULL | 存储值 |
| `sort_order` | INTEGER | DEFAULT 0 | 排序号 |
| `is_active` | BOOLEAN | DEFAULT true | 是否启用 |
| `css_class` | VARCHAR(50) | | 前端样式类 |

**系统参数表 (sys_config)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 参数 ID |
| `config_key` | VARCHAR(100) | UNIQUE, NOT NULL | 参数键 |
| `config_value` | TEXT | NOT NULL | 参数值 |
| `value_type` | VARCHAR(20) | DEFAULT 'string' | 值类型 (string/int/float/bool/json) |
| `description` | TEXT | | 描述 |
| `is_system` | BOOLEAN | DEFAULT false | 是否系统内置 |

**通知模板表 (notification_templates)**:

| 字段名 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | ULID | PK | 模板 ID |
| `template_code` | VARCHAR(50) | UNIQUE, NOT NULL | 模板编码 |
| `name` | VARCHAR(100) | NOT NULL | 模板名称 |
| `channel` | VARCHAR(20) | NOT NULL | 通道 (email/sms/in_system) |
| `subject` | VARCHAR(200) | | 邮件主题 (含模板变量) |
| `content` | TEXT | NOT NULL | 模板内容 (Jinja2) |
| `variables` | JSONB | | 可用变量说明 |
| `is_active` | BOOLEAN | DEFAULT true | 是否启用 |

### 3.12.5 输出项

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dict_tree` | JSON[] | 字典树 (类型 → 数据) |
| `config_value` | ANY | 参数值 (按类型转换) |
| `rendered_notification` | JSON | 渲染后的通知 (subject + body) |
| `operation_logs` | JSON[] | 操作日志列表 |

### 3.12.6 算法

**参数值类型转换**:
```
FUNCTION get_config(key):
    """
    从 Redis 缓存读取参数, 未命中则查数据库并写入缓存
    按 value_type 转换为对应类型
    """
    cached = redis.get('config:' + key)
    IF cached:
        RETURN deserialize(cached)

    row = SELECT * FROM sys_config WHERE config_key = key
    IF NOT row:
        RETURN None

    IF row.value_type == 'int':
        value = int(row.config_value)
    ELIF row.value_type == 'float':
        value = float(row.config_value)
    ELIF row.value_type == 'bool':
        value = row.config_value.lower() in ('true', '1', 'yes')
    ELIF row.value_type == 'json':
        value = json.loads(row.config_value)
    ELSE:
        value = row.config_value

    redis.set('config:' + key, serialize(value), ex=300)  -- 5 分钟
    RETURN value
```

**通知模板渲染**:
```
FUNCTION render_notification(template_code, context):
    template = SELECT * FROM notification_templates
               WHERE template_code = template_code AND is_active = true

    IF template.channel == 'email':
        subject = jinja2.Template(template.subject).render(context)
        body = jinja2.Template(template.content).render(context)
        RETURN {
            'channel': 'email',
            'subject': subject,
            'body': body
        }
    ELIF template.channel == 'sms':
        body = jinja2.Template(template.content).render(context)
        RETURN {
            'channel': 'sms',
            'body': body
        }
    ELSE:
        body = jinja2.Template(template.content).render(context)
        RETURN {
            'channel': 'in_system',
            'title': template.name,
            'body': body
        }
```

**操作日志写入 (中间件)**:
```
@app.middleware("http")
async def log_operations(request, call_next):
    if request.method not in ('POST', 'PUT', 'DELETE', 'PATCH'):
        RETURN await call_next(request)

    response = await call_next(request)

    IF response.status_code < 400:
        user = get_current_user_from_token(request)
        INSERT INTO audit_logs (
            user_id, action, resource, resource_id,
            details, ip_address, user_agent
        ) VALUES (
            user.id,
            request.method + ' ' + request.url.path,
            extract_resource(request.url.path),
            extract_id(request.url.path),
            extract_request_body(request),
            request.client.host,
            request.headers.get('user-agent')
        )

    RETURN response
```

### 3.12.7 流程逻辑

```
字典管理流程:
+------------------+
|  维护字典类型     | (样品类别、检测方法类型...)
+--------+---------+
         |
         v
+------------------+
|  维护字典数据     | (键值对、排序、样式)
+--------+---------+
         |
         v
+------------------+     +------------------+
|  变更检测        |---->| 刷新 Redis 缓存  |
|  (有变更?)       |     +------------------+
+--------+---------+
         |
         v
+------------------+
|  前端下拉渲染     | (按 dict_type 获取)
+------------------+

系统参数流程:
+------------------+
|  管理员修改参数   |
+--------+---------+
         |
         v
+------------------+
|  验证类型         | (int/float/bool/json)
+--------+---------+
         |
         v
+------------------+
|  写入数据库      |
+--------+---------+
         |
         v
+------------------+
|  失效 Redis 缓存  | (下次读取自动重新加载)
+--------+---------+
         |
         v
  全系统 5 秒内生效

通知模板流程:
+------------------+
|  定义通知模板     |
+--------+---------+
         |
         v
+------------------+
|  业务模块触发    | (如: 报告批准)
+--------+---------+
         |
         v
+------------------+
|  加载对应模板     | (by template_code)
+--------+---------+
         |
         v
+------------------+
|  Jinja2 渲染     | (注入变量)
+--------+---------+
         |
         v
+------------------+     +------------------+
|  发送通知         |---->| email/sms/站内  |
+------------------+     +------------------+
```

### 3.12.8 接口

**上层模块调用**: 全系统通过 `get_config(key)` 和 `get_dict_data(type)` 获取配置

**下层子模块**:
- `config_loader`: 系统参数加载 (含缓存管理)
- `dict_service`: 字典数据服务
- `audit_middleware`: 操作日志中间件
- `notification_service`: 通知渲染与发送

**API 端点**:

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| GET | `/api/v1/dict-types` | 字典类型列表 | dict:list |
| POST | `/api/v1/dict-types` | 创建字典类型 | dict:create |
| GET | `/api/v1/dict-types/{type}/data` | 字典数据 | dict:list |
| POST | `/api/v1/dict-types/{type}/data` | 创建字典条目 | dict:create |
| PUT | `/api/v1/dict-types/{type}/data/{id}` | 更新字典条目 | dict:update |
| GET | `/api/v1/configs` | 系统参数列表 | config:list |
| POST | `/api/v1/configs` | 创建参数 | config:create |
| PUT | `/api/v1/configs/{key}` | 更新参数 | config:update |
| GET | `/api/v1/configs/{key}` | 获取参数值 | config:read |
| GET | `/api/v1/notification-templates` | 通知模板列表 | template:list |
| POST | `/api/v1/notification-templates` | 创建模板 | template:create |
| PUT | `/api/v1/notification-templates/{id}` | 更新模板 | template:update |
| POST | `/api/v1/notification-templates/{id}/preview` | 预览渲染 | template:read |
| GET | `/api/v1/audit-logs` | 操作日志 (分页) | audit:list |
| GET | `/api/v1/audit-logs/export` | 导出审计日志 | audit:export |

**数据结构**:

```sql
CREATE TABLE sys_dict_type (
    id          ULID PRIMARY KEY,
    dict_type   VARCHAR(50) UNIQUE NOT NULL,
    dict_name   VARCHAR(100) NOT NULL,
    description TEXT,
    is_system   BOOLEAN DEFAULT false,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sys_dict_data (
    id          ULID PRIMARY KEY,
    dict_type_id ULID REFERENCES sys_dict_type(id) ON DELETE CASCADE,
    dict_label  VARCHAR(100) NOT NULL,
    dict_value  VARCHAR(100) NOT NULL,
    sort_order  INTEGER DEFAULT 0,
    is_active   BOOLEAN DEFAULT true,
    css_class   VARCHAR(50),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sys_config (
    id          ULID PRIMARY KEY,
    config_key  VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    value_type  VARCHAR(20) DEFAULT 'string',
    description TEXT,
    is_system   BOOLEAN DEFAULT false,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE notification_templates (
    id          ULID PRIMARY KEY,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    name        VARCHAR(100) NOT NULL,
    channel     VARCHAR(20) NOT NULL,  -- email/sms/in_system
    subject     VARCHAR(200),
    content     TEXT NOT NULL,
    variables   JSONB,
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_dict_data_type ON sys_dict_data(dict_type_id, sort_order);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource, created_at DESC);
CREATE INDEX idx_audit_logs_time ON audit_logs(created_at DESC);
```

-- 常见系统配置项初始化

```sql
INSERT INTO sys_config (config_key, config_value, value_type, description) VALUES
    ('lab.name', 'XX工程质量检测有限公司', 'string', '实验室名称'),
    ('lab.address', 'XX市XX区XX路XX号', 'string', '实验室地址'),
    ('lab.cma_certificate', 'CMA认证编号', 'string', 'CMA证书编号'),
    ('lab.cnas_certificate', 'CNAS认可编号', 'string', 'CNAS证书编号'),
    ('report.title', '检测报告', 'string', '报告标题'),
    ('barcode.printer', 'Zebra GK888t', 'string', '条码打印机型号'),
    ('barcode.label_size', '60x40', 'string', '标签尺寸 (mm)'),
    ('login.max_attempts', '5', 'int', '最大登录尝试次数'),
    ('login.lockout_minutes', '30', 'int', '锁定时长 (分钟)'),
    ('sample.retention_days', '180', 'int', '样品默认保留天数'),
    ('tat.warning_days', '3', 'int', 'TAT预警天数'),
    ('calibration.alert_days', '30', 'int', '校准到期提前提醒天数'),
    ('jwt.access_token_minutes', '15', 'int', 'Access Token有效期 (分钟)'),
    ('jwt.refresh_token_days', '7', 'int', 'Refresh Token有效期 (天)');
```

-- 常见字典类型初始化

```sql
INSERT INTO sys_dict_type (dict_type, dict_name, is_system) VALUES
    ('sample_category', '样品类别', true),
    ('sample_source', '样品来源', true),
    ('test_result', '检测结果', true),
    ('equipment_status', '设备状态', true),
    ('method_type', '标准类型', true),
    ('client_level', '客户等级', true),
    ('bill_status', '账单状态', true),
    ('ncr_type', '不符合类型', true),
    ('ncr_severity', '严重度', true),
    ('notification_channel', '通知渠道', true),
    ('dept', '部门', true);
```

-- END OF 02-detailed-design.md

## 附: 深层设计确认补充 (Phase 2)

> 以下章节为详细设计的补充说明，基于视觉化设计确认结果编写。

### 附.1 组织架构管理 (树形部门结构)

#### 数据结构
组织树采用邻接表模型 (Adjacency List)，表结构:
```sql
CREATE TABLE system.departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    parent_id UUID REFERENCES system.departments(id),
    dept_head_id UUID REFERENCES auth.users(id),
    category VARCHAR(20), -- '检测室' | '收样室' | '报告室' | '职能科室'
    detection_capabilities TEXT[], -- ['水泥', '混凝土', '钢筋', '沥青']
    status VARCHAR(10) DEFAULT 'active',
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_dept_parent ON system.departments(parent_id);
```

#### 行级权限映射规则
| 角色 | 数据可见范围 | 规则 |
|------|-------------|------|
| 检测员 | 仅本部门 + 仅本人任务 | `WHERE dept_id = current_user.dept_id AND assigned_to = current_user.id` |
| 审核员 | 本部门所有记录 | `WHERE dept_id = current_user.dept_id` |
| 技术负责人 | 本部门 + 子部门 | `WHERE dept_id IN (SELECT id FROM system.departments WHERE id = current_user.dept_id OR path LIKE current_user.dept_path || '%')` |
| 质量负责人 | 全局 (跨部门) | 无限制 |
| 系统管理员 | 全局 | 无限制 |

#### 树形查询 (Recursive CTE)
```sql
WITH RECURSIVE dept_tree AS (
    SELECT id, name, code, parent_id, ARRAY[id] as path, 0 as level
    FROM system.departments WHERE parent_id IS NULL
    UNION ALL
    SELECT d.id, d.name, d.code, d.parent_id, dt.path || d.id, dt.level + 1
    FROM system.departments d JOIN dept_tree dt ON d.parent_id = dt.id
)
SELECT * FROM dept_tree ORDER BY path;
```

### 附.2 人员角色权限矩阵 (可视化配置)

#### 权限矩阵数据模型
```sql
-- 权限粒度定义
CREATE TABLE auth.permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource VARCHAR(50) NOT NULL,  -- 'orders', 'samples', 'tasks', 'reports', 'records', 'equipment'
    action VARCHAR(20) NOT NULL,    -- 'create', 'view', 'edit', 'delete', 'review', 'export', 'approve', 'sign'
    scope VARCHAR(20) NOT NULL,     -- 'all' | 'dept' | 'self'
    description VARCHAR(200)
);
-- 复合唯一约束
CREATE UNIQUE INDEX uq_perm_ras ON auth.permissions(resource, action, scope);

-- 角色-权限关联 (矩阵行)
CREATE TABLE auth.role_permissions (
    role_id INT REFERENCES auth.roles(id),
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,
    scope VARCHAR(20) NOT NULL DEFAULT 'self',
    PRIMARY KEY (role_id, resource, action)
);
```

#### 可视化配置界面规则
- **行**: 资源类别 (委托单、样品、检测任务、报告、原始记录、设备、标准)
- **列**: 操作 (创建、查看、编辑、删除、审核、导出、签发)
- **单元格值**: 权限范围下拉 (无 / 仅自己 / 本部门 / 全部)
- **前端**: Ant Design Table + 下拉选择器，一键全选/清空
- **保存**: 批量更新 auth.role_permissions 表

#### 10 角色权限摘要
| 角色 | 委托单 | 样品 | 检测任务 | 报告 | 原始记录 | 设备 | 权限特点 |
|------|--------|------|---------|------|---------|------|---------|
| 委托方 | 创建/查看 | — | — | 查看(自己的) | — | — | 最小权限 |
| 收样员 | 查看/编辑 | 创建/编辑 | — | — | — | — | 仅限收样 |
| 检测员 | 创建/查看 | 查看(本部门) | 执行(仅自己) | 查看(本部门) | 创建/编辑(仅自己) | 查看(本部门) | 核心执行者 |
| 审核员 | 查看(本部门) | 查看(本部门) | 查看(本部门) | 审核(本部门) | 查看(本部门) | 查看(本部门) | 二级审核 |
| 批准人 | 查看(本部门) | 查看(本部门) | 查看(本部门) | 批准(本部门) | 查看(本部门) | 查看(本部门) | 三级批准 |
| 技术负责人 | 全部 | 全部 | 全部 | 全部 | 全部 | 全部 | 跨本部门+子部门 |
| 质量负责人 | 全部 | 全部 | 全部 | 全部 | 全部 | 全部 | 全局质控 |
| 设备管理员 | — | — | — | — | — | 全部 | 仅设备模块 |
| 样品管理员 | — | 全部 | — | — | — | — | 仅样品模块 |
| 系统管理员 | 全部 | 全部 | 全部 | 全部 | 全部 | 全部 | 所有权限+系统配置 |

### 附.3 人员完整档案管理 (CMA必需)

#### 额外表结构
```sql
CREATE TABLE auth.employee_profiles (
    user_id INT PRIMARY KEY REFERENCES auth.users(id),
    employee_no VARCHAR(20) UNIQUE NOT NULL,  -- EMP-YYYY-NNN
    id_card_encrypted VARCHAR(255),
    education VARCHAR(20),  -- '高中' | '大专' | '本科' | '硕士' | '博士'
    major VARCHAR(100),
    hire_date DATE,
    position VARCHAR(50),
    department_id UUID REFERENCES system.departments(id),
    status VARCHAR(10) DEFAULT 'active',  -- 'active' | 'on_leave' | 'resigned'
    photo_file_id UUID REFERENCES file_store(id)
);

CREATE TABLE auth.certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT REFERENCES auth.users(id),
    cert_type VARCHAR(30),  -- 'CMA上岗证' | '检测资质-水泥' | '检测资质-混凝土' | '审核员授权' | '批准人授权'
    cert_name VARCHAR(100),
    cert_no VARCHAR(50),
    issuing_org VARCHAR(100),
    issue_date DATE,
    expiry_date DATE,
    status VARCHAR(10),  -- 'valid' | 'expiring_soon' | 'expired'
    file_id UUID REFERENCES file_store(id),  -- 证书扫描件
    notes TEXT
);
CREATE INDEX idx_cert_expiry ON auth.certificates(expiry_date);

CREATE TABLE auth.training_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT REFERENCES auth.users(id),
    training_name VARCHAR(100) NOT NULL,
    training_date DATE,
    result VARCHAR(10),  -- 'pass' | 'fail'
    file_id UUID REFERENCES file_store(id)
);

-- 人员能力矩阵 (人员→检测方法的授权关系)
CREATE TABLE auth.staff_capabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT REFERENCES auth.users(id),
    test_method_id INT REFERENCES testing.test_methods(id),
    authorized_by INT REFERENCES auth.users(id),
    authorized_at TIMESTAMPTZ DEFAULT NOW(),
    valid_until DATE,
    status VARCHAR(10) DEFAULT 'active'
);
```

#### 资质到期预警机制
- **T-90 天**: 系统通知 → 人员本人 + 部门负责人
- **T-30 天**: 系统通知 + 标记为 "即将到期"，任务分配时提示风险
- **T-0 天**: 标记为 "已过期"，**自动取消该方法的检测任务分配资格**
- Celery 定时任务 (每天 08:00) 执行: `SELECT user_id, cert_type, expiry_date FROM auth.certificates WHERE expiry_date <= NOW() + INTERVAL '90 days' AND status = 'valid'`

### 附.4 标准管理 (标准→方法→参数三级)

#### 表关系确认
```
standards (1:N) → test_methods (1:N) → test_method_parameters (1:N)
```

#### 版本变更流程
1. 新版本标准录入 → 状态: `draft`
2. 标准管理员对比变更 → 填写 change_description
3. 系统自动标记受影响的 test_methods（同标准号旧版方法标记为 `pending_review`）
4. 技术负责人审核 → 状态: `approved`
5. 旧版标准标记为 `superseded`, replaced_by = 新版 ID
6. 旧版方法标记为 `deprecated` (历史数据仍可读，新委托不可选)

### 附.5 完整参数定义模板

#### 参数定义完整字段
```sql
CREATE TABLE testing.test_method_parameters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    method_id INT REFERENCES testing.test_methods(id),
    param_code VARCHAR(30) NOT NULL,          -- PAR-CONC-001
    param_name VARCHAR(100) NOT NULL,         -- 抗压强度
    param_type VARCHAR(20) NOT NULL,           -- 'numeric' | 'text' | 'select' | 'computed'
    unit VARCHAR(20),                          -- MPa, %, mm, kN
    data_format VARCHAR(20),                   -- 'integer' | 'float'
    decimal_places INT,                        -- 1
    rounding_rule VARCHAR(30),                 -- 'gb8170_0.1' | 'gb8170_1' | 'gb8170_0.5'
    formula TEXT,                             -- 'F / (W * H) * 1000' (DSL表达式)
    formula_inputs JSONB,                     -- {"F": {"label": "破坏荷载", "unit": "kN", "source": "instrument"}, "W": {"label": "宽度", "default": 150}}
    min_value DECIMAL,
    max_value DECIMAL,
    standard_value TEXT,                      -- '≥30' (C30)
    judgment_rule VARCHAR(20),                -- 'gte' | 'lte' | 'between' | 'exact'
    judgment_min DECIMAL,
    judgment_max DECIMAL,
    is_required BOOLEAN DEFAULT true,
    is_auto_collect BOOLEAN DEFAULT false,    -- 是否仪器自动采集
    sort_order INT DEFAULT 0,
    UNIQUE(method_id, param_code)
);
```

### 附.6 完整委托单

#### 委托单字段定义 (前端表单)
| 区域 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| 委托单位信息 | 单位名称 | 下拉(客户库) | ✓ | 自动带出联系人/电话/地址 |
| | 联系人 | 文本 | ✓ | |
| | 联系电话 | 文本 | ✓ | 手机格式校验 |
| | 通讯地址 | 文本 | | |
| 工程信息 | 工程名称 | 文本 | ✓ | |
| | 施工部位 | 文本 | | 如"3号桥墩" |
| | 监理单位 | 文本 | | |
| 检测要求 | 检测类别 | 单选 | ✓ | 委托/见证/监督/仲裁 |
| | 检测性质 | 单选 | ✓ | 常规/紧急/加急 |
| | 要求完成日期 | 日期选择器 | ✓ | 不得早于当天 |
| | 备注/特殊要求 | 多行文本 | | |
| 样品清单 (可多行) | 样品名称 | 下拉 | ✓ | |
| | 规格型号 | 文本 | ✓ | 如 Φ25/HRB400E |
| | 样品数量 | 数字 | ✓ | |
| | 代表数量 | 文本 | | 如 "60t" |
| | 生产厂家 | 文本 | | |
| | 检测项目 | 多选 | ✓ | 级联选择: 类别→方法 |
| | 检测标准 | 自动带出 | — | 根据检测方法自动关联 |

### 附.7 原始记录标准表式 (GB/T 规范)

#### 典型表式结构 (以混凝土抗压强度为例)
表头区域:
- 委托编号、样品编号、试验编号 (三联号关联，可扫码跳转)
- 检测依据 (标准名称+编号，自动带出)
- 检测日期、检测环境 (温湿度，自动读取或手动填写)
- 仪器设备 (名称+编号+校准状态，验证是否在校准有效期内)

数据表格区域:
- 每行为一个试件/样本
- 列包含: 试件编号、规格尺寸、截面积、破坏荷载、原始值、修约值、单项判定
- **自动计算列** (背景绿色): 强度值 = 破坏荷载 / 面积 × 1000
- **自动修约列** (背景浅绿): 按 GB/T 8170 修约
- **超标高亮**: 实测值超出标准范围时红色标记

表尾区域:
- 代表值计算 (平均值/最大值/最小值/标准差)
- 结论判定 (基于标准值比对)
- 签名栏: 检测员(电子签名) + 审核员 + 日期
- 条码: 原始记录唯一标识，可扫描关联

#### 打印输出
- 支持 A4 横向打印
- 打印格式与电子格式一致
- 可先打印 → 手写填写 → 拍照/扫描上传 → 自动关联对应任务

### 附.8 检测报告标准CMA表式

#### 页面布局
1. **页眉**: 实验室名称 + 地址 + CMA 章 (左上) + CNAS 章 (右上，仅 CNAS 报告)
2. **标题**: "检 测 报 告" (大字居中)
3. **报告编号**: 右上角，REP-YYYY-NNNN
4. **基本信息区**: 委托单位、工程名称、检测类别、报告日期 (浅灰背景表格)
5. **检测数据区**: 检测项目、标准要求、检测结果、单项判定 (粗线表格)
6. **结论区**: "该样品所检项目符合 XXX 要求。" (加粗)
7. **签章区**: 检测员 + 审核员 + 批准人 (三级签名) + 签发日期
8. **页脚**: 页码 (第X页 共Y页) + 防伪二维码
9. **骑缝章**: 多页报告 PDF 合并后在右侧加骑缝章图片

#### PDF 生成流程
1. Jinja2 渲染 HTML 报告模板
2. WeasyPrint 转换为 PDF
3. 叠加 CMA/CNAS 章图片 (位置固定)
4. 多页叠加骑缝章
5. 写入 MinIO (reports 桶)
6. 返回 PDF 下载 URL

### 附.9 编号生成规则

#### 规则定义表
```sql
CREATE TABLE system.numbering_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(50) UNIQUE NOT NULL,
    prefix VARCHAR(10) NOT NULL,
    date_format VARCHAR(20),   -- 'YYYYMM' | 'YYYYMMDD' | 'YYYY'
    sequence_length INT DEFAULT 4,
    reset_period VARCHAR(10),  -- 'monthly' | 'daily' | 'yearly' | 'never'
    description VARCHAR(200)
);

CREATE TABLE system.number_sequences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(50) REFERENCES system.numbering_rules(rule_name),
    period VARCHAR(20) NOT NULL,  -- '202506', '20250615', '2025'
    next_value INT NOT NULL DEFAULT 1,
    UNIQUE(rule_name, period)
);
```

#### 编号规则配置
| 类型 | 规则 | 格式 | 示例 | 重置周期 |
|------|------|------|------|---------|
| 委托编号 | WT-年月-4位序列 | WT-YYYYMM-NNNN | WT-202506-0042 | 月 |
| 样品编号 | YP-送样日期-4位序列-子序号 | YP-YYYYMMDD-NNNN-X | YP-20250615-0001-A | 日 |
| 报告编号 | REP-年-4位序列 | REP-YYYY-NNNN | REP-2025-0042 | 年 |
| 任务编号 | TK-年月-4位序列 | TK-YYYYMM-NNNN | TK-202506-0128 | 月 |

#### 跳号处理
CMA 要求编号连续。如遇删除/撤销导致跳号:
- 不真正删除记录，状态改为 `cancelled`
- 编号保留但不使用 (占位)
- 审计日志记录: `编号 WT-202506-0043 已撤销 (原因: XXX)`

#### 生成机制
```sql
-- 使用数据库函数 + 事务保证并发安全
CREATE OR REPLACE FUNCTION generate_number(rule_name_arg VARCHAR)
RETURNS TEXT AS $$
DECLARE
    current_period TEXT;
    next_val INT;
    result TEXT;
BEGIN
    -- 计算当前周期
    SELECT CASE 
        WHEN (SELECT reset_period FROM system.numbering_rules WHERE rule_name = rule_name_arg) = 'monthly' 
        THEN TO_CHAR(NOW(), 'YYYYMM')
        WHEN reset_period = 'daily'
        THEN TO_CHAR(NOW(), 'YYYYMMDD')
        WHEN reset_period = 'yearly'
        THEN TO_CHAR(NOW(), 'YYYY')
        ELSE '0'
    END INTO current_period FROM system.numbering_rules WHERE rule_name = rule_name_arg;
    
    -- 原子更新 (行级锁保证并发安全)
    UPDATE system.number_sequences 
    SET next_value = next_value + 1
    WHERE rule_name = rule_name_arg AND period = current_period
    RETURNING next_value INTO next_val;
    
    IF NOT FOUND THEN
        INSERT INTO system.number_sequences (rule_name, period, next_value)
        VALUES (rule_name_arg, current_period, 2)
        RETURNING next_value INTO next_val;
        next_val := 1;
    END IF;
    
    -- 拼装编号
    SELECT prefix || '-' || period || '-' || LPAD(next_val::TEXT, sequence_length, '0')
    INTO result FROM system.numbering_rules WHERE rule_name = rule_name_arg;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;
```

### 附.10 参数计算引擎 (DSL)

#### DSL 语言规范

**支持的运算符**: `+`, `-`, `*`, `/`, `**` (幂), `sqrt()`, `abs()`, `max()`, `min()`, `avg()`, `sum()`, `round()`

**参数引用**: 双引号包裹参数编码，如 `"F"`, `"W"`, `"H"`

**示例公式**:
```
# 混凝土抗压强度:
"F" / ("W" * "H") * 1000

# 钢筋屈服强度:
"F_yield" / (3.14159 * ("D" / 2) ** 2)

# 伸长率:
("L_final" - "L_original") / "L_original" * 100

# 含泥量:
("m_before" - "m_after") / "m_sample" * 100

# 三点弯曲抗折强度:
3 * "F" * "L" / (2 * "b" * "h" ** 2)
```

#### DSL 执行引擎
```python
# services/calculation/dsl_evaluator.py
import ast
import math
from decimal import Decimal, ROUND_HALF_EVEN

class DSLEncoder:
    """安全的公式语言解释器"""
    
    ALLOWED_NAMES = {
        'sqrt': math.sqrt,
        'abs': abs,
        'max': max,
        'min': min,
        'avg': lambda *args: sum(args) / len(args),
        'sum': sum,
        'round': round,
        'pi': math.pi,
    }
    
    def evaluate(self, formula: str, params: dict) -> Decimal:
        """执行公式计算，返回 Decimal 结果"""
        # 1. 替换参数引用 "CODE" -> Decimal(value)
        parsed = self._substitute_params(formula, params)
        # 2. AST 安全解析 (只允许算术运算)
        tree = ast.parse(parsed, mode='eval')
        self._validate_tree(tree)
        # 3. 在受限环境中执行
        result = eval(compile(tree, '<formula>', 'eval'), 
                     {"__builtins__": {}}, 
                     self._build_env(params))
        return Decimal(str(result))
    
    def _substitute_params(self, formula: str, params: dict) -> str:
        import re
        def replacer(match):
            code = match.group(1)
            value = params.get(code)
            if value is None:
                raise ValueError(f"参数 {code} 未提供")
            return f"Decimal('{value}')"
        return re.sub(r'"(\w+)"', replacer, formula)
```

#### DSL 公式存储与渲染
- **存储**: JSONB 字段 `formula` + `formula_inputs` (定义参数来源)
- **前端**: Monaco Editor 嵌入 (语法高亮 + 参数自动补全)
- **校验**: 保存时执行测试用例验证公式可执行
- **沙箱**: 禁止 import, exec, eval, 文件系统操作等危险操作
<!-- OMO_INTERNAL_INITIATOR -->

## 附.11 Phase 3 深层细节确认补充

> 以下章节基于 Phase 3 可视化决策确认结果编写。

### 附.11.1 开发进度管理 (看板式 Wave 追踪)

采用看板模式管理 6 个 Wave 的开发进度，每个 Wave 内拆分为 3-5 个可独立验收的 Task Card。

#### Wave 结构
| Wave | 内容 | 预计工期 | 依赖 |
|------|------|---------|------|
| W1 | 基础架构 (DB+Auth+存储) | 2周 | 无 |
| W2 | 核心流程 (委托+收样+检测+工作流) | 3周 | W1 |
| W3 | 报告生成 (模板+PDF+三级审核) | 2周 | W2 |
| W4 | 原始记录 (硬编码表单+数据采集) | 3周 | W2 |
| W5 | 设备+标准+计费 | 2周 | W1 |
| W6 | 质量管控+统计报表+部署验收 | 2周 | W1-W5 |

#### 看板视图定义
- **列**: Backlog → In Progress → Review → Done → Deployed
- **卡片字段**: Task ID、描述、负责人、截止日期、阻塞标识
- **阻塞项**: 红色高亮，标注阻塞原因

### 附.11.2 Web 系统页面导航结构 (角色分组菜单)

不同角色看到不同的侧边栏菜单。菜单树按 `role_id` 从 `auth.role_menus` 表动态加载。

#### 菜单权限表设计
```sql
CREATE TABLE system.role_menus (
    role_id INT REFERENCES auth.roles(id),
    menu_path VARCHAR(50) NOT NULL,  -- '/samples', '/reports'
    menu_label VARCHAR(50) NOT NULL,
    menu_icon VARCHAR(30),
    parent_path VARCHAR(50),  -- NULL = 顶级菜单
    sort_order INT DEFAULT 0,
    PRIMARY KEY (role_id, menu_path)
);
```

#### 10 角色菜单可见性矩阵
| 菜单模块 | 委托方 | 收样 | 检测员 | 审核员 | 批准人 | 技术负责 | 质量负责 | 设管理员 | 样管理员 | 系统管 |
|---------|--------|------|--------|--------|--------|---------|---------|---------|---------|-------|
| 📊 工作台 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 📋 委托管理 | 查看自己的 | ✓ | ✓ | 查看 | 查看 | ✓ | ✓ | — | ✓ | ✓ |
| 📦 样品管理 | — | ✓ | 查看本部门 | 查看本部门 | 查看 | ✓ | ✓ | — | ✓ | ✓ |
| 🔬 检测执行 | — | — | ✓ | — | — | ✓ | ✓ | ✓ | — | ✓ |
| 📄 报告管理 | 查看自己的 | — | 查看本部门 | ✓ | ✓ | ✓ | ✓ | — | — | ✓ |
| 🔧 设备管理 | — | — | — | — | — | ✓ | ✓ | ✓ | — | ✓ |
| 📚 标准方法 | — | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ |
| 💰 计费管理 | 查看自己的账单 | — | — | — | — | ✓ | ✓ | — | — | ✓ |
| 🛡️ 质量管控 | — | — | — | — | — | ✓ | ✓ | — | — | ✓ |
| ⚙️ 系统设置 | — | — | — | — | — | — | — | — | — | ✓ |

#### 前端实现 (React + Ant Design)
```tsx
// 侧边栏动态渲染
const Sidebar = () => {
  const user = useAuthStore(s => s.user);
  const menus = useMenuStore(s => s.getMenusByRole(user.role));
  return <Menu items={menus} mode="inline" theme="dark" />;
};
// 路由守卫
const RouteGuard = ({ children, allowedRoles }) => {
  const user = useAuthStore(s => s.user);
  if (!allowedRoles.includes(user.role)) return <Navigate to="/unauthorized" />;
  return children;
};
```

### 附.11.3 委托+样品组合录入 (单页分步)

采用三步分步表单 (Stepper Form)，支持中途暂存草稿。

#### 步骤设计
| 步骤 | 内容 | 必填校验 | 操作按钮 |
|------|------|---------|---------|
| Step 1: 委托信息 | 委托单位、工程名称、联系人、检测要求、要求完成日期 | 5个必填字段 | 暂存草稿 / 下一步 |
| Step 2: 样品清单 | 可添加 N 个样品，每个含名称/规格/数量/检测项目(级联选择) | 至少 1 个样品 | 上一步 / +添加样品 / 下一步 |
| Step 3: 提交确认 | 预览完整委托单，确认后生成委托编号并提交 | — | 上一步 / 提交委托 |

#### 数据流
```
Form Draft (localStorage) → POST /api/v1/orders (status='draft')
→ POST /api/v1/orders/{id}/samples (批量添加)
→ PUT /api/v1/orders/{id}/submit (status='submitted',生成委托编号)
```

### 附.11.4 原始记录创新表单 (模块化卡片+条码+粗框线)

#### 设计原则
- **独立模块卡片**: 每个检测参数 (如"抗压强度"、"环境条件") 为独立卡片
- **右上角条码**: 每个模块右上角包含唯一条码，扫描后定位到该模块
- **2px 粗框线**: 模块边界采用 2px 粗边框，作为 OCR 图像解析时的定位点
- **打印→手写→扫描→回填**: 支持电子填写直接打印，也支持打印后手写填写再拍照/扫描上传

#### 模块卡片结构
```
┌───────────────────────────────────────────┐ 2px 粗边框 (OCR 定位用)
│  💎 参数模块: 抗压强度         |||||||||  ← 右上角条码
├───────────────────────────────────────────┤
│  [表头: 试件/规格/面积/荷载/强度/判定]    │
│  [数据行: S-001-A | 150³ | 22500 | 532.5 │
│           23.7 [自动] | 合格]             │
│  [数据行: S-001-B | 150³ | 22500 | 612.0 │
│           27.2 [自动] | 合格]             │
├───────────────────────────────────────────┤
│  计算公式: F/(W×H)×1000 | 修约: GB/T 8170 │
└───────────────────────────────────────────┘
```

#### OCR 回填流程
1. **扫描**: 纸质原始记录拍照/扫描 → 上传至 MinIO (`attachments` 桶)
2. **图像预处理**: OpenCV 检测 2px 粗边框 → 定位每个模块卡片
3. **条码识别**: 读取右上角条码 → 解析模块ID (如 PAR-CONC-001)
4. **表格OCR**: 在定位区域内做表格结构识别 → 提取单元格文字
5. **数据回填**: 将 OCR 结果写入 `testing.test_results` 表，标记 `data_source='ocr'`
6. **人工校验**: 回填后高亮显示，检测员确认或修正

#### 技术选型
- **条码库**: python-barcode (生成) + pyzbar / zxing (解析)
- **OCR引擎**: PaddleOCR (中文+表格识别最佳)
- **图像处理**: OpenCV (边缘检测 + 透视变换 + 去噪)

### 附.11.5 退回/变更操作 (状态机回退+原因必填)

#### 退回规则
| 当前状态 | 可退回目标 | 退回原因 | 通知对象 | 审计记录 |
|---------|-----------|---------|---------|---------|
| 审核中 → 检测 | 检测中 | **必填** (至少10字) | 原检测员 | 操作人/时间/IP/原因 |
| 批准中 → 审核 | 审核中 | **必填** | 审核员 | 同上 |
| 签发后 → 批准 | 批准中 | **必填** (重大变更) | 批准人+技术负责人 | 同上+变更审批记录 |

#### 数据变更规范
- 检测报告或原始记录中修改任何数值：
  1. 必须填写变更原因 (下拉预设+自由文本)
  2. 系统自动保留旧值 (在 `test_results` 表增加 `original_value` 字段)
  3. 生成变更审计记录 → `audit_log.resource='test_results'`
  4. 报告版本号 +1 (旧版归档，新版生成)
  5. CMA 外审时须能提供变更原因记录

#### 状态转换 API
```python
# POST /api/v1/workflows/{instance_id}/transitions
{
    "transition": "reject_to_testing",
    "reason": "检测数据缺失:试件#2破坏荷载未录入,请重新补录",
    "target_user_id": 12  # 退回给谁
}
```

### 附.11.6 样品流转追踪 (可视化全生命周期)

#### 追踪节点
每个样品生命周期中的关键节点：
```
委托创建 → 收样(扫码+拍照) → 存储(扫码+位置记录) → 领取(扫码)
→ 检测开始(扫码) → 检测记录(数据录入/仪器采集) → 检测完成
→ 审核 → 批准 → 签发 → 样品处置(退回/留样/废弃)
```

#### 节点数据结构
```sql
CREATE TABLE commission.sample_tracking_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sample_id INT REFERENCES commission.samples(id),
    action VARCHAR(30) NOT NULL,  -- 'received', 'stored', 'issued', 'testing_started', 'testing_completed', etc.
    operator_id INT REFERENCES auth.users(id),
    location VARCHAR(50),         -- 'A区-3架-2层'
    device_id INT REFERENCES equipment.equipment(id),
    barcode_verified BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_sample_tracking ON commission.sample_tracking_logs(sample_id, created_at DESC);
```

### 附.11.7 三级审核 (逐级审核+逐级退回)

#### 审核流程
```
检测完成 → [审核] → 审核通过 → [批准] → 批准通过 → [签发] → 报告生效
              ↓ 不通过           ↓ 不通过
         退回检测员             退回审核人
```

#### 审核员权限约束
- 审核员**只能看到**状态为 `pending_review` (待审核) 的记录
- 审核员**不能修改**任何检测数据，只能审核通过或退回
- 审核后自动记录 `report_review_logs` 表：审核人、时间、意见、结果

### 附.11.8 报告修改留痕 (修订版本对比)

#### 版本管理
```sql
CREATE TABLE reporting.report_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id INT REFERENCES reporting.reports(id),
    version_no INT NOT NULL,  -- V1, V2, V3...
    html_content TEXT,
    pdf_file_id UUID REFERENCES file_store(id),
    modified_by INT REFERENCES auth.users(id),
    modification_reason TEXT NOT NULL,  -- **必填**
    approved_by INT REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- V1 永远不可删除 (WORM 存储)
```

#### 前端对比显示
- **红色删除线**: 旧版本独有的内容
- **绿色高亮**: 新版本新增/修改的内容
- **侧边栏**: 版本列表 (V1, V2, V3...)，点击切换查看

### 附.11.9 设备校准预警 (三级预警+过期拦截)

#### 预警规则
| 阶段 | 条件 | 动作 | 影响 |
|------|------|------|------|
| **T-30 天** | 校准到期前30天 | 邮件通知设备管理员 | 提醒预约校准 |
| **T-7 天** | 校准到期前7天 | 站内推送+黄色标记 | 日历提醒 |
| **T-0 天** | 校准到期当天 | 系统锁定设备 | **无法分配新检测任务**，已进行中的任务允许完成 |
| **过期后** | 超期未校准 | 红色高亮+持续锁定 | 每月自动发送催办报告 |

#### Celery 定时任务
```python
@celery_app.task
def check_calibration_expiry():
    """每天 08:00 执行，检查设备校准状态"""
    threshold_30 = date.today() + timedelta(days=30)
    threshold_7 = date.today() + timedelta(days=7)
    today = date.today()
    
    # T-30天预警
    equipments = Equipment.objects.filter(next_calibration_date=threshold_30, status='active')
    for eq in equipments:
        send_email(eq.custodian, f'设备 {eq.name} 校准将在30天后到期')
    
    # T-0天锁定
    expired = Equipment.objects.filter(next_calibration_date__lt=today, status='active')
    for eq in expired:
        eq.status = 'calibration_expired'
        eq.save()
```

### 附.11.10 质量管控仪表盘 (CMA/CNAS 专用)

#### 四大核心指标
| 指标 | 计算方式 | 阈值 | 预警颜色 |
|------|---------|------|---------|
| **检测合格率** | 合格报告数 / 总报告数 | ≥95% | <95%黄色, <90%红色 |
| **按期完成率 (TAT)** | 按期完成数 / 总任务数 | ≥90% | <90%黄色, <80%红色 |
| **超期未校准设备** | status='calibration_expired' 计数 | 0 为达标 | >0 红色 |
| **30天内到期证书** | expiry_date < NOW()+30d 计数 | — | 黄色预警 |

#### 不符合项跟踪表
```sql
CREATE TABLE quality.nonconformities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nc_no VARCHAR(20) UNIQUE,  -- NC-YYYY-NNN
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(30),  -- '检测环境' | '设备校准' | '人员资质' | '程序执行' | '数据记录'
    severity VARCHAR(10),  -- 'minor' | 'major' | 'critical'
    detected_by INT REFERENCES auth.users(id),
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    root_cause TEXT,
    corrective_action TEXT NOT NULL,
    responsible INT REFERENCES auth.users(id),
    deadline DATE NOT NULL,
    status VARCHAR(20),  -- 'open' | 'in_progress' | 'verified' | 'closed'
    closed_at TIMESTAMPTZ
);
```

### 附.11.11 数据导入导出 (模板化导入+校验报告)

#### 导入流程
1. **下载模板**: Excel 模板含列头+数据类型说明+必填项标红
2. **上传文件**: 拖拽或点击上传，最大 50MB
3. **预校验**: 后端逐行校验 (类型/范围/必填/关联数据存在性)
4. **预览结果**: 显示通过/失败行数，失败行标红+具体原因
5. **确认导入**: 仅导入通过校验的数据
6. **错误报告下载**: 可下载失败的行及错误原因

#### 校验规则引擎
```python
class ImportValidator:
    RULES = {
        'required': lambda v, r, c: v is not None and v != '',
        'range': lambda v, r, c: r.min_value <= float(v) <= r.max_value if v else False,
        'foreign_key': lambda v, r, c: db.exists(Model, id=v),
        'format': lambda v, r, c: re.match(r.pattern, str(v)) is not None,
        'unique': lambda v, r, c: not db.exists(Model, code=v),
    }
```

### 附.11.12 消息通知 (站内+推送双通道)

#### 通知通道
| 事件类型 | 站内信 | 浏览器推送 | 短信 (可选) | 邮件 |
|---------|--------|-----------|------------|------|
| 新任务分配 | ✓ | ✓ | — | — |
| 审核结果 | ✓ | ✓ | — | — |
| 检测超时 | ✓ | ✓ | ✓ | — |
| 校准到期 | ✓ | ✓ | ✓ | ✓ |
| 报告签发 | ✓ | ✓ | — | ✓ |
| 资质到期预警 | ✓ | — | ✓ | ✓ |

#### 通知数据模型
```sql
CREATE TABLE system.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT REFERENCES auth.users(id),
    type VARCHAR(30) NOT NULL,  -- 'task_assigned', 'review_result', 'calibration_warning', etc.
    title VARCHAR(200) NOT NULL,
    content TEXT,
    channel VARCHAR(20),  -- 'inapp', 'push', 'sms', 'email'
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_notif_user_unread ON system.notifications(user_id, is_read);
```

#### 浏览器推送实现
```typescript
// 前端 Notification API
if ('Notification' in window && Notification.permission === 'granted') {
    const ws = new WebSocket('/ws/notifications');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        new Notification(data.title, { body: data.content, icon: '/lims-icon.png' });
    };
}
```

### 附.11.13 权限操作审计 (完整权限操作审计)

#### 审计表结构
```sql
CREATE TABLE auth.permission_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    performed_by INT REFERENCES auth.users(id) NOT NULL,
    action VARCHAR(20) NOT NULL,  -- 'grant', 'revoke', 'role_change'
    target_user_id INT REFERENCES auth.users(id),
    old_value JSONB,
    new_value JSONB,
    reason TEXT,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- 此表数据不可修改/删除 (仅INSERT)
```

#### 审计内容示例
| 操作 | 旧值 | 新值 |
|------|------|------|
| 授权 | — | 张三 → 检测任务:查看(本部门) |
| 收回 | 李四 → 报告:批准 | — |
| 角色变更 | 检测员 | 审核员 |

### 附.11.14 检测周期超时预警 (TAT 倒计时)

#### 四级预警体系
| 级别 | 状态 | 条件 | 通知 | 处理 |
|------|------|------|------|------|
| 🟢 正常 | <70% TAT | — | 无 | — |
| 🟡 预警 | 70%-90% TAT | — | 通知检测员本人 | 加速处理 |
| 🔴 超时 | >100% TAT | — | 通知部门主管 | 主管介入 |
| 🚨 严重 | >150% TAT | — | 通知质量负责人 | 启动调查 |

#### TAT 计算
```
TAT = DATEDIFF(任务实际完成时间, 任务创建时间)
TAT_标准 = 检测方法的 turnaround_time 字段 (默认 7 天)
TAT_进度 = TAT / TAT_标准 * 100%
```

### 附.11.15 客户自助服务门户

#### 客户门户功能
- **在线委托**: 客户自行创建检测委托 (简化版表单)
- **进度查询**: 查看已委托样品的当前状态
- **报告下载**: 已签发的报告 PDF 下载
- **账单查询**: 查看历史账单和付款状态
- **消息沟通**: 与实验室人员站内消息沟通

#### 客户认证
- 独立登录入口 (`/client/login`)
- 每个客户一个账号 (由系统管理员或收样员创建)
- 客户只能看到**自己**的委托/报告/账单 (行级权限隔离)

### 附.11.16 电子签名 (三重确认签名)

#### 三重确认字段
| 字段 | 来源 | 作用 |
|------|------|------|
| **密码验证** | 用户输入 | 确认操作者身份 |
| **IP 白名单** | 系统自动获取 | 确认操作地点 (仅内网可签发) |
| **时间戳** | 系统服务器时间 | 固化签名时间点，不可篡改 |

#### 前端实现
```tsx
// 签名确认对话框
const SignatureConfirm = ({ reportId, onConfirm }) => {
  const [password, setPassword] = useState('');
  const { ip, timestamp } = useMachineInfo();
  
  const handleConfirm = async () => {
    await api.post(`/reports/${reportId}/actions/sign`, {
      password: hashPassword(password),
      ip_address: ip,
      timestamp: timestamp.toISOString(),
      signer_role: 'approver'
    });
  };
  // ... 渲染对话框
};
```

### 附.11.17 报告防伪 (二维码+骑缝章+在线验真)

#### 防伪要素
| 要素 | 位置 | 技术 |
|------|------|------|
| **防伪二维码** | PDF 页底右侧 | 包含报告编号+校验和, 扫码跳转到 https://lims.example.com/verify/{encoded_id} |
| **骑缝章** | 多页报告右侧 | PDF 合并后在右侧 1/4 处叠加骑缝章图片 |
| **CMA 章** | 首页左上角 | PNG 透明底图片叠加 |
| **在线验真页** | /verify/{id} | 显示报告基本信息(不显示完整数据), 验证编号有效性 |

#### 验真 API
```
GET /api/v1/public/verify/{report_encoded_id}
Response: {
    "report_no": "REP-2025-0042",
    "client_name": "杭州城市建设集团",
    "issue_date": "2025-06-18",
    "status": "issued",
    "integrity_hash": "sha256:a1b2c3d4...",
    "is_valid": true
}
```

### 附.11.18 自定义统计报表 (拖拽式构建器)

#### 组件库
| 组件 | 用途 | 配置项 |
|------|------|--------|
| 数字卡片 | 显示单个聚合值 | 聚合函数、筛选条件、颜色 |
| 柱状图 | 对比多维度数据 | X轴维度、Y轴聚合、分组 |
| 折线图 | 趋势分析 | X轴(时间)、Y轴、平滑曲线 |
| 饼图 | 占比分析 | 维度、排序 |
| 数据表格 | 明细展示 | 列选择、排序、分页 |

#### 报表定义结构
```json
{
    "name": "月度检测统计",
    "layout": [
        { "type": "card", "metric": "sample_count", "filter": {"month": "current"} },
        { "type": "card", "metric": "pass_rate", "filter": {"month": "current"} },
        { "type": "bar_chart", "x": "department", "y": "count", "group": "test_type" },
        { "type": "line_chart", "x": "date", "y": "daily_count", "range": "30d" },
        { "type": "data_table", "columns": ["order_no", "client", "status", "tat_days"] }
    ]
}
```

### 附.11.19 版本回滚 (Alembic 正逆向迁移)

#### 迁移脚本规范
每个正向迁移脚本必须包含 `upgrade()` 和 `downgrade()` 函数。

```python
def upgrade():
    op.create_table('test_parameters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(30), nullable=False),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_param_code', 'test_parameters', ['code'])

def downgrade():
    op.drop_index('idx_param_code', 'test_parameters')
    op.drop_table('test_parameters')
```

#### 回滚命令
```bash
# 正常升级
alembic upgrade head

# 失败时回滚到上一个版本
alembic downgrade -1

# 回滚到特定版本
alembic downgrade <revision_hash>
```

### 附.11.20 数据归档 (冷热分离+历史归档)

#### 归档策略
| 数据分类 | 保留期 | 存储方式 | 清理规则 |
|---------|--------|---------|---------|
| **热数据** (近2年) | 主表 | PostgreSQL 主表, SSD | — |
| **冷数据** (2-10年) | 归档表 | PostgreSQL _archive_YYYY 表, HDD | — |
| **审计日志** | 永久 | 压缩存储 (pg_archive) | 不可清理 |
| **MinIO 文件** | 10 年 | S3 Standard → S3 IA (5年后) | 到期自动清理 |

#### 归档 SQL (PostgreSQL Partition)
```sql
-- 按年分区
CREATE TABLE samples_archive_2023 PARTITION OF samples_archive
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
CREATE TABLE samples_archive_2024 PARTITION OF samples_archive
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- 每年1月自动执行归档
-- Celery Beat 定时任务: 每年1月1日 02:00
-- 将 2 年前数据从主表迁移到归档表
INSERT INTO samples_archive SELECT * FROM samples WHERE created_at < NOW() - INTERVAL '2 years';
DELETE FROM samples WHERE created_at < NOW() - INTERVAL '2 years';
```

### 附.11.21 异常检测数据标记 (自动标记+异常标识)

#### 异常检测规则
| 异常类型 | 检测逻辑 | 标记颜色 | 处理措施 |
|---------|---------|---------|---------|
| **超出量程** | raw_value > instrument.max_range 或 < min_range | 🔴 红 | 自动锁定，不可签发报告 |
| **超出范围** | raw_value < parameter.min_value 或 > max_value | 🟡 黄 | 弹窗确认，需记录原因 |
| **缺失数据** | required_param 为 NULL | 🟠 橙 | 不可提交记录 |
| **计算异常** | 公式计算结果 NaN/Inf | 🔴 红 | 标记无效，触发复测 |

#### 前端处理
```tsx
const DataCell = ({ value, isOutOfRange, isBeyondRange }) => {
    if (isBeyondRange) return (
        <Cell status="error">
            <Tag color="red">超出量程</Tag>
            <button onClick={triggerRetest}>触发复测</button>
        </Cell>
    );
    if (isOutOfRange) return (
        <Cell status="warning">
            <Tag color="orange">超出预期范围</Tag>
            <ConfirmModal title="是否确认此异常数据?" />
        </Cell>
    );
    return <Cell value={value} />;
};
```

---

# 第三部分: 数据库设计

# 数据库设计规格说明书

**项目名称：** 实验室信息管理系统（LIMS）  
**文档版本：** V1.0  
**数据库版本：** PostgreSQL 16  
**编制日期：** 2026-05-10

---

## 1. 概述

### 1.1数据库环境

| 项目 | 值 |
|---|---|
| DBMS | PostgreSQL 16.4 |
| 字符集 | UTF-8 |
| 排序规则 | zh_CN.UTF-8 |
| 时区 | Asia/Shanghai (UTC+8) |
| 最小版本要求 | 16.0 |
| 数据保留期 | 10年（自记录创建日起） |
| 审计模式 | PostgreSQL Trigger-based DML 审计 |
| 合规标准 | CMA / CNAS（RB/T 214-2017, ISO/IEC 17025:2017） |

### 1.2 数据库架构规划

系统按 Clean Architecture 模块拆分为以下 PostgreSQL Schema：

| Schema | 模块 | 说明 |
|---|---|---|
| `auth` | 用户与权限 | 用户、角色、权限、审计日志 |
| `commission` | 委托与收样 | 客户、委托单、样品 |
| `testing` | 检测任务 | 任务、方法、结果、附件 |
| `reporting` | 报告管理 | 报告模板、报告、签章 |
| `equipment` | 设备管理 | 设备档案、校准、维护、折旧 |
| `standards` | 标准方法库 | 标准、方法、变更追踪 |
| `workflow` | 工作流引擎 | 流程定义、实例、流转历史 |
| `billing` | 计费管理 | 价格表、发票、合同、折扣 |
| `quality` | 质量体系 | 不合格品、内审、能力验证、投诉 |
| `system` | 系统基础 | 配置、字典、通知、定时任务、文件 |
| `audit` | 审计基础 | 审计触发器函数、归档表 |

---

## 2. 数据库命名规范

### 2.1 Schema 命名

- 全部小写英文单词，下划线分隔，语义明确。

### 2.2 表命名

- 全部小写英文，复数形式，下划线分隔：`order_items`。
- 同 Schema 内表名全局唯一。

### 2.3 列命名

- 全部小写英文，下划线分隔：`created_at`。
- 主键统一使用 `id UUID PRIMARY KEY`。
- 外键列命名：`<关联表名单数形式>_id`，如 `client_id`。
- 布尔列以 `is_` 开头：`is_read`。
- 时间戳列统一为 `_at` 后缀：`created_at`、`updated_at`。

### 2.4 索引命名

- 主键：`<table>_pkey`（PostgreSQL 自动）。
- 唯一索引：`<table>_<column>_ukey`。
- 普通索引：`<table>_<column>_idx`。
- 复合索引：`<table>_<col1>_<col2>_idx`。

### 2.5 触发器命名

- 审计触发器：`<table>_audit_trg`。

### 2.6 约束命名

- 外键：`<table>_<column>_fkey`。
- 检查约束：`<table>_<column>_check`。
- 默认值约束：`<table>_<column>_default`。

---

## 3. ER 模型概述

### 3.1 核心实体关系（ASCII ER 图）

```
users ──1:N── user_roles ├──N:1── roles ──N:M── permissions
  │                       │
  │                       └──M:N── role_permissions
  │
  └──1:N── audit_log
  │
  └──1:N── orders (created_by)
             │
             ├──N:1── clients
             │
             └──1:N── order_items ──M:1── sample_types
                    │
                    └──N:M── test_methods
             │
             └──1:N── samples
                    │
                    └──1:N── test_tasks ──1:1── test_methods
                           │
                           ├──1:N── test_results
                           ├──1:N── test_task_attachments
                           └──1:N── test_task_logs

test_methods ──1:N── test_method_parameters

reports ──N:M── samples (sample_ids via ARRAY/JSONB)
  │
  ├──N:1── report_templates
  ├──1:N── report_review_logs
  ├──1:N── report_signatures ──N:1── users
  └──1:N── report_attachments

equipment ──1:N── equipment_calibrations
  ├──1:N── equipment_maintenance
  ├──1:N── equipment_usage_logs ──N:1── test_tasks
  ├──1:N── equipment_documents
  ├──1:N── equipment_alerts
  └──1:N── equipment_depreciation

standards ──1:N── standard_methods ──1:N── standard_method_parameters
  └──1:N── standard_changelog

workflow_definitions ──1:N── workflow_instances ──1:N── workflow_transitions
  ├──1:N── workflow_conditions
  └──1:N── workflow_history

clients ──1:N── contracts
  ├──1:N── invoices ──1:N── payment_records
  ├──1:N── billing_batches
  └──1:1── price_matrix

test_methods ──1:N── price_list

quality tables (nonconformities, internal_audits, proficiency_tests,
  complaints, management_reviews) reference users / samples

system: dictionaries (self-ref via parent_id)
        notifications (N:1 users)
        scheduled_jobs
        file_store
```

### 3.2 基数规则

- 所有外键强制 `ON DELETE RESTRICT` 防止级联误删。
- 软删除使用 `status` 列或 `deleted_at` 列（本规范优先 `status`）。
- 跨 Schema 引用通过全限定名 `schema.table` 实现。

---

## 4. 核心表详细设计

### 4.1 Category A — 用户与权限

#### 4.1.1 表：`auth.users`

**中文名：** 用户表  
**描述：** 存储系统用户账户信息，支持状态管理与锁定机制。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 用户唯一标识 |
| `username` | VARCHAR(64) | UNIQUE NOT NULL | — | 登录用户名 |
| `password_hash` | VARCHAR(255) | NOT NULL | — | bcrypt 哈希值 |
| `display_name` | VARCHAR(128) | NOT NULL | — | 显示名称 |
| `email` | VARCHAR(128) | UNIQUE | NULL | 邮箱地址 |
| `phone` | VARCHAR(20) | | NULL | 手机号码 |
| `role_id` | UUID | REFERENCES auth.roles(id) | NULL | 主角色（兼容旧版） |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('active','inactive','locked','suspended') | `'active'` | 账户状态 |
| `last_login` | TIMESTAMPTZ | | NULL | 最后登录时间 |
| `failed_attempts` | SMALLINT | NOT NULL | `0` | 连续登录失败次数 |
| `locked_until` | TIMESTAMPTZ | | NULL | 锁定截止时间 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 最后更新时间 |

**索引：**

| 索引名 | 类型 | 列 | 说明 |
|---|---|---|---|
| `users_pkey` | PRIMARY | `id` | 主键 |
| `users_username_ukey` | UNIQUE | `username` | 用户名唯一 |
| `users_email_ukey` | UNIQUE | `email` | 邮箱唯一 |
| `users_status_idx` | NORMAL | `status` | 按状态筛选 |
| `users_role_id_idx` | NORMAL | `role_id` | 按角色查询 |

**触发器：**

| 触发器名 | 事件 | 说明 |
|---|---|---|
| `users_audit_trg` | AFTER INSERT/UPDATE/DELETE | 记录操作到审计触发器日志 |

---

#### 4.1.2 表：`auth.roles`

**中文名：** 角色表  
**描述：** 系统角色定义，支持系统内置角色标记。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 角色ID |
| `name` | VARCHAR(64) | UNIQUE NOT NULL | — | 角色名称 |
| `code` | VARCHAR(32) | UNIQUE NOT NULL | — | 角色代码 |
| `description` | VARCHAR(256) | | NULL | 角色描述 |
| `is_system` | BOOLEAN | NOT NULL | `false` | 是否系统内置 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 创建时间 |

**索引：** `roles_pkey`, `roles_name_ukey`, `roles_code_ukey`  
**触发器：** `roles_audit_trg`

---

#### 4.1.3 表：`auth.permissions`

**中文名：** 权限表  
**描述：** 定义系统资源与操作权限。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 权限ID |
| `resource` | VARCHAR(64) | NOT NULL | — | 资源标识，如 `sample`、`report` |
| `action` | VARCHAR(32) | NOT NULL | — | 操作类型：`create`、`read`、`update`、`delete`、`approve` |
| `description` | VARCHAR(256) | | NULL | 权限描述 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 创建时间 |

**索引：** `permissions_pkey`, `permissions_resource_action_ukey (resource, action)`  
**触发器：** `permissions_audit_trg`

---

#### 4.1.4 表：`auth.role_permissions`

**中文名：** 角色权限关联表  
**描述：** 角色与权限的多对多映射。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `role_id` | UUID | PRIMARY KEY, REFERENCES auth.roles(id) | — | 角色ID |
| `permission_id` | UUID | PRIMARY KEY, REFERENCES auth.permissions(id) | — | 权限ID |

**索引：** `role_permissions_pkey (role_id, permission_id)`, `role_permissions_permission_id_idx (permission_id)`  
**触发器：** `role_permissions_audit_trg`

---

#### 4.1.5 表：`auth.user_roles`

**中文名：** 用户角色关联表  
**描述：** 用户与角色的多对多映射，支持授权人与过期时间。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `user_id` | UUID | PRIMARY KEY, REFERENCES auth.users(id) | — | 用户ID |
| `role_id` | UUID | PRIMARY KEY, REFERENCES auth.roles(id) | — | 角色ID |
| `granted_by` | UUID | REFERENCES auth.users(id) | NULL | 授权人 |
| `granted_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 授权时间 |
| `expires_at` | TIMESTAMPTZ | | NULL | 授权过期时间 |

**索引：** `user_roles_pkey (user_id, role_id)`, `user_roles_role_id_idx (role_id)`  
**触发器：** `user_roles_audit_trg`

---

#### 4.1.6 表：`audit.audit_log`

**中文名：** 审计日志表（由触发器填充）  
**描述：** 记录系统中所有关键数据变更操作，满足 CMA/CNAS 审计追踪要求。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | `nextval(...)` | 日志自增ID |
| `user_id` | UUID | REFERENCES auth.users(id) | NULL | 操作用户ID（NULL表示系统操作） |
| `action` | VARCHAR(16) | NOT NULL CHECK IN ('INSERT','UPDATE','DELETE') | — | DML操作类型 |
| `resource` | VARCHAR(64) | NOT NULL | — | 资源标识，格式 `schema.table` |
| `resource_id` | VARCHAR(128) | | NULL | 被操作记录的ID |
| `old_value` | JSONB | | NULL | 修改前数据快照 |
| `new_value` | JSONB | | NULL | 修改后数据快照 |
| `ip_address` | INET | | NULL | 客户端IP地址 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 操作时间 |

**索引：**

| 索引名 | 类型 | 列 | 说明 |
|---|---|---|---|
| `audit_log_pkey` | PRIMARY | `id` | 主键 |
| `audit_log_user_id_idx` | NORMAL | `user_id` | 按用户查询 |
| `audit_log_resource_idx` | NORMAL | `resource` | 按资源筛选 |
| `audit_log_resource_id_idx` | NORMAL | `resource_id` | 按记录ID查询 |
| `audit_log_created_at_idx` | NORMAL | `created_at` | 按时间范围查询 |
| `audit_log_resource_created_at_idx` | NORMAL | `resource, created_at` | 复合查询 |

**触发器：** 此表由全局审计触发函数自动写入，不附加触发器。

---

### 4.2 Category B — 委托与收样

#### 4.2.1 表：`commission.clients`

**中文名：** 客户表  
**描述：** 委托客户档案管理，支持信用等级与折扣管理。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 客户ID |
| `name` | VARCHAR(128) | NOT NULL | — | 客户名称 |
| `code` | VARCHAR(32) | UNIQUE NOT NULL | — | 客户编码 |
| `contact_person` | VARCHAR(64) | | NULL | 联系人 |
| `phone` | VARCHAR(20) | | NULL | 联系电话 |
| `email` | VARCHAR(128) | | NULL | 邮箱 |
| `address` | VARCHAR(512) | | NULL | 通讯地址 |
| `credit_level` | VARCHAR(10) | CHECK IN ('A','B','C','D') | `'B'` | 信用等级 |
| `discount_rate` | NUMERIC(5,2) | NOT NULL CHECK >= 0 AND <= 100 | `0` | 折扣率(%) |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('active','inactive','blacklisted') | `'active'` | 状态 |

**索引：** `clients_pkey`, `clients_code_ukey`, `clients_name_idx`, `clients_status_idx`  
**触发器：** `clients_audit_trg`

---

#### 4.2.2 表：`commission.sample_types`

**中文名：** 样品类型表  
**描述：** 样品分类字典。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 类型ID |
| `name` | VARCHAR(64) | NOT NULL | — | 类型名称 |
| `code` | VARCHAR(32) | UNIQUE NOT NULL | — | 类型代码 |
| `category` | VARCHAR(32) | | NULL | 大类 |
| `description` | TEXT | | NULL | 描述 |

**索引：** `sample_types_pkey`, `sample_types_code_ukey`, `sample_types_category_idx`  
**触发器：** `sample_types_audit_trg`

---

#### 4.2.3 表：`commission.orders`

**中文名：** 委托单表  
**描述：** 检测委托单主表，记录委托基本信息与状态。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 委托单ID |
| `order_no` | VARCHAR(32) | UNIQUE NOT NULL | — | 委托单号 |
| `client_id` | UUID | NOT NULL REFERENCES commission.clients(id) | — | 客户ID |
| `project_name` | VARCHAR(256) | | NULL | 项目名称 |
| `contact_person` | VARCHAR(64) | | NULL | 联系人 |
| `phone` | VARCHAR(20) | | NULL | 联系电话 |
| `address` | VARCHAR(512) | | NULL | 送检地址 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('draft','submitted','received','testing','reporting','completed','cancelled') | `'draft'` | 委托状态 |
| `total_price` | NUMERIC(12,2) | NOT NULL DEFAULT 0 | `0` | 委托总价 |
| `created_by` | UUID | NOT NULL REFERENCES auth.users(id) | — | 创建人 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 更新时间 |

**索引：**

| 索引名 | 类型 | 列 | 说明 |
|---|---|---|---|
| `orders_pkey` | PRIMARY | `id` | 主键 |
| `orders_order_no_ukey` | UNIQUE | `order_no` | 单号唯一 |
| `orders_client_id_idx` | NORMAL | `client_id` | 按客户查询 |
| `orders_status_idx` | NORMAL | `status` | 按状态筛选 |
| `orders_created_at_idx` | NORMAL | `created_at` | 按创建时间排序 |
| `orders_created_by_idx` | NORMAL | `created_by` | 按创建人筛选 |

**触发器：** `orders_audit_trg`

---

#### 4.2.4 表：`commission.order_items`

**中文名：** 委托明细表  
**描述：** 委托单中的检测项目明细。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 明细ID |
| `order_id` | UUID | NOT NULL REFERENCES commission.orders(id) | — | 委托单ID |
| `sample_type_id` | UUID | NOT NULL REFERENCES commission.sample_types(id) | — | 样品类型ID |
| `test_method_ids` | UUID[] | NOT NULL | `'{}'` | 检测方法ID数组 |
| `quantity` | INTEGER | NOT NULL CHECK > 0 | — | 数量 |
| `unit_price` | NUMERIC(10,2) | NOT NULL | — | 单价 |
| `subtotal` | NUMERIC(12,2) | NOT NULL | — | 小计金额 |

**索引：** `order_items_pkey`, `order_items_order_id_idx`  
**触发器：** `order_items_audit_trg`

---

#### 4.2.5 表：`commission.samples`

**中文名：** 样品表  
**描述：** 委托样品登记信息，支持条码管理。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 样品ID |
| `sample_no` | VARCHAR(32) | UNIQUE NOT NULL | — | 样品编号 |
| `barcode` | VARCHAR(64) | UNIQUE | NULL | 条码 |
| `order_id` | UUID | NOT NULL REFERENCES commission.orders(id) | — | 所属委托单 |
| `name` | VARCHAR(128) | NOT NULL | — | 样品名称 |
| `specification` | VARCHAR(256) | | NULL | 规格型号 |
| `quantity` | NUMERIC(10,2) | NOT NULL | — | 样品数量 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('received','in_testing','tested','returned','disposed','retained') | `'received'` | 样品状态 |
| `received_by` | UUID | REFERENCES auth.users(id) | NULL | 收样人 |
| `received_at` | TIMESTAMPTZ | | NULL | 收样时间 |
| `location` | VARCHAR(128) | | NULL | 存放位置 |
| `expiry_date` | DATE | | NULL | 到期日期 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 创建时间 |

**索引：** `samples_pkey`, `samples_sample_no_ukey`, `samples_barcode_ukey`, `samples_order_id_idx`, `samples_status_idx`, `samples_expiry_date_idx`  
**触发器：** `samples_audit_trg`

---

### 4.3 Category C — 检测任务

#### 4.3.1 表：`testing.test_methods`

**中文名：** 检测方法表  
**描述：** 检测方法库，含参数模板与计费代码。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 方法ID |
| `code` | VARCHAR(32) | UNIQUE NOT NULL | — | 方法代码 |
| `name` | VARCHAR(128) | NOT NULL | — | 方法名称 |
| `standard_id` | UUID | REFERENCES standards.standards(id) | NULL | 关联标准 |
| `category` | VARCHAR(32) | | NULL | 方法分类 |
| `description` | TEXT | | NULL | 方法描述 |
| `form_component` | VARCHAR(64) | | NULL | 前端表单组件标识 |
| `parameters` | JSONB | NOT NULL DEFAULT `'[]'::jsonb | `'[]'::jsonb` | 参数定义JSON模板 |
| `pricing_code` | VARCHAR(32) | | NULL | 计费代码 |

**索引：** `test_methods_pkey`, `test_methods_code_ukey`, `test_methods_category_idx`, `test_methods_standard_id_idx`  
**触发器：** `test_methods_audit_trg`

---

#### 4.3.2 表：`testing.test_method_parameters`

**中文名：** 检测方法参数表  
**描述：** 每个检测方法的参数定义，支持范围校验与舍入规则。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 参数ID |
| `method_id` | UUID | NOT NULL REFERENCES testing.test_methods(id) | — | 方法ID |
| `param_name` | VARCHAR(64) | NOT NULL | — | 参数名称 |
| `param_code` | VARCHAR(32) | NOT NULL | — | 参数代码 |
| `unit` | VARCHAR(20) | | NULL | 单位 |
| `data_type` | VARCHAR(16) | NOT NULL CHECK IN ('string','number','boolean','date') | — | 数据类型 |
| `decimal_places` | SMALLINT | | NULL | 小数位数 |
| `rounding_rule` | VARCHAR(16) | CHECK IN ('round_half_up','round_half_even','round_up','round_down','truncate') | `'round_half_up'` | 舍入规则 |
| `formula` | TEXT | | NULL | 计算公式 |
| `min_value` | NUMERIC(18,6) | | NULL | 最小允许值 |
| `max_value` | NUMERIC(18,6) | | NULL | 最大允许值 |
| `is_required` | BOOLEAN | NOT NULL DEFAULT true | `true` | 是否必填 |

**索引：** `test_method_parameters_pkey`, `test_method_parameters_method_id_idx`, `test_method_parameters_method_code_idx (method_id, param_code)`  
**触发器：** `test_method_parameters_audit_trg`

---

#### 4.3.3 表：`testing.test_tasks`

**中文名：** 检测任务表  
**描述：** 样品检测任务单，分配给检测人员并跟踪进度。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 任务ID |
| `task_no` | VARCHAR(32) | UNIQUE NOT NULL | — | 任务编号 |
| `sample_id` | UUID | NOT NULL REFERENCES commission.samples(id) | — | 样品ID |
| `test_method_id` | UUID | NOT NULL REFERENCES testing.test_methods(id) | — | 检测方法ID |
| `assigned_to` | UUID | REFERENCES auth.users(id) | NULL | 分配检测人 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('pending','assigned','in_progress','completed','cancelled','rework') | `'pending'` | 任务状态 |
| `priority` | VARCHAR(10) | NOT NULL CHECK IN ('low','normal','high','urgent') | `'normal'` | 优先级 |
| `started_at` | TIMESTAMPTZ | | NULL | 开始时间 |
| `completed_at` | TIMESTAMPTZ | | NULL | 完成时间 |
| `deadline` | TIMESTAMPTZ | | NULL | 截止时间 |

**索引：**

| 索引名 | 类型 | 列 | 说明 |
|---|---|---|---|
| `test_tasks_pkey` | PRIMARY | `id` | 主键 |
| `test_tasks_task_no_ukey` | UNIQUE | `task_no` | 任务编号唯一 |
| `test_tasks_sample_id_idx` | NORMAL | `sample_id` | 按样品查询 |
| `test_tasks_method_id_idx` | NORMAL | `test_method_id` | 按方法筛选 |
| `test_tasks_assigned_to_idx` | NORMAL | `assigned_to` | 按检测人筛选 |
| `test_tasks_status_idx` | NORMAL | `status` | 按状态过滤 |
| `test_tasks_deadline_idx` | NORMAL | `deadline` | 截止排序 |
| `test_tasks_priority_idx` | NORMAL | `priority` | 按优先级 |

**触发器：** `test_tasks_audit_trg`

---

#### 4.3.4 表：`testing.test_results`

**中文名：** 检测结果表  
**描述：** 检测任务参数的原始数据与判定结果。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 结果ID |
| `task_id` | UUID | NOT NULL REFERENCES testing.test_tasks(id) | — | 任务ID |
| `parameter_code` | VARCHAR(32) | NOT NULL | — | 参数代码 |
| `raw_value` | VARCHAR(256) | | NULL | 原始检测值 |
| `rounded_value` | NUMERIC(18,6) | | NULL | 修约后值 |
| `unit` | VARCHAR(20) | | NULL | 单位 |
| `standard_value` | VARCHAR(256) | | NULL | 标准限值 |
| `judgment` | VARCHAR(16) | CHECK IN ('pass','fail','unsure','not_tested') | NULL | 判定结果 |
| `recorded_by` | UUID | NOT NULL REFERENCES auth.users(id) | — | 记录人 |
| `recorded_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 记录时间 |

**索引：** `test_results_pkey`, `test_results_task_id_idx`, `test_results_task_param_idx (task_id, parameter_code)`, `test_results_recorded_by_idx`  
**触发器：** `test_results_audit_trg`

---

#### 4.3.5 表：`testing.test_task_attachments`

**中文名：** 检测任务附件表  
**描述：** 检测任务相关的附件文件记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 附件ID |
| `task_id` | UUID | NOT NULL REFERENCES testing.test_tasks(id) | — | 任务ID |
| `file_id` | UUID | NOT NULL REFERENCES system.file_store(id) | — | 文件ID |
| `description` | VARCHAR(256) | | NULL | 附件说明 |
| `uploaded_by` | UUID | NOT NULL REFERENCES auth.users(id) | — | 上传人 |
| `uploaded_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 上传时间 |

**索引：** `test_task_attachments_pkey`, `test_task_attachments_task_id_idx`  
**触发器：** `test_task_attachments_audit_trg`

---

#### 4.3.6 表：`testing.test_task_logs`

**中文名：** 检测任务日志表  
**描述：** 检测任务操作流水日志。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | `nextval(...)` | 日志ID |
| `task_id` | UUID | NOT NULL REFERENCES testing.test_tasks(id) | — | 任务ID |
| `action` | VARCHAR(32) | NOT NULL | — | 操作类型 |
| `operator` | UUID | NOT NULL REFERENCES auth.users(id) | — | 操作人 |
| `notes` | TEXT | | NULL | 操作备注 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 操作时间 |

**索引：** `test_task_logs_pkey`, `test_task_logs_task_id_idx`, `test_task_logs_created_at_idx`  
**触发器：** `test_task_logs_audit_trg`

---

### 4.4 Category D — 报告管理

#### 4.4.1 表：`reporting.report_templates`

**中文名：** 报告模板表  
**描述：** 检测报告模板定义，含CMA/CNAS标识配置。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 模板ID |
| `name` | VARCHAR(128) | NOT NULL | — | 模板名称 |
| `code` | VARCHAR(32) | UNIQUE NOT NULL | — | 模板代码 |
| `html_template_path` | VARCHAR(512) | NOT NULL | — | HTML模板路径 |
| `css_path` | VARCHAR(512) | | NULL | CSS样式路径 |
| `cma_seal` | UUID | | NULL | CMA标识图文件ID |
| `cnas_seal` | UUID | | NULL | CNAS标识图文件ID |
| `is_default` | BOOLEAN | NOT NULL DEFAULT false | `false` | 是否默认模板 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 创建时间 |

**索引：** `report_templates_pkey`, `report_templates_code_ukey`  
**触发器：** `report_templates_audit_trg`

---

#### 4.4.2 表：`reporting.reports`

**中文名：** 检测报告表  
**描述：** 检测报告主表，记录报告完整生命周期与版本信息。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 报告ID |
| `report_no` | VARCHAR(32) | UNIQUE NOT NULL | — | 报告编号 |
| `sample_ids` | UUID[] | NOT NULL | `'{}'` | 关联样品ID数组 |
| `template_id` | UUID | NOT NULL REFERENCES reporting.report_templates(id) | — | 使用模板ID |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('draft','generating','pending_review','reviewing','review_failed','pending_approval','approved','issued','rejected','cancelled') | `'draft'` | 报告状态 |
| `generated_at` | TIMESTAMPTZ | | NULL | 生成时间 |
| `reviewed_by` | UUID | REFERENCES auth.users(id) | NULL | 审核人 |
| `reviewed_at` | TIMESTAMPTZ | | NULL | 审核时间 |
| `approved_by` | UUID | REFERENCES auth.users(id) | NULL | 批准人 |
| `approved_at` | TIMESTAMPTZ | | NULL | 批准时间 |
| `issued_by` | UUID | REFERENCES auth.users(id) | NULL | 发放人 |
| `issued_at` | TIMESTAMPTZ | | NULL | 发放时间 |
| `cma_chapter` | VARCHAR(16) | | NULL | CMA章编号 |
| `cnas_chapter` | VARCHAR(16) | | NULL | CNAS章编号 |
| `version` | SMALLINT | NOT NULL DEFAULT 1 | `1` | 版本号 |

**索引：** `reports_pkey`, `reports_report_no_ukey`, `reports_status_idx`, `reports_reviewed_by_idx`, `reports_approved_by_idx`, `reports_issued_at_idx`, `reports_created_at_idx`  
**触发器：** `reports_audit_trg`

---

#### 4.4.3 表：`reporting.report_review_logs`

**中文名：** 报告审核日志表  
**描述：** 报告审核流程操作记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | `nextval(...)` | 日志ID |
| `report_id` | UUID | NOT NULL REFERENCES reporting.reports(id) | — | 报告ID |
| `reviewer_id` | UUID | NOT NULL REFERENCES auth.users(id) | — | 审核人 |
| `action` | VARCHAR(20) | NOT NULL CHECK IN ('submit_review','approve','reject','return') | — | 审核操作 |
| `comments` | TEXT | | NULL | 审核意见 |
| `reviewed_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 审核时间 |

**索引：** `report_review_logs_pkey`, `report_review_logs_report_id_idx`  
**触发器：** `report_review_logs_audit_trg`

---

#### 4.4.4 表：`reporting.report_signatures`

**中文名：** 报告签章表  
**描述：** 报告电子签章记录，满足法规要求的签署追溯。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 签章ID |
| `report_id` | UUID | NOT NULL REFERENCES reporting.reports(id) | — | 报告ID |
| `signer_id` | UUID | NOT NULL REFERENCES auth.users(id) | — | 签署人 |
| `role` | VARCHAR(20) | NOT NULL CHECK IN ('tester','reviewer','approver','authorizer') | — | 签署角色 |
| `signature_type` | VARCHAR(20) | NOT NULL CHECK IN ('electronic','wet','seal') | `'electronic'` | 签章类型 |
| `signed_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 签署时间 |
| `ip_address` | INET | | NULL | 签署时IP |

**索引：** `report_signatures_pkey`, `report_signatures_report_id_idx`, `report_signatures_signer_id_idx`  
**触发器：** `report_signatures_audit_trg`

---

#### 4.4.5 表：`reporting.report_attachments`

**中文名：** 报告附件表  
**描述：** 报告附带的附加文件记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 附件ID |
| `report_id` | UUID | NOT NULL REFERENCES reporting.reports(id) | — | 报告ID |
| `file_id` | UUID | NOT NULL REFERENCES system.file_store(id) | — | 文件ID |
| `type` | VARCHAR(20) | NOT NULL CHECK IN ('appendix','photo','certificate','other') | — | 附件类型 |
| `description` | VARCHAR(256) | | NULL | 附件说明 |

**索引：** `report_attachments_pkey`, `report_attachments_report_id_idx`  
**触发器：** `report_attachments_audit_trg`

---

### 4.5 Category E — 设备管理

#### 4.5.1 表：`equipment.equipment`

**中文名：** 设备档案表  
**描述：** 检测设备全生命周期管理的基础档案。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 设备ID |
| `code` | VARCHAR(32) | UNIQUE NOT NULL | — | 设备编号 |
| `name` | VARCHAR(128) | NOT NULL | — | 设备名称 |
| `qr_code` | VARCHAR(128) | UNIQUE | NULL | 二维码标识 |
| `model` | VARCHAR(128) | | NULL | 型号规格 |
| `serial_no` | VARCHAR(64) | | NULL | 序列号 |
| `manufacturer` | VARCHAR(128) | | NULL | 生产厂家 |
| `category` | VARCHAR(32) | | NULL | 设备分类 |
| `purchase_date` | DATE | | NULL | 购置日期 |
| `price` | NUMERIC(12,2) | | NULL | 购置价格 |
| `warranty_date` | DATE | | NULL | 保修到期日 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('idle','in_use','calibrating','maintenance','out_of_service','retired') | `'idle'` | 设备状态 |
| `location` | VARCHAR(128) | | NULL | 存放位置 |
| `custodian` | UUID | REFERENCES auth.users(id) | NULL | 保管人 |

**索引：** `equipment_pkey`, `equipment_code_ukey`, `equipment_qr_code_ukey`, `equipment_category_idx`, `equipment_status_idx`  
**触发器：** `equipment_audit_trg`

---

#### 4.5.2 表：`equipment.equipment_calibrations`

**中文名：** 设备校准表  
**描述：** 设备校准/检定记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 校准ID |
| `equipment_id` | UUID | NOT NULL REFERENCES equipment.equipment(id) | — | 设备ID |
| `calibration_date` | DATE | NOT NULL | — | 校准日期 |
| `next_calibration_date` | DATE | NOT NULL | — | 下次校准日期 |
| `calibration_org` | VARCHAR(128) | | NULL | 校准机构 |
| `certificate_no` | VARCHAR(64) | | NULL | 证书编号 |
| `result` | VARCHAR(32) | NOT NULL CHECK IN ('pass','fail','conditional') | — | 校准结果 |
| `status` | VARCHAR(20) | NOT NULL DEFAULT `'current'` CHECK IN ('current','expired','pending') | `'current'` | 记录状态 |
| `notes` | TEXT | | NULL | 备注 |

**索引：** `equipment_calibrations_pkey`, `equipment_calibrations_equipment_id_idx`, `equipment_calibrations_next_date_idx`  
**触发器：** `equipment_calibrations_audit_trg`

---

#### 4.5.3 表：`equipment.equipment_maintenance`

**中文名：** 设备维护表  
**描述：** 设备维修保养记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 维护ID |
| `equipment_id` | UUID | NOT NULL REFERENCES equipment.equipment(id) | — | 设备ID |
| `type` | VARCHAR(32) | NOT NULL CHECK IN ('routine','repair','upgrade','inspection') | — | 维护类型 |
| `date` | DATE | NOT NULL | — | 维护日期 |
| `description` | TEXT | NOT NULL | — | 维护说明 |
| `performer` | UUID | REFERENCES auth.users(id) | NULL | 执行人 |
| `cost` | NUMERIC(10,2) | | NULL | 费用 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('completed','in_progress','cancelled') | `'completed'` | 状态 |

**索引：** `equipment_maintenance_pkey`, `equipment_maintenance_equipment_id_idx`, `equipment_maintenance_date_idx`  
**触发器：** `equipment_maintenance_audit_trg`

---

#### 4.5.4 表：`equipment.equipment_usage_logs`

**中文名：** 设备使用记录表  
**描述：** 设备每次使用的时间段与操作人记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | `nextval(...)` | 记录ID |
| `equipment_id` | UUID | NOT NULL REFERENCES equipment.equipment(id) | — | 设备ID |
| `task_id` | UUID | | NULL | 关联检测任务ID |
| `started_at` | TIMESTAMPTZ | NOT NULL | — | 开始时间 |
| `ended_at` | TIMESTAMPTZ | | NULL | 结束时间 |
| `operator` | UUID | NOT NULL REFERENCES auth.users(id) | — | 操作人 |
| `hours_used` | NUMERIC(6,2) | | NULL | 使用时长(小时) |

**索引：** `equipment_usage_logs_pkey`, `equipment_usage_logs_equipment_id_idx`, `equipment_usage_logs_operator_idx`  
**触发器：** `equipment_usage_logs_audit_trg`

---

#### 4.5.5 表：`equipment.equipment_documents`

**中文名：** 设备文档表  
**描述：** 设备相关文档与资料附件索引。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 文档ID |
| `equipment_id` | UUID | NOT NULL REFERENCES equipment.equipment(id) | — | 设备ID |
| `doc_type` | VARCHAR(32) | NOT NULL CHECK IN ('manual','certificate','calibration_report','maintenance_log','warranty','other') | — | 文档类型 |
| `file_id` | UUID | NOT NULL REFERENCES system.file_store(id) | — | 文件ID |
| `description` | VARCHAR(256) | | NULL | 说明 |

**索引：** `equipment_documents_pkey`, `equipment_documents_equipment_id_idx`  
**触发器：** `equipment_documents_audit_trg`

---

#### 4.5.6 表：`equipment.equipment_alerts`

**中文名：** 设备告警表  
**描述：** 设备校准到期、维护提醒等告警记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | `nextval(...)` | 告警ID |
| `equipment_id` | UUID | NOT NULL REFERENCES equipment.equipment(id) | — | 设备ID |
| `alert_type` | VARCHAR(32) | NOT NULL CHECK IN ('calibration_due','maintenance_due','warranty_expire','status_change') | — | 告警类型 |
| `message` | VARCHAR(512) | NOT NULL | — | 告警内容 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('active','acknowledged','resolved','dismissed') | `'active'` | 告警状态 |
| `acknowledged_by` | UUID | REFERENCES auth.users(id) | NULL | 确认人 |
| `acknowledged_at` | TIMESTAMPTZ | | NULL | 确认时间 |

**索引：** `equipment_alerts_pkey`, `equipment_alerts_equipment_id_idx`, `equipment_alerts_status_idx`  
**触发器：** `equipment_alerts_audit_trg`

---

#### 4.5.7 表：`equipment.equipment_depreciation`

**中文名：** 设备折旧表  
**描述：** 设备年度折旧价值记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 折旧ID |
| `equipment_id` | UUID | NOT NULL REFERENCES equipment.equipment(id) | — | 设备ID |
| `year` | SMALLINT | NOT NULL | — | 折旧年份 |
| `value` | NUMERIC(12,2) | NOT NULL | — | 年末净值 |
| `method` | VARCHAR(20) | CHECK IN ('straight_line','double_declining','sum_of_years') | `'straight_line'` | 折旧方法 |

**索引：** `equipment_depreciation_pkey`, `equipment_depreciation_equipment_year_ukey (equipment_id, year)`  
**触发器：** `equipment_depreciation_audit_trg`

---

### 4.6 Category F — 标准方法库

#### 4.6.1 表：`standards.standards`

**中文名：** 标准表  
**描述：** 国家/行业/国际标准档案管理。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 标准ID |
| `code` | VARCHAR(32) | UNIQUE NOT NULL | — | 标准编号 |
| `name` | VARCHAR(256) | NOT NULL | — | 标准名称 |
| `category` | VARCHAR(32) | CHECK IN ('national','industry','local','international','enterprise') | — | 标准类别 |
| `level` | VARCHAR(10) | CHECK IN ('mandatory','recommended') | — | 标准级别 |
| `version` | VARCHAR(16) | | NULL | 版本号 |
| `effective_date` | DATE | | NULL | 实施日期 |
| `replaced_by` | UUID | REFERENCES standards.standards(id) | NULL | 替代标准ID |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('active','replaced','withdrawn','draft') | `'active'` | 状态 |

**索引：** `standards_pkey`, `standards_code_ukey`, `standards_category_idx`, `standards_status_idx`  
**触发器：** `standards_audit_trg`

---

#### 4.6.2 表：`standards.standard_methods`

**中文名：** 标准方法表  
**描述：** 标准中规定的检测方法条目。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 方法ID |
| `standard_id` | UUID | NOT NULL REFERENCES standards.standards(id) | — | 标准ID |
| `method_name` | VARCHAR(128) | NOT NULL | — | 方法名称 |
| `scope` | TEXT | | NULL | 适用范围 |
| `principle` | TEXT | | NULL | 检测原理 |
| `equipment_required` | TEXT | | NULL | 所需设备 |
| `notes` | TEXT | | NULL | 备注 |

**索引：** `standard_methods_pkey`, `standard_methods_standard_id_idx`  
**触发器：** `standard_methods_audit_trg`

---

#### 4.6.3 表：`standards.standard_method_parameters`

**中文名：** 标准方法参数表  
**描述：** 标准方法中规定的参数限值与修约要求。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 参数ID |
| `method_id` | UUID | NOT NULL REFERENCES standards.standard_methods(id) | — | 方法ID |
| `param_name` | VARCHAR(64) | NOT NULL | — | 参数名称 |
| `param_code` | VARCHAR(32) | NOT NULL | — | 参数代码 |
| `unit` | VARCHAR(20) | | NULL | 单位 |
| `limit_value` | NUMERIC(18,6) | | NULL | 限值 |
| `limit_operator` | VARCHAR(10) | CHECK IN ('<=','>=','<','>','between','exact') | NULL | 限值运算符 |
| `rounding` | VARCHAR(20) | | NULL | 修约规则 |

**索引：** `standard_method_parameters_pkey`, `standard_method_parameters_method_id_idx`  
**触发器：** `standard_method_parameters_audit_trg`

---

#### 4.6.4 表：`standards.standard_changelog`

**中文名：** 标准变更日志表  
**描述：** 标准状态变更与版本更新历史记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | `nextval(...)` | 日志ID |
| `standard_id` | UUID | NOT NULL REFERENCES standards.standards(id) | — | 标准ID |
| `change_type` | VARCHAR(20) | NOT NULL CHECK IN ('created','updated','version_changed','replaced','withdrawn') | — | 变更类型 |
| `description` | TEXT | NOT NULL | — | 变更描述 |
| `changed_by` | UUID | NOT NULL REFERENCES auth.users(id) | — | 变更人 |
| `changed_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 变更时间 |

**索引：** `standard_changelog_pkey`, `standard_changelog_standard_id_idx`  
**触发器：** `standard_changelog_audit_trg`

---

### 4.7 Category G — 工作流引擎

#### 4.7.1 表：`workflow.workflow_definitions`

**中文名：** 工作流定义表  
**描述：** 可配置工作流的状态与转移规则定义。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 流程ID |
| `name` | VARCHAR(128) | NOT NULL | — | 流程名称 |
| `code` | VARCHAR(32) | UNIQUE NOT NULL | — | 流程代码 |
| `entity_type` | VARCHAR(64) | NOT NULL | — | 关联实体类型，如 `report` |
| `states_json` | JSONB | NOT NULL | — | 状态定义JSON |
| `transitions_json` | JSONB | NOT NULL | — | 转移规则JSON |
| `version` | SMALLINT | NOT NULL DEFAULT 1 | `1` | 版本号 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('active','inactive','deprecated') | `'active'` | 启用状态 |

**索引：** `workflow_definitions_pkey`, `workflow_definitions_code_ukey`, `workflow_definitions_entity_type_idx`  
**触发器：** `workflow_definitions_audit_trg`

---

#### 4.7.2 表：`workflow.workflow_instances`

**中文名：** 工作流实例表  
**描述：** 工作流的运行时实例。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 实例ID |
| `definition_id` | UUID | NOT NULL REFERENCES workflow.workflow_definitions(id) | — | 定义ID |
| `entity_type` | VARCHAR(64) | NOT NULL | — | 关联实体类型 |
| `entity_id` | UUID | NOT NULL | — | 关联实体记录ID |
| `current_state` | VARCHAR(64) | NOT NULL | — | 当前状态 |
| `started_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 启动时间 |
| `completed_at` | TIMESTAMPTZ | | NULL | 完成时间 |

**索引：** `workflow_instances_pkey`, `workflow_instances_definition_id_idx`, `workflow_instances_entity_id_idx`  
**触发器：** `workflow_instances_audit_trg`

---

#### 4.7.3 表：`workflow.workflow_transitions`

**中文名：** 工作流转移记录表  
**描述：** 工作流实例中每次状态转移的详细记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | `nextval(...)` | 记录ID |
| `instance_id` | UUID | NOT NULL REFERENCES workflow.workflow_instances(id) | — | 实例ID |
| `from_state` | VARCHAR(64) | NOT NULL | — | 源状态 |
| `to_state` | VARCHAR(64) | NOT NULL | — | 目标状态 |
| `transition_name` | VARCHAR(64) | NOT NULL | — | 转移名称 |
| `operator` | UUID | NOT NULL REFERENCES auth.users(id) | — | 操作人 |
| `comments` | TEXT | | NULL | 备注 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 操作时间 |

**索引：** `workflow_transitions_pkey`, `workflow_transitions_instance_id_idx`  
**触发器：** `workflow_transitions_audit_trg`

---

#### 4.7.4 表：`workflow.workflow_conditions`

**中文名：** 工作流条件表  
**描述：** 流程中特定转移的前置条件定义。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 条件ID |
| `definition_id` | UUID | NOT NULL REFERENCES workflow.workflow_definitions(id) | — | 定义ID |
| `condition_name` | VARCHAR(64) | NOT NULL | — | 条件名称 |
| `condition_expression_json` | JSONB | NOT NULL | — | 条件表达式JSON |
| `target_state` | VARCHAR(64) | NOT NULL | — | 目标状态 |

**索引：** `workflow_conditions_pkey`, `workflow_conditions_definition_id_idx`  
**触发器：** `workflow_conditions_audit_trg`

---

#### 4.7.5 表：`workflow.workflow_history`

**中文名：** 工作流历史表  
**描述：** 工作流实例的所有操作历史记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | BIGSERIAL | PRIMARY KEY | `nextval(...)` | 历史ID |
| `instance_id` | UUID | NOT NULL REFERENCES workflow.workflow_instances(id) | — | 实例ID |
| `action` | VARCHAR(64) | NOT NULL | — | 操作类型 |
| `operator` | UUID | NOT NULL REFERENCES auth.users(id) | — | 操作人 |
| `notes` | TEXT | | NULL | 备注 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 时间 |

**索引：** `workflow_history_pkey`, `workflow_history_instance_id_idx`, `workflow_history_created_at_idx`  
**触发器：** `workflow_history_audit_trg`

---

### 4.8 Category H — 计费管理

#### 4.8.1 表：`billing.price_list`

**中文名：** 价格表  
**描述：** 检测方法标准价格目录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 价格ID |
| `test_method_id` | UUID | NOT NULL REFERENCES testing.test_methods(id) | — | 方法ID |
| `base_price` | NUMERIC(10,2) | NOT NULL | — | 基础价格 |
| `unit` | VARCHAR(20) | NOT NULL | — | 计价单位 |
| `category` | VARCHAR(32) | | NULL | 分类 |
| `effective_date` | DATE | NOT NULL | — | 生效日期 |
| `expiry_date` | DATE | | NULL | 失效日期 |

**索引：** `price_list_pkey`, `price_list_test_method_id_idx`, `price_list_effective_date_idx`  
**触发器：** `price_list_audit_trg`

---

#### 4.8.2 表：`billing.price_matrix`

**中文名：** 价格矩阵表  
**描述：** 按客户与数量梯度的差异化折扣价格。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 矩阵ID |
| `client_id` | UUID | NOT NULL REFERENCES commission.clients(id) | — | 客户ID |
| `method_id` | UUID | NOT NULL REFERENCES testing.test_methods(id) | — | 方法ID |
| `min_quantity` | INTEGER | NOT NULL | — | 最小数量 |
| `max_quantity` | INTEGER | | NULL | 最大数量 |
| `discount_rate` | NUMERIC(5,2) | NOT NULL DEFAULT 0 | `0` | 折扣率(%) |
| `price` | NUMERIC(10,2) | NOT NULL | — | 折后单价 |

**索引：** `price_matrix_pkey`, `price_matrix_client_method_idx (client_id, method_id)`  
**触发器：** `price_matrix_audit_trg`

---

#### 4.8.3 表：`billing.invoices`

**中文名：** 发票表  
**描述：** 财务发票管理。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 发票ID |
| `invoice_no` | VARCHAR(32) | UNIQUE NOT NULL | — | 发票号 |
| `client_id` | UUID | NOT NULL REFERENCES commission.clients(id) | — | 客户ID |
| `order_id` | UUID | REFERENCES commission.orders(id) | NULL | 关联委托单 |
| `amount` | NUMERIC(12,2) | NOT NULL | — | 金额 |
| `tax_amount` | NUMERIC(12,2) | NOT NULL | — | 税额 |
| `total_amount` | NUMERIC(12,2) | NOT NULL | — | 价税合计 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('draft','issued','paid','cancelled','refunded') | `'draft'` | 发票状态 |
| `issue_date` | DATE | NOT NULL | — | 开票日期 |
| `due_date` | DATE | | NULL | 到期日 |
| `type` | VARCHAR(20) | NOT NULL CHECK IN ('normal','special','electronic') | — | 发票类型 |

**索引：** `invoices_pkey`, `invoices_invoice_no_ukey`, `invoices_client_id_idx`, `invoices_status_idx`, `invoices_order_id_idx`  
**触发器：** `invoices_audit_trg`

---

#### 4.8.4 表：`billing.payment_records`

**中文名：** 收款记录表  
**描述：** 发票回款记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 收款ID |
| `invoice_id` | UUID | NOT NULL REFERENCES billing.invoices(id) | — | 发票ID |
| `amount` | NUMERIC(12,2) | NOT NULL | — | 收款金额 |
| `payment_date` | DATE | NOT NULL | — | 收款日期 |
| `payment_method` | VARCHAR(20) | NOT NULL CHECK IN ('bank_transfer','cash','check','credit_card','other') | — | 收款方式 |
| `operator` | UUID | NOT NULL REFERENCES auth.users(id) | — | 经办人 |
| `receipt_no` | VARCHAR(32) | | NULL | 收据号 |
| `notes` | TEXT | | NULL | 备注 |

**索引：** `payment_records_pkey`, `payment_records_invoice_id_idx`  
**触发器：** `payment_records_audit_trg`

---

#### 4.8.5 表：`billing.contracts`

**中文名：** 合同表  
**描述：** 客户框架合同管理。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 合同ID |
| `contract_no` | VARCHAR(32) | UNIQUE NOT NULL | — | 合同编号 |
| `client_id` | UUID | NOT NULL REFERENCES commission.clients(id) | — | 客户ID |
| `title` | VARCHAR(256) | NOT NULL | — | 合同标题 |
| `start_date` | DATE | NOT NULL | — | 生效日期 |
| `end_date` | DATE | NOT NULL | — | 到期日期 |
| `total_amount` | NUMERIC(14,2) | | NULL | 合同总额 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('draft','active','expired','terminated') | `'draft'` | 合同状态 |
| `signatory` | UUID | REFERENCES auth.users(id) | NULL | 签约人 |
| `signed_at` | TIMESTAMPTZ | | NULL | 签约时间 |

**索引：** `contracts_pkey`, `contracts_contract_no_ukey`, `contracts_client_id_idx`, `contracts_status_idx`  
**触发器：** `contracts_audit_trg`

---

#### 4.8.6 表：`billing.billing_batches`

**中文名：** 计费批次表  
**描述：** 按周期批量结算的计费批次。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 批次ID |
| `batch_no` | VARCHAR(32) | UNIQUE NOT NULL | — | 批次编号 |
| `client_id` | UUID | NOT NULL REFERENCES commission.clients(id) | — | 客户ID |
| `period_start` | DATE | NOT NULL | — | 周期开始 |
| `period_end` | DATE | NOT NULL | — | 周期结束 |
| `total_orders` | INTEGER | NOT NULL DEFAULT 0 | `0` | 委托单数量 |
| `total_amount` | NUMERIC(14,2) | NOT NULL DEFAULT 0 | `0` | 批次总额 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('draft','confirmed','invoiced','settled','cancelled') | `'draft'` | 批次状态 |

**索引：** `billing_batches_pkey`, `billing_batches_batch_no_ukey`, `billing_batches_client_id_idx`  
**触发器：** `billing_batches_audit_trg`

---

#### 4.8.7 表：`billing.discount_rules`

**中文名：** 折扣规则表  
**描述：** 自动折扣规则配置。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 规则ID |
| `name` | VARCHAR(128) | NOT NULL | — | 规则名称 |
| `condition_json` | JSONB | NOT NULL | — | 触发条件JSON |
| `discount_type` | VARCHAR(20) | NOT NULL CHECK IN ('percentage','fixed_amount','tiered') | — | 折扣类型 |
| `discount_value` | NUMERIC(10,2) | NOT NULL | — | 折扣值 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('active','inactive') | `'active'` | 状态 |

**索引：** `discount_rules_pkey`, `discount_rules_status_idx`  
**触发器：** `discount_rules_audit_trg`

---

#### 4.8.8 表：`billing.financial_summaries`

**中文名：** 财务汇总表  
**描述：** 按周期与客户维度的财务统计聚合。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 汇总ID |
| `period` | VARCHAR(16) | NOT NULL | — | 统计周期, 如 `2026-Q1` |
| `client_id` | UUID | | NULL | 客户ID (NULL表示全部) |
| `revenue` | NUMERIC(14,2) | NOT NULL | — | 营业收入 |
| `collection_rate` | NUMERIC(5,2) | | NULL | 回款率(%) |
| `outstanding` | NUMERIC(14,2) | NOT NULL DEFAULT 0 | `0` | 应收未收 |

**索引：** `financial_summaries_pkey`, `financial_summaries_period_idx`, `financial_summaries_client_id_idx`  
**触发器：** `financial_summaries_audit_trg`

---

### 4.9 Category I — 质量体系

#### 4.9.1 表：`quality.nonconformities`

**中文名：** 不合格品/不符合项表  
**描述：** 不符合工作要求的事件记录与纠正措施跟踪。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 记录ID |
| `title` | VARCHAR(256) | NOT NULL | — | 标题 |
| `description` | TEXT | NOT NULL | — | 不符合描述 |
| `category` | VARCHAR(32) | NOT NULL CHECK IN ('testing','equipment','environment','document','sample','other') | — | 不符合类型 |
| `severity` | VARCHAR(10) | NOT NULL CHECK IN ('minor','major','critical') | — | 严重程度 |
| `detected_by` | UUID | NOT NULL REFERENCES auth.users(id) | — | 发现人 |
| `detected_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 发现时间 |
| `root_cause` | TEXT | | NULL | 根因分析 |
| `corrective_action` | TEXT | | NULL | 纠正措施 |
| `responsible` | UUID | NOT NULL REFERENCES auth.users(id) | — | 责任人 |
| `deadline` | TIMESTAMPTZ | | NULL | 整改截止日期 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('open','investigating','correcting','closed','rejected') | `'open'` | 状态 |
| `closed_at` | TIMESTAMPTZ | | NULL | 关闭时间 |

**索引：** `nonconformities_pkey`, `nonconformities_status_idx`, `nonconformities_category_idx`, `nonconformities_deadline_idx`  
**触发器：** `nonconformities_audit_trg`

---

#### 4.9.2 表：`quality.internal_audits`

**中文名：** 内部审核表  
**描述：** 质量体系内部审核计划与结果。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 审核ID |
| `audit_no` | VARCHAR(32) | UNIQUE NOT NULL | — | 审核编号 |
| `auditor` | UUID | NOT NULL REFERENCES auth.users(id) | — | 审核员 |
| `audit_date` | DATE | NOT NULL | — | 审核日期 |
| `scope` | TEXT | NOT NULL | — | 审核范围 |
| `findings` | TEXT | | NULL | 审核发现 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('planned','in_progress','completed','follow_up') | `'planned'` | 审核状态 |
| `report_date` | DATE | | NULL | 报告出具日期 |

**索引：** `internal_audits_pkey`, `internal_audits_audit_no_ukey`, `internal_audits_audit_date_idx`  
**触发器：** `internal_audits_audit_trg`

---

#### 4.9.3 表：`quality.proficiency_tests`

**中文名：** 能力验证表  
**描述：** 实验室间比对/能力验证结果记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 验证ID |
| `name` | VARCHAR(256) | NOT NULL | — | 能力验证名称 |
| `organizer` | VARCHAR(128) | | NULL | 组织方 |
| `test_item` | VARCHAR(128) | NOT NULL | — | 验证项目 |
| `assigned_value` | NUMERIC(18,6) | | NULL | 指定值/参考值 |
| `lab_result` | NUMERIC(18,6) | | NULL | 本室结果 |
| `z_score` | NUMERIC(6,2) | | NULL | Z比分数 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('enrolled','in_progress','completed','unsatisfactory') | `'enrolled'` | 状态 |
| `date` | DATE | NOT NULL | — | 日期 |

**索引：** `proficiency_tests_pkey`, `proficiency_tests_date_idx`, `proficiency_tests_status_idx`  
**触发器：** `proficiency_tests_audit_trg`

---

#### 4.9.4 表：`quality.complaints`

**中文名：** 投诉表  
**描述：** 客户投诉记录与处理追踪。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 投诉ID |
| `complaint_no` | VARCHAR(32) | UNIQUE NOT NULL | — | 投诉编号 |
| `client_id` | UUID | REFERENCES commission.clients(id) | NULL | 投诉客户 |
| `content` | TEXT | NOT NULL | — | 投诉内容 |
| `received_by` | UUID | NOT NULL REFERENCES auth.users(id) | — | 接收人 |
| `received_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 接收时间 |
| `investigation` | TEXT | | NULL | 调查过程 |
| `resolution` | TEXT | | NULL | 处理结果 |
| `closed_by` | UUID | REFERENCES auth.users(id) | NULL | 关闭人 |
| `closed_at` | TIMESTAMPTZ | | NULL | 关闭时间 |

**索引：** `complaints_pkey`, `complaints_complaint_no_ukey`, `complaints_client_id_idx`, `complaints_received_at_idx`  
**触发器：** `complaints_audit_trg`

---

#### 4.9.5 表：`quality.management_reviews`

**中文名：** 管理评审表  
**描述：** 管理层定期评审记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 评审ID |
| `review_no` | VARCHAR(32) | UNIQUE NOT NULL | — | 评审编号 |
| `date` | DATE | NOT NULL | — | 评审日期 |
| `participants` | UUID[] | | NULL | 参会人员ID数组 |
| `agenda` | TEXT | NOT NULL | — | 评审议程 |
| `conclusions` | TEXT | | NULL | 评审结论 |
| `follow_up_actions` | JSONB | | NULL | 后续措施JSON |

**索引：** `management_reviews_pkey`, `management_reviews_review_no_ukey`, `management_reviews_date_idx`  
**触发器：** `management_reviews_audit_trg`

---

### 4.10 Category J — 系统基础

#### 4.10.1 表：`system.system_config`

**中文名：** 系统配置表  
**描述：** Key-Value 格式的系统配置参数。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 配置ID |
| `key` | VARCHAR(128) | UNIQUE NOT NULL | — | 配置键 |
| `value` | JSONB | NOT NULL | — | 配置值 |
| `description` | VARCHAR(256) | | NULL | 说明 |
| `updated_by` | UUID | NOT NULL REFERENCES auth.users(id) | — | 最后更新人 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 最后更新时间 |

**索引：** `system_config_pkey`, `system_config_key_ukey`  
**触发器：** `system_config_audit_trg`

---

#### 4.10.2 表：`system.dictionaries`

**中文名：** 数据字典表  
**描述：** 自引用层级字典数据。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 字典ID |
| `category` | VARCHAR(64) | NOT NULL | — | 分类标识 |
| `code` | VARCHAR(32) | NOT NULL | — | 字典代码 |
| `label` | VARCHAR(128) | NOT NULL | — | 显示标签 |
| `parent_id` | UUID | REFERENCES system.dictionaries(id) | NULL | 父级ID |
| `sort_order` | SMALLINT | NOT NULL DEFAULT 0 | `0` | 排序序号 |
| `status` | VARCHAR(20) | NOT NULL DEFAULT `'active'` CHECK IN ('active','inactive') | `'active'` | 状态 |

**索引：** `dictionaries_pkey`, `dictionaries_category_code_idx (category, code)`, `dictionaries_parent_id_idx`  
**触发器：** `dictionaries_audit_trg`

---

#### 4.10.3 表：`system.notifications`

**中文名：** 通知表  
**描述：** 用户站内通知消息。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 通知ID |
| `user_id` | UUID | NOT NULL REFERENCES auth.users(id) | — | 接收用户 |
| `type` | VARCHAR(32) | NOT NULL | — | 通知类型 |
| `title` | VARCHAR(256) | NOT NULL | — | 标题 |
| `content` | TEXT | | NULL | 内容 |
| `is_read` | BOOLEAN | NOT NULL DEFAULT false | `false` | 是否已读 |
| `read_at` | TIMESTAMPTZ | | NULL | 已读时间 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 创建时间 |

**索引：** `notifications_pkey`, `notifications_user_id_idx`, `notifications_is_read_idx`, `notifications_created_at_idx`, `notifications_user_read_idx (user_id, is_read)`  
**触发器：** `notifications_audit_trg`

---

#### 4.10.4 表：`system.scheduled_jobs`

**中文名：** 定时任务表  
**描述：** 后台定时任务调度与状态记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 任务ID |
| `name` | VARCHAR(128) | NOT NULL | — | 任务名称 |
| `cron_expr` | VARCHAR(64) | NOT NULL | — | Cron表达式 |
| `handler` | VARCHAR(128) | NOT NULL | — | 处理器标识 |
| `status` | VARCHAR(20) | NOT NULL CHECK IN ('enabled','disabled','error') | `'enabled'` | 启用状态 |
| `last_run` | TIMESTAMPTZ | | NULL | 最后执行时间 |
| `next_run` | TIMESTAMPTZ | | NULL | 下次执行时间 |
| `result` | VARCHAR(32) | | NULL | 最后执行结果 |

**索引：** `scheduled_jobs_pkey`, `scheduled_jobs_status_idx`, `scheduled_jobs_next_run_idx`  
**触发器：** `scheduled_jobs_audit_trg`

---

#### 4.10.5 表：`system.file_store`

**中文名：** 文件存储表  
**描述：** MinIO 对象存储索引，记录上传文件元信息。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 文件ID |
| `minio_key` | VARCHAR(256) | UNIQUE NOT NULL | — | MinIO存储路径 |
| `original_name` | VARCHAR(256) | NOT NULL | — | 原始文件名 |
| `mime_type` | VARCHAR(128) | | NULL | MIME类型 |
| `size` | BIGINT | NOT NULL | — | 文件大小(字节) |
| `bucket` | VARCHAR(64) | NOT NULL | — | 存储桶名称 |
| `uploaded_by` | UUID | NOT NULL REFERENCES auth.users(id) | — | 上传人 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | 上传时间 |

**索引：** `file_store_pkey`, `file_store_minio_key_ukey`, `file_store_bucket_idx`, `file_store_uploaded_by_idx`, `file_store_created_at_idx`  
**触发器：** `file_store_audit_trg`

---

## 5. 索引优化策略

### 5.1 索引创建原则

1. **主键索引**：所有 UUID 主键自动创建 B-tree 索引。
2. **唯一约束索引**：所有 `_ukey` 唯一约束自动创建唯一索引。
3. **复合索引顺序**：等值条件列在前, 范围条件列在后, 高区分度列优先。
4. **覆盖索引**：对高频查询（如报告列表）使用包含查询列的宽索引减少回表。

### 5.2 PostgreSQL 特殊索引

| 场景 | 索引类型 | 示例 |
|---|---|---|
| 数组查询（`sample_ids`、`test_method_ids`） | GIN | `CREATE INDEX reports_sample_ids_idx ON reporting.reports USING GIN (sample_ids)` |
| 全文搜索（投诉内容、审核发现） | GIN + tsvector | `CREATE INDEX complaints_content_gin ON quality.complaints USING GIN (to_tsvector('chinese', content))` |
| JSONB 查询（configuration.value、workflow 定义） | GIN | `CREATE INDEX system_config_value_gin ON system.system_config USING GIN (value)` |
| 时间范围查询（所有 `_at` 列） | BRIN | `CREATE INDEX audit_log_created_at_brin ON audit.audit_log USING BRIN (created_at)` |

### 5.3 建议的性能索引

```sql
-- 报告按状态+时间的高频查询
CREATE INDEX reports_status_issued_at_idx ON reporting.reports (status, issued_at DESC);

-- 检测任务按状态+优先级+截止时间的看板查询
CREATE INDEX test_tasks_status_priority_deadline_idx
  ON testing.test_tasks (status, priority, deadline ASC);

-- 委托单按客户+状态+时间的复合查询
CREATE INDEX orders_client_status_created_at_idx
  ON commission.orders (client_id, status, created_at DESC);

-- 审计日志按资源+时间的范围查询
CREATE INDEX audit_log_resource_created_at_gin
  ON audit.audit_log USING GIN (resource, created_at);
```

### 5.4 索引维护

- 定期执行 `REINDEX` 应对碎片化。
- 监控 `pg_stat_user_indexes` 消除未使用索引。
- BRIN 索引需配置 `pages_per_range`。

---

## 6. 审计触发器设计

### 6.1 全局审计触发函数

所有核心业务表均挂载统一审计触发器，自动将 DML 操作记录到 `audit.audit_log`。

```sql
-- 审计触发函数（全局共享）
CREATE OR REPLACE FUNCTION audit.audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    changed_record_id UUID;
    old_data JSONB;
    new_data JSONB;
    app_user_id UUID;
    client_ip INET;
BEGIN
    -- 获取上下问: 用户与IP via SET LOCAL / application settings
    app_user_id := COALESCE(
        current_setting('audit.current_user_id', true)::UUID,
        NULL
    );
    client_ip := COALESCE(
        NULLIF(current_setting('audit.client_ip', true), '')::INET,
        NULL
    );

    IF TG_OP = 'INSERT' THEN
        changed_record_id := NEW.id::UUID;
        old_data := NULL;
        new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        changed_record_id := NEW.id::UUID;
        old_data := to_jsonb(OLD);
        new_data := to_jsonb(NEW);
        -- 优化: 仅在有实质变化时记录
        IF old_data = new_data THEN
            RETURN NEW;
        END IF;
    ELSIF TG_OP = 'DELETE' THEN
        changed_record_id := OLD.id::UUID;
        old_data := to_jsonb(OLD);
        new_data := NULL;
    END IF;

    INSERT INTO audit.audit_log (
        user_id, action, resource, resource_id,
        old_value, new_value, ip_address
    ) VALUES (
        app_user_id,
        TG_OP,
        TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
        changed_record_id::TEXT,
        old_data,
        new_data,
        client_ip
    );

    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 6.2 触发器挂载模板

对每张业务表挂载独立触发器，便于独立管理：

```sql
CREATE TRIGGER users_audit_trg
    AFTER INSERT OR UPDATE OR DELETE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION audit.audit_trigger_func();

CREATE TRIGGER orders_audit_trg
    AFTER INSERT OR UPDATE OR DELETE ON commission.orders
    FOR EACH ROW EXECUTE FUNCTION audit.audit_trigger_func();

-- ...所有业务表同上模板
```

### 6.3 用户上下文传递

应用层在执行 SQL 前通过以下方式传递审计上下文：

```sql
SET LOCAL audit.current_user_id = '550e8400-e29b-41d4-a716-446655440000';
SET LOCAL audit.client_ip = '192.168.1.100';
```

或使用连接级设置 + 事务提交后自动清理。

### 6.4 审计日志保护

```sql
-- 禁止直接修改审计日志
CREATE OR REPLACE FUNCTION audit.prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log entries are immutable';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_log_immutable_trg
    BEFORE UPDATE OR DELETE ON audit.audit_log
    FOR EACH ROW EXECUTE FUNCTION audit.prevent_audit_modification();
```

### 6.5 敏感字段过滤

对 `password_hash` 等敏感字段，在触发器中脱敏后写入审计日志：

```sql
-- 在 audit_trigger_func 中加入敏感字段过滤
IF TG_TABLE_NAME = 'users' THEN
    IF new_data IS NOT NULL THEN
        new_data := new_data - 'password_hash';
    END IF;
    IF old_data IS NOT NULL THEN
        old_data := old_data - 'password_hash';
    END IF;
END IF;
```

---

## 7. 数据归档策略

### 7.1 保留周期

| 数据类型 | 在线保留 | 归档保留 | 总保留 |
|---|---|---|---|
| 审计日志 (`audit_log`) | 3年 | 7年 | 10年 |
| 报告及相关数据 | 永久 | — | 永久 |
| 检测任务与结果 | 永久 | — | 永久 |
| 设备使用日志 | 2年 | 8年 | 10年 |
| 定时任务结果 | 90天 | — | 90天 |
| 会话通知（已读超30天） | — | — | 30天后清除 |

### 7.2 冷热数据分离

采用 PostgreSQL 分区表 + 文件组策略实现冷热分离：

```sql
-- 示例: audit_log 按月分区
CREATE TABLE audit.audit_log (
    id BIGSERIAL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ...
) PARTITION BY RANGE (created_at);

-- 当前在线数据分区（保留36个月）
CREATE TABLE audit.audit_log_y2026m05 PARTITION OF audit.audit_log
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01')
    TABLESPACE pg_default;

-- 历史归档分区
CREATE TABLE audit.audit_log_y2016m05 PARTITION OF audit.audit_log
    FOR VALUES FROM ('2016-05-01') TO ('2016-06-01')
    TABLESPACE cold_storage;
```

### 7.3 自动分区管理

使用 `pg_partman` 扩展实现自动分区创建与清理：

```sql
-- 安装 pg_partman
CREATE EXTENSION IF NOT EXISTS pg_partman;

-- 配置自动分区
SELECT partman.create_parent(
    p_parent_table := 'audit.audit_log',
    p_control      := 'created_at',
    p_type         := 'range',
    p_interval     := '1 month',
    p_premake      := 3
);

-- 配置保留策略
UPDATE partman.part_config
SET retention = '36 months',
    retention_keep_table = false,
    retention_keep_data = true
WHERE parent_table = 'audit.audit_log';
```

### 7.4 归档表空间

```sql
-- 冷数据表空间（低成本存储）
CREATE TABLESPACE cold_storage
    LOCATION '/data/postgres/cold_storage';
```

### 7.5 数据销毁流程

超过10年保留期的数据，须经以下流程方可销毁：

1. 系统自动标记过期数据（每月执行一次）。
2. 数据管理员审核确认销毁清单。
3. 在审计日志中记录销毁操作。
4. 物理删除数据行（软删除后 `VACUUM FULL`）。
5. 对备份介质执行对应清除。

---

## 8. 备份与恢复

### 8.1 备份策略

| 备份类型 | 频率 | 保留 | 工具 |
|---|---|---|---|
| 完整备份 (Full) | 每周日 02:00 | 8周 | `pg_dump --format=custom` |
| 增量备份 (WAL) | 每 15 分钟 | 30天 | `pg_basebackup` + WAL 归档 |
| PITR 支持 | 连续 | — | WAL-G / pgBackRest |
| Schema 导出 | 每次DDL变更后 | 永久 | `pg_dump --schema-only` |

### 8.2 备份配置

```bash
# pgBaseBackup 配置
pg_basebackup \
    --pgdata=/backup/base/$(date +%F) \
    --wal-method=stream \
    --checkpoint=fast \
    --label="lims_base_backup_$(date +%F)" \
    --verbose
```

### 8.3 WAL 归档

```postgresql
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'pgbackrest --stanza=lims archive-push %p'
archive_timeout = 60
```

### 8.4 恢复策略

| 场景 | RTO | RPO | 方法 |
|---|---|---|---|
| 单行误删 | < 30 min | 0 (通过审计日志恢复) | 从审计日志 JSONB 重建行 |
| 表级恢复 | < 2 小时 | < 15 min | WAL PITR 到子库 |
| 全库恢复 | < 4 小时 | < 15 min | 完整备份 + WAL 重放 |
| 灾难恢复 | < 8 小时 | < 1 小时 | 异地备份还原 |

### 8.5 恢复验证

- 每月执行一次恢复演练，验证备份完整性。
- 使用 `pg_restore --list` 检查备份内容。
- 恢复演练记录写入质量体系表 `quality.internal_audits`。

### 8.6 异地灾备

- 异地部署只读副本（Streaming Replication）。
- 每日将完整备份推送到对象存储（MinIO/S3）的异地 Bucket。
- 每半年执行一次跨站点灾难恢复演练。

---

## 附录 A: 数据类型规范

| 用途 | PostgreSQL 类型 | 说明 |
|---|---|---|
| 主键 | `UUID` | 使用 `gen_random_uuid()` |
| 自增ID（日志） | `BIGSERIAL` | 高写入日志表 |
| 货币金额 | `NUMERIC(14,2)` | 精确到分 |
| 百分比/比率 | `NUMERIC(5,2)` | 精确到 0.01% |
| 时间戳 | `TIMESTAMPTZ` | 带时区 |
| 日期 | `DATE` | 不含时分秒 |
| IP地址 | `INET` | 原生IP类型 |
| 布尔 | `BOOLEAN` | — |
| 短文本 | `VARCHAR(N)` | 限制长度 |
| 长文本 | `TEXT` | 无长度限制 |
| JSON数据 | `JSONB` | 二进制JSON可索引 |
| 数组 | `<type>[]` | 如 `UUID[]` |
| 枚举值 | `VARCHAR(N) + CHECK` | 不使用 ENUM 以保留灵活性 |

## 附录 B: 通用列定义

### 审计字段（所有业务表）

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `created_at` | TIMESTAMPTZ | `NOW()` | 创建时间 |
| `updated_at` | TIMESTAMPTZ | `NOW()` | 更新时间（由触发器自动更新） |

### 自动更新时间触发器

```sql
CREATE OR REPLACE FUNCTION system.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 对所有含 updated_at 的表挂载
CREATE TRIGGER set_users_updated_at
    BEFORE UPDATE ON auth.users
    FOR EACH ROW WHEN (OLD.updated_at IS NOT DISTINCT FROM NEW.updated_at)
    EXECUTE FUNCTION system.set_updated_at();
```

## 附录 C: 表统计

| Category | 模块 | 表数量 |
|---|---|---|
| A | 用户与权限 | 6 |
| B | 委托与收样 | 5 |
| C | 检测任务 | 6 |
| D | 报告管理 | 5 |
| E | 设备管理 | 7 |
| F | 标准方法库 | 4 |
| G | 工作流引擎 | 5 |
| H | 计费管理 | 8 |
| I | 质量体系 | 5 |
| J | 系统基础 | 5 |
| **合计** | **10个模块** | **56张表** |

---

# 第四部分: API 接口设计

# API 接口设计说明书

> LIMS v1 — 建筑工程材料检测实验室信息管理系统
> URL 版本策略：`/api/v1/...`，协议：HTTPS only，数据格式：JSON

---

## 目录

1. [API 设计规范](#1-api-设计规范)
2. [核心 API 端点](#2-核心-api-端点)
3. [WebSocket 接口](#3-websocket-接口)
4. [GraphQL 查询](#4-graphql-查询)
5. [权限矩阵](#5-权限矩阵)
6. [API 版本管理策略](#6-api-版本管理策略)

---

## 1. API 设计规范

### 1.1 URL 命名规则

| 规则 | 说明 | 示例 |
|------|------|------|
| 使用复数名词 | 资源集合用复数形式 | `/api/v1/orders/` |
| 全小写+连字符 | 单词间用 `-` 分隔 | `/api/v1/test-tasks/` |
| 层级嵌套 | 子资源作为路径嵌套，最多三级 | `/api/v1/orders/{id}/samples/` |
| 动作用 POST | 非 CRUD 操作使用 `/api/v1/{resource}/actions/{action}` | `/api/v1/reports/123/actions/sign` |

### 1.2 HTTP 方法约定

| 方法 | 语义 | 幂等 | 返回码 |
|------|------|------|--------|
| GET | 读取资源 | 是 | 200 |
| POST | 创建资源或执行操作 | 否 | 201 / 200 |
| PUT | 完整替换资源 | 是 | 200 |
| PATCH | 部分更新资源 | 否 | 200 |
| DELETE | 删除资源 | 是 | 204 / 200 |

### 1.3 请求 / 响应格式

所有请求和响应 `Content-Type: application/json`，字段名使用 `snake_case`。

**请求头**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
X-Request-ID: <uuid>  (可选, 用于链路追踪)
Accept-Language: zh-CN  (可选, 默认 zh-CN)
```

**通用响应信封**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

**列表响应信封**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [],
    "next_cursor": "eyJpZCI6MjAsInRzIjoxNzE... ",
    "has_more": true,
    "total": 158
  }
}
```

### 1.4 分页

采用 **cursor-based 分页**，每页默认 20 条，最大 50 条。

| 参数 | 类型 | 必须 | 默认值 | 说明 |
|------|------|------|--------|------|
| `cursor` | string | 否 | - | 上一页返回的 `next_cursor`，首请求省略 |
| `limit` | integer | 否 | 20 | 每页条数，最大 50 |

### 1.5 排序 / 过滤 / 搜索

| 参数 | 格式 | 示例 |
|------|------|------|
| `sort` | `field:asc` 或 `field:desc`，多字段逗号分隔 | `sort=created_at:desc,status:asc` |
| `filter` | `field__op=value` | `filter=status__in=active,pending` |
| `q` | 全文搜索关键词 | `q=C30混凝土` |

支持的过滤操作符：`eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `like`, `is_null`。

### 1.6 错误响应格式

```json
{
  "code": 40010,
  "message": "参数校验失败",
  "detail": "委托编号已存在",
  "field_errors": [
    {
      "field": "order_code",
      "message": "该委托编号已被使用"
    }
  ],
  "request_id": "req_a1b2c3d4",
  "timestamp": "2025-06-15T09:30:00Z"
}
```

**错误码区间**:

| 区间 | 类型 |
|------|------|
| 40000-40099 | 请求参数错误 |
| 40100-40199 | 认证失败 |
| 40300-40399 | 权限不足 |
| 40400-40499 | 资源不存在 |
| 40900-40999 | 冲突 / 状态不一致 |
| 42200-42299 | 业务逻辑校验失败 |
| 50000-50099 | 服务器内部错误 |

### 1.7 认证

Bearer JWT Token，置于 `Authorization` 请求头：

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Token 有效期 2 小时。使用 `/api/v1/auth/refresh` 换取新的 access_token。

JWT Payload 包含：`sub`（用户 ID）、`role_codes`（角色编码列表）、`exp`（过期时间）、`jti`（唯一标识，用于登出黑名单）。

### 1.8 幂等性支持

对 POST 请求，允许在请求头附加 `Idempotency-Key: <uuid>`。服务端缓存 24 小时内同一 key 的首次响应，重复请求直接返回缓存结果。

### 1.9 速率限制

| 级别 | 限制 |
|------|------|
| 匿名用户 | 30 req/min |
| 已认证用户 | 600 req/min |
| 批量导入端点 | 10 req/min |

响应头返回 `X-RateLimit-Remaining` 和 `X-RateLimit-Reset`。

---

## 2. 核心 API 端点

以下端点 OpenAPI 规范中每个字段均有 `schema`、`example`、`description`，由 `drf-spectacular` 自动生成 Swagger UI (`/api/v1/schema/swagger-ui/`) 和 JSON/YAML (`/api/v1/schema/`)。

---

### 2.1 认证模块 `/api/v1/auth/`

#### 2.1.1 登录

```
POST /api/v1/auth/login/
```

**请求体**:
```json
{
  "username": "zhangsan",
  "password": "MyP@ssw0rd!",
  "tenant_code": "lab-sh-001"
}
```

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "dGhpcyBpcyBhIHJlZnJl...",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "id": 12,
      "username": "zhangsan",
      "display_name": "张三",
      "roles": ["lab_manager", "report_reviewer"],
      "permissions": ["order.create", "sample.read", "report.submit"]
    }
  }
}
```

#### 2.1.2 登出

```
POST /api/v1/auth/logout/
```

**请求体**: 空（携带当前 token）

**响应** (200): `{"code": 0, "message": "ok", "data": null}`

#### 2.1.3 刷新 Token

```
POST /api/v1/auth/refresh/
```

**请求体**:
```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl..."
}
```

**响应** (200): 同登录响应中的 token 部分。

#### 2.1.4 修改密码

```
POST /api/v1/auth/change-password/
```

**请求体**:
```json
{
  "old_password": "OldP@ss!",
  "new_password": "NewP@ss123!",
  "confirm_password": "NewP@ss123!"
}
```

**响应** (200): `{"code": 0, "message": "密码已修改", "data": null}`

---

### 2.2 用户模块 `/api/v1/users/`

#### 2.2.1 获取用户列表

```
GET /api/v1/users/
```

**查询参数**:
| 参数 | 类型 | 必须 | 说明 |
|------|------|------|------|
| `cursor` | string | 否 | 分页游标 |
| `limit` | int | 否 | 每页数 |
| `sort` | string | 否 | 排序字段 |
| `filter` | string | 否 | 过滤条件 |
| `q` | string | 否 | 搜索关键词（姓名/账号/手机号） |

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 12,
        "username": "zhangsan",
        "display_name": "张三",
        "email": "zhangsan@example.com",
        "phone": "13800138000",
        "roles": [{"id": 3, "code": "lab_manager", "name": "实验室管理员"}],
        "status": "active",
        "created_at": "2025-01-10T08:00:00Z",
        "last_login": "2025-06-15T09:00:00Z"
      }
    ],
    "next_cursor": "eyJpZCI6MTIs...",
    "has_more": false,
    "total": 1
  }
}
```

#### 2.2.2 获取单个用户

```
GET /api/v1/users/{id}/
```

#### 2.2.3 创建用户

```
POST /api/v1/users/
```

**请求体**:
```json
{
  "username": "lisi",
  "display_name": "李四",
  "email": "lisi@example.com",
  "phone": "13900139000",
  "role_ids": [2, 5],
  "password": "DefaultP@ss1!",
  "status": "active"
}
```

#### 2.2.4 更新用户

```
PATCH /api/v1/users/{id}/
```

**请求体**: 部分字段即可。

#### 2.2.5 删除用户

```
DELETE /api/v1/users/{id}/
```

#### 2.2.6 批量导入用户

```
POST /api/v1/users/actions/bulk-import/
```

**请求体**:
```json
{
  "csv_content": "username,display_name,email,role\nwangwu,王五,wangwu@example.com,lab_technician\n...",
  "overwrite_existing": false
}
```

**响应** (202):
```json
{
  "code": 0,
  "message": "导入任务已提交",
  "data": {
    "task_id": "task_import_88a7b2",
    "total_rows": 150,
    "status_url": "/api/v1/users/actions/import-status/task_import_88a7b2/"
  }
}
```

#### 2.2.7 修改状态

```
PATCH /api/v1/users/{id}/actions/change-status/
```

**请求体**:
```json
{
  "status": "suspended"
}
```

---

### 2.3 角色模块 `/api/v1/roles/`

#### 2.3.1 获取角色列表

```
GET /api/v1/roles/
```

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 3,
        "code": "lab_manager",
        "name": "实验室管理员",
        "permissions": [
          {"code": "order.create", "name": "创建委托", "module": "order"},
          {"code": "order.read", "name": "查看委托", "module": "order"},
          {"code": "report.review", "name": "审核报告", "module": "report"}
        ],
        "user_count": 12
      }
    ],
    "next_cursor": null,
    "has_more": false,
    "total": 1
  }
}
```

#### 2.3.2 创建角色

```
POST /api/v1/roles/
```

**请求体**:
```json
{
  "code": "custom_role_01",
  "name": "自定义角色",
  "permission_codes": ["order.read", "sample.read", "report.create"]
}
```

#### 2.3.3 更新角色

```
PATCH /api/v1/roles/{id}/
```

#### 2.3.4 删除角色

```
DELETE /api/v1/roles/{id}/
```

#### 2.3.5 分配权限

```
POST /api/v1/roles/{id}/actions/assign-permissions/
```

**请求体**:
```json
{
  "permission_codes": ["order.create", "order.read", "sample.create"]
}
```

#### 2.3.6 获取全部权限定义

```
GET /api/v1/roles/actions/permission-list/
```

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {"code": "order.create", "name": "创建委托", "module": "order"},
    {"code": "order.read", "name": "查看委托", "module": "order"},
    {"code": "order.update", "name": "编辑委托", "module": "order"},
    {"code": "sample.create", "name": "登记样品", "module": "sample"},
    {"code": "sample.read", "name": "查看样品", "module": "sample"},
    {"code": "test_task.assign", "name": "分配检测任务", "module": "test_task"},
    {"code": "test_task.execute", "name": "执行检测", "module": "test_task"},
    {"code": "report.create", "name": "编制报告", "module": "report"},
    {"code": "report.review", "name": "审核报告", "module": "report"},
    {"code": "report.approve", "name": "批准报告", "module": "report"},
    {"code": "report.sign", "name": "签发报告", "module": "report"}
  ]
}
```

---

### 2.4 委托模块 `/api/v1/orders/`

#### 2.4.1 获取委托列表

```
GET /api/v1/orders/
```

**查询参数**: `filter=client__eq=XX公司&filter=status__in=registered,in_progress`、`q=委托编号`、`sort=created_at:desc`。

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 1001,
        "order_code": "WT-2025-0088",
        "client": {"id": 5, "name": "XX建设集团", "contact": "王总"},
        "project_name": "滨江花园3#楼",
        "status": "in_progress",
        "order_type": "construction",
        "sample_count": 12,
        "total_amount": 8500.00,
        "created_by": {"id": 12, "display_name": "张三"},
        "created_at": "2025-06-01T10:00:00Z",
        "updated_at": "2025-06-05T14:30:00Z"
      }
    ],
    "next_cursor": "eyJpZCI6MTAwMSw...",
    "has_more": true,
    "total": 88
  }
}
```

#### 2.4.2 获取单个委托

```
GET /api/v1/orders/{id}/
```

#### 2.4.3 创建委托

```
POST /api/v1/orders/
```

**请求体**:
```json
{
  "client_id": 5,
  "project_name": "滨江花园3#楼",
  "order_type": "construction",
  "test_items": [
    {"test_method_id": 1, "quantity": 3},
    {"test_method_id": 5, "quantity": 2}
  ],
  "notes": "加急，需3个工作日内出具报告",
  "attachments": []
}
```

#### 2.4.4 更新委托

```
PATCH /api/v1/orders/{id}/
```

#### 2.4.5 删除委托

```
DELETE /api/v1/orders/{id}/
```

#### 2.4.6 委托状态流转操作

```
POST /api/v1/orders/{id}/actions/submit/
POST /api/v1/orders/{id}/actions/review/
POST /api/v1/orders/{id}/actions/reject/
```

**请求体** (`review`):
```json
{
  "action": "approve",
  "comment": "检测项目完整，数据无误"
}
```

**请求体** (`reject`):
```json
{
  "action": "reject",
  "comment": "缺抗压强度数据，请补充"
}
```

#### 2.4.7 获取委托的样品列表

```
GET /api/v1/orders/{id}/samples/
```

---

### 2.5 样品模块 `/api/v1/samples/`

#### 2.5.1 获取样品列表

```
GET /api/v1/samples/
```

**查询参数**: `filter=status__eq=received`、`filter=order__eq=1001`、`q=样品编号`。

#### 2.5.2 获取单个样品

```
GET /api/v1/samples/{id}/
```

#### 2.5.3 登记样品

```
POST /api/v1/samples/
```

**请求体**:
```json
{
  "order_id": 1001,
  "sample_name": "混凝土抗压试块",
  "sample_type": "cube_150",
  "specification": "150×150×150mm",
  "grade": "C30",
  "quantity": 3,
  "received_date": "2025-06-01",
  "received_by": 12,
  "storage_condition": "标准养护室温养",
  "curing_age": 28,
  "notes": "现场取样",
  "images": ["upload_abc123.jpg"]
}
```

**响应** (201):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 5001,
    "sample_code": "YB-2025-06-005001",
    "barcode": "1830100000005001",
    "status": "received",
    "created_at": "2025-06-01T10:30:00Z"
  }
}
```

#### 2.5.4 更新样品

```
PATCH /api/v1/samples/{id}/
```

#### 2.5.5 删除样品

```
DELETE /api/v1/samples/{id}/
```

#### 2.5.6 生成条码

```
POST /api/v1/samples/{id}/actions/generate-barcode/
```

**请求体**:
```json
{
  "barcode_type": "ean13"
}
```

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "sample_id": 5001,
    "barcode": "1830100000005001",
    "barcode_image_url": "/api/v1/samples/5001/barcode-image/"
  }
}
```

#### 2.5.7 获取条码图片

```
GET /api/v1/samples/{id}/barcode-image/
```

#### 2.5.8 更新样品状态

```
PATCH /api/v1/samples/{id}/actions/update-status/
```

**请求体**:
```json
{
  "status": "testing",
  "reason": "已移交检测室"
}
```

#### 2.5.9 获取流转记录

```
GET /api/v1/samples/{id}/trace/
```

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "sample_code": "YB-2025-06-005001",
    "history": [
      {
        "id": 1,
        "status_from": null,
        "status_to": "received",
        "operator": {"id": 12, "display_name": "张三"},
        "timestamp": "2025-06-01T10:30:00Z",
        "note": "样品接收登记"
      },
      {
        "id": 2,
        "status_from": "received",
        "status_to": "testing",
        "operator": {"id": 15, "display_name": "赵六"},
        "timestamp": "2025-06-02T08:00:00Z",
        "note": "领样至力学室"
      }
    ]
  }
}
```

---

### 2.6 检测任务模块 `/api/v1/test-tasks/`

#### 2.6.1 获取任务列表

```
GET /api/v1/test-tasks/
```

**查询参数**: `filter=assignee__eq=12`、`filter=status__in=pending,in_progress`。

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 301,
        "task_code": "RW-2025-0301",
        "sample": {"id": 5001, "sample_code": "YB-2025-06-005001", "sample_name": "混凝土抗压试块"},
        "test_method": {"id": 1, "name": "混凝土抗压强度", "standard": "GB/T 50081-2019"},
        "status": "pending",
        "assignee": null,
        "equipment": null,
        "assigned_at": null,
        "deadline": "2025-06-10T18:00:00Z",
        "created_at": "2025-06-01T10:35:00Z"
      }
    ],
    "next_cursor": null,
    "has_more": false,
    "total": 1
  }
}
```

#### 2.6.2 获取单个任务

```
GET /api/v1/test-tasks/{id}/
```

#### 2.6.3 创建任务

```
POST /api/v1/test-tasks/
```

**请求体**:
```json
{
  "sample_id": 5001,
  "test_method_id": 1,
  "assignee_id": 15,
  "equipment_id": 8,
  "deadline": "2025-06-10",
  "priority": "normal",
  "notes": ""
}
```

#### 2.6.4 更新任务

```
PATCH /api/v1/test-tasks/{id}/
```

#### 2.6.5 分配任务

```
POST /api/v1/test-tasks/{id}/actions/assign/
```

**请求体**:
```json
{
  "assignee_id": 15,
  "equipment_id": 8,
  "deadline": "2025-06-10T18:00:00Z"
}
```

#### 2.6.6 开始检测

```
POST /api/v1/test-tasks/{id}/actions/start/
```

#### 2.6.7 提交检测结果

```
POST /api/v1/test-tasks/{id}/actions/submit/
```

#### 2.6.8 撤回提交

```
POST /api/v1/test-tasks/{id}/actions/retract/
```

---

### 2.7 检测方法模块 `/api/v1/test-methods/`

#### 2.7.1 获取方法列表

```
GET /api/v1/test-methods/
```

**查询参数**: `q=抗压`、`filter=standard__eq=GB/T 50081-2019`。

#### 2.7.2 获取单个方法详情

```
GET /api/v1/test-methods/{id}/
```

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "code": "TM-CONC-COMP",
    "name": "混凝土抗压强度",
    "standard": "GB/T 50081-2019",
    "standard_id": 10,
    "category": "力学性能",
    "description": "测定混凝土立方体试件的抗压强度",
    "parameters": [
      {
        "id": 1,
        "code": "max_load",
        "name": "最大荷载",
        "unit": "kN",
        "data_type": "decimal",
        "decimal_places": 1,
        "required": true
      },
      {
        "id": 2,
        "code": "area",
        "name": "受压面积",
        "unit": "mm²",
        "data_type": "decimal",
        "decimal_places": 1,
        "required": true
      }
    ],
    "calculated_fields": [
      {
        "code": "compressive_strength",
        "name": "抗压强度",
        "unit": "MPa",
        "formula": "max_load * 1000 / area",
        "rounding": {
          "method": "round_even",
          "decimal_places": 1
        }
      }
    ],
    "status": "active",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-03-15T10:00:00Z"
  }
}
```

#### 2.7.3 创建方法

```
POST /api/v1/test-methods/
```

#### 2.7.4 更新方法

```
PATCH /api/v1/test-methods/{id}/
```

#### 2.7.5 停用 / 启用方法

```
POST /api/v1/test-methods/{id}/actions/deactivate/
POST /api/v1/test-methods/{id}/actions/activate/
```

---

### 2.8 检测结果模块 `/api/v1/test-results/`

#### 2.8.1 获取任务结果

```
GET /api/v1/test-results/{task_id}/
```

#### 2.8.2 录入 / 更新结果

```
POST /api/v1/test-results/
PATCH /api/v1/test-results/{task_id}/
```

**请求体**:
```json
{
  "task_id": 301,
  "raw_data": {
    "max_load": 685.3,
    "area": 22500.0,
    "curing_age": 28,
    "test_date": "2025-06-03T14:00:00Z",
    "temperature": 22.5,
    "humidity": 60
  },
  "calculated_values": {
    "compressive_strength": 30.5
  },
  "conclusion": "合格",
  "attachments": ["upload_photo1.jpg"],
  "notes": "第三组试块"
}
```

#### 2.8.3 触发重新计算

```
POST /api/v1/test-results/{task_id}/actions/recalculate/
```

#### 2.8.4 获取修约规则

```
GET /api/v1/test-results/actions/rounding-rules/
```

---

### 2.9 报告模块 `/api/v1/reports/`

#### 2.9.1 获取报告列表

```
GET /api/v1/reports/
```

**查询参数**: `filter=status__in=compiling,under_review`、`filter=order__eq=1001`、`q=报告编号`。

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 701,
        "report_code": "BG-2025-0701",
        "order_code": "WT-2025-0088",
        "order": {"id": 1001, "project_name": "滨江花园3#楼"},
        "status": "under_review",
        "compiled_by": {"id": 15, "display_name": "赵六"},
        "reviewed_by": {"id": 12, "display_name": "张三"},
        "approved_by": null,
        "signed_by": null,
        "issue_date": null,
        "created_at": "2025-06-05T10:00:00Z"
      }
    ],
    "next_cursor": null,
    "has_more": false,
    "total": 1
  }
}
```

#### 2.9.2 获取单个报告

```
GET /api/v1/reports/{id}/
```

#### 2.9.3 创建 / 编制报告

```
POST /api/v1/reports/
```

**请求体**:
```json
{
  "order_id": 1001,
  "template_code": "default",
  "title": "混凝土抗压强度检测报告",
  "conclusion_summary": "所检项目均满足设计要求",
  "attachments": []
}
```

#### 2.9.4 更新报告

```
PATCH /api/v1/reports/{id}/
```

#### 2.9.5 删除报告

```
DELETE /api/v1/reports/{id}/
```

#### 2.9.6 提交审核

```
POST /api/v1/reports/{id}/actions/submit-for-review/
```

#### 2.9.7 审核

```
POST /api/v1/reports/{id}/actions/review/
```

**请求体**:
```json
{
  "action": "approve",
  "comment": "数据准确，格式规范，同意审核通过"
}
```

#### 2.9.8 批准

```
POST /api/v1/reports/{id}/actions/approve/
```

**请求体**:
```json
{
  "comment": "批准签发"
}
```

#### 2.9.9 签发

```
POST /api/v1/reports/{id}/actions/sign/
```

**请求体**:
```json
{
  "signature_method": "digital",
  "comment": "报告已签发"
}
```

#### 2.9.10 下载 PDF

```
GET /api/v1/reports/{id}/download/
```

返回 `application/pdf` 二进制流。

**查询参数**: `preview=true` 时返回水印预览版。

#### 2.9.11 重新生成

```
POST /api/v1/reports/{id}/actions/regenerate/
```

---

### 2.10 设备模块 `/api/v1/equipment/`

#### 2.10.1 获取设备列表

```
GET /api/v1/equipment/
```

**查询参数**: `filter=status__eq=active`、`filter=calibration_due__lte=2025-07-01`、`q=压力机`。

#### 2.10.2 获取单个设备

```
GET /api/v1/equipment/{id}/
```

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 8,
    "code": "EQ-YL-001",
    "name": "3000kN压力试验机",
    "model": "DYE-3000",
    "manufacturer": "济南试金",
    "serial_number": "20230518",
    "status": "active",
    "location": "力学实验室",
    "calibration_due": "2025-09-15",
    "calibration_status": "valid",
    "last_calibration_date": "2024-09-15",
    "next_calibration_date": "2025-09-15",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 2.10.3 创建设备

```
POST /api/v1/equipment/
```

#### 2.10.4 更新设备

```
PATCH /api/v1/equipment/{id}/
```

#### 2.10.5 删除设备

```
DELETE /api/v1/equipment/{id}/
```

#### 2.10.6 登记校准

```
POST /api/v1/equipment/{id}/actions/calibrate/
```

**请求体**:
```json
{
  "calibration_company": "上海市计量院",
  "certificate_number": "CAL-2025-12345",
  "calibration_date": "2025-09-10",
  "next_calibration_date": "2026-09-10",
  "result": "qualified",
  "certificate_url": "upload_cert.pdf",
  "notes": ""
}
```

#### 2.10.7 登记维修

```
POST /api/v1/equipment/{id}/actions/maintenance/
```

**请求体**:
```json
{
  "type": "repair",
  "description": "液压阀泄漏，更换密封件",
  "performed_by": "设备部-李技师",
  "maintenance_date": "2025-06-10",
  "cost": 2500.00,
  "result": "restored"
}
```

#### 2.10.8 获取使用记录

```
GET /api/v1/equipment/{id}/usage-logs/
```

---

### 2.11 流程定义模块 `/api/v1/workflows/`

#### 2.11.1 获取流程定义列表

```
GET /api/v1/workflows/
```

#### 2.11.2 获取单个流程定义

```
GET /api/v1/workflows/{id}/
```

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "code": "WF-ORDER",
    "name": "委托处理流程",
    "description": "从委托登记到报告签发的完整流程",
    "states": [
      {"code": "draft", "name": "草稿", "initial": true},
      {"code": "registered", "name": "已登记"},
      {"code": "received", "name": "已收样"},
      {"code": "in_progress", "name": "检测中"},
      {"code": "under_review", "name": "审核中"},
      {"code": "completed", "name": "已完成"}
    ],
    "transitions": [
      {"from": "draft", "to": "registered", "name": "提交", "required_permissions": ["order.create"]},
      {"from": "registered", "to": "received", "name": "收样确认", "required_permissions": ["sample.create"]},
      {"from": "received", "to": "in_progress", "name": "开始检测", "required_permissions": ["test_task.execute"]},
      {"from": "in_progress", "to": "under_review", "name": "提交审核", "required_permissions": ["report.create"]},
      {"from": "under_review", "to": "completed", "name": "审核通过", "required_permissions": ["report.review"]}
    ],
    "status": "active"
  }
}
```

#### 2.11.3 创建流程定义

```
POST /api/v1/workflows/
```

#### 2.11.4 更新流程定义

```
PATCH /api/v1/workflows/{id}/
```

#### 2.11.5 获取流程实例

```
GET /api/v1/workflows/instances/
GET /api/v1/workflows/instances/{instance_id}/
```

#### 2.11.6 获取实例流转历史

```
GET /api/v1/workflows/instances/{instance_id}/history/
```

#### 2.11.7 执行状态转换

```
POST /api/v1/workflows/instances/{instance_id}/actions/transition/
```

**请求体**:
```json
{
  "transition_code": "submit",
  "comment": "样品已收齐，开始检测"
}
```

---

### 2.12 价格管理模块 `/api/v1/pricing/`

#### 2.12.1 获取价格矩阵

```
GET /api/v1/pricing/
```

#### 2.12.2 创建价格规则

```
POST /api/v1/pricing/
```

**请求体**:
```json
{
  "client_type": "enterprise",
  "test_method_id": 1,
  "base_price": 50.00,
  "unit": "每试件",
  "discount_rate": 0.90,
  "effective_from": "2025-01-01",
  "effective_to": "2025-12-31",
  "notes": "大客户9折"
}
```

#### 2.12.3 更新价格规则

```
PATCH /api/v1/pricing/{id}/
```

#### 2.12.4 删除价格规则

```
DELETE /api/v1/pricing/{id}/
```

#### 2.12.5 自动算价

```
POST /api/v1/pricing/actions/calculate/
```

**请求体**:
```json
{
  "order_id": 1001
}
```

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "order_id": 1001,
    "items": [
      {
        "test_method_id": 1,
        "test_method_name": "混凝土抗压强度",
        "quantity": 3,
        "unit_price": 45.00,
        "subtotal": 135.00,
        "pricing_rule_id": 10
      },
      {
        "test_method_id": 5,
        "test_method_name": "钢筋拉伸",
        "quantity": 2,
        "unit_price": 3600.00,
        "subtotal": 7200.00,
        "pricing_rule_id": 15
      }
    ],
    "total_amount": 7335.00,
    "discount_applied": true,
    "notes": "已应用大客户折扣"
  }
}
```

---

### 2.13 发票模块 `/api/v1/invoices/`

#### 2.13.1 获取发票列表

```
GET /api/v1/invoices/
```

#### 2.13.2 获取单个发票

```
GET /api/v1/invoices/{id}/
```

#### 2.13.3 创建发票

```
POST /api/v1/invoices/
```

**请求体**:
```json
{
  "order_id": 1001,
  "invoice_type": "vat_special",
  "client_name": "XX建设集团",
  "tax_id": "91310000123456789X",
  "amount": 7335.00,
  "notes": ""
}
```

#### 2.13.4 更新发票

```
PATCH /api/v1/invoices/{id}/
```

#### 2.13.5 作废发票

```
DELETE /api/v1/invoices/{id}/
```

#### 2.13.6 登记支付

```
POST /api/v1/invoices/{id}/actions/record-payment/
```

**请求体**:
```json
{
  "amount": 7335.00,
  "payment_method": "bank_transfer",
  "payment_date": "2025-06-15",
  "transaction_id": "TXN-20250615-001",
  "notes": "银行转账"
}
```

#### 2.13.7 获取支付记录

```
GET /api/v1/invoices/{id}/payment-records/
```

---

### 2.14 标准模块 `/api/v1/standards/`

#### 2.14.1 获取标准列表

```
GET /api/v1/standards/
```

**查询参数**: `q=混凝土`、`filter=status__eq=active`、`filter=category__eq=national`。

#### 2.14.2 获取单个标准

```
GET /api/v1/standards/{id}/
```

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 10,
    "code": "GB/T 50081-2019",
    "name": "混凝土物理力学性能试验方法标准",
    "category": "national",
    "publisher": "住建部",
    "publish_date": "2019-09-01",
    "status": "active",
    "description": "规定混凝土立方体抗压强度、轴心抗压强度等试验方法",
    "related_methods": [
      {"id": 1, "code": "TM-CONC-COMP", "name": "混凝土抗压强度"}
    ]
  }
}
```

#### 2.14.3 创建标准

```
POST /api/v1/standards/
```

#### 2.14.4 更新标准

```
PATCH /api/v1/standards/{id}/
```

#### 2.14.5 废止标准

```
POST /api/v1/standards/{id}/actions/repeal/
```

---

### 2.15 系统配置模块 `/api/v1/config/`

#### 2.15.1 获取所有配置

```
GET /api/v1/config/
```

#### 2.15.2 获取特定配置组

```
GET /api/v1/config/{group}/
```

#### 2.15.3 更新配置

```
PATCH /api/v1/config/{key}/
```

**请求体**:
```json
{
  "value": "new_value"
}
```

#### 2.15.4 字典列表

```
GET /api/v1/config/dictionaries/
```

#### 2.15.5 获取单本字典

```
GET /api/v1/config/dictionaries/{dict_code}/
```

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "dict_code": "sample_type",
    "dict_name": "样品类型",
    "entries": [
      {"value": "cube_150", "label": "150mm立方体", "sort_order": 1, "is_active": true},
      {"value": "cube_100", "label": "100mm立方体", "sort_order": 2, "is_active": true},
      {"value": "cylinder_150", "label": "150mm圆柱体", "sort_order": 3, "is_active": false}
    ]
  }
}
```

#### 2.15.6 管理字典条目

```
POST /api/v1/config/dictionaries/{dict_code}/entries/
PATCH /api/v1/config/dictionaries/{dict_code}/entries/{entry_id}/
DELETE /api/v1/config/dictionaries/{dict_code}/entries/{entry_id}/
```

---

### 2.16 通知模块 `/api/v1/notifications/`

#### 2.16.1 获取通知列表

```
GET /api/v1/notifications/
```

**查询参数**: `filter=is_read__eq=false`、`filter=type__eq=task_assigned`。

#### 2.16.2 获取单个通知

```
GET /api/v1/notifications/{id}/
```

#### 2.16.3 创建通知 (服务端内部调用)

```
POST /api/v1/notifications/
```

#### 2.16.4 标记已读

```
POST /api/v1/notifications/actions/mark-read/
```

**请求体** (全部标记为已读):
```json
{}
```

或带 `ids`:
```json
{
  "ids": [101, 102, 103]
}
```

#### 2.16.5 获取未读计数

```
GET /api/v1/notifications/actions/unread-count/
```

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "unread_count": 7
  }
}
```

---

### 2.17 统计模块 `/api/v1/statistics/`

#### 2.17.1 委托统计

```
GET /api/v1/statistics/orders/
```

**查询参数**:
| 参数 | 必须 | 说明 |
|------|------|------|
| `start_date` | 是 | 起始日期 YYYY-MM-DD |
| `end_date` | 是 | 截止日期 YYYY-MM-DD |
| `group_by` | 否 | `day` / `week` / `month` / `status` / `order_type` |

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "period": {"start_date": "2025-06-01", "end_date": "2025-06-30"},
    "summary": {
      "total": 45,
      "registered": 5,
      "in_progress": 20,
      "completed": 18,
      "rejected": 2
    },
    "trend": [
      {"date": "2025-06-01", "count": 3},
      {"date": "2025-06-02", "count": 5}
    ],
    "by_type": [
      {"type": "construction", "count": 30},
      {"type": "acceptance", "count": 15}
    ]
  }
}
```

#### 2.17.2 样品统计

```
GET /api/v1/statistics/samples/
```

#### 2.17.3 检测任务统计

```
GET /api/v1/statistics/test-tasks/
```

#### 2.17.4 人员工作量统计

```
GET /api/v1/statistics/workload/
```

**查询参数**: `start_date=2025-06-01&end_date=2025-06-30&group_by=user`。

**响应** (200):
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "period": {"start_date": "2025-06-01", "end_date": "2025-06-30"},
    "workload": [
      {
        "user_id": 15,
        "display_name": "赵六",
        "tasks_completed": 28,
        "tasks_pending": 5,
        "reports_created": 12,
        "avg_turnaround_hours": 18.5
      }
    ]
  }
}
```

#### 2.17.5 设备使用率统计

```
GET /api/v1/statistics/equipment-usage/
```

#### 2.17.6 财务报表统计

```
GET /api/v1/statistics/financial/
```

---

## 3. WebSocket 接口

### 3.1 实时通知推送

```
/ws/notifications/
```

**连接要求**: URL query 附加 `?token=<jwt_token>`。

**服务端推送消息格式**:
```json
{
  "type": "notification",
  "data": {
    "id": 201,
    "type": "task_assigned",
    "title": "新检测任务已分配",
    "body": "您有一个新的混凝土抗压强度检测任务，请在系统中查看",
    "target_url": "/test-tasks/301",
    "created_at": "2025-06-15T10:00:00Z"
  }
}
```

**支持的 `type` 值**:

| type | 说明 |
|------|------|
| `notification` | 新通知 |
| `heartbeat` | 心跳包，每 30 秒一次：`{"type": "heartbeat"}` |
| `error` | 连接错误：`{"type": "error", "data": {"code": 4001, "message": "Token expired"}}` |

**客户端可发送**:
```json
{"type": "ping"}
```

**心跳超时**: 60 秒无消息则服务端自动断开连接。

### 3.2 仪器实时数据流

```
/ws/instrument/{equipment_id}/
```

**连接要求**: `?token=<jwt_token>`，path 参数 `equipment_id` 指定仪器编号。

**服务端推送**:
```json
{
  "type": "reading",
  "data": {
    "equipment_id": 8,
    "equipment_code": "EQ-YL-001",
    "timestamp": "2025-06-15T10:05:32.123Z",
    "channels": [
      {"name": "荷载", "value": 685.32, "unit": "kN"},
      {"name": "位移", "value": 0.085, "unit": "mm"}
    ],
    "status": "running"
  }
}
```

**推送频率**: 约 5 Hz（每 200ms）。若连接带宽不足自动降频至 1 Hz。

**客户端可发送**:
```json
{"type": "subscribe", "data": {"channels": ["荷载", "位移"]}}
```
```json
{"type": "unsubscribe", "data": {"channels": ["位移"]}}
```

---

## 4. GraphQL 查询

复杂统计报表通过 GraphQL 端点获取，支持灵活组合查询条件、嵌套聚合。

### 4.1 入口

```
/api/v1/graphql/          (POST)
/api/v1/graphql/          (GET，开发用，带 GraphiQL)
```

### 4.2 Schema 定义

```graphql
"""
LIMS 统计查询根节点
"""
type Query {
  # ---- 委托 ----
  orderStats(
    startDate: Date!
    endDate: Date!
    groupBy: OrderGroupBy
    clientIds: [ID!]
    status: OrderStatus
  ): OrderStatsResult!

  # ---- 样品 ----
  sampleStats(
    startDate: Date!
    endDate: Date!
    groupBy: SampleGroupBy
  ): SampleStatsResult!

  # ---- 检测报告 ----
  reportStats(
    startDate: Date!
    endDate: Date!
  ): ReportStatsResult!

  # ---- 人员工作量 ----
  userWorkload(
    startDate: Date!
    endDate: Date!
    userIds: [ID!]
  ): UserWorkloadResult!

  # ---- 设备使用率 ----
  equipmentUsage(
    startDate: Date!
    endDate: Date!
    equipmentIds: [ID!]
  ): EquipmentUsageResult!

  # ---- 财务 ----
  financialStats(
    startDate: Date!
    endDate: Date!
    groupBy: FinancialGroupBy
  ): FinancialStatsResult!
}
```

### 4.3 类型定义

```graphql
"""
委托统计结果
"""
type OrderStatsResult {
  summary: OrderSummary!
  trend: [DateGroupedValue!]!
  byType: [CategoryGroupedValue!]!
  byClient: [CategoryGroupedValue!]!
}

type OrderSummary {
  total: Int!
  registered: Int!
  inProgress: Int!
  completed: Int!
  rejected: Int!
}

type DateGroupedValue {
  date: Date!
  count: Int!
  amount: Float!
}

type CategoryGroupedValue {
  category: String!
  count: Int!
  amount: Float!
}

"""
人员工作量
"""
type UserWorkloadResult {
  users: [UserWorkload!]!
}

type UserWorkload {
  userId: ID!
  displayName: String!
  tasksCompleted: Int!
  tasksPending: Int!
  tasksInProgress: Int!
  reportsCreated: Int!
  reportsReviewed: Int!
  avgTurnaroundHours: Float!
}

"""
设备使用率
"""
type EquipmentUsageResult {
  equipment: [EquipmentUsage!]!
}

type EquipmentUsage {
  equipmentId: ID!
  equipmentCode: String!
  equipmentName: String!
  totalHours: Float!
  activeHours: Float!
  usageRate: Float!
  idleHours: Float!
  maintenanceHours: Float!
}

"""
财务报表
"""
type FinancialStatsResult {
  totalRevenue: Float!
  totalInvoiced: Float!
  totalPaid: Float!
  totalUnpaid: Float!
  trend: [DateGroupedValue!]!
  byClient: [CategoryGroupedValue!]!
  paymentRate: Float!
}

scalar Date
scalar DateTime
```

### 4.4 查询示例

**查询月度委托趋势**:
```graphql
query MonthlyOrderStats {
  orderStats(
    startDate: "2025-06-01"
    endDate: "2025-06-30"
    groupBy: DAY
  ) {
    summary {
      total
      completed
      rejected
    }
    trend {
      date
      count
    }
  }
}
```

**查询指定人员工作量**:
```graphql
query UserWorkload {
  userWorkload(
    startDate: "2025-06-01"
    endDate: "2025-06-30"
    userIds: [12, 15]
  ) {
    users {
      userId
      displayName
      tasksCompleted
      tasksPending
      reportsCreated
      avgTurnaroundHours
    }
  }
}
```

**仪表盘全量查询**:
```graphql
query DashboardSummary {
  orderStats(startDate: "2025-06-01", endDate: "2025-06-30") {
    summary { total inProgress completed }
    byType { category count amount }
  }
  userWorkload(startDate: "2025-06-01", endDate: "2025-06-30") {
    users { displayName tasksCompleted avgTurnaroundHours }
  }
  financialStats(startDate: "2025-06-01", endDate: "2025-06-30") {
    totalRevenue totalPaid paymentRate
  }
  equipmentUsage(startDate: "2025-06-01", endDate: "2025-06-30") {
    equipment { equipmentCode usageRate totalHours }
  }
}
```

### 4.5 GraphQL 限流

| 指标 | 限制 |
|------|------|
| 单次查询深度 | 最大 10 层 |
| 单次请求复杂度 | 最大 500 |
| 请求频率 | 100 req/min |
| 超时 | 30 秒 |

---

## 5. 权限矩阵

| 端点 | 方法 | 最小权限 | 说明 |
|------|------|----------|------|
| `/api/v1/auth/login/` | POST | — | 匿名公开 |
| `/api/v1/auth/logout/` | POST | `auth.logout` | 需认证 |
| `/api/v1/auth/refresh/` | POST | — | 匿名（refresh token） |
| `/api/v1/auth/change-password/` | POST | `auth.change_password` | 修改自身密码 |
| `/api/v1/users/` | GET | `user.read` | 仅管理员可查全部 |
| `/api/v1/users/` | POST | `user.create` | 管理员 |
| `/api/v1/users/{id}/` | PATCH | `user.update` | 可修改其他用户信息 |
| `/api/v1/users/{id}/` | DELETE | `admin` | 仅超级管理员 |
| `/api/v1/users/actions/bulk-import/` | POST | `admin` | 仅超级管理员 |
| `/api/v1/roles/` | GET | `role.read` | |
| `/api/v1/roles/` | POST | `admin` | |
| `/api/v1/roles/{id}/actions/assign-permissions/` | POST | `admin` | |
| `/api/v1/orders/` | GET | `order.read` | 普通用户仅看本人创建 |
| `/api/v1/orders/` | POST | `order.create` | |
| `/api/v1/orders/{id}/` | PATCH | `order.update` | |
| `/api/v1/orders/{id}/` | DELETE | `order.delete` | |
| `/api/v1/orders/{id}/actions/submit/` | POST | `order.submit` | |
| `/api/v1/orders/{id}/actions/review/` | POST | `order.review` | 审核人角色 |
| `/api/v1/samples/` | GET | `sample.read` | |
| `/api/v1/samples/` | POST | `sample.create` | |
| `/api/v1/samples/{id}/` | PATCH | `sample.update` | |
| `/api/v1/samples/{id}/` | DELETE | `sample.delete` | |
| `/api/v1/samples/{id}/actions/generate-barcode/` | POST | `sample.update` | |
| `/api/v1/samples/{id}/actions/update-status/` | PATCH | `sample.update` | |
| `/api/v1/samples/{id}/trace/` | GET | `sample.read` | |
| `/api/v1/test-tasks/` | GET | `test_task.read` | 仅看自己任务 |
| `/api/v1/test-tasks/` | POST | `test_task.create` | |
| `/api/v1/test-tasks/{id}/` | PATCH | `test_task.update` | |
| `/api/v1/test-tasks/{id}/actions/assign/` | POST | `test_task.assign` | 负责人分配 |
| `/api/v1/test-tasks/{id}/actions/start/` | POST | `test_task.execute` | 仅被分配人 |
| `/api/v1/test-tasks/{id}/actions/submit/` | POST | `test_task.submit` | 仅被分配人 |
| `/api/v1/test-tasks/{id}/actions/retract/` | POST | `test_task.retract` | 仅被分配人 |
| `/api/v1/test-methods/` | GET | `test_method.read` | |
| `/api/v1/test-methods/` | POST | `admin` | |
| `/api/v1/test-methods/{id}/` | PATCH | `admin` | |
| `/api/v1/test-results/{task_id}/` | GET | `test_result.read` | |
| `/api/v1/test-results/` | POST | `test_result.create` | |
| `/api/v1/test-results/{task_id}/` | PATCH | `test_result.update` | |
| `/api/v1/test-results/{task_id}/actions/recalculate/` | POST | `test_result.update` | |
| `/api/v1/reports/` | GET | `report.read` | |
| `/api/v1/reports/` | POST | `report.create` | |
| `/api/v1/reports/{id}/` | PATCH | `report.update` | 仅编制人 |
| `/api/v1/reports/{id}/actions/submit-for-review/` | POST | `report.submit` | |
| `/api/v1/reports/{id}/actions/review/` | POST | `report.review` | 审核人角色 |
| `/api/v1/reports/{id}/actions/approve/` | POST | `report.approve` | 批准人角色 |
| `/api/v1/reports/{id}/actions/sign/` | POST | `report.sign` | 签发人角色 |
| `/api/v1/reports/{id}/download/` | GET | `report.read` | |
| `/api/v1/reports/{id}/actions/regenerate/` | POST | `report.create` | |
| `/api/v1/equipment/` | GET | `equipment.read` | |
| `/api/v1/equipment/` | POST | `equipment.create` | |
| `/api/v1/equipment/{id}/` | PATCH | `equipment.update` | |
| `/api/v1/equipment/{id}/` | DELETE | `admin` | |
| `/api/v1/equipment/{id}/actions/calibrate/` | POST | `equipment.calibrate` | |
| `/api/v1/equipment/{id}/actions/maintenance/` | POST | `equipment.maintenance` | |
| `/api/v1/equipment/{id}/usage-logs/` | GET | `equipment.read` | |
| `/api/v1/workflows/` | GET | `workflow.read` | |
| `/api/v1/workflows/` | POST | `admin` | |
| `/api/v1/workflows/{id}/` | PATCH | `admin` | |
| `/api/v1/workflows/instances/` | GET | `workflow.read` | |
| `/api/v1/workflows/instances/{instance_id}/actions/transition/` | POST | 由 transition 定义中 required_permissions 决定 | |
| `/api/v1/pricing/` | GET | `pricing.read` | |
| `/api/v1/pricing/` | POST | `pricing.manage` | |
| `/api/v1/pricing/{id}/` | PATCH | `pricing.manage` | |
| `/api/v1/pricing/{id}/` | DELETE | `pricing.manage` | |
| `/api/v1/pricing/actions/calculate/` | POST | `pricing.read` | |
| `/api/v1/invoices/` | GET | `invoice.read` | 仅看本人权限涉及订单 |
| `/api/v1/invoices/` | POST | `invoice.create` | |
| `/api/v1/invoices/{id}/` | PATCH | `invoice.update` | |
| `/api/v1/invoices/{id}/` | DELETE | `invoice.manage` | |
| `/api/v1/invoices/{id}/actions/record-payment/` | POST | `invoice.manage` | |
| `/api/v1/invoices/{id}/payment-records/` | GET | `invoice.read` | |
| `/api/v1/standards/` | GET | `standard.read` | |
| `/api/v1/standards/` | POST | `admin` | |
| `/api/v1/standards/{id}/` | PATCH | `admin` | |
| `/api/v1/standards/{id}/actions/repeal/` | POST | `admin` | |
| `/api/v1/config/` | GET | `config.read` | |
| `/api/v1/config/{key}/` | PATCH | `admin` | |
| `/api/v1/config/dictionaries/` | GET | `config.read` | |
| `/api/v1/config/dictionaries/{dict_code}/entries/` | POST | `admin` | |
| `/api/v1/notifications/` | GET | `notification.read` | 仅查本人 |
| `/api/v1/notifications/actions/mark-read/` | POST | — | 标记本人通知 |
| `/api/v1/notifications/actions/unread-count/` | GET | — | |
| `/api/v1/statistics/orders/` | GET | `statistics.read` | |
| `/api/v1/statistics/samples/` | GET | `statistics.read` | |
| `/api/v1/statistics/test-tasks/` | GET | `statistics.read` | |
| `/api/v1/statistics/workload/` | GET | `statistics.workload` | 管理员 |
| `/api/v1/statistics/equipment-usage/` | GET | `statistics.read` | |
| `/api/v1/statistics/financial/` | GET | `statistics.financial` | |
| `/api/v1/graphql/` | POST | `graphql.query` | 权限由查询字段级别检查 |

---

## 6. API 版本管理策略

### 6.1 当前版本

```
/api/v1/...
```

v1 为当前稳定版本，处于 **Active 阶段**。

### 6.2 版本号演进规则

| 变更类型 | 版本策略 | 说明 |
|----------|----------|------|
| 新增非破坏性端点 | 同版本追加 | 加端点、加可选字段，不需新 v 号 |
| 新增可选字段 | 同版本 | 向后兼容 |
| 字段作废（已有客户端使用） | 新主版本 | v1 → v2 |
| 端点 URL 变更 | 新主版本 | v1 → v2 |
| 字段语义变更 | 新主版本 | v1 → v2 |
| 认证方式变更 | 新主版本 | v1 → v2 |

### 6.3 Migration 路径 (v1 → v2)

```
Phase 1 — 开发期 (v2 与 v1 并行运行)
  └ v2 端点上线，v1 不受影响
  └ Swagger 上 v1、v2 文档并存
  └ 时长: 2 个 Sprint

Phase 2 — 灰度期 (Deprecation Warning)
  └ v1 响应头加 X-API-Deprecation-Warning 和迁移指南 URL
  └ 日志中统计仍调用 v1 的客户端 IP/User-Agent
  └ 时长: 3 个月

Phase 3 — 冻结期 (v1 Read-Only)
  └ v1 端点保留 GET/查询能力，POST/PATCH/DELETE 返回 410 Gone
  └ 返回体附带 v2 迁移路径
  └ 时长: 1 个月

Phase 4 — 下线 (v1 Remove)
  └ v1 路由移除，返回 410 Gone
  └ 保留 /api/v1/schema 历史文档访问
```

### 6.4 客户端迁移指引

当 v2 上线时，响应头返回：

```
X-API-Version: v2
X-API-Deprecation-Warning: v1 will be removed on 2026-06-01. See https://docs.example.com/v2-migration
Link: </api/v2/schema/swagger-ui/>; rel="versioned-docs"
```

### 6.5 向后兼容原则

- **新增字段**永远附加到响应体，不删除已有字段
- **删除字段**需经一个完整的 Deprecation 周期
- **枚举值新增**向后兼容，删除或重命名需 v+1
- **查询参数**新增可选参数不影响现有调用

---

## 附录 A. OpenAPI / Swagger 自动化

本项目通过 `drf-spectacular` 自动生成 OpenAPI 3.0.3 规范文档：

| 端点 | 用途 |
|------|------|
| `GET /api/v1/schema/` | OpenAPI JSON 描述文件 |
| `GET /api/v1/swagger.yaml` | OpenAPI YAML 描述文件 |
| `GET /api/v1/swagger/ui/` | Swagger UI 交互式文档 |
| `GET /api/v1/redoc/` | ReDoc 静态文档 |

自动生成内容包括：
- 所有端点的请求/响应 schema
- JWT 认证安全方案（securityScheme: `bearerAuth`, type: `http`, scheme: `bearer`, bearerFormat: `JWT`）
- 错误响应 schema
- 端点分组（按 app / tag）
- 自定义示例值（通过 `@extend_schema` 装饰器注解）

客户端代码生成命令：
```bash
# TypeScript (axios)
openapi-generator-cli generate -i http://localhost:8000/api/v1/schema/ -g typescript-axios -o ./generated-api-client

# Python
openapi-generator-cli generate -i http://localhost:8000/api/v1/schema/ -g python -o ./generated-python-client
```

---

## 附录 B. 通用 Schema 定义

### B.1 通用错误响应 Schema

```json
{
  "type": "object",
  "properties": {
    "code": { "type": "integer", "example": 40010 },
    "message": { "type": "string", "example": "参数校验失败" },
    "detail": { "type": "string", "example": "详细信息" },
    "field_errors": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "field": { "type": "string" },
          "message": { "type": "string" }
        }
      }
    },
    "request_id": { "type": "string", "format": "uuid" },
    "timestamp": { "type": "string", "format": "date-time" }
  },
  "required": ["code", "message", "timestamp"]
}
```

### B.2 通用分页 Schema

```json
{
  "type": "object",
  "properties": {
    "items": { "type": "array", "items": {} },
    "next_cursor": { "type": "string", "nullable": true },
    "has_more": { "type": "boolean" },
    "total": { "type": "integer" }
  },
  "required": ["items", "next_cursor", "has_more", "total"]
}
```

### B.3 通用列表响应 Schema

```json
{
  "type": "object",
  "properties": {
    "code": { "type": "integer" },
    "message": { "type": "string" },
    "data": { "$ref": "#/components/schemas/PaginatedResponse" }
  }
}
```

---

# 第五部分: 部署与运维

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

---

# 第六部分: 附录

# 附录

> LIMS v1 — 建筑工程材料检测实验室信息管理系统
> 本文档汇总系统开发所需的全部参考数据、合规清单、标准列表与执行建议。

---

## 目录

- [附录 A: GB/T 8170 数值修约规则速查表](#附录-a-gbt-8170-数值修约规则速查表)
- [附录 B: CMA/CNAS 合规检查清单](#附录-b-cmacnas-合规检查清单)
- [附录 C: 建设材料检测标准清单](#附录-c-建设材料检测标准清单)
- [附录 D: 术语表](#附录-d-术语表)
- [附录 E: 第三方仪器通信协议参考](#附录-e-第三方仪器通信协议参考)
- [附录 F: 项目执行建议](#附录-f-项目执行建议)

---

## 附录 A: GB/T 8170 数值修约规则速查表

### A.1 "四舍六入五成双" 完整规则

GB/T 8170-2008《数值修约规则与极限数值的表示和判定》采用**修约间隔**概念，规定以下修约规则（俗称"四舍六入五成双"或"银行家舍入"）：

| 情形 | 规则 | 示例（修约间隔 0.1） |
|------|------|---------------------|
| 拟舍弃数字 < 5 | 舍去，保留位不变 | 12.34 → 12.3 |
| 拟舍弃数字 > 5 | 进一，保留位加 1 | 12.36 → 12.4 |
| 拟舍弃数字 = 5，且 5 后有非零数字 | 进一 | 12.351 → 12.4 |
| 拟舍弃数字 = 5，且 5 后全为 0（或无数字），保留位为**偶数** | 舍去 | 12.25 → 12.2 |
| 拟舍弃数字 = 5，且 5 后全为 0（或无数字），保留位为**奇数** | 进一 | 12.35 → 12.4 |

**口诀**：四舍、六入、五后非零则进、五后皆零看奇偶（奇进偶不进）。

### A.2 修约间隔定义

修约间隔（rounding interval）是指修约值的最小单位。修约到某一间隔时，修约后的数值必须为该间隔的整数倍。

| 修约间隔 | 含义 | 操作 | 示例 |
|---------|------|------|------|
| 0.1 | 修约至十分位（保留 1 位小数） | 除以 0.1 → 修约到整数 → 乘以 0.1 | 23.45 → 23.4 |
| 0.01 | 修约至百分位（保留 2 位小数） | 除以 0.01 → 修约到整数 → 乘以 0.01 | 23.456 → 23.46 |
| 1 | 修约至个位（整数） | 直接按规则修约 | 23.5 → 24 |
| 5 | 修约至 5 的倍数 | 除以 5 → 修约到整数 → 乘以 5 | 127 → 125 |
| 10 | 修约至 10 的倍数 | 除以 10 → 修约到整数 → 乘以 10 | 125 → 130 |

### A.3 建设材料常用修约规则对照表

| 检测项目 | 执行标准 | 修约间隔 | 修约至 | Python/DB 实现说明 |
|---------|---------|---------|--------|-------------------|
| 水泥抗折强度 | GB/T 17671-2021 | 0.1 MPa | 1 位小数 | `round_half_even(value, 0.1)` |
| 水泥抗压强度 | GB/T 17671-2021 | 0.1 MPa | 1 位小数 | `round_half_even(value, 0.1)` |
| 混凝土抗压强度 | GB/T 50081-2019 | 0.1 MPa | 1 位小数 | `round_half_even(value, 0.1)` |
| 混凝土抗折强度 | GB/T 50081-2019 | 0.1 MPa | 1 位小数 | `round_half_even(value, 0.1)` |
| 钢筋屈服强度 (ReL) | GB/T 228.1-2021 | 1 MPa | 整数 | `round_half_even(value, 1)` |
| 钢筋抗拉强度 (Rm) | GB/T 228.1-2021 | 1 MPa | 整数 | `round_half_even(value, 1)` |
| 钢筋断后伸长率 (A) | GB/T 228.1-2021 | 0.5% | 0.5 的倍数 | `round_half_even_to_multiple(value, 0.5)` |
| 钢筋最大力总伸长率 (Agt) | GB/T 228.1-2021 | 0.5% | 0.5 的倍数 | `round_half_even_to_multiple(value, 0.5)` |
| 砂含泥量 | GB/T 14684-2022 | 0.1% | 1 位小数 | `round_half_even(value, 0.1)` |
| 石含泥量 | GB/T 14685-2022 | 0.1% | 1 位小数 | `round_half_even(value, 0.1)` |
| 砂泥块含量 | GB/T 14684-2022 | 0.1% | 1 位小数 | `round_half_even(value, 0.1)` |
| 沥青针入度 | JTG E30-2011 T0604 | 0.1 mm (0.1 单位) | 1 位小数 | `round_half_even(value, 0.1)` |
| 沥青延度 | JTG E30-2011 T0605 | 1 cm | 整数 | `round_half_even(value, 1)` |
| 沥青软化点 | JTG E30-2011 T0606 | 0.5 °C | 0.5 的倍数 | `round_half_even_to_multiple(value, 0.5)` |
| 土工含水率 | GB/T 50123-2019 | 0.1% | 1 位小数 | `round_half_even(value, 0.1)` |
| 土的干密度 | GB/T 50123-2019 | 0.01 g/cm³ | 2 位小数 | `round_half_even(value, 0.01)` |
| 混凝土坍落度 | GB/T 50081-2019 | 1 mm | 整数（修约至 5mm） | `round_half_even_to_multiple(value, 5)` |
| 道路压实度 | JTG 3450-2019 | 0.1% | 1 位小数 | `round_half_even(value, 0.1)` |

### A.4 Python 实现

```python
# -*- coding: utf-8 -*-
"""
GB/T 8170-2008 数值修约规则实现
采用 Decimal 实现，避免浮点数精度问题。
"""

from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, InvalidOperation
from typing import Union


def round_half_even(value: Union[int, float, str], interval: Union[int, float, str]) -> Union[int, float]:
    """
    按 GB/T 8170 "四舍六入五成双" 规则修约到指定修约间隔。

    参数:
        value:     待修约的数值（int/float/str，推荐传入 str 或 Decimal 字符串形式避免浮点误差）
        interval:  修约间隔（1, 0.1, 0.01, 5, 10 等）

    返回:
        修约后的 float（若 interval >= 1 则返回 int）

    示例:
        >>> round_half_even('12.35', 0.1)   # 12.35 -> 12.4 (3是奇数，进)
        12.4
        >>> round_half_even('12.25', 0.1)   # 12.25 -> 12.2 (2是偶数，舍)
        12.2
        >>> round_half_even('12.34', 0.1)   # 12.34 -> 12.3 (<5，舍)
        12.3
        >>> round_half_even('12.36', 0.1)   # 12.36 -> 12.4 (>5，进)
        12.4
        >>> round_half_even('23.5', 1)      # 23.5 -> 24 (3是奇数，进)
        24
        >>> round_half_even('24.5', 1)      # 24.5 -> 24 (4是偶数，舍)
        24
    """
    d_value = Decimal(str(value))
    d_interval = Decimal(str(interval))

    # 计算需要保留的小数位数
    # Decimal.quantize() 的指数决定精度：0.1 -> '0.1', 0.01 -> '0.01', 1 -> '1'
    if d_interval >= 1:
        # 整数修约：quantize 到 1
        quantized = d_value.quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)
        return int(quantized)
    else:
        # 小数修约：quantize 到对应精度
        quantize_exp = Decimal(str(interval))
        quantized = d_value.quantize(quantize_exp, rounding=ROUND_HALF_EVEN)
        return float(quantized)


def round_half_even_to_multiple(value: Union[int, float, str], multiple: Union[int, float, str]) -> Union[int, float]:
    """
    按 GB/T 8170 规则修约到指定倍数（非十进制间隔），例如 0.5%、5mm 等。

    算法：value / multiple → 按 ROUND_HALF_EVEN 修约到整数 → × multiple

    参数:
        value:    待修约的数值
        multiple: 目标倍数（如 0.5, 5）

    返回:
        修约后的数值

    示例:
        >>> round_half_even_to_multiple('12.75', 0.5)   # 12.75 -> 13.0 (nearest 0.5, .75 rounds up)
        13.0
        >>> round_half_even_to_multiple('12.25', 0.5)   # 12.25 -> 12.5 (nearest 0.5, .25 rounds up)
        12.5
        >>> round_half_even_to_multiple('123', 5)       # 123 -> 125 (nearest 5)
        125
        >>> round_half_even_to_multiple('122', 5)       # 122 -> 120 (nearest 5)
        120
    """
    d_value = Decimal(str(value))
    d_multiple = Decimal(str(multiple))
    ratio = d_value / d_multiple
    ratio_rounded = ratio.quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)
    result = ratio_rounded * d_multiple
    if d_multiple >= 1:
        return int(result)
    return float(result)


def gbt8170_round(value: Union[int, float, str], spec: dict) -> Union[int, float]:
    """
    通用的 GB/T 8170 修约函数，根据 spec 字典自动选择修约策略。

    spec 格式：
        {'type': 'interval', 'value': 0.1}          <- 十进制修约间隔
        {'type': 'multiple', 'value': 0.5}          <- 倍数修约

    示例:
        >>> gbt8170_round('12.35', {'type': 'interval', 'value': 0.1})
        12.4
        >>> gbt8170_round('12.75', {'type': 'multiple', 'value': 0.5})
        13.0
    """
    if spec['type'] == 'interval':
        return round_half_even(value, spec['value'])
    elif spec['type'] == 'multiple':
        return round_half_even_to_multiple(value, spec['value'])
    else:
        raise ValueError(f"不支持的修约类型: {spec['type']}")
```

### A.5 PostgreSQL 存储过程实现

```sql
-- ============================================================
-- GB/T 8170-2008 数值修约函数 (PostgreSQL)
-- 使用 numeric 类型避免浮点精度问题
-- ============================================================

-- 1. 四舍六入五成双 — 十进制修约间隔版
CREATE OR REPLACE FUNCTION gbt8170_round(
    p_value numeric,
    p_interval numeric
)
RETURNS numeric
IMMUTABLE
LANGUAGE plpgsql
AS $$
DECLARE
    v_scaled numeric;
    v_rounded numeric;
    v_result numeric;
BEGIN
    IF p_interval IS NULL OR p_value IS NULL THEN
        RETURN NULL;
    END IF;

    IF p_interval = 0 THEN
        RAISE EXCEPTION '修约间隔不能为 0';
    END IF;

    -- 缩放：value / interval → 四舍五入到整数 → × interval
    v_scaled := p_value / p_interval;

    -- round(x) 在 PostgreSQL 中对 numeric 类型使用 "四舍五入"
    -- 要实现 "四舍六入五成双"，需要手动判断。
    -- 这里利用 numeric/round 组合 + 手动奇偶判断：

    v_rounded := floor(v_scaled);
    -- 计算小数部分
    IF (v_scaled - v_rounded) > 0.5 THEN
        -- 大于 0.5，进一
        v_rounded := v_rounded + 1;
    ELSIF (v_scaled - v_rounded) < 0.5 THEN
        -- 小于 0.5，舍去 (v_rounded 不变)
        NULL;
    ELSE
        -- 恰好 0.5：看整数部分奇偶
        -- 奇数进，偶数舍
        IF mod(v_rounded, 2) = 1 OR mod(v_rounded, 2) = -1 THEN
            v_rounded := v_rounded + 1;
        END IF;
    END IF;

    v_result := v_rounded * p_interval;

    -- 根据 interval 决定最终精度
    IF p_interval >= 1 THEN
        RETURN round(v_result, 0);
    ELSE
        -- interval < 1 时，保留 log10(1/interval) 位小数
        RETURN round(v_result, abs(CAST(log(p_interval) AS integer)));
    END IF;
END;
$$;

-- 2. 倍数修约版（如 0.5%, 5mm）
CREATE OR REPLACE FUNCTION gbt8170_round_to_multiple(
    p_value numeric,
    p_multiple numeric
)
RETURNS numeric
IMMUTABLE
LANGUAGE plpgsql
AS $$
DECLARE
    v_ratio numeric;
    v_integer_part numeric;
    v_fraction numeric;
BEGIN
    IF p_multiple IS NULL OR p_value IS NULL THEN
        RETURN NULL;
    END IF;

    IF p_multiple = 0 THEN
        RAISE EXCEPTION '倍数不能为 0';
    END IF;

    v_ratio := p_value / p_multiple;
    v_integer_part := floor(v_ratio);
    v_fraction := v_ratio - v_integer_part;

    IF v_fraction > 0.5 THEN
        v_integer_part := v_integer_part + 1;
    ELSIF v_fraction = 0.5 THEN
        IF mod(v_integer_part, 2) = 1 OR mod(v_integer_part, 2) = -1 THEN
            v_integer_part := v_integer_part + 1;
        END IF;
    END IF;

    RETURN v_integer_part * p_multiple;
END;
$$;

-- ============================================================
-- 使用示例
-- ============================================================

-- 水泥抗压强度: 56.75 MPa → 修约到 0.1 → 56.8
-- SELECT gbt8170_round(56.75, 0.1);

-- 钢筋屈服强度: 402.5 MPa → 修约到 1 → 402 (偶数舍)
-- SELECT gbt8170_round(402.5, 1);

-- 钢筋屈服强度: 403.5 MPa → 修约到 1 → 404 (奇数进)
-- SELECT gbt8170_round(403.5, 1);

-- 钢筋伸长率: 25.75% → 修约到 0.5% 的倍数 → 26.0
-- SELECT gbt8170_round_to_multiple(25.75, 0.5);

-- 混凝土坍落度: 148mm → 修约到 5mm → 150
-- SELECT gbt8170_round_to_multiple(148, 5);
```

---

## 附录 B: CMA/CNAS 合规检查清单

### B.1 CMA 合规检查清单

依据：《检验检测机构资质认定能力评价 检验检测机构通用要求》（RB/T 214-2017）

| 要求编号 | 要求内容 | LIMS 对应功能 | 验收步骤 |
|---------|---------|-------------|---------|
| 4.1.1 | 机构应建立并保持管理体系 | 系统内置标准操作程序(SOP)管理模块；支持体系文件版本控制、审批流程、发布/召回机制 | 1) 上传 SOP 文件，验证版本递增<br>2) 触发审批流，确认多级审批<br>3) 验证旧版本自动标记"已失效" |
| 4.1.2 | 公正性和保密性 | 数据访问权限基于 RBAC；敏感操作审计日志；数据脱敏导出 | 1) 用户 B 尝试访问用户 A 的委托数据，确认拒绝<br>2) 导出报告检查脱敏字段<br>3) 查看审计日志确认记录 |
| 4.2.1 | 人员资质管理 | 人员档案、资质证书有效期管理、上岗资格审批、授权签字人管理 | 1) 录入人员资质，设置到期提醒<br>2) 到期后验证系统自动禁用相关检测权限<br>3) 确认签字人授权列表可维护 |
| 4.2.2 | 人员培训和能力确认 | 培训计划管理、培训记录、能力验证记录 | 1) 创建培训计划并关联人员<br>2) 上传培训考核记录<br>3) 验证能力矩阵报表 |
| 4.3.1 | 设施和环境条件 | 检测环境（温湿度）记录与监控，超标预警 | 1) 模拟温湿度超标，验证告警<br>2) 查看环境记录历史曲线<br>3) 确认记录不可篡改 |
| 4.3.2 | 环境监控记录 | 环境数据采集、存储、报表 | 1) 手动录入环境数据<br>2) 导出环境月度报表<br>3) 验证数据与原始记录一致 |
| 4.4.1 | 设备管理 | 仪器设备台账、校准/检定计划、状态标识、使用记录 | 1) 录入仪器信息，设置校准到期日<br>2) 到期前 30 天验证提醒<br>3) 校准超期后验证系统标记"停用" |
| 4.4.2 | 设备校准和维护 | 校准证书管理、期间核查记录、维护保养记录 | 1) 上传校准证书，关联仪器<br>2) 录入期间核查结果<br>3) 验证校准有效性自动判断 |
| 4.4.3 | 设备溯源 | 量值溯源记录，计量确认 | 1) 查看仪器溯源链<br>2) 确认溯源信息包含标准器信息 |
| 4.5.1 | 标准方法确认 | 检测标准库管理、方法验证/确认记录 | 1) 维护检测标准库<br>2) 关联标准到检测项目<br>3) 验证标准更新后影响分析 |
| 4.5.2 | 非标方法确认 | 非标方法/自制方法审批与确认记录 | 1) 提交非标方法审批流程<br>2) 确认方法验证数据完整<br>3) 验证方法仅授权人员可使用 |
| 4.5.3 | 数据控制 | 原始数据记录、修约规则、计算公式、判定规则 | 1) 录入原始数据，验证自动修约<br>2) 确认计算公式可配置<br>3) 验证判定结果与标准一致 |
| 4.5.4 | 测量不确定度评定 | 不确定度计算模型、评定记录 | 1) 配置不确定度评定公式<br>2) 输入参数，验证计算结果<br>3) 导出不确定度评定报告 |
| 4.5.5 | 抽样管理 | 抽样计划、抽样记录、样品流转记录 | 1) 创建抽样任务<br>2) 录入抽样信息包括地点、方法<br>3) 验证样品唯一标识追踪 |
| 4.5.6 | 样品处置 | 样品接收、标识、流转、贮存、处置 | 1) 扫描样品条形码完成接收<br>2) 跟踪样品在各检测室流转<br>3) 确认到期样品处置提醒 |
| 4.5.7 | 结果质量控制 | 内部质量控制（盲样、平行样、加标回收）、外部能力验证 | 1) 创建质控计划<br>2) 录入质控样品检测结果<br>3) 验证质控图（如Xbar-R图）自动生成 |
| 4.5.8 | 结果报告 | 检测报告模板管理、自动编号、审批签发、电子签名 | 1) 生成检测报告，验证信息完整<br>2) 走审批流，确认多级审核<br>3) 验证报告修改后重出版本控制 |
| 4.5.9 | 记录管理 | 原始记录、报告副本、电子记录归档，保存期限 ≥ 6 年 | 1) 查询历史委托及报告<br>2) 验证记录只读归档<br>3) 确认保存期限可配置 |
| 4.8.1 | 管理体系内部审核 | 内审计划、内审记录、不符合项管理 | 1) 创建内审计划并关联条款<br>2) 录入不符合项<br>3) 跟踪纠正措施闭环 |
| 4.8.2 | 管理评审 | 管理评审计划、输入输出记录 | 1) 创建管理评审计划<br>2) 关联评审议题<br>3) 输出评审结论并跟踪 |
| 4.8.3 | 纠正措施与持续改进 | 不符合项管理、纠正措施跟踪、预防措施 | 1) 创建纠正措施任务<br>2) 跟踪整改进度<br>3) 验证预防措施的提出与实施 |

### B.2 CNAS 合规检查清单

依据：CNAS-CL01:2018《检测和校准实验室能力认可准则》（等同采用 ISO/IEC 17025:2017）

| 要求编号 | 要求内容 | LIMS 对应功能 | 验收步骤 |
|---------|---------|-------------|---------|
| 5.2 | 人员 | 人员能力矩阵、授权范围管理、监督记录 | 1) 查看人员授权范围列表<br>2) 验证操作超出权限时被阻止<br>3) 监督记录可追溯 |
| 5.3 | 设施和环境条件 | 环境条件监控、偏离许可条件的处理记录 | 1) 录入环境条件要求<br>2) 验证偏离时自动标记检测记录<br>3) 导出偏离报告 |
| 5.4 | 设备 | 设备全生命周期管理、期间核查、偏离校准状态的检测控制 | 1) 超校准期仪器尝试录入数据，系统拒绝或标记<br>2) 查看设备期间核查计划执行率<br>3) 验证停用仪器状态全局可见 |
| 5.5 | 计量溯源性 | 量值溯源信息、标准物质管理 | 1) 查询标准物质证书信息<br>2) 验证标准物质有效期管理<br>3) 确认溯源信息可导出 |
| 5.6 | 外部提供的产品和服务 | 供应商/分包方管理、采购验收记录 | 1) 维护供应商信息及评价<br>2) 录入采购验收记录<br>3) 验证不合格供应商标记 |
| 5.7 | 要求、标书和合同的评审 | 委托评审记录、客户要求确认 | 1) 录入委托评审记录<br>2) 验证评审意见不可随意删除<br>3) 确认客户要求传达至检测环节 |
| 5.8 | 方法的选择、验证和确认 | 方法有效性验证、偏离审批方法偏离的审批和记录 | 1) 维护标准方法库（含方法编号、名称、版本）<br>2) 验证方法选择限制<br>3) 确认方法偏离需审批 |
| 5.9 | 抽样 | 抽样程序、抽样偏差记录 | 1) 抽样方案关联到委托<br>2) 抽样数据（时间、地点、方法）完整记录<br>3) 偏差记录不可删除 |
| 6.1 | 结果质量保证 | 质量控制计划、统计质量控制（控制图）、实验室间比对 | 1) 配置质控规则（如 Westgard 规则）<br>2) 质控数据超限报警并阻止报告发布<br>3) 质控图自动绘制 |
| 6.2 | 结果报告 | 报告格式、信息完整性、修改控制、电子报告安全 | 1) 验证报告包含所有必需信息（标题、唯一性标识、方法、结果、签名、日期）<br>2) 修改报告后生成新版本，旧版本保留<br>3) 电子报告 PDF/A 格式归档 |
| 7.1 | 不符合工作管理 | 不符合工作识别、隔离、处置、记录 | 1) 标记不符合工作（如质控失败）<br>2) 追溯评估影响范围<br>3) 记录处置决定 |
| 7.2 | 客户投诉 | 投诉接收、调查、处理、回复记录 | 1) 录入投诉并分配处理<br>2) 跟踪调查过程<br>3) 确认处理结果记录可追溯 |
| 7.3 | 数据控制和信息管理 | 电子数据完整性、信息管理系统验证、电子记录变更追踪 | 1) 数据修改保留审计追踪（谁、何时、改了什么、为什么）<br>2) 验证系统变更需经批准<br>3) 数据备份与恢复测试 |
| 7.8 | 结果报告（补充） | 报告中的测量不确定度声明 | 1) 报告自动包含不确定度评估结果<br>2) 验证声明格式符合 CNAS 要求 |

### B.3 合规功能对照矩阵

| 要求来源 | 要求编号 | 要求类别 | LIMS 模块 | 合规状态 | 验证方式 |
|---------|---------|---------|----------|---------|---------|
| RB/T 214 | 4.1.1-4.1.2 | 组织与公正性 | 权限管理、审计日志 | ✅ 覆盖 | 渗透测试 + 权限穿透测试 |
| RB/T 214 | 4.2.1-4.2.2 | 人员管理 | 人员管理、培训管理 | ✅ 覆盖 | 功能测试 + 流程验证 |
| RB/T 214 | 4.3.1-4.3.2 | 环境条件 | 环境监控 | ✅ 覆盖 | 数据录入 + 告警验证 |
| RB/T 214 | 4.4 | 设备管理 | 仪器设备管理 | ✅ 覆盖 | 台账 CRUD + 状态自动化 |
| RB/T 214 | 4.5.1-4.5.3 | 方法和数据 | 标准管理、数据录入、修约 | ✅ 覆盖 | 修约测试 + 公式验证 |
| RB/T 214 | 4.5.4 | 不确定度 | 不确定度评定 | ✅ 覆盖 | 计算验证 + 报告导出 |
| RB/T 214 | 4.5.5-4.5.6 | 抽样和样品 | 样品管理 | ✅ 覆盖 | 追踪测试 + 状态流转 |
| RB/T 214 | 4.5.7 | 质量控制 | 质控管理 | ✅ 覆盖 | 质控图 + 规则验证 |
| RB/T 214 | 4.5.8-4.5.9 | 报告和记录 | 报告管理、档案管理 | ✅ 覆盖 | 报告完整性 + 归档测试 |
| RB/T 214 | 4.8 | 体系改进 | 内审、管理评审、纠正措施 | ✅ 覆盖 | 闭环流程验证 |
| CNAS-CL01 | 5.2-5.5 | 资源要求 | 人员、设备、计量 | ✅ 覆盖 | 综合流程验证 |
| CNAS-CL01 | 5.6-5.9 | 过程要求 | 采购、评审、方法、抽样 | ✅ 覆盖 | 端到端流程测试 |
| CNAS-CL01 | 6 | 管理体系要求 | 质控、结果保证 | ✅ 覆盖 | 质控规则验证 |
| CNAS-CL01 | 7.1-7.3 | 不符合和数据 | 纠正措施、数据完整性 | ✅ 覆盖 | 审计追踪 + 数据完整性 |
| CNAS-CL01 | 7.8 | 结果报告 | 报告管理 | ✅ 覆盖 | 报告模板 + 格式验证 |

### B.4 关键合规注意事项

**数据完整性（ALCOA+ 原则）**：
- **Attributable（可归属）**：每条数据记录关联到具体操作人
- **Legible（清晰可读）**：数据永久可读，不依赖特定软件版本
- **Contemporaneous（同步记录）**：检测数据实时采集，不可事后伪造
- **Original（原始）**：保留原始数据副本，修改不覆盖原文
- **Accurate（准确）**：数据自动修约，避免人工修约错误
- **+ 完整、一致、持久、可用**

**电子签名合规**：
- 采用符合《中华人民共和国电子签名法》要求的可靠电子签名
- 授权签字人的电子签名绑定唯一数字证书
- 签名后文档内容变更自动使签名失效

**审计追踪**：
- 所有数据的**创建、修改、删除**均记录审计日志
- 审计日志包含：操作人、操作时间、操作内容、修改前值、修改后值、修改原因
- 审计日志**不可修改、不可删除**

---

## 附录 C: 建设材料检测标准清单

### C.1 钢材 / 金属

| 标准编号 | 标准名称 | 检测项目 | 备注 |
|---------|---------|---------|------|
| GB/T 228.1-2021 | 金属材料 拉伸试验 第 1 部分：室温试验方法 | 屈服强度、抗拉强度、断后伸长率、最大力总伸长率 | 核心标准，替代 2010 版 |
| GB/T 232-2010 | 金属材料 弯曲试验方法 | 弯曲性能 | 适用于钢筋、型钢弯曲 |
| GB/T 239-2012 | 金属材料 线材 反复弯曲试验方法 | 反复弯曲性能 | 适用于钢丝、钢绞线 |
| GB/T 5224-2014 | 预应力混凝土用钢绞线 | 钢绞线力学性能 | 预应力工程专用 |
| GB/T 1499.1-2017 | 钢筋混凝土用钢 第 1 部分：热轧光圆钢筋 | HPB300 等光圆钢筋力学、工艺性能 | - |
| GB/T 1499.2-2018 | 钢筋混凝土用钢 第 2 部分：热轧带肋钢筋 | HRB400/HRB500 等带肋钢筋力学、重量偏差 | 核心钢筋标准 |
| GB/T 13788-2017 | 冷轧带肋钢筋 | CRB550/CRB650 等冷轧钢筋 | 冷轧薄壁构件 |
| GB/T 21839-2019 | 金属材料 拉伸试验 第 2 部分：高温试验方法 | 高温拉伸 | 特殊用途 |
| GB/T 11263-2017 | H 型钢和剖分 T 型钢 | H 型钢尺寸、外形、重量及允许偏差 | 钢结构用 |
| YB/T 081-2013 | 钢材力学及工艺性能试验取样规定 | 取样方法、取样数量 | 取样依据 |

### C.2 水泥

| 标准编号 | 标准名称 | 检测项目 | 备注 |
|---------|---------|---------|------|
| GB 175-2007 | 通用硅酸盐水泥 | 化学指标、物理指标（凝结时间、安定性、强度等） | 核心水泥标准，有第 1-3 号修改单 |
| GB/T 17671-2021 | 水泥胶砂强度检验方法（ISO 法） | 抗折强度、抗压强度 | 替代 1999 版 |
| GB/T 1346-2011 | 水泥标准稠度用水量、凝结时间、安定性检验方法 | 标准稠度用水量、初凝/终凝时间、安定性 | - |
| GB/T 8074-2008 | 水泥比表面积测定方法 勃氏法 | 比表面积 | - |
| GB/T 2419-2005 | 水泥胶砂流动度测定方法 | 胶砂流动度 | - |
| GB/T 176-2017 | 水泥化学分析方法 | 氧化钙、氧化镁、三氧化硫等化学成分 | - |
| GB/T 750-1992 | 水泥压蒸安定性试验方法 | 压蒸安定性 | - |

### C.3 集料（砂、石）

| 标准编号 | 标准名称 | 检测项目 | 备注 |
|---------|---------|---------|------|
| GB/T 14684-2022 | 建设用砂 | 颗粒级配、含泥量、泥块含量、表观密度、堆积密度、压碎指标等 | 替代 2011 版 |
| GB/T 14685-2022 | 建设用卵石、碎石 | 颗粒级配、含泥量、泥块含量、针片状颗粒、压碎指标等 | 替代 2011 版 |
| JGJ 52-2006 | 普通混凝土用砂、石质量及检验方法标准 | 砂、石质量要求及检验方法 | 行业标准 |
| GB/T 14684-2022 | 建设用砂 | 机制砂亚甲蓝值 | 替代 2011 版 |
| JG/T 486-2015 | 混凝土用复合掺合料 | 掺合料性能 | - |

### C.4 混凝土 / 砂浆

| 标准编号 | 标准名称 | 检测项目 | 备注 |
|---------|---------|---------|------|
| GB/T 50081-2019 | 混凝土物理力学性能试验方法标准 | 抗压强度、抗折强度、轴心抗压、弹性模量、收缩、徐变 | 核心混凝土试验方法 |
| GB 50010-2010 | 混凝土结构设计规范（2015 年版） | 混凝土强度等级、设计指标 | 设计规范，非试验方法 |
| GB/T 50080-2016 | 普通混凝土拌合物性能试验方法标准 | 坍落度、扩展度、含气量、凝结时间等 | 新拌混凝土性能 |
| GB/T 50082-2024 | 普通混凝土长期性能和耐久性能试验方法标准 | 抗渗、抗冻、抗硫酸盐、碳化、收缩等 | 耐久性试验 |
| GB/T 50083-2014 | 混凝土结构设计规范 | 结构耐久性设计 | - |
| JGJ/T 70-2009 | 建筑砂浆基本性能试验方法标准 | 砂浆稠度、保水性、抗压强度、拉伸粘结强度 | 砂浆检测 |
| JGJ 55-2011 | 普通混凝土配合比设计规程 | 配合比设计 | 设计规程 |
| GB/T 50081-2019 | 混凝土物理力学性能试验方法标准 | 抗弯拉强度、劈裂抗拉强度 | 替代 2002 版 |
| GB/T 50082-2024 | 普通混凝土长期性能和耐久性试验方法标准 | 抗渗等级、抗冻等级、抗氯离子渗透 | 替代 2009 版 |

### C.5 沥青及沥青混合料

| 标准编号 | 标准名称 | 检测项目 | 备注 |
|---------|---------|---------|------|
| JTG E20-2011 | 公路工程沥青及沥青混合料试验规程 | 针入度、延度、软化点、密度、粘度、闪点、溶解度等全部沥青性能 | 公路行业核心标准 |
| GB/T 15180-2010 | 重交通道路石油沥青 | 沥青产品技术要求 | 产品标准 |
| JTG F40-2004 | 公路沥青路面施工技术规范 | 沥青混合料配合比设计、施工质量控制 | 施工规范 |
| JTG/T 3240-2017 | 公路沥青路面再生技术规范 | 再生沥青混合料性能 | - |
| GB/T 26941-2011 | 隔离栅 | 隔离栅性能 | 交通安全设施 |

### C.6 土工 / 地基

| 标准编号 | 标准名称 | 检测项目 | 备注 |
|---------|---------|---------|------|
| GB/T 50123-2019 | 土工试验方法标准 | 含水率、密度、界限含水率、颗粒分析、击实、压缩、剪切、渗透等 | 核心土工试验标准 |
| GB/T 50123-2019 | 土工试验方法标准 | 无侧限抗压强度、回弹模量 | - |
| JTG 3430-2020 | 公路土工试验规程 | 含水率、密度、颗粒分析、界限含水率、击实、CBR、剪切等 | 公路行业土工标准 |
| JTG/T 3610-2019 | 公路路基施工技术规范 | 压实度、承载比（CBR）、回弹模量 | - |
| GB 50007-2011 | 建筑地基基础设计规范 | 地基承载力、变形模量 | 设计规范 |
| JGJ 79-2012 | 建筑地基处理技术规范 | 地基处理后的检测 | 处理规范 |

### C.7 道路工程

| 标准编号 | 标准名称 | 检测项目 | 备注 |
|---------|---------|---------|------|
| JTG 3450-2019 | 公路路基路面现场测试规程 | 压实度、平整度、弯沉、构造深度、摩擦系数等现场检测 | 核心现场检测标准 |
| JTG F80/1-2017 | 公路工程质量检验评定标准 第一册 土建工程 | 分项、分部、单位工程质量评定 | 验收依据 |
| JTG F80/2-2017 | 公路工程质量检验评定标准 第二册 机电工程 | 机电工程质量评定 | - |
| GB/T 17181-2021 | 沥青路面压实度检测方法 | 压实度（核子密度仪法、灌砂法） | - |
| JTG E51-2009 | 公路工程无机结合料稳定材料试验规程 | 水泥/石灰稳定土无侧限抗压强度、配合比设计 | - |
| JTG E60-2008 | 公路路基路面现场测试规程 | 弯沉、平整度、渗水系数等 | 被 JTG 3450 部分替代 |

### C.8 防水材料

| 标准编号 | 标准名称 | 检测项目 | 备注 |
|---------|---------|---------|------|
| GB 18242-2008 | 弹性体改性沥青防水卷材 | 拉力、延伸率、不透水性、耐热度、低温柔性 | SBS 防水卷材 |
| GB 18243-2008 | 塑性体改性沥青防水卷材 | 同上 | APP 防水卷材 |
| GB 18967-2009 | 改性沥青聚乙烯胎防水卷材 | 同上（聚乙烯胎基） | - |
| GB/T 328 系列 | 建筑防水卷材试验方法 | 拉伸性能、不透水性、耐热性、低温柔性、尺寸稳定性等 | 共 27 个分册 |
| GB/T 16777-2008 | 建筑防水涂料试验方法 | 拉伸强度、断裂延伸率、固体含量、不透水性等 | 涂料类防水材料 |
| JC/T 1046-2007 | 坡屋面用高分子防水片材 | 高分子防水片材性能 | 坡屋面专用 |

---

## 附录 D: 术语表

### D.1 业务术语

| 中文 | 英文 | 释义 |
|------|------|------|
| 委托 | Commission / Request | 检测委托人向实验室提交检测任务的行为及对应记录 |
| 委托编号 | Commission Number | 唯一标识一次委托检测的编号，如 W2025-00001 |
| 样品 | Sample | 送检或抽样获取的被检测实物 |
| 样品编号 | Sample Number | 唯一标识一个检测样品的编号 |
| 检测任务 | Test Task / Test Order | 针对样品具体执行的一组检测项目 |
| 检测方法 | Test Method | 执行检测所依据的国家/行业/企业标准 |
| 检测项目 / 检测参数 | Test Item / Test Parameter | 检测的具体指标，如"抗压强度"、"屈服强度" |
| 原始记录 | Original Record | 检测过程中直接产生的、未经过加工的数据记录 |
| 检测报告 | Test Report | 根据检测原始数据编制的、对外出具的正式结果文件 |
| 授权签字人 | Authorized Signatory | 经认可机构批准，有权签发检测报告的技术人员 |
| 审核人 | Reviewer | 对检测数据和报告进行审核的技术人员 |
| 检验员 / 检测员 | Tester / Analyst | 执行具体检测操作的人员 |
| 质控样品 | Quality Control Sample | 用于验证检测结果准确性的标准样品或已知值样品 |
| 盲样 | Blind Sample | 检测员不知道真实值或来源的质控样品 |
| 平行样 | Duplicate Sample | 同一样品分割后同时检测的两个子样 |
| 加标回收 | Spike Recovery | 在已知样品中加入标准物质后复测，检验方法准确性 |
| 修约 | Rounding | 按 GB/T 8170 规则将数值舍入到指定精度 |
| 测量不确定度 | Measurement Uncertainty | 表征合理赋予被测量值分散性的非负参数 |
| 检出限 / 检测下限 | Limit of Detection (LOD) | 方法可检出的最低浓度或最小量 |
| 校准 | Calibration | 在规定条件下确定仪器示值与标准值之间关系的操作 |
| 检定 | Verification | 查明和确认计量器具是否符合法定要求的程序 |
| 量值溯源 | Metrological Traceability | 测量结果通过连续比较链与规定参考标准联系 |
| 标准物质 | Reference Material (RM) | 具有足够均匀和稳定特性的物质，用作校准或方法确认 |
| 期间核查 | Intermediate Check | 在两次校准之间，对仪器状态的确认检查 |
| 不符合工作 | Nonconforming Work | 不满足程序要求、标准规范或客户要求的检测活动或结果 |
| 能力验证 | Proficiency Testing (PT) | 利用实验室间比对确定实验室检测能力的活动 |
| 内审 | Internal Audit | 实验室对自己管理体系的定期检查 |
| 管理评审 | Management Review | 最高管理者对管理体系的系统评价 |
| 纠正措施 | Corrective Action | 消除已发现的不符合原因并防止再发生的措施 |
| 预防措施 | Preventive Action | 消除潜在不符合原因并防止发生的措施 |
| 周转时间 | Turnaround Time (TAT) | 从样品接收到出具报告的时间间隔 |
| 样品流转 | Sample Workflow | 样品在实验室内部各检测环节之间的传递过程 |

### D.2 缩写词

| 缩写 | 全称 | 说明 |
|------|------|------|
| CMA | China Metrology Accreditation | 中国计量认证，检验检测机构资质认定 |
| CNAS | China National Accreditation Service for Conformity Assessment | 中国合格评定国家认可委员会 |
| RB/T | Recommended Standard / 推荐性标准 | 认证认可行业标准 |
| ISO | International Organization for Standardization | 国际标准化组织 |
| IEC | International Electrotechnical Commission | 国际电工委员会 |
| GB | 国家标准 (Guobiao) | 强制性国家标准 |
| GB/T | 推荐性国家标准 (Guobiao/Tuijian) | 推荐性国家标准 |
| JTG | 交通运输行业标准 (Jiaotong Gonglu) | 公路/水运行业工程建设标准 |
| JGJ | 建筑工程行业标准 (Jianzhu Gongcheng) | 建筑工业行业标准 |
| YB | 冶金行业标准 (Yejin Biaozhun) | 冶金行业标准 |
| JC | 建材行业标准 (Jiancai) | 建筑材料行业标准 |
| SOP | Standard Operating Procedure | 标准操作程序 |
| RBAC | Role-Based Access Control | 基于角色的访问控制 |
| JWT | JSON Web Token | 用于身份认证的开放标准 |
| API | Application Programming Interface | 应用程序编程接口 |
| REST | Representational State Transfer | 表现层状态转换，一种 API 架构风格 |
| WORM | Write Once Read Many | 一次写入多次读取的存储策略，用于数据归档 |
| TAT | Turnaround Time | 检测周转时间 |
| ALCOA+ | Attributable, Legible, Contemporaneous, Original, Accurate, plus Complete, Consistent, Enduring, Available | 数据完整性原则 |
| PT | Proficiency Testing | 能力验证 |
| QC | Quality Control | 质量控制 |
| QA | Quality Assurance | 质量保证 |
| LOD | Limit of Detection | 检出限 |
| LOQ | Limit of Quantitation | 定量限 |
| CRD | Certified Reference Material | 有证标准物质 |
| PDF/A | PDF for Archiving | ISO 19005，用于长期归档的 PDF 格式 |
| NTP | Network Time Protocol | 网络时间协议，用于系统时钟同步 |
| RS-232 | Recommended Standard 232 | EIA 定义的串行通信接口标准 |
| RS-485 | Recommended Standard 485 | EIA 定义的串行通信接口标准，支持多点通信 |
| USB | Universal Serial Bus | 通用串行总线 |
| CSV | Comma-Separated Values | 逗号分隔值文件格式 |
| ETL | Extract, Transform, Load | 数据抽取、转换、加载 |
| CRUD | Create, Read, Update, Delete | 数据库基本操作 |
| UUID | Universally Unique Identifier | 通用唯一识别码 |
| OAuth2 | Open Authorization 2.0 | 开放式授权协议 |
| SSL/TLS | Secure Sockets Layer / Transport Layer Security | 安全传输层协议 |
| JWT | JSON Web Token | 基于 JSON 的开放认证标准 |
| WIP | Work in Progress | 在制品（待检测样品） |
| LIMS | Laboratory Information Management System | 实验室信息管理系统 |

---

## 附录 E: 第三方仪器通信协议参考

### E.1 串行通信基础知识

#### RS-232

RS-232 是最常用的点对点串行通信标准，适用于短距离（通常 < 15 米）仪器数据通信。

| 参数 | 典型值 | 说明 |
|------|--------|------|
| 通信距离 | < 15 m | 电缆长度限制 |
| 波特率 | 300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200 | 最常见 9600 bps |
| 数据位 | 5, 6, 7, 8 | 最常见 8 位 |
| 停止位 | 1, 1.5, 2 | 最常见 1 位 |
| 校验位 | None, Even, Odd | 最常见 None |
| 连接器 | DB9 (9-pin) | - |
| 全双工 | 是 | 同时收发 |

**DB9 引脚定义（DTE 端，如 PC）**：

| 引脚 | 名称 | 方向 | 说明 |
|------|------|------|------|
| 1 | DCD | 输入 | 数据载波检测 |
| 2 | RXD | 输入 | 接收数据 |
| 3 | TXD | 输出 | 发送数据 |
| 4 | DTR | 输出 | 数据终端就绪 |
| 5 | GND | - | 信号地 |
| 6 | DSR | 输入 | 数据设备就绪 |
| 7 | RTS | 输出 | 请求发送 |
| 8 | CTS | 输入 | 清除发送 |
| 9 | RI | 输入 | 振铃指示 |

**最小连接（仅 3 线）**：TXD ↔ RXD、RXD ↔ TXD、GND ↔ GND。绝大多数仪器通信只需要这 3 根线。

#### RS-485（EIA-485）

| 参数 | 典型值 | 说明 |
|------|--------|------|
| 通信距离 | < 1200 m | 电缆长度，使用屏蔽双绞线 |
| 波特率 | 300 ~ 115200 | 距离越高速率越低 |
| 拓扑 | 多点总线 | 最多 32 个设备（标准），最多 256 个（增强型） |
| 半双工 | 是 | 收发不能同时进行 |
| 差分信号 | 是 | 抗干扰能力强 |
| 接线 | A(+), B(-), GND | 3 线连接 |

**接线注意**：
- A 接 A，B 接 B（不同厂商可能使用不同命名，以实测为准）
- 总线终端加 120Ω 匹配电阻（长距离时）
- GND 必须共地

#### 通用通信格式表示

仪器通信参数通常表示为：**波特率-数据位-校验-停止位**

例如：**9600-8-N-1** 表示 9600 bps、8 数据位、无校验、1 停止位。

### E.2 万能材料试验机通信协议

#### 2.2.1 MTS（美国 MTS 系统公司）

| 属性 | 值 |
|------|------|
| 接口类型 | RS-232 |
| 波特率 | 9600 |
| 数据格式 | 8-N-1 |
| 通信模式 | 主动发送（仪器到 PC）或 查询应答 |

**典型数据格式（MTS FlexTest 系列）**：
```
<START> 载荷值(N) <TAB> 位移值(mm) <TAB> 变形值(mm) <LF>
```

部分型号支持 MTS TestWorks 专用协议，需通过 OPC Server 或 MTS API 获取数据。

**查询命令（部分型号）**：
```
发送: *IDN?\r\n
回复: MTS Systems Corporation,FlexTest SE,Vx.x.x,<serial>
```

#### 2.2.2 INSTRON（英斯特朗）

| 属性 | 值 |
|------|------|
| 接口类型 | RS-232 / USB |
| 波特率 | 9600 / 19200 |
| 数据格式 | 8-N-1 |
| 通信模式 | 查询-应答 |

**Bluehill 软件 OPC 接口**：
INSTRON Bluehill 软件支持通过 OPC DA / OPC UA 接口实时输出测试数据，推荐优先使用 OPC 方式对接。

**串口数据格式（老型号）**：
```
<STX> 载荷值 <ETX>
<STX> 位移值 <ETX>
<STX> 峰值载荷 <ETX>
```

#### 2.2.3 济南试金集团

| 属性 | 值 |
|------|------|
| 接口类型 | RS-232 |
| 波特率 | 9600 |
| 数据格式 | 8-N-1 |
| 通信模式 | 连续发送 |

**WAW 系列电液伺服万能试验机**（常见协议）：
```
数据帧格式：
[SOH] [载荷数据 8 字节] [位移数据 8 字节] [状态字节] [校验和] [EOT]

载荷数据：ASCII 字符串表示的力值 (N)，单位 N，如 "04523.56"
位移数据：ASCII 字符串表示的位移 (mm)，单位 mm，如 "00012.34"
```

**部分型号简单协议**：
```
仪器每 200ms 发送一行：
12345.67, 12.34, 0.056\r\n
(力值N, 位移mm, 变形mm)
```

#### 2.2.4 深圳瑞格尔仪器（RIGOL）

| 属性 | 值 |
|------|------|
| 接口类型 | RS-232 / USB |
| 波特率 | 9600 / 19200 |
| 数据格式 | 8-N-1 |
| 通信模式 | 连续发送 / 查询应答 |

**WDS / RWD 系列**：
```
发送指令: READ\r\n
返回: LOAD=1234.5N,DIST=56.78mm,DEF=0.123mm\r\n
```

### E.3 压力机通信协议

#### 2.3.1 长春科新试验仪器有限公司

| 属性 | 值 |
|------|------|
| 接口类型 | RS-232 |
| 波特率 | 9600 / 19200 |
| 数据格式 | 8-N-1 |
| 通信模式 | 连续发送或查询 |

**YAW 系列电液伺服压力机**：
```
连续发送模式，每秒发送 5-10 组数据：
LOAD=1234.5kN,RATE=2.3kN/s,STATUS=TEST\r\n
```

**状态字段**：
- `LOAD`：当前载荷 (kN)
- `RATE`：加载速率 (kN/s)
- `STATUS`：`IDLE`=待机, `LOAD`=加载中, `PEAK`=达到峰值, `HOLD`=保持, `RESET`=复位
- `DISP`：活塞位移 (mm)（部分型号）

#### 2.3.2 济南试金压力机

```
DYE-2000/3000 系列压力机：
每 500ms 发送：
1234.56\n
(单行纯数值，单位 kN)
```

### E.4 电子天平通信协议

#### 2.4.1 梅特勒-托利多（Mettler Toledo）

| 属性 | 值 |
|------|------|
| 接口 | RS-232 / USB |
| 波特率 | 1200 ~ 115200（默认 9600） |
| 数据格式 | 8-N-1 或 7-E-1 |
| 协议 | SICS (Standard Interface Command Set) |

**SICS 标准命令集**：

| 命令 | 说明 | 示例 |
|------|------|------|
| `S` | 发送当前称量值（稳定后） | 发送 `S\r\n`，回复 `S S 123.45 g` |
| `SI` | 立即发送称量值（不等待稳定） | 发送 `SI\r\n`，回复 `SI S 123.45 g` |
| `SR` | 连续发送称量值 | 发送 `SR\r\n`，持续返回 `S S xxx.xx g` |
| `SIR` | 立即连续发送 | 发送 `SIR\r\n`，持续返回 `SI S xxx.xx g` |
| `SC` | 停止连续发送 | 发送 `SC\r\n` |
| `TI` | 发送天平 ID | 回复 `T MT-SICS Balance,Vx.x` |
| `ZI` | 清零（去皮） | 发送 `ZI\r\n` |

**SICS 响应格式**：
```
S S 123.45 g
│ │ │      │
│ │ │      └─ 单位 (g/mg/kg)
│ │ └─ 称量值
│ └─ 状态: S=稳定, D=不稳定
└─ 命令类型: S/SI/SIR
```

**老式梅特勒天平格式（非 SICS）**：
```
+   123.45 g\r        (稳定状态，正号)
-    12.34 g\r        (不稳定状态)
```

#### 2.4.2 赛多利斯（Sartorius）

| 属性 | 值 |
|------|------|
| 接口 | RS-232 / USB |
| 波特率 | 300 ~ 19200（默认 9600） |
| 数据格式 | 8-N-1 |
| 协议 | Sartorius 专有协议 |

**命令集**：

| 命令 | 说明 | 示例 |
|------|------|------|
| `P` | 打印（发送当前称量值） | 发送 `P\r\n`，回复 `S 123.45 g` |
| `PS` | 连续打印 | 发送 `PS\r\n` |
| `PC` | 停止连续打印 | 发送 `PC\r\n` |
| `Z` | 清零（去皮） | 发送 `Z\r\n` |
| `ESC` | 取消当前操作 | 发送 `\x1B` |

**返回格式**：
```
S          123.45  g\r
│          │       │
│          │       └─ 单位
│          └─ 数值（固定宽度字段）
└─ 状态: S=稳定, D=动态, -=?
```

**无稳定标识格式**：
```
+123.45g\r\n
```

### E.5 串口调试工具推荐

| 工具 | 平台 | 特点 | 适用场景 |
|------|------|------|---------|
| 串口调试助手（SSCOM） | Windows | 免费、轻量、支持 HEX/ASCII、定时发送、数据保存 | 快速调试、数据抓取 |
| Putty | Windows/Linux/macOS | 免费开源、支持串口、SSH、Telnet | 跨平台调试 |
| RealTerm | Windows | 免费开源、二进制数据可视、控制流监控 | 二进制协议分析 |
| Docklight | Windows | 功能强大、脚本自动化、序列分析 | 复杂协议开发与测试 |
| Minicom | Linux | 终端界面、脚本支持 | Linux 环境串口调试 |
| screen / cu | Linux/macOS | 系统自带、简单可靠 | 快速连接测试 |
| CuteCom | Linux | GUI 界面、HEX 显示 | Linux 图形化串口调试 |
| Serial Port Monitor | Windows | 商业软件、端口嗅探（无需物理连接） | 分析第三方软件串口通信 |
| Termite | Windows | 免费轻量、插件支持 | 日常串口通信 |
| Hercules | Windows | 免费、TCP/UDP/串口全能 | 多协议调试 |

### E.6 集成通信模块设计建议

**LIMS 仪器数据采集架构**：

```
仪器 (RS-232/RS-485) ──→ [串口服务器/USB转换器] ──→ [数据采集网关服务] ──→ LIMS API
```

**数据采集网关设计要求**：
1. **自动识别**：通过 `*IDN?` 或协议特征自动识别仪器型号
2. **参数可配置**：波特率、数据位、校验位、停止位均可配
3. **数据缓冲**：采用队列缓存数据，防止 LIMS 不可达时数据丢失
4. **时间戳**：每条数据在采集网关打时间戳（NTP 同步）
5. **原始数据存档**：保留仪器原始输出，不丢弃任何字节
6. **断线重连**：自动重连机制，重连后标记数据段
7. **多实例**：一台网关可同时连接多台仪器

**Python 示例（pyserial）**：
```python
# -*- coding: utf-8 -*-
import serial
import time
import threading
import re
from datetime import datetime, timezone

class InstrumentReader:
    """通用仪器数据采集器"""

    def __init__(self, port, baudrate=9600, parity='N',
                 bytesize=8, stopbits=1, timeout=1.0):
        self.port = port
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            parity=parity,
            bytesize=bytesize,
            stopbits=stopbits,
            timeout=timeout
        )
        self.callbacks = []
        self._running = False
        self._thread = None

    def on_data(self, callback):
        """注册数据回调: callback(raw_data: str, timestamp: datetime)"""
        self.callbacks.append(callback)

    def start(self):
        """开始连续采集"""
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止采集"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)

    def _read_loop(self):
        buffer = ''
        while self._running:
            try:
                raw = self.ser.read(256)
                if raw:
                    buffer += raw.decode('ascii', errors='replace')
                    # 按行处理
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if line:
                            ts = datetime.now(timezone.utc)
                            for cb in self.callbacks:
                                cb(line, ts)
            except serial.SerialException as e:
                print(f"[{self.port}] 串口异常: {e}")
                break

    def send(self, command: str):
        """发送命令"""
        self.ser.write((command + '\r\n').encode('ascii'))


# 使用示例
def handle_data(raw: str, ts: datetime):
    # 解析梅特勒 SICS 格式：S S 123.45 g
    match = re.match(r'S\s+(\S+)\s+([\d.]+)\s+(g|mg|kg)', raw)
    if match:
        stable = match.group(1)
        weight = float(match.group(2))
        unit = match.group(3)
        print(f"[{ts}] {weight} {unit} (稳定={stable == 'S'})")
    else:
        print(f"[{ts}] 原始: {raw}")

reader = InstrumentReader(port='/dev/ttyUSB0', baudrate=9600)
reader.on_data(handle_data)
reader.start()
time.sleep(60)
reader.stop()
```

---

## 附录 F: 项目执行建议

### F.1 开发阶段划分 (Wave 规划)

#### Wave 1: 基础设施与核心委托流 (第 1-4 周)

**目标**：跑通从委托创建到报告生成的最简闭环。

| 任务 | 交付物 | 验收标准 |
|------|--------|---------|
| 项目环境搭建 | Docker Compose 开发环境、CI/CD 流水线 | `docker compose up` 一键启动，测试通过 |
| 数据库设计与迁移 | 核心表 schema（委托、样品、检测任务、报告） | 所有表创建成功，迁移脚本可重复执行 |
| RBAC 权限系统 | 用户、角色、权限管理 | 登录/鉴权/权限拦截正常 |
| 委托管理 | 委托 CRUD、委托编号自动生成 | 创建委托返回唯一编号 |
| 样品管理 | 样品登记、条形码生成 | 扫码可查样品信息 |
| 检测任务分派 | 任务分配至检测员 | 检测员可看到被分配的任务 |
| 检测数据录入 | 手动录入检测数据、自动修约 | 数据入库后 GB/T 8170 自动修约 |
| 报告生成 | 检测报告模板、自动生成报告 | 报告包含委托、样品、检测、结论信息 |

**里程碑**：一个委托从创建到报告输出的完整流程可演示。

#### Wave 2: 样品全流程与检测记录完善 (第 5-8 周)

**目标**：完善样品生命周期管理和检测记录的标准化。

| 任务 | 交付物 | 验收标准 |
|------|--------|---------|
| 样品流转管理 | 样品状态机（待检/在检/已检/留样/处置） | 状态流转正确，不可逆向 |
| 原始记录模板 | 按检测项目配置的原始记录表 | 模板可编辑，数据正确回写 |
| 公式引擎实现 | 计算公式解析与执行 | 公式自动计算，支持常见函数 |
| 判定规则 | 合格/不合格自动判定 | 判定结果与标准一致 |
| 报告审批流 | 编制 → 审核 → 批准 → 签发 | 多级审批，签名可追溯 |
| 报告模板编辑器 | 可视化报告模板配置 | 拖拽/配置方式修改模板 |
| 电子签名 | 合规电子签名 | 签名后数据变更自动失效 |

**里程碑**：检测全流程覆盖原记录到签发报告，含审批和质量控制节点。

#### Wave 3: 仪器设备管理与仪器对接 (第 9-12 周)

**目标**：设备全生命周期管理 + 仪器数据自动采集。

| 任务 | 交付物 | 验收标准 |
|------|--------|---------|
| 仪器设备台账 | 设备 CRUD、校准计划 | 仪器状态实时可见 |
| 校准/检定管理 | 校准证书、期间核查、到期提醒 | 超期设备自动标记"停用" |
| 串口数据采集网关 | 仪器数据采集服务 | 连接万能试验机可实时采集 |
| 协议适配层 | 多仪器协议适配 | 至少对接 2 种型号压力机 |
| 仪器数据自动绑定 | 采集数据自动关联检测任务 | 无需人工录入 |
| 环境监控 | 温湿度记录、超标告警 | 数据入库，超阈值告警 |

**里程碑**：至少一台仪器实现自动数据采集并录入 LIMS。

#### Wave 4: 质量控制与报告管理 (第 13-16 周)

**目标**：完整的质量管理体系和报告管理。

| 任务 | 交付物 | 验收标准 |
|------|--------|---------|
| 质控计划管理 | 质控计划制定、质控样品 | 计划可按周期执行 |
| 质控数据录入 | 盲样、平行样、加标回收 | 数据录入完整 |
| 质控图 | Xbar-R 图、控制限自动计算 | 图表正确绘制，超限告警 |
| Westgard 规则 | 多规则质控判断 | 规则触发时正确告警 |
| 报告归档 | PDF/A 格式存档、不可篡改 | 归档文件可检索 |
| 委托查询与统计 | 多维度搜索、统计报表 | 查询响应 < 2 秒 |
| 不确定度评定 | 常见项目不确定度计算 | 计算结果纳入报告 |

**里程碑**：质控体系运行，可自动生成控制图，报告归档符合 CMA 要求。

#### Wave 5: 合规完善与系统增强 (第 17-20 周)

**目标**：满足 CMA/CNAS 全部合规要求，增强系统能力。

| 任务 | 交付物 | 验收标准 |
|------|--------|---------|
| 审计追踪 | 全操作审计日志、不可篡改 | 每条数据修改均可追溯 |
| 数据完整性 | ALCOA+ 数据保护 | WORM 存储策略实施 |
| 内审/管理评审 | 内审计划、不符合项管理 | 纠正措施闭环追踪 |
| 能力验证 | PT 计划管理、结果录入 | PT 数据纳入质控体系 |
| 人员能力矩阵 | 人员技能、授权范围、培训记录 | 到期自动提醒 |
| 文件管理 | SOP 管理、版本控制 | 文件审批发布流程 |
| 数据备份与恢复 | 自动备份、恢复测试 | RPO ≤ 1h, RTO ≤ 4h |
| 报表中心 | 自定义报表、数据导出 | Excel/PDF 导出 |

**里程碑**：系统通过 CMA/CNAS 合规自查，所有检查项覆盖。

#### Wave 6: 试运行与上线 (第 21-24 周)

**目标**：试运行验证、性能优化、正式上线。

| 任务 | 交付物 | 验收标准 |
|------|--------|---------|
| 数据迁移 | 历史数据导入 | 迁移数据完整性校验通过 |
| 性能优化 | 慢查询优化、缓存策略 | 接口 P95 响应 < 1 秒 |
| 安全加固 | 渗透测试修复、安全审计 | 无高危漏洞 |
| 用户培训 | 培训教材、操作手册 | 用户通过操作考核 |
| 试运行 | 真实业务运行 ≥ 2 周 | 无 P0/P1 级别缺陷 |
| 正式上线 | 生产环境部署、监控上线 | 系统 7×12h 稳定运行 |

**里程碑**：系统正式上线运行。

### F.2 各 Wave 交付物总览

| Wave | 周期 | 核心功能 | 代码产出 | 文档产出 |
|------|------|---------|---------|---------|
| Wave 1 | 周 1-4 | 委托流 MVP | 核心后端 API、前端页面、数据库迁移 | 架构文档、API 文档 |
| Wave 2 | 周 5-8 | 全流程覆盖 | 公式引擎、报告引擎、审批流 | 用户操作手册 (V1) |
| Wave 3 | 周 9-12 | 仪器对接 | 数据采集网关、协议适配器 | 仪器对接指南 |
| Wave 4 | 周 13-16 | 质控与报告 | 质控模块、质控图引擎 | 质控操作指南 |
| Wave 5 | 周 17-20 | 合规与增强 | 审计追踪、文件管理模块 | CMA/CNAS 合规自查报告 |
| Wave 6 | 周 21-24 | 上线 | 性能优化、安全加固代码 | 运维手册、培训教材 |

### F.3 验收标准

#### F.3.1 功能性验收

| 类别 | 验收项 | 标准 |
|------|--------|------|
| 委托管理 | 委托创建、编辑、查询、编号规则 | 编号规则: `W{年份}-{序号}`，如 W2025-00001 |
| 样品管理 | 样品登记、条形码、流转追踪 | 条形码扫描响应 < 0.5s，流转状态无遗漏 |
| 检测录入 | 手动录入、自动修约、公式计算 | 修约结果与 GB/T 8170 逐条一致 |
| 仪器采集 | 自动采集、数据绑定 | 采集数据延迟 < 1s，断线恢复无丢失 |
| 报告 | 自动生成、审批流、电子签名 | 报告生成 < 3s，签名验证通过 |
| 质控 | 质控图、规则判断、告警 | 控制图绘制正确，超限 100% 告警 |
| 权限 | RBAC、数据隔离 | 无权限用户 100% 拒绝访问 |
| 审计 | 操作日志、数据变更追踪 | 所有数据变更 100% 可追溯 |

#### F.3.2 非功能性验收

| 指标 | 目标值 | 测试方法 |
|------|--------|---------|
| API 响应时间 (P95) | < 1 秒 | JMeter / k6 压测 |
| API 响应时间 (P99) | < 3 秒 | JMeter / k6 压测 |
| 并发用户数 | ≥ 100 | 负载测试 |
| 数据库单表可承载行数 | ≥ 100 万 | 数据填充 + 查询性能 |
| 系统可用性 | ≥ 99.5% | 7×24h 稳定性测试 |
| 数据备份 RPO | ≤ 1 小时 | 恢复演练 |
| 数据备份 RTO | ≤ 4 小时 | 恢复演练 |
| 电子签名响应时间 | < 1 秒 | 前端计时测量 |
| 报告生成时间 | < 3 秒 | 包含 50+ 检测项目的复杂报告 |
| 页面加载时间 | < 2 秒 | Lighthouse 测试 |

#### F.3.3 合规性验收

| 检查项 | 验收标准 | 验证方法 |
|--------|---------|---------|
| 数据修改留痕 | 所有数据变更 100% 记录审计日志 | 修改数据后查询审计表 |
| 不可篡改性 | 审计日志不可删除、不可修改 | 尝试删除/修改审计记录，系统拒绝 |
| 电子签名合规 | 符合《电子签名法》可靠电子签名要求 | 第三方 CA 验证 |
| 授权签字人控制 | 仅授权签字人可签发报告 | 非授权人尝试签发，系统拒绝 |
| 数据归档保存期 | 委托 + 报告 ≥ 6 年可查询 | 模拟 6 年后查询 |
| 仪器校准控制 | 超校准期仪器无法录入/采集数据 | 模拟超期仪器状态 |

### F.4 风险清单及缓解措施

| 编号 | 风险描述 | 影响 | 概率 | 缓解措施 | 责任人 |
|------|---------|------|------|---------|--------|
| R01 | 仪器协议不兼容，无法自动采集 | 高 | 中 | 1) 项目前期收集仪器型号清单<br>2) 每种型号提前测试连通性<br>3) 预留手动录入兜底方案 | 技术负责人 |
| R02 | CMA/CNAS 评审标准变化 | 中 | 低 | 1) 系统设计留扩展点<br>2) 合规规则可配置化<br>3) 定期跟踪最新标准 | 合规负责人 |
| R03 | 数据迁移不完整或错误 | 高 | 中 | 1) 迁移脚本可重复执行<br>2) 数据校验（行数、关键指标）<br>3) 保留旧系统并行运行期 | DBA |
| R04 | 关键人员离职 | 高 | 低 | 1) 代码规范 + 文档完整<br>2) 关键岗位双人备份<br>3) 知识共享机制 | 项目经理 |
| R05 | 性能不达标（大数据量查询慢） | 中 | 中 | 1) 早期压力测试（10 万级数据）<br>2) 数据库索引优化<br>3) 热点查询预计算+缓存 | 后端负责人 |
| R06 | 用户抵触新系统 | 中 | 高 | 1) 界面设计贴近操作习惯<br>2) 充分培训+操作手册<br>3) 保留旧系统过渡期 | 项目经理 |
| R07 | 电子签名法律效力争议 | 高 | 低 | 1) 使用合规 CA 机构证书<br>2) 咨询法律顾问<br>3) 保留纸质签名备选 | 项目经理 |
| R08 | 第三方依赖（云服务/数据库）故障 | 高 | 低 | 1) 多可用区部署<br>2) 定期灾备演练<br>3) 监控告警 | 运维负责人 |
| R09 | 修约逻辑与检测员习惯不符 | 中 | 中 | 1) 修约规则完全可配置<br>2) 项目初期与检测员确认<br>3) 修约结果可手动修正但留痕 | 产品负责人 |
| R10 | 需求范围蔓延 | 高 | 高 | 1) 明确 MVP 范围<br>2) 变更走审批流程<br>3) Wave 外需求纳入后续版本 | 项目经理 |

### F.5 团队组建建议

#### F.5.1 人员角色配置

| 角色 | 人数 | 技能要求 | 职责 |
|------|------|---------|------|
| 项目经理 | 1 | 5+ 年项目管理经验，熟悉检测行业 | 整体规划、风险管控、客户沟通 |
| 产品负责人 | 1 | 熟悉 CMA/CNAS 体系，理解检测流程 | 需求分析、验收标准制定、用户培训 |
| 后端开发（高级） | 2 | Python/FastAPI 或 Go/Gin，PostgreSQL，Redis，Docker | API 开发、公式引擎、质控逻辑 |
| 后端开发（中级） | 1 | Python 或 Go，REST API 开发经验 | API 开发、报告引擎、数据迁移 |
| 前端开发（高级） | 1 | React/Vue 3，TypeScript，ECharts，响应式设计 | 核心页面、报表、质控图 |
| 前端开发（中级） | 1 | React/Vue 3，TypeScript | 表单、列表、报告预览 |
| 仪器集成工程师 | 1 | 串口通信协议、pyserial、嵌入式开发经验 | 仪器对接、数据采集网关 |
| QA/测试 | 1 | 自动化测试、性能测试，熟悉检测行业 | 功能测试、合规测试、压测 |
| DevOps/运维 | 1 | Docker, K8s, CI/CD, 监控（Prometheus/Grafana） | 环境搭建、部署、监控 |

**总计：10 人**

#### F.5.2 人员分阶段投入

| 角色 | Wave 1 | Wave 2 | Wave 3 | Wave 4 | Wave 5 | Wave 6 |
|------|--------|--------|--------|--------|--------|--------|
| 项目经理 | 50% | 50% | 50% | 50% | 50% | 50% |
| 产品负责人 | 100% | 100% | 50% | 50% | 100% | 100% |
| 后端 (高级) | 100% | 100% | 100% | 100% | 100% | 50% |
| 后端 (中级) | 100% | 100% | 100% | 100% | 100% | 50% |
| 前端 (高级) | 50% | 100% | 100% | 100% | 100% | 50% |
| 前端 (中级) | 50% | 100% | 100% | 100% | 100% | 50% |
| 仪器集成 | 0% | 0% | 100% | 50% | 0% | 0% |
| QA | 0% | 25% | 50% | 100% | 100% | 100% |
| DevOps | 100% | 50% | 50% | 50% | 100% | 100% |

#### F.5.3 关键技能要求清单

**后端技术栈**：
- 核心框架：FastAPI (Python) 或 Go (gin/echo)
- 数据库：PostgreSQL 15+（CTE、JSONB、全文检索）
- 缓存：Redis 7+（Session、限速、分布式锁）
- 任务队列：Celery (Python) 或 Asynq (Go)
- ORM/SQL：SQLAlchemy / PSQL
- 测试：pytest / go test + 覆盖率 ≥ 80%

**前端技术栈**：
- 框架：Vue 3 (Composition API) 或 React 18+
- 状态管理：Pinia (Vue) / Zustand (React)
- UI 组件：Element Plus / Ant Design
- 图表：ECharts 5+（质控图、报表）
- 构建：Vite

**基础设施**：
- 容器：Docker + Docker Compose（开发）/Kubernetes（生产）
- CI/CD：GitHub Actions / GitLab CI
- 监控：Prometheus + Grafana
- 日志：ELK Stack 或 Loki + Grafana
- 数据库备份：pg_dump + WAL-G

---

> **文档版本**: v1.0
> **最后更新**: 2025-06-15
> **维护人**: LIMS 项目组

---

# 第七部分: 新增开发决策与代码示例 (Phase 4)

# 第七部分: 新增开发决策与代码示例

## 附.12 新增决策 (#23-#49)

### 附.12.1 数据库分表策略 (#20) - PostgreSQL 16 声明式分区

**决策**: 按时间月分区。预计 1000 样品/天 × 30 天 = 30,000 条/月。10 年 = 730 万-3650 万条。

```sql
-- 检测任务表按月分区
CREATE TABLE testing.test_tasks (
    id UUID NOT NULL,
    task_no VARCHAR(30) NOT NULL,
    sample_id UUID,
    test_method_id UUID,
    assigned_to INT,
    status VARCHAR(30) DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 创建分区
CREATE TABLE testing.test_tasks_2025_01 PARTITION OF testing.test_tasks
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- 自动创建下月分区 (Alembic 迁移脚本)
```

**Python 自动分区**:
```python
from datetime import date
from alembic import op

def upgrade():
    conn = op.get_bind()
    for i in range(1, 3):
        month = date.today().replace(day=1)
        # 跳过当前月
        if month <= date.today().replace(day=1):
            month = month.replace(month=month.month + 1 if month.month < 12 else 1)
        next_month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
        partition_name = f"test_tasks_{month.strftime('%Y_%m')}"
        conn.execute(f"""CREATE TABLE IF NOT EXISTS testing.{partition_name}
            PARTITION OF testing.test_tasks
            FOR VALUES FROM ('{month.isoformat()}') TO ('{next_month.isoformat()}');""")
```

### 附.12.2 仪器数据对接 (#22) - 统一协议网关

**架构**: 仪器 → Protocol Gateway (独立 Python 服务) → WebSocket → LIMS Backend

```python
# services/instrument_gateway/main.py
import serial
import json
import asyncio
from websockets.client import connect

class SerialCollector:
    def __init__(self, port: str, baudrate: int = 9600, instrument_id: str = "", instrument_type: str = ""):
        self.port = port
        self.baudrate = baudrate
        self.instrument_id = instrument_id
        self.instrument_type = instrument_type

    async def collect(self, ws_url: str = "ws://localhost:8765/instrument"):
        self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        async with connect(ws_url) as ws:
            while True:
                raw = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if not raw: continue
                parsed = self._parse(raw)
                if parsed:
                    await ws.send(json.dumps({
                        "instrument_id": self.instrument_id,
                        "type": self.instrument_type,
                        "time": datetime.now().isoformat(),
                        "value": parsed['value'],
                        "unit": parsed['unit'],
                        "raw": raw,
                    }))

    def _parse(self, raw: str) -> dict | None:
        # JAW-300: "FN005325E1" → 532.5 kN
        import re
        match = re.search(r'FN(\d+)E', raw)
        if match:
            return {'value': int(match.group(1)) / 10.0, 'unit': 'kN'}
        # 梅特勒天平: "S S  123.4567 g"
        parts = raw.strip().split()
        if len(parts) >= 3:
            try:
                return {'value': float(parts[-2]), 'unit': parts[-1].replace('g', 'g')}
            except ValueError: pass
        return None
```

### 附.12.3 API 版本管理 (#23) - URL 路径版本

```python
# src/api/__init__.py
from fastapi import APIRouter
v1_router = APIRouter(prefix="/api/v1")
v2_router = APIRouter(prefix="/api/v2")
app.include_router(v1_router)
app.include_router(v2_router)

# 废弃标记中间件
class APIVersionMiddleware:
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/v1"):
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = "2026-01-01T00:00:00Z"
            response.headers["Link"] = '</api/v2>; rel="successor"'
        return response
```

### 附.12.4 文件存储方案 (#24) - 本地存储 + DB 元数据

```python
# src/core/file_storage.py
from pathlib import Path
import uuid

class LocalFileStorage:
    def __init__(self, base_dir: str = "/data/lims/files"):
        self.base_dir = Path(base_dir)
        self.buckets = {
            "reports": self.base_dir / "reports",
            "attachments": self.base_dir / "attachments",
            "records": self.base_dir / "records",
            "backups": self.base_dir / "backups",
        }
        for b in self.buckets.values():
            b.mkdir(parents=True, exist_ok=True)

    def store(self, content: bytes, bucket: str, original_name: str) -> dict:
        sub_dir = self.buckets[bucket] / datetime.now().strftime("%Y/%m/%d")
        sub_dir.mkdir(parents=True, exist_ok=True)
        file_id = str(uuid.uuid4())
        file_path = sub_dir / f"{file_id}{Path(original_name).suffix}"
        file_path.write_bytes(content)
        return {"id": file_id, "path": str(file_path), "size": len(content)}

# system.file_store 表已定义 (见 03-database-design.md)
```

### 附.12.5 WebSocket 连接管理 (#26) - Redis pub/sub

```python
# src/core/websocket_manager.py
import redis.asyncio as redis
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.redis: redis.Redis | None = None
        self.subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, channel: str):
        await ws.accept()
        self.subscriptions.setdefault(channel, set()).add(ws)

    async def publish(self, channel: str, msg: dict):
        if self.redis:
            await self.redis.publish(channel, json.dumps(msg, default=str))

    async def broadcast(self, channel: str, msg: dict):
        payload = json.dumps(msg, default=str)
        for ws in list(self.subscriptions.get(channel, [])):
            try: await ws.send_text(payload)
            except: self.subscriptions[channel].discard(ws)

# FastAPI 路由
@router.websocket("/ws/instrument/{task_id}")
async def instrument_ws(ws: WebSocket, task_id: str):
    await manager.connect(ws, f"task:{task_id}")
    while True:
        raw = await ws.receive_text()
        # 存储原始数据 → 广播前端
        await manager.broadcast(f"task:{task_id}", {"type": "data", "payload": raw})
```

### 附.12.6 测试策略 (#28) - 60/30/10 分层测试

**目录结构**:
```
tests/
├── unit/          # 60% - 无 I/O
│   ├── test_gb8170_rounding.py
│   ├── test_dsl_evaluator.py
│   ├── test_workflow_state_machine.py
│   └── test_number_generator.py
├── integration/   # 30% - DB/API
│   ├── test_sample_api.py
│   ├── test_report_generation.py
│   └── test_audit_trigger.py
├── e2e/           # 10% - Playwright
│   ├── test_login_flow.py
│   └── test_review_workflow.py
└── factories/     # 测试工厂
```

**GB/T 8170 单元测试**:
```python
import pytest
from src.core.rounding import round_gb8170

@pytest.mark.parametrize("value, interval, expected", [
    (12.34, 0.1, 12.3),   # <5 舍去
    (12.36, 0.1, 12.4),   # >5 进一
    (12.351, 0.1, 12.4),  # =5后非零 进一
    (12.25, 0.1, 12.2),   # =5后全0,偶数位 舍去
    (12.35, 0.1, 12.4),   # =5后全0,奇数位 进一
    (23.7, 1.0, 24.0),    # 间隔1
    (12.5, 0.5, 12.5),    # 间隔0.5
])
def test_gb8170_rounding(value, interval, expected):
    assert round_gb8170(value, interval) == pytest.approx(expected, rel=1e-9)
```

### 附.12.7 前端动态表单引擎 (#40, #42, #44)

```python
# src/services/form_engine/renderer.py
class FormSchema:
    @staticmethod
    def build(method_id: int, db) -> dict:
        fields = db.execute("""
            SELECT param_code, param_name, param_type, unit,
                   decimal_places, rounding_rule, formula, formula_inputs,
                   is_required, min_value, max_val, sort_order
            FROM testing.test_method_parameters
            WHERE method_id = %s ORDER BY sort_order
        """, (method_id,)).fetchall()

        return {"fields": [{
            "code": f.param_code,
            "label": f.param_name,
            "type": f.param_type,
            "unit": f.unit,
            "required": f.is_required,
            "precision": f.decimal_places if f.param_type == 'number' else None,
            "formula": f.formula if f.param_type == 'computed' else None,
            "rounding": f.rounding_rule,
        } for f in fields]}
```

**前端渲染** (`DynamicForm.tsx`):
```tsx
export const DynamicForm = ({ methodId }: { methodId: number }) => {
  const [form] = Form.useForm();
  const [schema, setSchema] = useState<any>(null);
  const values = Form.useWatch([], form);

  useEffect(() => {
    fetch(`/api/v1/form-schemas/${methodId}`).then(r => r.json()).then(setSchema);
  }, [methodId]);

  return (
    <Form form={form} layout="vertical">
      {schema?.fields.map(f =>
        f.type === 'computed'
          ? <ComputedField key={f.code} field={f} formValues={values} />
          : f.type === 'number'
          ? <Form.Item key={f.code} name={f.code} label={f.label}
              rules={[{ required: f.required }, { type: 'number', min: f.min, max: f.max }]}>
              <InputNumber precision={f.precision} addonAfter={f.unit} />
            </Form.Item>
          : <Form.Item key={f.code} name={f.code} label={f.label}>
              <Input />
            </Form.Item>
      )}
    </Form>
  );
};
```

### 附.12.8 前端错误边界 (#41, #48)

```tsx
// src/components/ErrorBoundary.tsx
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null, errorInfo: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // 上报全局错误到后端
    fetch('/api/v1/client-errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        url: window.location.href,
      }),
    });
    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <Result status="error" title="页面出错" subTitle={this.state.error?.message}
          extra={<Button type="primary" onClick={() => window.location.reload()}>刷新</Button>}
        />
      );
    }
    return this.props.children;
  }
}
```

### 附.12.9 日志策略 (#27) - 结构化 JSON 日志

```python
# src/core/logging.py
import logging
import json
from pythonjsonlogger import jsonlogger

class LIMSFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['service'] = 'lims-backend'
        log_record['version'] = '1.0.0'
        log_record['pid'] = record.process
        log_record['thread'] = record.threadName

handler = logging.FileHandler('/var/log/lims/app.log')
handler.setFormatter(LIMSFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])

# 使用:
logger = logging.getLogger(__name__)
logger.info("sample_created", extra={"sample_id": "YP-001", "user_id": 12})
```

### 附.12.10 错误处理策略 (#31) - 全局异常处理

```python
# src/core/exceptions.py
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

class LIMSException(HTTPException):
    """自定义业务异常基类"""
    def __init__(self, code: str, status_code: int = 400, detail: str = ""):
        super().__init__(status_code, {"code": code, "message": detail})

class BusinessError(LIMSException):
    """业务规则违反"""
    pass

class ValidationError(LIMSException):
    """数据校验失败"""
    pass

class WorkflowError(LIMSException):
    """状态机转换失败"""
    pass

# FastAPI 异常处理器
@app.exception_handler(LIMSException)
async def lims_exception_handler(req: Request, exc: LIMSException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "code": exc.detail.get("code", exc.code),
                 "message": exc.detail.get("message", ""), "path": str(req.url)},
    )

@app.exception_handler(RequestValidationError)
async def validation_error_handler(req: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={
        "error": True, "code": "VALIDATION_ERROR", "message": "请求参数校验失败",
        "details": exc.errors(),
    })

# 使用示例
@router.post("/samples")
def create_sample(data: SampleCreate, db):
    if not db.exists(Order, id=data.order_id):
        raise BusinessError("ORDER_NOT_FOUND", 404, "委托单不存在")
```

### 附.12.11 国际化方案 (#32) - Flask-Babel 占位预留

虽然当前只支持简体中文，但系统架构预留 i18n 位置：
```python
# src/core/i18n.py
from babel.support import Translations

# 标准号中的英文术语使用 Translations
def get_standard_name(zh_code: str) -> str:
    """GB/T 标准名称 -> 中文/英文"""
    mapping = {
        "GB/T 8170-2008": {"zh": "数值修约规则", "en": "Rules for rounding-off of numerical values"},
        "GB/T 228.1-2021": {"zh": "金属材料 拉伸试验", "en": "Metallic materials - Tensile testing"},
    }
    return mapping.get(zh_code, {"zh": zh_code, "en": zh_code})
```

### 附.12.12 报告审批流程 (#36) - 三级审批 (编制→审核→签发)

已在 02-detailed-design.md 附.11.7 详细定义，此处补充完整代码：
```python
# src/services/report_approval.py
from enum import Enum

class ReportStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"      # 待审核
    REVIEW_REJECTED = "review_rejected"     # 审核驳回
    PENDING_APPROVAL = "pending_approval"   # 待批准
    APPROVAL_REJECTED = "approval_rejected" # 批准驳回
    SIGNED = "signed"                       # 已签发

class ReportApprovalService:
    def submit_for_review(self, report_id: int, operator_id: int, db):
        """检测员提交报告进入审核"""
        report = db.get_report(report_id)
        if report.status != ReportStatus.DRAFT:
            raise WorkflowError("NOT_DRAFT", "仅草稿可提交审核")
        report.status = ReportStatus.PENDING_REVIEW
        db.commit()

    def review(self, report_id: int, operator_id: int, approved: bool, reason: str, db):
        """审核员审核"""
        report = db.get_report(report_id)
        if report.status != ReportStatus.PENDING_REVIEW:
            raise WorkflowError("NOT_PENDING_REVIEW", "当前状态不可审核")
        if not approved and len(reason) < 10:
            raise ValidationError("REASON_TOO_SHORT", "驳回原因至少10字")

        if approved:
            report.status = ReportStatus.PENDING_APPROVAL
            # 创建审核记录
            self._log_review(report_id, operator_id, "approved", reason, db)
        else:
            report.status = ReportStatus.REVIEW_REJECTED
            self._log_review(report_id, operator_id, "rejected", reason, db)
            self._notify(report.assignee_id, "审核未通过，请修改后重新提交", db)
        db.commit()

    def approve(self, report_id: int, operator_id: int, approved: bool, reason: str, db):
        """批准人批准"""
        report = db.get_report(report_id)
        if report.status != ReportStatus.PENDING_APPROVAL:
            raise WorkflowError("NOT_PENDING_APPROVAL")
        if approved:
            report.status = ReportStatus.SIGNED
            report.issued_at = datetime.now()
            self._generate_pdf(report_id, db)
        db.commit()
```

### 附.12.13 缓存策略 (#25) - Redis 集中式缓存

```python
# src/core/cache.py
import redis
import json
from functools import wraps

redis_client = redis.from_url("redis://localhost:6379/2", decode_responses=True)

def cache(key_prefix: str, ttl: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{args[0]}:{hash(frozenset(kwargs.items()))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            result = func(*args, **kwargs)
            redis_client.set(cache_key, json.dumps(result, default=str), ex=ttl)
            return result
        return wrapper
    return decorator

# 使用:
@cache("sample_detail", ttl=60)
def get_sample_detail(sample_id, db):
    return db.query(Sample).get(sample_id)

# 缓存失效:
def invalidate_sample_cache(sample_id):
    for key in redis_client.scan_iter(f"sample_detail:{sample_id}:*"):
        redis_client.delete(key)
```

### 附.12.14 认证方案 (#30) - Session Cookie + CSRF 保护

**注意**: 本决策确认从 JWT Token 切换为 Session Cookie + CSRF 保护。

```python
# src/core/auth.py
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from starlette.middleware.sessions import SessionMiddleware
from itsdangerous import URLSafeTimedSerializer
import hashlib

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=86400*7)

class SessionAuth:
    @staticmethod
    def login(request: Request, response: Response, username: str, password: str, db):
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(401, "用户名或密码错误")
        request.session["user_id"] = user.id
        request.session["role"] = user.role_code
        return {"message": "登录成功"}

    @staticmethod
    def get_current_user(request: Request, db):
        user_id = request.session.get("user_id")
        if not user_id:
            raise HTTPException(401, "未登录")
        return db.query(User).get(user_id)

# CSRF 保护
from starlette_csrf import CSRFMiddleware
app.add_middleware(CSRFMiddleware, secret=SECRET_KEY)
```

### 附.12.15 数据库索引策略 (#38)

```sql
-- 高频查询索引
CREATE INDEX idx_orders_client ON commission.orders(client_id, created_at DESC);
CREATE INDEX idx_samples_status ON commission.samples(status, created_at DESC);
CREATE INDEX idx_samples_barcode ON commission.samples(barcode);
CREATE INDEX idx_test_tasks_assignee ON testing.test_tasks(assigned_to, status);
CREATE INDEX idx_test_results_task ON testing.test_results(task_id);
CREATE INDEX idx_reports_status ON reporting.reports(status, created_at DESC);
CREATE INDEX idx_audit_log_user ON auth.audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_log_resource ON auth.audit_log(resource, resource_id);

-- 复合索引 (覆盖索引优化)
CREATE INDEX idx_reports_review_status ON reporting.reports(status, reviewed_by, approved_by);

-- 部分索引 (只索引活跃数据)
CREATE INDEX idx_active_samples ON commission.samples(created_at) WHERE status != 'disposed';
```

### 附.12.16 部署架构 (#39) - 独立服务器 (内网)

**系统拓扑**:
```
┌─────────────────────────────────────────────────┐
│  内网 192.168.1.0/24                            │
│                                                   │
│  ┌─────────┐    ┌──────────────────────┐         │
│  │ Nginx   │──→│ Gunicorn + Uvicorn   │         │
│  │ :80/443 │    │ :8000 (9 workers)     │         │
│  └─────────┘    └──────┬──────────────┘         │
│                         │                          │
│  ┌─────────┐    ┌──────┼──────┬────────┐         │
│  │PostgreSQL│   │      │      │        │         │
│  │:5432     │←──┘      │      │        │         │
│  └─────────┘           │      │        │         │
│                    ┌───┴──┐ ┌─┴──┐ ┌───┴───┐   │
│                    │Redis │ │Celery│MinIO │   │
│                    │:6379 │ │:8765 │:9000 │   │
│                    └──────┘ └──────┘ └─────┘   │
└─────────────────────────────────────────────────┘

硬件: 8C16G, 500GB SSD
```

### 附.12.17 Gunicorn Worker 数量 (#49)

公式: `workers = (2 × CPU_cores) + 1`

| CPU | Workers | Memory 分配 |
|-----|---------|---------------|
| 4C  | 9       | 每个 worker ~300MB, 总 ~2.7GB |
| 8C  | 17      | 每个 worker ~300MB, 总 ~5.1GB |

详见 `config/gunicorn.conf.py` (前文已列)。
<!-- OMO_INTERNAL_INITIATOR -->

---
*文档结束*
