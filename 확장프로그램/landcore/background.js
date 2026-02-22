chrome.runtime.onMessage.addListener((message, sender) => {
  if (message.type === 'OPEN_EXTENSION_POPUP') {
    // MV3 에서만 동작합니다 (크롬 109+)
    chrome.action.openPopup()
      .catch(err => console.error('팝업 열기 실패:', err));
  }
});

// 확장 프로그램 아이콘 클릭 시 사이드패널 열기 설정(true로 설정하면 아이콘 클릭 시 사이드패널이 열립니다)
chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: false })
  .catch((error) => console.error(error));

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