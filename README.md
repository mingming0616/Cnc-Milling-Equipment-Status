<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>2廠2F 銑床設備即時狀態看板</title>
  <style>
    /* ===== 全局與基礎樣式 ===== */
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    }
    body {
      background-color: #0f172a;
      color: #f8fafc;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* ===== 頂部標題與導覽列 ===== */
    header {
      background-color: #1e293b;
      padding: 0.8rem 1.2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
      border-bottom: 1px solid #334155;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    header h1 {
      font-size: 1.2rem;
      font-weight: 700;
      color: #38bdf8;
    }
    .nav-tabs {
      display: flex;
      gap: 0.5rem;
    }
    .tab-btn {
      padding: 0.5rem 1rem;
      background-color: #334155;
      color: #cbd5e1;
      border: none;
      border-radius: 0.375rem;
      cursor: pointer;
      font-weight: 600;
      transition: all 0.2s;
    }
    .tab-btn.active {
      background-color: #0284c7;
      color: #ffffff;
    }

    /* ===== 即時數據統計看板 ===== */
    #dashboard {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
      gap: 0.8rem;
      padding: 0.8rem 1.2rem;
      background-color: #1e293b;
      border-bottom: 1px solid #334155;
    }
    .card {
      background-color: #0f172a;
      padding: 0.6rem 0.8rem;
      border-radius: 0.5rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      border-left: 4px solid #94a3b8;
    }
    .card.running { border-left-color: #22c55e; }
    .card.fault { border-left-color: #ef4444; }
    .card.waiting { border-left-color: #eab308; }
    .card.idle { border-left-color: #94a3b8; }

    .card .count {
      font-size: 1.4rem;
      font-weight: 800;
    }
    .card .label {
      font-size: 0.75rem;
      color: #cbd5e1;
      margin-top: 0.1rem;
    }

    /* ===== 內容區域與分頁切換 ===== */
    .tab-content {
      display: none;
      flex: 1;
      padding: 1rem;
    }
    .tab-content.active {
      display: flex;
      flex-direction: column;
    }

    /* --- 平面圖分頁 --- */
    #mapContainer {
      position: relative;
      background-color: #020617;
      overflow: auto;
      display: flex;
      justify-content: center;
      align-items: center;
      border-radius: 0.5rem;
      border: 1px solid #334155;
      min-height: 75vh;
      padding: 1rem;
    }
    #svgWrapper {
      width: 100%;
      max-width: 1400px;
      height: 100%;
    }
    .machine-node {
      cursor: pointer;
      transition: all 0.2s;
    }
    .machine-node:hover {
      filter: drop-shadow(0 0 6px #38bdf8);
      opacity: 0.8;
    }

    /* --- 設備清單分頁 --- */
    .filter-bar {
      display: flex;
      gap: 0.8rem;
      margin-bottom: 1rem;
      flex-wrap: wrap;
    }
    .filter-bar input, .filter-bar select {
      padding: 0.5rem 0.8rem;
      border-radius: 0.375rem;
      border: 1px solid #475569;
      background-color: #1e293b;
      color: #fff;
    }
    .table-container {
      overflow-x: auto;
      background-color: #1e293b;
      border-radius: 0.5rem;
      border: 1px solid #334155;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.9rem;
    }
    th, td {
      padding: 0.75rem 1rem;
      border-bottom: 1px solid #334155;
    }
    th {
      background-color: #0f172a;
      color: #38bdf8;
    }
    tr:hover {
      background-color: #334155;
      cursor: pointer;
    }
    .status-badge {
      padding: 0.2rem 0.6rem;
      border-radius: 1rem;
      font-size: 0.75rem;
      font-weight: bold;
      display: inline-block;
    }
    .badge-running { background-color: #166534; color: #4ade80; }
    .badge-fault { background-color: #991b1b; color: #fca5a5; }
    .badge-waiting { background-color: #854d0e; color: #fef08a; }
    .badge-idle { background-color: #374151; color: #d1d5db; }

    /* ===== 編輯彈窗 Modal ===== */
    .modal {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background-color: rgba(0, 0, 0, 0.75);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
      backdrop-filter: blur(4px);
    }
    .modal.hidden { display: none; }
    .modal-content {
      background-color: #1e293b;
      padding: 1.5rem;
      border-radius: 0.75rem;
      width: 90%;
      max-width: 440px;
      border: 1px solid #475569;
      position: relative;
    }
    .close-btn {
      position: absolute;
      top: 1rem;
      right: 1.2rem;
      font-size: 1.5rem;
      color: #94a3b8;
      cursor: pointer;
    }
    .modal h2 { font-size: 1.2rem; color: #38bdf8; margin-bottom: 1rem; }
    .form-group { margin-bottom: 0.8rem; display: flex; flex-direction: column; gap: 0.3rem; }
    .form-group label { font-size: 0.85rem; color: #cbd5e1; }
    .form-group input, .form-group select {
      padding: 0.5rem;
      border-radius: 0.375rem;
      border: 1px solid #475569;
      background-color: #0f172a;
      color: #fff;
    }
    .btn-submit {
      width: 100%;
      padding: 0.7rem;
      background-color: #16a34a;
      color: #fff;
      border: none;
      border-radius: 0.375rem;
      font-weight: 700;
      cursor: pointer;
      margin-top: 0.5rem;
    }
  </style>
</head>
<body>

  <header>
    <h1>🏭 2廠2F 銑床設備即時狀態看板</h1>
    <div class="nav-tabs">
      <button class="tab-btn active" onclick="switchTab('mapTab')">🗺️ 平面圖 Layout</button>
      <button class="tab-btn" onclick="switchTab('listTab')">📋 全部設備清單</button>
    </div>
  </header>

  <!-- 頂部即時統計 -->
  <section id="dashboard">
    <div class="card running">
      <span class="count" id="countRunning">0</span>
      <span class="label">🟢 生產中</span>
    </div>
    <div class="card fault">
      <span class="count" id="countFault">0</span>
      <span class="label">🔴 設備故障</span>
    </div>
    <div class="card waiting">
      <span class="count" id="countWaiting">0</span>
      <span class="label">🟡 待料</span>
    </div>
    <div class="card idle">
      <span class="count" id="countIdle">0</span>
      <span class="label">⚪ 無排產</span>
    </div>
  </section>

  <!-- 分頁 1: 平面圖 Layout -->
  <main id="mapTab" class="tab-content active">
    <div id="mapContainer">
      <div id="svgWrapper">
        <svg viewBox="0 0 1400 900" xmlns="http://www.w3.org/2000/svg">
          <!-- 廠房外框與區域劃分 -->
          <rect x="10" y="10" width="1380" height="880" fill="#1e293b" stroke="#475569" stroke-width="4" rx="8"/>
          
          <rect x="30" y="30" width="200" height="70" fill="#0f172a" stroke="#334155" stroke-dasharray="4"/>
          <text x="130" y="70" fill="#64748b" font-size="16" text-anchor="middle">QC 檢驗室</text>
          
          <rect x="1170" y="30" width="200" height="70" fill="#0f172a" stroke="#334155" stroke-dasharray="4"/>
          <text x="1270" y="70" fill="#64748b" font-size="16" text-anchor="middle">電器室</text>
          
          <text x="700" y="60" fill="#475569" font-size="20" text-anchor="middle" font-weight="bold">2廠 2F 銑床加工區 (全 134 台)</text>

          <!-- 動態渲染機台的容器容器 -->
          <g id="machineNodesGroup"></g>
        </svg>
      </div>
    </div>
  </main>

  <!-- 分頁 2: 全部設備清單 -->
  <main id="listTab" class="tab-content">
    <div class="filter-bar">
      <input type="text" id="searchInput" placeholder="搜尋資產編號/型號..." oninput="renderTable()">
      <select id="statusFilter" onchange="renderTable()">
        <option value="ALL">全部狀態</option>
        <option value="running">🟢 生產中</option>
        <option value="fault">🔴 設備故障</option>
        <option value="waiting">🟡 待料</option>
        <option value="idle">⚪ 無排產</option>
      </select>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>資產編號</th>
            <th>廠牌</th>
            <th>機台型號</th>
            <th>目前狀態</th>
            <th>生產料號</th>
            <th>製程</th>
            <th>故障原因/備註</th>
            <th>更新人員</th>
          </tr>
        </thead>
        <tbody id="machineTableBody">
        </tbody>
      </table>
    </div>
  </main>

  <!-- 狀態編輯彈窗 (Modal) -->
  <div id="statusModal" class="modal hidden">
    <div class="modal-content">
      <span class="close-btn" onclick="closeModal()">&times;</span>
      <h2 id="modalTitle">設備狀態更新</h2>
      <form id="updateForm">
        <input type="hidden" id="modalMachineId">
        <div class="form-group">
          <label for="modalStatus">設備狀態：</label>
          <select id="modalStatus">
            <option value="running">🟢 生產中</option>
            <option value="fault">🔴 設備故障</option>
            <option value="waiting">🟡 待料</option>
            <option value="idle">⚪ 無排產</option>
          </select>
        </div>
        <div class="form-group">
          <label for="modalPartNumber">生產料號：</label>
          <input type="text" id="modalPartNumber" placeholder="例如: PN-9082">
        </div>
        <div class="form-group">
          <label for="modalProcess">製程：</label>
          <input type="text" id="modalProcess" placeholder="例如: OP20 銑1">
        </div>
        <div class="form-group" id="faultReasonGroup">
          <label for="modalFaultReason">故障原因 / 備註：</label>
          <input type="text" id="modalFaultReason" placeholder="請輸入故障原因">
        </div>
        <div class="form-group">
          <label for="modalUpdatedBy">更新人員：</label>
          <input type="text" id="modalUpdatedBy" placeholder="維護技術員 / 工程師">
        </div>
        <button type="submit" class="btn-submit">儲存並即時同步</button>
      </form>
    </div>
  </div>

  <!-- Firebase 與邏輯膠水碼 -->
  <script type="module">
    import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
    import { 
      getFirestore, collection, doc, setDoc, addDoc, onSnapshot, serverTimestamp 
    } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js";

    // 1. Firebase 設定
    const firebaseConfig = {
      apiKey: "AIzaSyBLe8_cwgGolIQVJyVl7w_Xrf1Bu4LNPnk",
      authDomain: "cnc-milling-equipment-status.firebaseapp.com",
      projectId: "cnc-milling-equipment-status",
      storageBucket: "cnc-milling-equipment-status.firebasestorage.app",
      messagingSenderId: "824263707679",
      appId: "1:824263707679:web:a8aed17d867f610cb6d92a",
      measurementId: "G-QGR2H51K66"
    };

    const app = initializeApp(firebaseConfig);
    const db = getFirestore(app);

    // 2. 匯入 134 台設備資料
    const baseEquipmentList = [{"id": "M02", "model": "TR-45L", "brand": "森合"}, {"id": "M38", "model": "TR-60A", "brand": "森合"}, {"id": "M47", "model": "TR-60A", "brand": "森合"}, {"id": "M48", "model": "TR-60A", "brand": "森合"}, {"id": "M58", "model": "TR-60A", "brand": "森合"}, {"id": "M73", "model": "TR-60A", "brand": "森合"}, {"id": "M121", "model": "TR-60A", "brand": "森合"}, {"id": "M122", "model": "TR-60A", "brand": "森合"}, {"id": "M123", "model": "TR-60A", "brand": "森合"}, {"id": "M126", "model": "TR-45E", "brand": "森合"}, {"id": "M144", "model": "TR-70A", "brand": "森合"}, {"id": "M153", "model": "TC-S2DN", "brand": "Brother"}, {"id": "M154", "model": "TC-S2DN", "brand": "Brother"}, {"id": "M155", "model": "TC-S2DN", "brand": "Brother"}, {"id": "M156", "model": "TC-S2DN", "brand": "Brother"}, {"id": "M157", "model": "TC-S2DN", "brand": "Brother"}, {"id": "M158", "model": "TC-S2DN", "brand": "Brother"}, {"id": "M159", "model": "TC-S2DN", "brand": "Brother"}, {"id": "M160", "model": "TC-S2DN", "brand": "Brother"}, {"id": "M161", "model": "TC-S2DN", "brand": "Brother"}, {"id": "M163", "model": "TC-S2DN-O", "brand": "Brother"}, {"id": "M164", "model": "TC-S2DN-O", "brand": "Brother"}, {"id": "M165", "model": "TC-S2DN-O", "brand": "Brother"}, {"id": "M166", "model": "TC-S2DN-O", "brand": "Brother"}, {"id": "M167", "model": "TC-S2DN-O", "brand": "Brother"}, {"id": "M171", "model": "TC-R2B", "brand": "Brother"}, {"id": "M173", "model": "TC-R2B", "brand": "Brother"}, {"id": "M175", "model": "TC-R2B", "brand": "Brother"}, {"id": "M176", "model": "TC-R2B", "brand": "Brother"}, {"id": "M177", "model": "TC-R2B", "brand": "Brother"}, {"id": "M178", "model": "TC-R2B", "brand": "Brother"}, {"id": "M180", "model": "TC-R2B", "brand": "Brother"}, {"id": "M181", "model": "TC-R2B", "brand": "Brother"}, {"id": "M182", "model": "TC-R2B", "brand": "Brother"}, {"id": "M183", "model": "TC-R2B", "brand": "Brother"}, {"id": "M184", "model": "TC-R2B", "brand": "Brother"}, {"id": "M188", "model": "R450X1", "brand": "Brother"}, {"id": "M192", "model": "R450X1", "brand": "Brother"}, {"id": "M193", "model": "R450X1", "brand": "Brother"}, {"id": "M194", "model": "R450X1", "brand": "Brother"}, {"id": "M195", "model": "R450X1", "brand": "Brother"}, {"id": "M196", "model": "R450X1", "brand": "Brother"}, {"id": "M197", "model": "R450X1", "brand": "Brother"}, {"id": "M198", "model": "R450X1", "brand": "Brother"}, {"id": "M199", "model": "R450X1", "brand": "Brother"}, {"id": "M200", "model": "R450X1", "brand": "Brother"}, {"id": "M201", "model": "R450X1", "brand": "Brother"}, {"id": "M202", "model": "R450X1", "brand": "Brother"}, {"id": "M203", "model": "R450X1", "brand": "Brother"}, {"id": "M204", "model": "R450X1", "brand": "Brother"}, {"id": "M205", "model": "R450X1", "brand": "Brother"}, {"id": "M206", "model": "R450X1", "brand": "Brother"}, {"id": "M207", "model": "R450X1", "brand": "Brother"}, {"id": "M208", "model": "R450X1", "brand": "Brother"}, {"id": "M209", "model": "R450X1", "brand": "Brother"}, {"id": "M210", "model": "R450X1", "brand": "Brother"}, {"id": "M211", "model": "R450X1", "brand": "Brother"}, {"id": "M212", "model": "R450X1", "brand": "Brother"}, {"id": "M213", "model": "R450X1", "brand": "Brother"}, {"id": "M214", "model": "R450X1", "brand": "Brother"}, {"id": "M215", "model": "R450X1", "brand": "Brother"}, {"id": "M216", "model": "R450X1", "brand": "Brother"}, {"id": "M217", "model": "R450X1", "brand": "Brother"}, {"id": "M218", "model": "S700X1", "brand": "Brother"}, {"id": "M219", "model": "S700X1", "brand": "Brother"}, {"id": "M220", "model": "S700X1", "brand": "Brother"}, {"id": "M221", "model": "S700X1", "brand": "Brother"}, {"id": "M222", "model": "S700X1", "brand": "Brother"}, {"id": "M223", "model": "S700X1", "brand": "Brother"}, {"id": "M224", "model": "S700X1", "brand": "Brother"}, {"id": "M225", "model": "S700X1", "brand": "Brother"}, {"id": "M226", "model": "S700X1", "brand": "Brother"}, {"id": "M227", "model": "S700X1", "brand": "Brother"}, {"id": "M228", "model": "S700X1", "brand": "Brother"}, {"id": "M229", "model": "S700X1", "brand": "Brother"}, {"id": "M230", "model": "S700X1", "brand": "Brother"}, {"id": "M234", "model": "S700X1", "brand": "Brother"}, {"id": "M237", "model": "S700X1", "brand": "Brother"}, {"id": "M251", "model": "S500X1", "brand": "Brother"}, {"id": "M252", "model": "S500X1", "brand": "Brother"}, {"id": "M253", "model": "S500X1", "brand": "Brother"}, {"id": "M254", "model": "S500X1", "brand": "Brother"}, {"id": "M255", "model": "S500X1", "brand": "Brother"}, {"id": "M256", "model": "R450X1", "brand": "Brother"}, {"id": "M257", "model": "S700X2", "brand": "Brother"}, {"id": "M258", "model": "S700X2", "brand": "Brother"}, {"id": "M259", "model": "S700X2", "brand": "Brother"}, {"id": "M260", "model": "S700X2", "brand": "Brother"}, {"id": "M261", "model": "S700X2", "brand": "Brother"}, {"id": "M262", "model": "S700X2", "brand": "Brother"}, {"id": "M266", "model": "R450X2", "brand": "Brother"}, {"id": "M267", "model": "R450X2", "brand": "Brother"}, {"id": "M268", "model": "R450X2", "brand": "Brother"}, {"id": "M269", "model": "R450X2", "brand": "Brother"}, {"id": "M270", "model": "S500X2", "brand": "Brother"}, {"id": "M271", "model": "S500X2", "brand": "Brother"}, {"id": "M272", "model": "S500X2", "brand": "Brother"}, {"id": "M273", "model": "S500X2", "brand": "Brother"}, {"id": "M274", "model": "S500X2", "brand": "Brother"}, {"id": "M276", "model": "U500XD1 RD", "brand": "Brother"}, {"id": "M277", "model": "U500XD1 RD", "brand": "Brother"}, {"id": "M278", "model": "U500XD1 RD", "brand": "Brother"}, {"id": "M279", "model": "U500XD1 RD", "brand": "Brother"}, {"id": "M280", "model": "S500XD1", "brand": "Brother"}, {"id": "M281", "model": "S500XD1", "brand": "Brother"}, {"id": "M282", "model": "S500XD1", "brand": "Brother"}, {"id": "M283", "model": "S500XD1", "brand": "Brother"}, {"id": "M284", "model": "S500XD1", "brand": "Brother"}, {"id": "M285", "model": "S500XD1", "brand": "Brother"}, {"id": "M286", "model": "S500XD1", "brand": "Brother"}, {"id": "M287", "model": "S500XD1", "brand": "Brother"}, {"id": "M288", "model": "S500X2", "brand": "Brother"}, {"id": "M289", "model": "S500X2", "brand": "Brother"}, {"id": "M290", "model": "S500X2", "brand": "Brother"}, {"id": "M291", "model": "S500X2", "brand": "Brother"}, {"id": "M292", "model": "S500X2", "brand": "Brother"}, {"id": "M293", "model": "S500X2", "brand": "Brother"}, {"id": "M294", "model": "S500X2", "brand": "Brother"}, {"id": "M295", "model": "S500X2", "brand": "Brother"}, {"id": "M296", "model": "S500X2", "brand": "Brother"}, {"id": "M297", "model": "S500X2", "brand": "Brother"}, {"id": "M298", "model": "S500X2", "brand": "Brother"}, {"id": "M299", "model": "S500X2", "brand": "Brother"}, {"id": "M300", "model": "S500X2", "brand": "Brother"}, {"id": "M301", "model": "S500X2", "brand": "Brother"}, {"id": "M302", "model": "S500X2", "brand": "Brother"}, {"id": "M303", "model": "S500X2", "brand": "Brother"}, {"id": "M304", "model": "S500X2", "brand": "Brother"}, {"id": "M305", "model": "S500X2", "brand": "Brother"}, {"id": "M306", "model": "S500X2", "brand": "Brother"}, {"id": "M307", "model": "S500XD1-5AX", "brand": "Brother"}, {"id": "M308", "model": "S500XD1-5AX", "brand": "Brother"}, {"id": "M309", "model": "S500XD1-5AX", "brand": "Brother"}, {"id": "M310", "model": "S500XD1-5AX", "brand": "Brother"}];

    let realtimeData = {};

    const statusColors = {
      running: "#22c55e",
      fault: "#ef4444",
      waiting: "#eab308",
      idle: "#475569"
    };

    const statusBadges = {
      running: '<span class="status-badge badge-running">🟢 生產中</span>',
      fault: '<span class="status-badge badge-fault">🔴 設備故障</span>',
      waiting: '<span class="status-badge badge-waiting">🟡 待料</span>',
      idle: '<span class="status-badge badge-idle">⚪ 無排產</span>'
    };

    document.addEventListener("DOMContentLoaded", () => {
      renderSvgMachines();
      listenFirestoreRealtime();
      initFormEvents();
      renderTable();
    });

    // 3. 切換分頁
    window.switchTab = function(tabId) {
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
      
      event.target.classList.add('active');
      document.getElementById(tabId).classList.add('active');
    };

    // 4. 動態渲染 134 台設備點位至 SVG 平面圖
    function renderSvgMachines() {
      const group = document.getElementById("machineNodesGroup");
      group.innerHTML = "";

      const cols = 15; // 每行放 15 台設備
      const startX = 50;
      const startY = 130;
      const stepX = 88;
      const stepY = 75;
      const width = 72;
      const height = 48;

      baseEquipmentList.forEach((equip, index) => {
        const col = index % cols;
        const row = Math.floor(index / cols);

        const x = startX + col * stepX;
        const y = startY + row * stepY;

        const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g.setAttribute("class", "machine-node");
        g.setAttribute("data-machine-id", equip.id);
        g.onclick = () => openModal(equip.id);

        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", y);
        rect.setAttribute("width", width);
        rect.setAttribute("height", height);
        rect.setAttribute("rx", "6");
        rect.setAttribute("fill", "#475569");
        rect.setAttribute("stroke", "#64748b");
        rect.setAttribute("stroke-width", "1.5");

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", x + width / 2);
        text.setAttribute("y", y + height / 2 + 5);
        text.setAttribute("fill", "#ffffff");
        text.setAttribute("font-size", "12");
        text.setAttribute("font-weight", "bold");
        text.setAttribute("text-anchor", "middle");
        text.textContent = equip.id;

        g.appendChild(rect);
        g.appendChild(text);
        group.appendChild(g);
      });
    }

    // 5. 監聽 Firestore 即時數據
    function listenFirestoreRealtime() {
      onSnapshot(collection(db, "machines"), (snapshot) => {
        snapshot.forEach((doc) => {
          realtimeData[doc.id] = doc.data();
          updateSvgMachineColor(doc.id, doc.data().status);
        });
        updateDashboardCounts();
        renderTable();
      });
    }

    function updateSvgMachineColor(id, status) {
      const node = document.querySelector(`[data-machine-id="${id}"] rect`);
      if (node) {
        node.setAttribute("fill", statusColors[status] || "#475569");
      }
    }

    function updateDashboardCounts() {
      let counts = { running: 0, fault: 0, waiting: 0, idle: 0 };
      
      baseEquipmentList.forEach(item => {
        const status = (realtimeData[item.id] && realtimeData[item.id].status) || 'idle';
        if (counts[status] !== undefined) counts[status]++;
      });

      document.getElementById("countRunning").textContent = counts.running;
      document.getElementById("countFault").textContent = counts.fault;
      document.getElementById("countWaiting").textContent = counts.waiting;
      document.getElementById("countIdle").textContent = counts.idle;
    }

    // 6. 渲染表格清單
    window.renderTable = function() {
      const tbody = document.getElementById("machineTableBody");
      const search = document.getElementById("searchInput").value.toLowerCase();
      const filter = document.getElementById("statusFilter").value;

      tbody.innerHTML = "";

      baseEquipmentList.forEach(equip => {
        const live = realtimeData[equip.id] || {};
        const currentStatus = live.status || "idle";

        if (filter !== "ALL" && currentStatus !== filter) return;
        if (search && !equip.id.toLowerCase().includes(search) && !equip.model.toLowerCase().includes(search)) return;

        const tr = document.createElement("tr");
        tr.onclick = () => openModal(equip.id);
        tr.innerHTML = `
          <td><strong>${equip.id}</strong></td>
          <td>${equip.brand}</td>
          <td>${equip.model}</td>
          <td>${statusBadges[currentStatus]}</td>
          <td>${live.partNumber || "-"}</td>
          <td>${live.process || "-"}</td>
          <td>${live.faultReason || "-"}</td>
          <td>${live.updatedBy || "-"}</td>
        `;
        tbody.appendChild(tr);
      });
    };

    // 7. 彈窗與表單邏輯
    window.openModal = function(id) {
      const modal = document.getElementById("statusModal");
      const data = realtimeData[id] || {};
      const baseInfo = baseEquipmentList.find(e => e.id === id) || {};

      document.getElementById("modalTitle").textContent = `⚙️ 設備 ${id} (${baseInfo.model || ""}) 狀態更新`;
      document.getElementById("modalMachineId").value = id;
      document.getElementById("modalStatus").value = data.status || "idle";
      document.getElementById("modalPartNumber").value = data.partNumber || "";
      document.getElementById("modalProcess").value = data.process || "";
      document.getElementById("modalFaultReason").value = data.faultReason || "";
      document.getElementById("modalUpdatedBy").value = data.updatedBy || "";

      modal.classList.remove("hidden");
    };

    window.closeModal = function() {
      document.getElementById("statusModal").classList.add("hidden");
    };

    function initFormEvents() {
      document.getElementById("updateForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const id = document.getElementById("modalMachineId").value;
        const updateData = {
          status: document.getElementById("modalStatus").value,
          partNumber: document.getElementById("modalPartNumber").value,
          process: document.getElementById("modalProcess").value,
          faultReason: document.getElementById("modalFaultReason").value,
          updatedBy: document.getElementById("modalUpdatedBy").value
        };

        try {
          await setDoc(doc(db, "machines", id), {
            ...updateData,
            updatedAt: serverTimestamp()
          }, { merge: true });

          await addDoc(collection(db, "history"), {
            machineId: id,
            ...updateData,
            timestamp: serverTimestamp()
          });

          closeModal();
        } catch (err) {
          console.error(err);
          alert("更新失敗，請檢查網路連線！");
        }
      });
    }
  </script>
</body>
</html>
