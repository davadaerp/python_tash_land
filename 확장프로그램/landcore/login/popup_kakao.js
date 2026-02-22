// ====== 공통 ======
//const SERVER = "http://127.0.0.1:5000";
const SERVER = "https://www.landcore.co.kr";          // 175.106.99.143
//const SERVER = 'http://127.0.0.1:5000';
const OAUTH_LOGIN_URL = `${SERVER}/api/kakao/login`;
const OAUTH_LOGOUT_URL = `${SERVER}/api/kakao/logout`;
const API_ME_URL = `${SERVER}/api/kakao/me`;

// 구독 생성(신규/연장) API (예시)
const SUB_CREATE_URL = `${SERVER}/api/subscription/create`;

const loginSection = document.getElementById("login-section");
const userSection  = document.getElementById("user-section");
const nicknameEl   = document.getElementById("nickname");
const smsCountEl   = document.getElementById("sms-count");
const subStatusEl  = document.getElementById("sub-status");
const subscribeWrap= document.getElementById("subscribe-wrap");
const btnCharge    = document.getElementById("btn-charge");
const btnLogin     = document.getElementById("btn-login");
const btnLogout    = document.getElementById("btn-logout");
const btnMypage    = document.getElementById("btn-mypage");
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

function applySubUI({ is_subscribed, plan_name, plan_date, is_recharged }) {
    // 구독 상태 뱃지
    if (is_subscribed === "active") {
        //subStatusEl.textContent = `${plan_name}(구독중-${plan_date})`;
        subStatusEl.innerHTML = `<span style="color:blue; font-weight:bold; font-size:11px;">${plan_name}(구독중-${plan_date})</span>`;
        subStatusEl.classList.remove("hidden","tag-nosub");
        subStatusEl.classList.add("tag-sub");
    } else if (is_subscribed === "request") {
        subStatusEl.innerHTML = `<span style="color:green; font-weight:bold; font-size:14px;">(${plan_name}-구독요청)</span>`;
        subStatusEl.classList.remove("hidden","tag-sub");
        subStatusEl.classList.add("tag-nosub");
    } else {
        //subStatusEl.textContent = "(미구독)";
        subStatusEl.innerHTML = `<span style="color:red; font-weight:bold; font-size:14px;">(미구독)</span>`;
        subStatusEl.classList.remove("hidden","tag-sub");
        subStatusEl.classList.add("tag-nosub");
    }

    // ✅ 마이페이지 버튼을 구독/마이페이지 모드로 전환 => is_subscribed가 'active'일 때만 true
    const isSubscribed = (is_subscribed === "active");
    setMypageButton(isSubscribed);

    // 🔽🔽🔽 [추가] 구독 '요청중(request)' 상태면 구독 버튼 비활성화
    if (is_subscribed === "request") {
        // setMypageButton()에서 미구독 상태로 '구독하기' 버튼이 세팅된 뒤, 비활성화만 적용
        btnMypage.disabled = true;
        btnMypage.textContent = "구독요청진행중..";
        btnMypage.classList.add("btn-disabled");   // 선택: 스타일이 있다면 사용
    }

    // 🔽🔽🔽 [추가] 문자 충전 상태가 'request'일 경우 버튼 내용 변경
    if (is_recharged === "request") {
        btnCharge.textContent = "충전중..";
        btnCharge.disabled = true;
        btnCharge.style.color = "white";
        btnCharge.classList.add("btn-disabled");
    } else if (btnCharge) {
        btnCharge.textContent = "문자충전";
        btnCharge.disabled = false;
        btnCharge.style.color = "blue";
        btnCharge.classList.remove("btn-disabled");
    }
}

// 마이페이지 / 구독 버튼 설정
function setMypageButton(isSubscribed) {
  if (isSubscribed) {
    // 구독중 → 마이페이지 버튼
    btnMypage.textContent = "마이페이지";
    btnMypage.classList.remove("btn-subscribe");
    btnMypage.classList.add("btn-secondary");
    btnMypage.dataset.mode = "mypage";
    // 충전 버튼 표시
    if (btnCharge) btnCharge.classList.remove("hidden");
  } else {
    // 미구독 → 구독 버튼
    btnMypage.textContent = "💎 구독하기";
    btnMypage.classList.remove("btn-secondary");
    btnMypage.classList.add("btn-subscribe");
    btnMypage.dataset.mode = "subscribe";
    // 충전 버튼 숨김
    if (btnCharge) btnCharge.classList.add("hidden");
  }
}

function setLoggedInUI(profile) {
      nicknameEl.textContent = profile.nickname || "-";
      smsCountEl.textContent = (profile.sms_count ?? 0).toString();

      // 구독 상태 적용
      applySubUI({
        is_subscribed: profile.is_subscribed,
        plan_name: profile.plan_name,
        plan_date: profile.plan_date,
        is_recharged: profile.is_recharged
      });
      //
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

        // is_subscribed = null(cancelled), active(true), plan_name = "프리미엄", ...
        const me = await r.json(); // { nickname, is_subscribed, is_recharged, plan_name, plan_date, sms_count, ... }
        // 저장 동기화
        await csSet({
            access_token: token,
            is_subscribed: me.is_subscribed,
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
      await restoreSession();

      // 메시지 리스너는 유지해도 무방하지만, 한번만 받도록 제거하고 싶다면 아래 주석 해제
      window.removeEventListener("message", handleLoginMessage);
}

// 안전한 이벤트 리스너 추가 함수
function safeAddListener(selectorOrEl, event, handler, options) {
    const el = (typeof selectorOrEl === "string")
      ? document.querySelector(selectorOrEl)
      : selectorOrEl;

    if (!el) {
      console.warn("⚠️ addEventListener 대상이 없습니다:", selectorOrEl);
      return false;
    }
    el.addEventListener(event, handler, options);
    return true;
}

// 로그인 버튼 클릭 - 팝업후 post메시지로 리턴받음
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

      // 로그인후에 상가페이지로 이동
      const NAVER_LAND_URL = 'https://new.land.naver.com/offices?a=SG:SMS&b=A1:B2&e=RETAIL&ad=true';

      // 현재 활성화된 탭의 URL을 변경
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
            chrome.tabs.update(tabs[0].id, { url: NAVER_LAND_URL });
            // 팝업창을 닫고 싶다면 추가
            // window.close();
        }
      });
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
      } catch (_) {
        // 네트워크 오류여도 로컬 정리 진행
      }
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

// ====== 마이페이지 / 구독 버튼 ======
let mypagePopup = null;  // 전역변수로 팝업 핸들 저장
btnMypage.addEventListener('click', async () => {
  const mode = btnMypage.dataset.mode;
  const token = (await csGet(['access_token']))?.access_token || '';

  if (mode === 'subscribe') {
    if (!token) { showToast('로그인 후 이용해주세요.'); return; }
    openSubscribePopup(token);          // ✅ 구독 팝업 열기
  } else {
    openMypageWithToken();              // ✅ 마이페이지 열기
  }
});

// ====== 마이페이지 처리 ======
async function openMypageWithToken() {
      let access_token = '';
      try { access_token = localStorage.getItem('access_token') || ''; } catch (e) {}

      if (!access_token && typeof chrome !== 'undefined' && chrome.storage?.local) {
        await new Promise((resolve) => {
          chrome.storage.local.get(['access_token'], (res) => {
            if (res && res.access_token) access_token = res.access_token;
            resolve();
          });
        });
      }

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

// ====== 문자 충전 버튼 ======
btnCharge.addEventListener("click", async () => {
      const cs = await csGet(["access_token"]);
      let token = cs.access_token;
      if (!token) { showToast("로그인 후 이용해주세요."); return; }
      //
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


// popup_kakao.html 내의 사이드패널 관련 특정 버튼 클릭 시
document.getElementById('btn-panel').addEventListener('click', () => {
  // 현재 활성화된 탭에 사이드패널 열기 명령 전달
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const currentTab = tabs[0];
    if (currentTab) {
      chrome.sidePanel.open({ tabId: currentTab.id });
      // 패널을 열고 나서 팝업창을 닫고 싶다면:
      // window.close();
    }
  });
});

// ====== 초기 구동 ======
document.addEventListener("DOMContentLoaded", restoreSession);
