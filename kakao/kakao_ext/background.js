chrome.runtime.onMessage.addListener((message, sender) => {
  if (message.type === 'OPEN_EXTENSION_POPUP') {
    // MV3 에서만 동작합니다 (크롬 109+)
    chrome.action.openPopup()
      .catch(err => console.error('팝업 열기 실패:', err));
  }
});
