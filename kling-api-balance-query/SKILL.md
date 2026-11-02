---
name: kling-api-balance-query
description: Use when 查可灵(Kling)账户还剩多少积分/资源包余额（API 方式）。
version: 1.0.0
author: 飞书21号
license: internal
metadata:
  hermes:
    tags: [kling, 可灵, api, 余额, 积分, resource-pack]
tags: [kling, 可灵, api, 余额, 积分, resource-pack]
---

## When to Use（何时用）
用户问"可灵还剩多少积分/余额/资源包"，或要确认某 key 账户可用额度时。

# 可灵 API 余额/资源包查询

## 端点（关键：不是 /v1/ 前缀）
`GET https://api-beijing.klingai.com/account/costs?start_time=<ms>&end_time=<ms>`
- **不带 /v1/**（`/v1/account/costs` 会 404）。
- 必须带 `start_time`（否则 400 Missing Request Parameter）；用 `start_time=0&end_time=now_ms` 拿全量。
- 鉴权：`Authorization: Bearer <JWT>`，JWT = HS256(iss=AccessKey, exp=now+1800, nbf=now-5) 用 SecretKey 签。
- 全球域名 `api.klingai.com/account/costs` 用国内 beijing key 会 401；**国内一律用 api-beijing.klingai.com**。

## 返回
`data.resource_pack_subscribe_infos[]`，每包字段：`resource_pack_name / total_quantity / remaining_quantity / status(online有效|expired过期|runOut用完) / invalid_time(到期ms)`。
- 可用余额 = 各 `status==online` 包的 `remaining_quantity` 之和（视频/图像分开，按名称含"视频/图像"区分）。
- **过期包即使 remaining>0 也算 0**（作废）。

## 单位（易错）
`remaining_quantity` 是**积分(Units)**，不是视频条数。1积分≈1元。按秒计费：标准模式~0.5积分/秒、高品质~0.8、高配模型(4.0/带原生音)~1.0积分/秒。
换算条数：5秒/条 ≈ 积分 / (每秒积分×5)。

## 取 key
`/path/to/project / _SECRET_KEY；default 常与某 label 同账户）；kling_api.py 也可能读 `/path/to/project key 可能指向同一账户。139 类失效 key 会 401 access key not found。

## 脚本套路
见本机 `/path/to/project `/path/to/project urllib + 上面签名即可。

## 注意
- API 不查"视频条数"，只给积分；用户常把积分当条数 → 主动说清 1积分≈1元、按秒扣。
- 用户反复问"还有多少"时，每次都实时重查（会用随降），可报与上次的差值证实时。
