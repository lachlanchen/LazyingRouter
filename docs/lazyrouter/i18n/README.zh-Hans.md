<p align="center">
  <a href="https://lazying.art">
    <img src="../../../web/default/public/logo.png" alt="LazyingArt logo" width="140" />
  </a>
</p>

# LazyRouter

[English](../../../README.md) | 简体中文 | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [한국어](README.ko.md) | [Русский](README.ru.md) | [Português](README.pt.md) | [العربية](README.ar.md)

LazyRouter 是一个私有 AI API 聚合网关，用于统一管理用户账号、用户 API Key、额度、用量记录和上游模型服务路由。

它基于成熟的开源 New API 项目构建，目标是让 AgInTiFlow 和其他 LazyingArt 工具只需要登录 LazyRouter，就可以通过统一的额度和模型路由访问 OpenRouter、Venice、GRSAI、Claude 兼容服务以及后续供应商。

核心能力包括用户注册登录、管理员面板、用户 Token、额度计费、用量日志、OpenAI 兼容接口、Claude Messages 接口、自定义上游渠道、加权路由和 Docker 部署。

本地入口：`http://127.0.0.1:3218`

计划公网入口：`https://router.lazying.art`

详细操作说明见：[LazyRouter operator guide](../README.md)。
