# 腾讯云部署指南

本项目推荐部署到腾讯云 CVM 或轻量应用服务器。服务形态是一个 Python 后台，同时托管静态前端和 JSON API。

## 推荐架构

```text
浏览器
  |
  | http://服务器公网IP:8891
  v
腾讯云 CVM / 轻量应用服务器
  |
  | Docker container
  v
开文伊美姬 server.py -> data/prompts.json
```

如果要绑定域名和 HTTPS，可以后续再加 Nginx、宝塔、腾讯云 CDN 或证书服务。第一步建议先用 `8891` 端口跑通。

## 服务器要求

- Ubuntu 20.04+、Debian 11+、TencentOS、CentOS 7+ 均可。
- 建议内存 1 GB 起步。
- 需要开放 TCP `8891` 端口。
- 需要能从服务器访问 GitHub 和 Docker 镜像源。

## 一键部署

在服务器上运行：

```bash
curl -fsSL https://raw.githubusercontent.com/mangooding/kaiwen-yimeiji/main/deploy/tencent-cvm-docker.sh | bash
```

默认会：

- 安装 `git`、`curl`、Docker。
- 克隆 `https://github.com/mangooding/kaiwen-yimeiji.git` 到 `/opt/kaiwen-yimeiji`。
- 构建 Docker 镜像。
- 启动名为 `kaiwen-yimeiji` 的容器。
- 映射服务器 `8891` 端口到容器内 `8891` 端口。
- 执行 `/api/health` 健康检查。

部署完成后访问：

```text
http://服务器公网IP:8891
```

## 自定义端口

如果想用 80 端口：

```bash
APP_PORT=80 bash deploy/tencent-cvm-docker.sh
```

如果 80 端口已被 Nginx、宝塔或其他服务占用，请继续使用 `8891`，或改成其它端口。

## 更新线上版本

服务器上执行：

```bash
cd /opt/kaiwen-yimeiji
git pull
bash deploy/tencent-cvm-docker.sh
```

也可以直接重跑远程脚本：

```bash
curl -fsSL https://raw.githubusercontent.com/mangooding/kaiwen-yimeiji/main/deploy/tencent-cvm-docker.sh | bash
```

## 常用排查命令

查看容器：

```bash
docker ps
```

查看日志：

```bash
docker logs --tail 100 kaiwen-yimeiji
```

本机健康检查：

```bash
curl http://127.0.0.1:8891/api/health
```

如果服务器本机健康检查正常，但外网访问失败，通常是腾讯云安全组或轻量服务器防火墙没有放行端口。

## 需要在腾讯云控制台确认

- CVM：安全组入站规则放行 TCP `8891`。
- 轻量应用服务器：防火墙规则放行 TCP `8891`。
- 如果使用 80/443，同样需要放行对应端口。
