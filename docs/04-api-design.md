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
