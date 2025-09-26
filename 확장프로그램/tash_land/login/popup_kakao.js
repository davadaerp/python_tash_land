// ====== 공통 ======
//const SERVER = "http://127.0.0.1:5000";
const SERVER = "https://erp-dev.bacchuserp.com";
const OAUTH_LOGIN_URL = `${SERVER}/api/kakao/login`;
const OAUTH_LOGOUT_URL = `${SERVER}/api/kakao/logout`;
const API_ME_URL = `${SERVER}/api/kakao/me`;

const loginSection = document.getElementById("login-section");
const userSection  = document.getElementById("user-section");
const nicknameEl   = document.getElementById("nickname");
const smsCountEl   = document.getElementById("sms-count");
const btnLogin     = document.getElementById("btn-login");
const btnLogout    = document.getElementById("btn-logout");
const toast        = document.getElementById("toast");

// ---- 유틸: chrome.storage를 Promise로 래핑 ----
function csGet(keys) {
    return new Promise(resolve => chrome.storage.local.get(keys, resolve));
}

// chrome.storage.local을 Promise로 감싸서 정확히 저장 후 UI 갱신
function csSet(obj) {
    return new Promise(resolve => chrome.storage.local.set(obj, resolve));
}

function showToast(msg) {
    toast.textContent = msg;
    toast.classList.remove("hidden");
    setTimeout(() => toast.classList.add("hidden"), 1500);
}

function setLoggedOutUI() {
    userSection.classList.add("hidden");
    loginSection.classList.remove("hidden");
}

function setLoggedInUI(profile) {
    nicknameEl.textContent = profile.nickname || "-";
    smsCountEl.textContent = (profile.sms_count ?? 0).toString();
    loginSection.classList.add("hidden");
    userSection.classList.remove("hidden");
}

// ====== 세션 복원 ======
async function restoreSession() {
      // 1) chrome.storage 우선
      const cs = await csGet(["access_token", "nickname", "sms_count"]);
      let token     = cs.access_token;
      // let nickname  = cs.nickname     || localStorage.getItem("nickname");
      // let sms_count = cs.sms_count    || localStorage.getItem("sms_count");

      if (!token) {
        setLoggedOutUI();
        return;
      }

      try {
        const r = await fetch(API_ME_URL, {
          method: "GET",
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (!r.ok) throw new Error("세션 만료");

        const me = await r.json(); // { nickname, sms_count, ... }
        // 저장 동기화
        await csSet({
          access_token: token,
          nickname: me.nickname,
          sms_count: me.sms_count,
          apt_key: me.apt_key,
          villa_key: me.villa_key,
          sanga_key: me.sanga_key
        });

        // ✨ 현재 팝업 DIV UI 업데이트만 수행 (닫지 않음)
        setLoggedInUI(me);
      } catch (e) {
        // 만료/오류 시 정리
        await csSet({ access_token: "" });
        //
        setLoggedOutUI();
      }
}

// ====== 로그인 버튼 ======
let loginWin = null;
function handleLoginMessage(ev) {
      // 필요시 출처 체크를 엄격히 적용하세요.
      // if (!ev.origin.startsWith(SERVER)) return;

      const data = ev.data || {};
      if (data.type !== "kakao_login_success") return;

      // ✅ 로그인 성공: 팝업 DIV는 닫지 않는다 (loginWin도 닫지 않음)
      const { token, nickname, sms_count, apt_key, villa_key, sanga_key } = data;

      // 저장-chrome.storage.local을 Promise로 감싸서 정확히 저장 후 UI 갱신
      csSet({
        access_token: token,
        nickname,
        sms_count,
        apt_key,
        villa_key,
        sanga_key
      }).then(() => {

        // ✨ 현재 팝업 DIV UI 갱신
        setLoggedInUI({ nickname, sms_count });

        // 안내
        showToast("로그인 완료");
      });

      // 메시지 리스너는 유지해도 무방하지만, 한번만 받도록 제거하고 싶다면 아래 주석 해제
      window.removeEventListener("message", handleLoginMessage);
}

// 로그인 버튼 클릭
btnLogin.addEventListener("click", () => {
      const w = 480, h = 640;
      const left = Math.round((screen.width - w) / 2);
      const top  = Math.round((screen.height - h) / 2);

      // 🔸 loginWin을 전역변수에 보관 (닫지 않음)
      loginWin = window.open(
        OAUTH_LOGIN_URL,
        "kakao_login",
        `width=${w},height=${h},left=${left},top=${top},resizable=yes,scrollbars=yes,status=no`
      );

      // ❌ alert/confirm은 포커스를 빼앗아 팝업 UI가 닫히는 원인이 되기도 합니다. 제거 권장
      // window.alert("postMessage 수신...");

      // 메시지 리스너 (한 번만 등록)
      window.removeEventListener("message", handleLoginMessage);
      window.addEventListener("message", handleLoginMessage);
});

// ====== 로그아웃 버튼 ======
btnLogout.addEventListener("click", async () => {
      //const token = localStorage.getItem("access_token");
      const cs = await csGet(["access_token", "nickname", "sms_count"]);
      let token     = cs.access_token;
      try {
        await fetch(OAUTH_LOGOUT_URL, {
          method: "POST",
          headers: { "Authorization": `Bearer ${token}` }
        });
      } catch (_) { /* 네트워크 오류여도 로컬 정리 진행 */ }

      // 저장-chrome.storage.local을 Promise로 감싸서 정확히 저장 후 UI 갱신
      await csSet({ access_token: "" })

      // localStorage 동기화-사용안함
      // localStorage.setItem("access_token", token);
      // localStorage.setItem("nickname", me.nickname);
      // localStorage.setItem("sms_count", me.sms_count);
      //
      // localStorage.removeItem("access_token");
      // localStorage.removeItem("nickname");
      // localStorage.removeItem("sms_count");

      setLoggedOutUI();
      showToast("로그아웃 완료");
});

// ====== 초기 구동 ======
document.addEventListener("DOMContentLoaded", restoreSession);