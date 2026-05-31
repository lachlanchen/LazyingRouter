<p align="center">
  <a href="https://lazying.art">
    <img src="../../../web/default/public/logo.png" alt="LazyingArt logo" width="140" />
  </a>
</p>

# LazyingRouter

[English](../../../README.md) | [简体中文](README.zh-Hans.md) | 繁體中文 | [日本語](README.ja.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [한국어](README.ko.md) | [Русский](README.ru.md) | [Português](README.pt.md) | [العربية](README.ar.md)

LazyingRouter 是一個私有 AI API 聚合閘道，用於集中管理使用者帳號、使用者 API Key、額度、用量紀錄與上游模型服務路由。

它基於成熟的開源 New API 專案建立，目標是讓 AgInTiFlow 與其他 LazyingArt 工具只需登入 LazyingRouter，即可透過統一額度與模型路由存取 OpenRouter、Venice、GRSAI、Claude 相容服務以及未來供應商。

核心能力包含使用者註冊登入、管理員面板、使用者 Token、額度計費、用量日誌、OpenAI 相容介面、Claude Messages 介面、自訂上游渠道、加權路由與 Docker 部署。

本機入口：`http://127.0.0.1:3218`

計畫公開入口：`https://router.lazying.art`

詳細操作說明見：[LazyingRouter operator guide](../README.md)。
