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
