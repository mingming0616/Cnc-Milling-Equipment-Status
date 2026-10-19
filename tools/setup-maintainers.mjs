// 建立 / 更新維護員帳號（管理者在自己電腦上執行一次即可，不要放到網站上）
//
//   1. Firebase 主控台 → 專案設定 → 服務帳戶 → 產生新的私密金鑰，存成 serviceAccount.json
//   2. npm install firebase-admin
//   3. node tools/setup-maintainers.mjs ./serviceAccount.json
//
// 會為每位人員建立 Firebase 帳號（工號@EMAIL_DOMAIN）、產生隨機初始密碼，
// 並寫入 maintainers/{uid}。初始密碼輸出到 initial-passwords.csv，發給本人後請刪除該檔。
// 已存在的帳號不會重設密碼。要移除某人權限：刪除 Firestore 中他的 maintainers 文件，並在 Authentication 停用帳號。

import { readFileSync, writeFileSync } from "node:fs";
import { randomInt } from "node:crypto";
import admin from "firebase-admin";

const EMAIL_DOMAIN = "cnc-milling-equipment-status.firebaseapp.com"; // 需與 index.html 相同

// [工號, 姓名]
const STAFF = [
  ["09043", "劉德康"], ["08020", "何敬豐"], ["08003", "陳明秀"], ["88822004", "李意明"],
  ["17036", "賴頎仁"], ["12024", "邱柏雄"], ["08013", "姜棋祥"], ["12101", "江明旭"],
  ["13092", "林昊騰"], ["15048", "黎文杰"], ["10171", "林秉健"], ["10149", "李國偉"],
  ["11049", "阮玉碧"], ["11054", "黎芳瑜"], ["21033", "葉兆嵐"], ["19007", "李文傑"],
  ["13012", "唐婉綺"]
];

const keyPath = process.argv[2];
if (!keyPath) {
  console.error("用法：node tools/setup-maintainers.mjs ./serviceAccount.json");
  process.exit(1);
}

admin.initializeApp({ credential: admin.credential.cert(JSON.parse(readFileSync(keyPath, "utf8"))) });
const auth = admin.auth();
const db = admin.firestore();

function genPassword() {
  const chars = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let s = "";
  for (let i = 0; i < 10; i++) s += chars[randomInt(chars.length)];
  return s;
}

const rows = [["工號", "姓名", "初始密碼"]];
for (const [empNo, name] of STAFF) {
  const email = `${empNo.toLowerCase()}@${EMAIL_DOMAIN}`;
  let user;
  let password = "";
  try {
    user = await auth.getUserByEmail(email);
    console.log(`已存在　${empNo} ${name}`);
  } catch (err) {
    if (err.code !== "auth/user-not-found") throw err;
    password = genPassword();
    user = await auth.createUser({ email, password, displayName: name });
    console.log(`已建立　${empNo} ${name}`);
  }
  await db.doc(`maintainers/${user.uid}`).set({ name, empNo }, { merge: true });
  rows.push([empNo, name, password || "(沿用原密碼)"]);
}

writeFileSync("initial-passwords.csv", "﻿" + rows.map(r => r.join(",")).join("\r\n"));
console.log("\n完成。初始密碼已輸出到 initial-passwords.csv（發給本人後請刪除）");
