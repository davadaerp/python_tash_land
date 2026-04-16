// ====== 공통 ======
//const SERVER = "https://www.landcore.co.kr";          // 175.106.99.143
//const SERVER = 'http://127.0.0.1:5000';
const SERVER = (typeof LANDCORE_URL !== 'undefined' && LANDCORE_URL) ? LANDCORE_URL : "https://www.landcore.co.kr";
const OAUTH_LOGIN_URL = `${SERVER}/api/kakao/login`;
const OAUTH_LOGOUT_URL = `${SERVER}/api/kakao/logout`;
const API_ME_URL = `${SERVER}/api/kakao/me`;

// 구독 생성(신규/연장) API (예시)
const SUB_CREATE_URL = `${SERVER}/api/subscription/create`;

const loginSection    = document.getElementById("login-section");
const userSection     = document.getElementById("user-section");
// let userSection     = null;
const loginLinks      = document.getElementById("login-links");
const nicknameEl      = document.getElementById("nickname");
const panelNicknameEl = document.getElementById("panel-nickname");
const smsCountEl      = document.getElementById("sms-count");
const subStatusEl     = document.getElementById("sub-status");
const nicknameToggle  = document.getElementById("nickname-toggle");
const userInfoPanel   = document.getElementById("user-info-panel");
const userInfoClose   = document.getElementById("user-info-close");
const topUserStrip    = document.getElementById("top-user-strip");
//
const subscribeWrap= document.getElementById("subscribe-wrap");
const btnCharge    = document.getElementById("btn-charge");
const btnLogin     = document.getElementById("btn-login");
const btnLogout    = document.getElementById("btn-logout");
const btnMypage    = document.getElementById("btn-mypage");
let toast        = document.getElementById("toast");


// ---- 유틸: chrome.storage를 Promise로 래핑 ----
function csGet(keys) {
    return new Promise(resolve => chrome.storage.local.get(keys, resolve));
}

// chrome.storage.local을 Promise로 감싸서 정확히 저장 후 UI 갱신
function csSet(obj) {
    return new Promise(resolve => chrome.storage.local.set(obj, resolve));
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    if (!toast) {
        console.warn('[showToast] toast 요소가 없습니다.');
        return;
    }

    toast.textContent = msg;
    toast.classList.remove('hidden');
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
        toast.classList.add('hidden');
    }, 5000);
}

function setLoggedOutUI() {
    topUserStrip?.classList.add("hidden");
    userSection?.classList.add("hidden");
    loginLinks?.classList.add("hidden");
    userInfoPanel?.classList.add("hidden");
    loginSection?.classList.remove("hidden");
}

function applySubUI({ is_subscribed, plan_name, plan_date, is_recharged }) {
  const isSubscribed = (is_subscribed === "active");
  const isRequesting = (is_subscribed === "request");

  if (isSubscribed) {
    const safePlanName = plan_name || "0개월";
    const safePlanDate = plan_date || "0일남음";
    subStatusEl.textContent = `${safePlanName}(${safePlanDate})`;
    subStatusEl.className = "top-user-period";
    subStatusEl.classList.remove("hidden");
    subStatusEl.style.background = "transparent";
    subStatusEl.style.color = "#666";
    // 구독요청중 버튼 깜빡임 제거
    btnMypage.classList.remove("requesting-blink-btn");
  } else if (isRequesting) {
    const safePlanName = plan_name || "구독요청";
    const safePlanDate = plan_date || "확인중";
    subStatusEl.textContent = `${safePlanName}(${safePlanDate})`;
    subStatusEl.className = "top-user-period";
    subStatusEl.classList.remove("hidden");
    subStatusEl.style.background = "transparent";
    subStatusEl.style.color = "#326CF9";
  } else {
    subStatusEl.textContent = "미구독(0일남음)";
    subStatusEl.className = "top-user-period";
    subStatusEl.classList.remove("hidden");
    subStatusEl.style.background = "transparent";
    subStatusEl.style.color = "#d90429";
  }

  setMypageButton(isSubscribed);

  if (isRequesting) {
    btnMypage.disabled = true;
    btnMypage.textContent = "구독요청진행중..";
    btnMypage.classList.add("btn-disabled", "requesting-blink-btn");

    if (btnCharge) {
      btnCharge.classList.add("hidden");
      btnCharge.disabled = true;
    }
    return;
  }

  if (!isSubscribed) {
    btnMypage.disabled = false;
    btnMypage.classList.remove("btn-disabled");
    btnMypage.textContent = "💎 구독하기";
    btnMypage.dataset.mode = "subscribe";

    if (btnCharge) {
      btnCharge.classList.add("hidden");
      btnCharge.disabled = true;
      btnCharge.textContent = "문자충전";
      btnCharge.classList.remove("btn-disabled");
    }
    return;
  }

  if (btnCharge) {
    btnCharge.classList.remove("hidden");
    btnCharge.disabled = false;
    btnCharge.textContent = "문자충전";
    btnCharge.classList.remove("btn-disabled");
  }

  if (is_recharged === "request") {
    btnCharge.textContent = "충전중..";
    btnCharge.disabled = true;
    btnCharge.classList.add("btn-disabled");
  }
}

// 마이페이지 / 구독 버튼 설정
function setMypageButton(isSubscribed) {
  btnMypage.disabled = false;
  btnMypage.classList.remove("btn-disabled", "requesting-blink-btn");

  if (isSubscribed) {
    btnMypage.textContent = "마이페이지";
    btnMypage.classList.remove("btn-subscribe");
    btnMypage.classList.add("btn-secondary");
    btnMypage.dataset.mode = "mypage";

    if (btnCharge) btnCharge.classList.remove("hidden");
  } else {
    btnMypage.textContent = "💎 구독하기";
    btnMypage.classList.remove("btn-secondary");
    btnMypage.classList.add("btn-subscribe");
    btnMypage.dataset.mode = "subscribe";

    if (btnCharge) btnCharge.classList.add("hidden");
  }
}

function setLoggedInUI(profile) {
      const nickname = profile.nickname || "-";
      const smsCount = (profile.sms_count ?? 0).toString();

      nicknameEl.textContent = nickname;
      if (panelNicknameEl) {
        panelNicknameEl.textContent = nickname;
      }

      smsCountEl.textContent = smsCount;

      applySubUI({
        is_subscribed: profile.is_subscribed,
        plan_name: profile.plan_name,
        plan_date: profile.plan_date,
        is_recharged: profile.is_recharged
      });

      topUserStrip?.classList.remove("hidden");
      loginSection.classList.add("hidden");
      userSection.classList.remove("hidden");
      loginLinks?.classList.remove("hidden");
      userInfoPanel?.classList.add("hidden");
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

        // is_subscribed = null(cancelled), active(true), plan_name = "프리미엄", ...
        const me = await r.json(); // { nickname, is_subscribed, is_recharged, plan_name, plan_date, sms_count, ... }
        // 저장 동기화
        await csSet({
            access_token: token,
            is_subscribed: me.is_subscribed,
            nickname: me.nickname,
            sms_count: me.sms_count
        });

        // ✨ 현재 팝업 DIV UI 업데이트만 수행 (닫지 않음)
        setLoggedInUI(me);
      } catch (e) {
        // 만료/오류 시 정리
        //await csSet({ access_token: "" });
        //
        setLoggedOutUI();
      }
      // subscribeWrap 영역은 사용하지 않음
      if (subscribeWrap) subscribeWrap.classList.add("hidden");
}

// ====== 로그인 버튼 ======
let loginWin = null;
async function handleLoginMessage(ev) {
      // 필요시 출처 체크를 엄격히 적용하세요.
      // if (!ev.origin.startsWith(SERVER)) return;

      const data = ev.data || {};
      if (data.type !== "kakao_login_success") return;

      // ✅ 로그인 성공: 팝업 DIV는 닫지 않는다 (loginWin도 닫지 않음)
      const { token, nickname, sms_count, apt_key, villa_key, sanga_key } = data;

      // 저장-chrome.storage.local을 Promise로 감싸서 정확히 저장 후 UI 갱신
      // 1. 토큰 우선 저장
      await csSet({
        access_token: token,
        nickname,
        sms_count,
        apt_key,
        villa_key,
        sanga_key
      });

      // ✨ 현재 팝업 DIV UI 갱신
      //setLoggedInUI({ nickname, sms_count });

      showToast("카카오 로그인 완료");

      // 2. ✨ 핵심: 로그인 성공 직후 바로 restoreSession을 호출하여
      // 서버의 최신 구독 상태(api_me)를 가져와 UI를 완벽하게 갱신합니다.
      restoreSession().catch((err) => {
        console.warn("restoreSession 실패:", err);
      });

      // 메시지 리스너는 유지해도 무방하지만, 한번만 받도록 제거하고 싶다면 아래 주석 해제
      window.removeEventListener("message", handleLoginMessage);
}

// 안전한 이벤트 리스너 추가 함수
function safeAddListener(selectorOrEl, event, handler, options) {
    const el = (typeof selectorOrEl === "string")
      ? document.querySelector(selectorOrEl)
      : selectorOrEl;

    if (!el) {
      //console.warn("⚠️ addEventListener 대상이 없습니다:", selectorOrEl);
      return false;
    }
    el.addEventListener(event, handler, options);
    return true;
}

// ====== 마이페이지 / 구독 버튼 ======
let mypagePopup = null;  // 전역변수로 팝업 핸들 저장

// ====== 마이페이지 처리 ======
async function openMypageWithToken() {
      //
      const cs = await csGet(["access_token"]);
      let access_token = cs.access_token || '';

      const base = (typeof SERVER !== 'undefined' && SERVER) ? SERVER : '';
      // const query = access_token ? `?access_token=${encodeURIComponent(access_token)}` : '';
      // const url = `${base}/api/user/mypage${query}`;
      const url  = `${base}/api/ext_tool/menu?menu=mypage&tk=${encodeURIComponent(access_token)}`;

      const width = 590, height = 800;
      const screenW = window.screen.availWidth;
      const screenH = window.screen.availHeight;
      const left = (screenW - width) / 2;
      const top  = (screenH - height) / 2;

      const features = [
        `width=${Math.floor(width)}`,
        `height=${Math.floor(height)}`,
        `left=${Math.floor(left)}`,
        `top=${Math.floor(top)}`,
        'resizable=yes','scrollbars=yes','status=no','menubar=no','toolbar=no','location=no'
      ].join(',');

      if (mypagePopup && !mypagePopup.closed) mypagePopup.close();

      mypagePopup = window.open(url, 'user_mypage', features);
      if (!mypagePopup) {
        showToast('팝업이 차단되었습니다. 브라우저에서 팝업 허용을 켜주세요.');
        return;
      }
      mypagePopup.focus?.();
}

// ====== 구독 팝업 열기 ======
function openSubscribePopup(token) {
  const w = 420, h = 570;
  const left = Math.round((screen.width - w) / 2);
  const top  = Math.round((screen.height - h) / 2);

  const base = (typeof SERVER !== 'undefined' && SERVER) ? SERVER : '';
  const url  = `${base}/api/ext_tool/menu?menu=subscribe&tk=${encodeURIComponent(token)}`;

  const pop = window.open(
    url,
    'subscribe_popup',
    `width=${w},height=${h},left=${left},top=${top},resizable=yes,scrollbars=yes,status=no`
  );

  if (!pop) {
    showToast('팝업이 차단되었습니다. 브라우저에서 팝업 허용을 켜주세요.');
    return;
  }
  pop.focus?.();
}

// ====== 이벤트 리스너 등록 ======
// 로그인 버튼 클릭 - 팝업후 post메시지로 리턴받음
safeAddListener(btnLogin, "click", () => {
  const w = 480, h = 640;
  const left = Math.round((screen.width - w) / 2);
  const top  = Math.round((screen.height - h) / 2);

  loginWin = window.open(
    OAUTH_LOGIN_URL,
    "kakao_login",
    `width=${w},height=${h},left=${left},top=${top},resizable=yes,scrollbars=yes,status=no`
  );

  window.removeEventListener("message", handleLoginMessage);
  window.addEventListener("message", handleLoginMessage);

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.tabs.update(tabs[0].id, { url: NAVER_LAND_URL });
    }
  });
});

safeAddListener(btnLogout, "click", async () => {
  const cs = await csGet(["access_token", "nickname", "sms_count"]);
  let token = cs.access_token;
  try {
    await fetch(OAUTH_LOGOUT_URL, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` }
    });
  } catch (_) {}

  await csSet({ access_token: "" });

  // panel.js의 화면 초기화 함수 호출
  if (typeof resetPanel === "function") {
    resetPanel();
  }

  setLoggedOutUI();
  showToast("로그아웃 완료");
});

// 마이페이지 / 구독 버튼 클릭
safeAddListener(btnMypage, "click", async () => {
  const mode = btnMypage.dataset.mode;
  const token = (await csGet(['access_token']))?.access_token || '';

  if (mode === 'subscribe') {
    if (!token) { showToast('로그인 후 이용해주세요.'); return; }
    openSubscribePopup(token);
  } else {
    openMypageWithToken();
  }
});

// 문자충전 버튼 클릭
safeAddListener(btnCharge, "click", async () => {
  const cs = await csGet(["access_token"]);
  let token = cs.access_token;
  if (!token) { showToast("로그인 후 이용해주세요."); return; }

  const w = 420, h = 420;
  const left = Math.round((screen.width - w) / 2);
  const top  = Math.round((screen.height - h) / 2);

  const base = (typeof SERVER !== 'undefined' && SERVER) ? SERVER : '';
  const url  = `${base}/api/ext_tool/menu?menu=recharge&tk=${encodeURIComponent(token)}`;

  const pop = window.open(
    url,
    'recharge_popup',
    `width=${w},height=${h},left=${left},top=${top},resizable=yes,scrollbars=yes,status=no`
  );

  if (!pop) {
    showToast('팝업이 차단되었습니다. 브라우저에서 팝업 허용을 켜주세요.');
    return;
  }
  pop.focus?.();
});

safeAddListener(nicknameToggle, "click", async (e) => {
  e.preventDefault();

  const willOpen = userInfoPanel?.classList.contains("hidden");

  // 열 때만 최신 정보 재조회
  if (willOpen) {
    await restoreSession();
    userInfoPanel?.classList.remove("hidden");
  } else {
    userInfoPanel?.classList.add("hidden");
  }
});

safeAddListener(userInfoClose, "click", (e) => {
  e.preventDefault();
  userInfoPanel?.classList.add("hidden");
});

document.addEventListener("click", (e) => {
  const clickedInsideUserSection = userSection?.contains(e.target);
  const clickedInsideTopStrip = topUserStrip?.contains(e.target);
  const clickedInsideInfoPanel = userInfoPanel?.contains(e.target);

  if (!clickedInsideUserSection && !clickedInsideTopStrip && !clickedInsideInfoPanel) {
    userInfoPanel?.classList.add("hidden");
  }
});

// ====== 초기 구동 ======
document.addEventListener("DOMContentLoaded", restoreSession);
