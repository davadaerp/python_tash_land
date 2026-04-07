// 확장 프로그램 아이콘 클릭 시 사이드패널 열기 설정(true로 설정하면 아이콘 클릭 시 사이드패널이 열립니다)
chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
});

chrome.runtime.onStartup?.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
});

chrome.runtime.onMessage.addListener((message, sender) => {
  if (message.type === 'OPEN_EXTENSION_POPUP') {
    // MV3 에서만 동작합니다 (크롬 109+)
    chrome.action.openPopup()
      .catch(err => console.error('팝업 열기 실패:', err));
  }
});

// (선택사항) 특정 도메인에서만 사이드패널이 활성화되길 원할 경우
/*
chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
  if (!tab.url) return;
  const url = new URL(tab.url);
  // 네이버 부동산 등 특정 사이트에서만 사이드패널 사용 설정
  if (url.origin.includes("naver.com")) {
    await chrome.sidePanel.setOptions({
      tabId,
      path: '/sidepanel/panel.html',
      enabled: true
    });
  }
});
*/


// 매물분석및 팝업이나 컨텐트 스크립트에서 보낸 '패널 열기' 요청 처리
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

  // 네이버부동산으로 탭 이동 요청이 오면 해당 탭으로 이동하거나 새 탭으로 엽니다.
  if (message.type === 'MOVE_TAB_TO_NAVER_LAND') {
    const { tabId, url } = message;

    if (!tabId || !url) {
      sendResponse({ success: false, error: 'tabId 또는 url이 없습니다.' });
      return true;
    }

    chrome.tabs.update(tabId, { url, active: true }, () => {
      if (chrome.runtime.lastError) {
        console.error('네이버부동산 이동 실패:', chrome.runtime.lastError.message);
        sendResponse({ success: false, error: chrome.runtime.lastError.message });
      } else {
        sendResponse({ success: true });
      }
    });

    return true;
  }

  // 패널이 열릴 때 현재 윈도우에서 네이버부동산 탭을 확인하고
  // 있으면 그 탭을 활성화, 없으면 새 탭으로 엽니다.
  if (message.type === 'ENSURE_NAVER_LAND_TAB') {
    // 네이버부동산 URL은 메시지에서 받아옵니다. (예: 'https://new.land.naver.com/' 또는 'https://m.land.naver.com/')
    const NAVER_LAND_URL = message.url;

    chrome.tabs.query({ currentWindow: true }, (tabs) => {
      if (chrome.runtime.lastError) {
        sendResponse({
          success: false,
          error: chrome.runtime.lastError.message
        });
        return;
      }

      // 네이버부동산 탭 찾기
      const naverLandTab = tabs.find(tab => {
        const url = tab.url || '';
        return url.includes('new.land.naver.com') || url.includes('m.land.naver.com');
      });

      // 이미 열려 있으면 해당 탭 활성화
      if (naverLandTab?.id) {
        chrome.tabs.update(naverLandTab.id, { active: true }, () => {
          if (chrome.runtime.lastError) {
            sendResponse({
              success: false,
              error: chrome.runtime.lastError.message
            });
            return;
          }

          sendResponse({
            success: true,
            action: 'focus',
            tabId: naverLandTab.id,
            url: naverLandTab.url
          });
        });
        return;
      }

      // 없으면 새 탭 열기
      chrome.tabs.create({ url: NAVER_LAND_URL, active: true }, (createdTab) => {
        if (chrome.runtime.lastError) {
          sendResponse({
            success: false,
            error: chrome.runtime.lastError.message
          });
          return;
        }

        sendResponse({
          success: true,
          action: 'create',
          tabId: createdTab?.id,
          url: createdTab?.url || NAVER_LAND_URL
        });
      });
    });

    return true;
  }

  // 사이드패널 열기 요청이 오면, 해당 탭에서 사이드패널을 엽니다.
  if (message.type === 'OPEN_SIDE_PANEL') {
    // 메시지를 보낸 탭의 ID를 확인하여 해당 탭에 사이드패널을 엽니다.
    chrome.sidePanel.open({ windowId: sender.tab ? sender.tab.windowId : null })
      .then(() => sendResponse({ success: true }))
      .catch((error) => {
        console.error(error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  // 매물분석관련 content script(landcore.js)에서 분석 요청이 오면, 현재 활성 탭으로 메시지 전달 후 응답 받기
  // START_ANALYSIS 등 기존 리스너 유지...
  if (message.type === 'START_ANALYSIS') {
    // 현재 보고 있는 활성화된 탭(네이버 부동산)을 찾음
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) {
        sendResponse({ success: false, error: "활성 탭을 찾을 수 없습니다." });
        return;
      }
      // 해당 탭(landcore.js)으로 메시지 토스
      chrome.tabs.sendMessage(tabs[0].id, message, (response) => {
        if (chrome.runtime.lastError) {
          sendResponse({ success: false, error: "페이지와 연결할 수 없습니다. 새로고침을 해주세요." });
        } else {
          sendResponse(response);
        }
      });
    });
    return true; // 중요!
  }
});