# Geminar Console

微课平台用户门户

## 功能

- 用户登录（OAuth2）
- 微课管理（创建、编辑、删除）
- 讲师管理
- 视频生成任务提交
- 前端 SPA

## 架构

```
┌─────────────────────────────────────┐
│  geminar-console (本仓库)            │
│  ├── 用户 API                       │
│  ├── OAuth2 登录                    │
│  ├── 前端 SPA                       │
│  └── 共享数据库（只读/受限写入）      │
└─────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│  geminar-admin                      │
│  └── 数据库管理（主库）              │
└─────────────────────────────────────┘
```

## 快速开始

1. 配置环境变量
```bash
cp .env.example .env
```

2. 确保数据库已由 geminar-admin 初始化

3. 启动服务
```bash
# 开发环境
python manage.py runserver 0.0.0.0:8000

# 生产环境
docker compose up -d
```

## API 端点

| 路径 | 说明 |
|------|------|
| / | 首页 |
| /oauth2/login/ | OAuth2 登录 |
| /user/me/ | 当前用户信息 |
| /seminars/ | 微课列表 |
| /speakers/ | 讲师列表 |
| /avatars/ | 头像列表 |
| /voices/ | 声音列表 |

## 注意事项

- 数据库由 geminar-admin 管理，本项目的 models 设置 `managed = False`
- 不要在本项目运行 `migrate` 命令

