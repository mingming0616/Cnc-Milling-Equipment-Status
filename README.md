# 旭申 銑床設備即時看板 v3.3：上線設定步驟

v3.x 改用 **Firebase Authentication** 登入，並由 **Firestore 安全規則** 在伺服器端擋下未授權的修改。
上線前，管理者需要完成下面 4 個步驟（約 20 分鐘）。

> ⚠️ 請先完成步驟 1～3，再替換網頁。否則新版網頁會因為沒有帳號而無法登入。

## 1. 開啟 Email/密碼登入
Firebase 主控台 → **Authentication** → 登入方式 → 啟用「**電子郵件/密碼**」。

## 2. 建立維護員帳號（二擇一）

**A. 用腳本一次建立（建議）**
1. Firebase 主控台 → ⚙️ 專案設定 → **服務帳戶** → 「產生新的私密金鑰」，存成 `serviceAccount.json`。
   這把金鑰權限很大，**不要上傳到網站或 Git**。
2. 在這個資料夾執行：
   ```bash
   npm install firebase-admin
   node tools/setup-maintainers.mjs ./serviceAccount.json
   ```
3. 產生的 `initial-passwords.csv` 裡有每個人的初始密碼。發給本人後請刪除檔案，
   並請大家登入後點右上角頭像 →「修改密碼」。

**B. 手動建立**
1. Authentication → 使用者 → 新增使用者
   - 電子郵件：`工號@cnc-milling-equipment-status.firebaseapp.com`（例：`09043@cnc-milling-equipment-status.firebaseapp.com`）
   - 密碼：至少 8 碼
2. 複製該使用者的 **UID**。
3. Firestore → 建立集合 `maintainers` → 文件 ID 填 UID，欄位 `name`（姓名，字串）、`empNo`（工號，字串）。

登入畫面輸入的是「**工號 + 密碼**」。

## 3. 部署安全規則與索引
**用 Firebase CLI：**
```bash
npm install -g firebase-tools
firebase login
firebase deploy --only firestore:rules,firestore:indexes
```
**或手動：** 把 `firestore.rules` 的內容貼到 Firestore →「規則」→ 發布。
索引的部分，第一次在「異動履歷」選擇單一機台時，畫面會顯示一個建立索引的連結，點擊即可建立。

## 4. 替換網頁
把 `index.html` 放到原本的網址。

---

## 人員異動
- **新增人員**：把他加到 `tools/setup-maintainers.mjs` 的 `STAFF` 清單，再執行一次腳本（已存在的帳號不會被重設）。
- **移除人員**：刪除他在 `maintainers` 集合中的文件（立即失去寫入權限），再到 Authentication 停用帳號。
- **忘記密碼**：到 Authentication 找到該帳號，重設密碼。

## 可調整的設定（index.html 最上方的「設定區」）
| 常數 | 用途 |
|---|---|
| `FAULT_LONG_MIN` | 故障超過幾分鐘改為快速粗框閃爍（預設 120） |
| `TV_ROTATE_SEC` / `TV_FLOORS` | 看板模式的輪播秒數與廠區順序 |
| `TV_SOUND` | 看板模式有新故障時嗶兩聲（瀏覽器規定頁面要先被點過一次才能出聲） |
| `TV_RELOAD_HOUR` | 看板模式每天幾點自動重新整理，讓電視載入最新版網頁（預設 5 點） |
| `UTIL` | 稼動率公式。例如要把借出機台排除在分母外：`excludeFromTotal: ["borrowed"]` |
| `FAULT_CATEGORIES` | 故障分類選項 |

## 看板電視網址
- `index.html?tv=1`：看板模式，自動輪播所有廠區
- `index.html?tv=1&floor=2F_2`：看板模式，固定顯示 2廠 2F

電視看板模式會保持螢幕常亮（需瀏覽器支援 Wake Lock，Chrome / Edge 可以）。
有機台變成故障時，畫面會自動跳到該廠區並發出提示音。

## 與舊版資料的相容性
- 舊的 `machines` 和 `history` 資料可以直接沿用。
- 舊資料沒有「狀態開始時間」，持續時間會先以「最後更新時間」估算。下一次變更狀態之後就會準確。
- 舊版的寫死密碼已從網頁移除。由於原始碼曾經公開，請不要再把工號當作密碼使用。

## 平面圖（v3.3）
- **2廠 2F 依正式 DXF 圖面產生**：牆、柱、樓梯、門、區域名稱、預定通道、消防設施都照圖面，134 台機台照實際位置與大小。
- 資料檔是 `floorplans/2F_2.js`，**上傳網站時要連同 `floorplans` 資料夾一起上傳**，否則 2廠 2F 會顯示「找不到平面圖資料檔」。
- 地圖右上角可以切換「平面 / 立體」，以及開關「通道 / 設施細節 / 消防」圖層。
- 其他廠區還沒有 DXF，暫時維持原本的區塊式排列。

### 廠房配置變更時（重新產生平面圖）
1. 在 AutoCAD 另存成 DXF（2013 或 2018 版）。
2. 執行：
   ```bash
   pip install ezdxf
   python tools/dxf-to-floorplan.py 新圖面.dxf 2F_2 > floorplans/2F_2.js
   ```
3. 程式會在畫面上列出機台數量；如果有機台沒有畫成圖塊，也會列出是參考哪台估算的。
4. 打開網頁的開發者工具 Console，確認「設備配置檢查」沒有出現警告（例如圖面上的機台不在設備主檔裡）。

**畫圖時的注意事項**（讓程式能正確辨識）：
- 每台機台要有含編號的文字，例如 `M296`，並且放在機台圖塊的範圍內。
- 機台最好畫成圖塊（block），不要用散線。
- 牆放在「建築結構」圖層，通道放在「預定通道」圖層，消防設施放在「消防設施」圖層。

**其他廠區要改用 DXF**：產生 `floorplans/<廠區代碼>.js` 之後，在 `index.html` 加一行 `<script src="floorplans/<廠區代碼>.js"></script>`，並把 `floorConfigs` 裡該廠區改成 `plan: (window.FLOORPLANS || {})["<廠區代碼>"]` 即可。
