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
