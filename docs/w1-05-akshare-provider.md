# W1-05：AkShare 真实行情 Provider

## 本阶段交付

- 建立可替换的 `MarketDataProvider` 接口。
- 接入 AkShare，支持 A 股、美股和港股日线行情。
- 将不同市场的中英文列名统一为 OHLCV 数据结构。
- Data Agent 使用真实日线计算近 30 个交易日涨跌幅和年化波动率。
- 报告证据中记录 `provider`、数据条数、获取时间和是否为 Mock。
- 数据源失败时任务停在 Data Agent，并返回可追踪错误，不生成虚假报告。

## 当前数据范围

| 市场 | AkShare 接口 | 货币 |
| --- | --- | --- |
| A 股 | `stock_zh_a_hist` | CNY |
| 美股 | `stock_us_daily` | USD |
| 港股 | `stock_hk_hist` | HKD |

当前使用未复权日线。真实行情来自公开网站，可能存在延迟、接口变更或临时不可用，产品仍只用于研究和教学。
