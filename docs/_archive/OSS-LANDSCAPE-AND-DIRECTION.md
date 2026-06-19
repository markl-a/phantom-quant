> ARCHIVED 2026-06-19 — 內容已併入 docs/phantom-quant.md;此為歷史版本。

# phantom-quant 的開源生態盤點與建議方向

> 研究參考資料彙整於 2026-06-19。以下每一項專案陳述皆有所擷取來源佐證（GitHub 倉庫頁面，或
> 2025/2026 年的網路來源）；URL 皆內嵌於文中，而星數／授權／活躍度數據皆引用自這些擷取來源。
> 凡未經直接查證的數據，皆標記 `[unverified]`。本文為決策輔助，而非規格書 —— 專案狀態請以
> `ROADMAP.md` 為準裁定。

---

## 1. phantom-quant 現況（依據 README.md + ROADMAP.md @ `ed6a1f1`）

- **它是什麼：** 一套 台股（Taiwan-stock）的 **回測 → 模擬 → 實盤**（backtest → paper → live）
  交易引擎，以 **Python** 撰寫，封裝為 `phantom-quant`，附帶 CLI（`backtest`、`paper`、`import-csv`）。
  屬於 phantom-mesh 生態系的一部分。
- **設計立場：** 回測完全 **離線**，僅以快取的 CSV/Parquet K 線為來源 —— 執行期無券商、
  無網路、無真實金錢。高度強調 **可稽核性**（auditability）：位元穩定（byte-stable）、
  確定性（deterministic）的產出物（`trades.csv`、`equity.csv`、`run.json`、`report.md`），
  以 golden-byte 測試把關，執行期不取時鐘／SHA，使輸出可重現。
- **今日已交付（126 個通過的測試）：** 凍結的 OHLCV `Bar`；`Decimal` 投資組合；一套真實的
  台股 手續費／稅／跳動點（tick）**成本模型**；±10% 漲跌停 限制鎖定（limit-lock）的成交把關；
  滑價（slippage）模型；事件驅動（event-driven）的 `Strategy`/`Order`/`Context` 契約；
  `BarProvider` ABC + `CsvProvider` + Parquet 儲存層 + `CachedProvider`；結構化資料驗證
  （遇到壞 K 線即大聲失敗）；**一支** 策略（`sma_cross`）；事件驅動的回測引擎；一個
  `BarEventDriver`；一套 **封閉式的模擬模擬交易核心**（`PaperBroker`/`PaperAccount`，並已證明
  `paper == backtest` 等價）；一個具型別（typed）的 `StrategyRegistry`；以及風險指標
  （Sharpe / CAGR / 年化波動率，即將延伸至 Sortino/Calmar）。
- **明確尚未建置：** 任何 **實盤券商下單路徑**（`pyproject.toml` 中宣告了 `Broker` ABC 與一個選用的
  `shioaji` extra，但尚無實盤路徑）；超過一支以上的策略；任何 **線上市場資料抓取器**
  （依設計，所有 provider 皆僅限離線）。

**對本專案性格的解讀：** phantom-quant 是一套小巧、**紀律嚴明、以正確性為先的單一資產類別引擎**。
相較於以下開源生態，它的差異化 *並非* 廣度或效能 —— 而是 **確定性 + 可稽核性 + 台股 專屬的市場
微結構**（手續費、稅、跳動點、漲跌停 限制），這些是底下幾個大型通用框架開箱即用都不會建模的。
這正是要保護的資產。

---

## 2. 開源生態盤點

### 2.1 經典量化框架 —— 回測 +（有時）實盤

| Project | What it is | URL | Lang | License | Maturity / activity | Backtest / Live |
|---|---|---|---|---|---|---|
| **NautilusTrader** | 生產級、Rust-core + Python 事件驅動交易引擎；回測與實盤之間「零程式碼變更對等（zero-code-change parity）」。 | https://github.com/nautechsystems/nautilus_trader | Rust + Python | LGPL-3.0 `[unverified license]` | ~23.6k★；**非常活躍**（v1.228.0 Beta, 2026-06-08） | 兩者皆有 |
| **backtrader** | 經典的事件驅動 Python 回測函式庫（含部分券商整合）。 | https://github.com/mementum/backtrader | Python | GPL-3.0 | ~22k★；**維護模式**（原作者大致已不活躍；社群分支如 `backtrader_next` 存在） | 回測 + 部分實盤 |
| **vectorbt** | 向量化（NumPy/pandas/Numba）回測器，用於大規模參數掃描；「~70–100ms 內處理一百萬筆訂單」。 | https://github.com/polakowo/vectorbt | Python | Apache-2.0 `[unverified license]` | ~6.8k★；活躍；另有付費「PRO」版本 | 回測（研究用） |
| **Zipline-reloaded** | 由 Stefan-Jansen 維護的 Quantopian Zipline 分支；Pythonic 的事件驅動回測器（書籍配套）。 | https://github.com/stefan-jansen/zipline-reloaded | Python | Apache-2.0 `[unverified license]` | 2025 年積極維護（Py 3.9+） | 回測 |
| **QuantConnect LEAN** | 久經沙場的雲端平台骨幹；股票/外匯/期貨/選擇權/加密貨幣。 | https://github.com/QuantConnect/Lean `[unverified URL]` | C# + Python | Apache-2.0 | 活躍、規模大 | 兩者皆有（尤其透過 QC 雲端） |
| **Freqtrade** | 加密貨幣交易機器人 → 完整的策略開發框架；回測 + **實盤**、ML hyperopt（FreqAI）、Telegram UI。 | https://github.com/freqtrade/freqtrade | Python | **GPL-3.0** | ~51.6k★；**非常活躍**（2026.5.1, 2026-06-03） | 兩者皆有（僅限加密貨幣） |
| **Jesse** | 加密貨幣策略研究 + 實盤框架。 | https://github.com/jesse-ai/jesse `[unverified URL]` | Python | MIT | 活躍 | 兩者皆有（加密貨幣） |
| **Hummingbot** | 用於 CEX + DEX 的造市（market-making）／自動化交易框架。 | https://github.com/hummingbot/hummingbot `[unverified URL]` | Python | Apache-2.0 | 活躍 | 實盤（加密貨幣造市） |
| **vn.py** | 聚焦中國市場的完整量化平台（CTP 等）。 | https://github.com/vnpy/vnpy `[unverified URL]` | Python | MIT `[unverified]` | 活躍（中國 A 股／期貨） | 兩者皆有 |
| **bt / vectorbt-lite, etc.** | 輕量的投資組合／策略回測函式庫。 | — | Python | varies | varies | 回測 |

**對 phantom-quant 的啟示：**
- 加密貨幣機器人（Freqtrade/Jesse/Hummingbot/Hummingbot）是 **錯誤的資產類別**（台股，非加密貨幣）—— 僅可作為實盤迴圈／風控／Telegram 控制設計的 *樣式（pattern）* 參考，不適合作為基底。
- **GPL-3.0（backtrader、Freqtrade）** 是實質限制：連結／衍生會迫使 phantom-quant 也變成 GPL。phantom-mesh 核心已採用 **AGPL**（依生態記憶），因此 GPL *算是相容*，但仍值得做一次自覺的授權決策。**Apache-2.0/MIT** 選項（NautilusTrader 之類、vectorbt、Zipline-reloaded、LEAN、Jesse、vn.py）則較容易混用。
- **NautilusTrader** 是最可信的「回測==實盤對等、生產級」引擎，但它是一套 **沉重** 的 Rust+Python 平台 —— 採用它意味著要繼承龐大的相依，並在其抽象之中重新表達 台股 成本模型。對一套個人單兵引擎而言很可能是 **過度建置**。
- **vectorbt** 是最強的 *互補品*：phantom-quant 的事件驅動引擎以正確性為先，但在參數掃描時偏慢；vectorbt 恰恰相反。它是 **研究級掃描的輔助工具**，而非可稽核核心的替代品。

### 2.2 AI / ML / LLM-agent 交易

| Project | Approach | URL | Lang | License | Maturity | Real vs demo |
|---|---|---|---|---|---|---|
| **Microsoft Qlib** | 以 AI 為導向的量化平台：監督式 ML + RL + 市場動態建模；現已整合 RD-Agent 以自動化研究。 | https://github.com/microsoft/qlib | Python | **MIT** | ~44.8k★；v0.9.7（2025-08-15） | **真實** 的研究平台 |
| **FinRL**（AI4Finance） | 用於交易的深度強化學習（deep-reinforcement-learning）函式庫。 | https://github.com/AI4Finance-Foundation/FinRL `[unverified URL]` | Python | MIT `[unverified]` | 活躍 | 研究／教育 |
| **FinGPT**（AI4Finance） | 金融 NLP 的 LLM 試驗場（在 ~50k 金融樣本上對 LLaMA/ChatGLM 做 LoRA 微調）。 | https://github.com/AI4Finance-Foundation/FinGPT `[unverified URL]` | Python | MIT `[unverified]` | 活躍 | 研究 |
| **TradingAgents**（Tauric Research） | **多代理（multi-agent）LLM** 公司模擬（基本面/情緒/技術分析師 → 交易員 → 風控團隊）；LangGraph；眾多 LLM 供應商，含 **Ollama（本地）**、Anthropic、OpenAI。 | https://github.com/TauricResearch/TradingAgents | Python | **Apache-2.0** | ~87.2k★；v0.2.5（2026-05-11） | **僅供研究/示範**（「非投資建議」；模擬執行） |
| **virattt/ai-hedge-fund** | 多代理系統，19 個代理（14 個仿照知名投資人 + 4 個分析型 + 風控 + PM）；支援 Ollama 本地。 | https://github.com/virattt/ai-hedge-fund | Python | **MIT** | ~60.2k★；更新於 2026-06-17 | **僅供模擬** —— 「系統實際上不會進行任何交易」 |

**啟示：**
- 大型 LLM-agent 倉庫（**TradingAgents**、**ai-hedge-fund**）**明確只做訊號生成／決策模擬 —— 它們並不執行交易。** 這正是 phantom-mesh+phantom-quant 可填補的缺口：在代理的訊號底下，提供一層 *受治理、可稽核的執行 + 模擬交易基底*。兩者皆支援 **本地 Ollama**，契合 phantom-mesh 的本地優先（local-first）／自帶模型（BYO-model）立場。
- **Qlib** 是嚴肅的 ML 研究平台（MIT），但其資料假設以中國 A 股為中心，且是一套沉重的框架；可作為 **特徵/alpha 研究來源**，而非執行基底。
- **RL（FinRL）** 高投入、脆弱，對單兵操作者而言鮮少勝過簡單的基準 —— **誠實警告：初期不值得。**

### 2.3 交易自動化／執行包裝層

| Project | What it is | URL | Lang | License | Notes |
|---|---|---|---|---|---|
| **Shioaji（永豐金）** | 官方永豐金（SinoPac）跨平台交易 API —— **台股 股票/期貨/選擇權**，原生 Python（`import shioaji as sj`），即時資料 + 下單 + 帳務。 | https://github.com/Sinotrade/Shioaji | Python（+others） | proprietary-ish broker SDK `[verify license]` | **台股 實盤的正確券商** —— 已宣告於 phantom-quant 的 `broker` extra 中。 |
| **ccxt** | 橫跨 **105 個加密貨幣交易所** 的統一 API。 | https://github.com/ccxt/ccxt | JS/TS/Py/C#/PHP/Go/Java | **MIT** | ~43k★；極度活躍（96k+ commits）。**僅加密貨幣 —— 非 台股。** 僅在範圍擴及加密貨幣時才相關。 |
| **alpaca-py** | 官方 Alpaca SDK —— 美股/加密貨幣，模擬 + 實盤。 | https://github.com/alpacahq/alpaca-py `[unverified URL]` | Python | Apache-2.0 `[unverified]` | 美國市場；良好的 *模擬交易* 參考。 |
| **ib_insync** | 對 Interactive Brokers（全球，含部分亞洲）的 Pythonic 同步/非同步包裝。 | https://github.com/erdewit/ib_insync `[unverified URL]` | Python | BSD `[unverified]` | IBKR 可觸及 TW，但 Shioaji 才是原生契合。注意：原 `ib_insync` 在作者辭世後已封存（archived），社群以 `ib_async` 延續。`[verify]` |

**啟示：** 對 台股 實盤而言，**Shioaji 是要包裝的那一個** —— 它已是規劃中的 `broker` extra。ccxt/alpaca/ib_insync 皆超出資產類別，僅在範圍擴張時才重要。

### 2.4 資料來源（免費／便宜，與 台股 相關）

| Source | What | URL | Notes |
|---|---|---|---|
| **FinMind** | 開放的、聚焦 台股 的資料：50+ 資料集（日線 + 自 2019-05 起的 5 秒 tick、財報、法人買賣超），每日更新的 Python SDK。 | https://github.com/FinMind/FinMind | **無須註冊**（300 req/hr；持免費 token 為 600）。**最佳的免費 台股 抓取器。** |
| **Shioaji market data** | 透過券商 API 取得的即時 + 歷史 台股 報價。 | https://github.com/Sinotrade/Shioaji | 與實盤執行自然搭配。 |
| **TWSE / TPEx open data** | 官方交易所端點（代碼、日線）。 | https://www.twse.com.tw `[reference]` | 權威但原始；FinMind 已包裝其中大部分。 |
| **twstock** | 輕量的 台股 報價函式庫。 | https://github.com/mlouielu/twstock `[unverified URL]` | 簡單；完整度不如 FinMind。 |

---

## 3. phantom-quant 的建議方向

**論點：保持可稽核、確定性、台股 原生的核心（CORE）原樣不動，並 停止 試圖在工程上勝過那些大型
框架。僅在 phantom-quant 真正薄弱的兩個邊緣採用開源 —— (a) 線上資料擷取 與 (b) 實盤執行 ——
並把 *代理層（agent layer）* 定位為差異化所在，而非回測引擎。**

- **保留／**請勿**替換：** 事件驅動引擎、`Decimal` 投資組合、台股 成本模型、漲跌停／成交把關、
  確定性產出物、paper==backtest 等價。這份可稽核性是 phantom-quant 的護城河；在
  NautilusTrader/Zipline 上重建只會 *失去* 它。**不要為了採用框架而抽掉核心。**
- **在 資料邊緣 直接採用：** 新增一個由 **FinMind**（免費、台股 原生、免註冊）支撐的 *線上*
  `BarProvider`，寫入既有的 Parquet 快取。這既保持回測離線/確定性（抓取一次後即快取），又消除
  「僅限 CSV」的缺口。
- **在 執行邊緣 直接採用：** 針對 **Shioaji** 實作已宣告的 `Broker` ABC，作為實盤/模擬實盤路徑。
  保留模擬的 `PaperBroker` 作為預設，並把任何真實金錢路徑閘控在明確的治理之後（契合 phantom-mesh
  的 ④-安全無人值守 + governor + 手機核可 樣式）。
- **向 vectorbt 借樣式而非借程式碼，** 以供未來的「研究模式」參數掃描 —— 僅在單次回測變得太慢時
  才需要。在那之前都屬 **過度建置**。
- **把 LLM-agent 層（phantom-mesh）定位為訊號的消費者，而非重寫：** 大型代理倉庫
  （TradingAgents、ai-hedge-fund）證明了對多代理 *訊號生成* 有巨大興趣，但它們
  **刻意不執行**。phantom-quant 那受治理、可稽核的 回測→模擬→實盤 基底，正是這類代理底下所缺的
  「安全執行底盤（safe execution floor）」。整合方式為：*代理發出訊號 → phantom-quant 以確定性
  方式回測/模擬驗證 → 透過 Shioaji 進行受治理的實盤執行*。這就是那個獨特、可防禦的利基。
- **不要在初期 做強化學習（FinRL）或微調金融 LLM（FinGPT）。** 高投入、脆弱，對單兵操作者而言
  鮮少勝過簡單基準。標記為研究好奇心，而非路線圖。

### 分階段路徑（務實、單兵尺度）

1. **P-next-A —— 線上資料（低風險）：** FinMind 支撐的 `BarProvider` → Parquet 快取；
   保持確定性的離線回測。消除最大的實務缺口（僅限 CSV）。
2. **P-next-B —— 透過註冊表擴增策略：** 經由既有的 `StrategyRegistry` 加入 2–3 支參考策略
   （例如 動量/突破、均值回歸）。便宜、高價值，能操練接縫（seam）。
3. **P-next-C —— Shioaji 模擬實盤 `Broker`：** 接上 `broker` extra；路由經過既有的 `Broker`
   ABC；**模擬/實盤閘控於治理之後**，真實金錢預設關閉（OFF）。
4. **P-next-D —— phantom-mesh 代理橋接：** 暴露一個輕薄介面，讓 phantom-mesh 代理能 (i) 請求對
   提案策略/參數做確定性回測，以及 (ii) 提交一筆 *受治理* 的模擬/實盤訂單。這是 phantom-quant
   成為生態系獨有之處。
5. **P-later（選用）—— vectorbt 研究模式** 用於快速掃描；僅在需要時才做。

### 誠實的風險／過度建置警告

- **最大風險 = 範圍蔓延成通用框架。** NautilusTrader/Qlib/LEAN 很誘人，但每一套都是多年期平台；
  採用其一等於拿可稽核的 台股 核心，去交換你身為單兵 台股 操作者並不需要的通用性。**抵抗它。**
- **授權衛生：** 避免 *衍生自* GPL-3.0 程式碼（backtrader、Freqtrade），除非你接受 GPL/AGPL
  的傳染性。優先採用 MIT/Apache 參考（Qlib、vectorbt、Zipline-reloaded、TradingAgents、
  ai-hedge-fund）。在交付實盤路徑前，先查證 Shioaji 的 SDK 授權條款。
- **真實金錢 = 危險區。** 把真實執行閘控在 phantom-mesh 治理 + 手機核可 之後；預設關閉（OFF）；
  對稱的關閉開關（symmetric off-switch）。你已擁有的可稽核產出物，正是實盤交易飛行記錄器
  （flight-recorder）的正確基底。
- **上述各個 `[unverified]` 標記**（部分 URL、數個授權、ib_insync→ib_async 分支狀態）在被寫入
  程式碼/相依之前，皆應對照活躍倉庫加以確認。

---

## 4. 最值得採用的單一開源（精選短名單）

1. **FinMind** —— https://github.com/FinMind/FinMind —— 免費、台股 原生資料；資料邊緣的採用對象。（MIT 之類，免註冊。）
2. **Shioaji** —— https://github.com/Sinotrade/Shioaji —— 實盤/模擬實盤路徑的原生 台股 券商；已在你的 `broker` extra 中。
3. **vectorbt** —— https://github.com/polakowo/vectorbt —— Apache-2.0 向量化掃描引擎；未來研究模式的 *互補品*，而非核心替代。
4. **TradingAgents** —— https://github.com/TauricResearch/TradingAgents —— Apache-2.0、~87k★，多代理 LLM 訊號層的參考（可用本地 Ollama）；它明確 *不執行* → 正是 phantom-quant 填補的缺口。
5. **virattt/ai-hedge-fund** —— https://github.com/virattt/ai-hedge-fund —— MIT、~60k★，與 #4 同一課題（只有訊號、不執行）；代理橋接的良好架構參考。

---

### 來源（擷取於 2026-06-19）
- https://github.com/microsoft/qlib (44.8k★, MIT, v0.9.7 2025-08-15)
- https://github.com/TauricResearch/TradingAgents (87.2k★, Apache-2.0, v0.2.5 2026-05-11)
- https://github.com/virattt/ai-hedge-fund (60.2k★, MIT, 2026-06-17)
- https://github.com/freqtrade/freqtrade (51.6k★, GPL-3.0, 2026.5.1 2026-06-03)
- https://github.com/mementum/backtrader (~22k★, GPL-3.0)
- https://github.com/ccxt/ccxt (~43k★, MIT, 105 exchanges)
- https://github.com/Sinotrade/Shioaji (台股 broker API)
- https://github.com/FinMind/FinMind (台股 open data)
- https://github.com/nautechsystems/nautilus_trader (~23.6k★, Rust+Python, v1.228.0 2026-06-08)
- https://github.com/polakowo/vectorbt (~6.8k★)
- https://github.com/stefan-jansen/zipline-reloaded (maintained 2025)
- Comparison context: https://autotradelab.com/blog/backtrader-vs-nautilusttrader-vs-vectorbt-vs-zipline-reloaded ; https://python.financial/
