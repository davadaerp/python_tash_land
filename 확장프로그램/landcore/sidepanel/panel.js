/**
 * landcore - Excel Style Panel JS
 */

// DOM Elements
const analyzeBtn = document.getElementById('analyze-btn');
const resetBtn = document.getElementById('reset-btn');
const realAuctionBtn = document.getElementById('real-auction-btn');
const realAuctionMenu = document.getElementById('real-auction-menu');
const calculatorBtn = document.getElementById('calculator-btn');
//const memoBtn = document.getElementById('memo-btn');
const baehuBtn = document.getElementById('baehu-btn');
const naverLandBtn = document.getElementById('naver-land-btn');
const guideBtn = document.getElementById('guide-btn');
const statusBar = document.getElementById('status-bar');
const resultsContainer = document.getElementById('results-container');
const areaChartContainer = document.getElementById('area-chart');
const historyList = document.getElementById('history-list');

// API Base URL
const BASE_URL = "https://www.landcore.co.kr";

// 네이버 부동산 상가 페이지 URL (마지막 위치 기억)
const NAVER_LAND_URL = 'https://new.land.naver.com/offices?a=SG:SMS&b=A1:B2&e=RETAIL&ad=true';

// State
let lastAnalysisData = null;
let currentChartType = '월세';
// 실시간 분석 업데이트를 위한 현재 지역 라벨 (예: "서울 강남구 역삼동")
let currentRegionLabel = '';

// 상세 목록/최저가 보기 상태
let currentDetailView = 'list'; // 'list' | 'cheapest'

// 정렬 상태
let currentListSort = {
    field: 'pricePerPyeong',   // 'floor' | 'pricePerPyeong' | 'area'
    direction: 'asc'           // 'asc' | 'desc'
};
// 현재 층 필터 상태 (예: '전체', '1층', '2층', '상층')
let currentFloorFilter = '전체';

let currentRegionInfo = {
    region: '',
    sigungu: '',
    umdNm: ''
};

// 초기화
document.addEventListener('DOMContentLoaded', async () => {
    // 로그인 상태 업데이트
    //updateUserSession();

    console.log('Panel Initialized');
    await checkCurrentTab();
    loadHistory();

    analyzeBtn.addEventListener('click', startAnalysis);
    resetBtn.addEventListener('click', resetPanel);
    realAuctionBtn.addEventListener('click', toggleAnalysisMenu);
    calculatorBtn.addEventListener('click', openCalculator);
    //memoBtn.addEventListener('click', openMemo);
    baehuBtn.addEventListener('click', openBaehu);
    naverLandBtn.addEventListener('click', openNaverLand);
    guideBtn.addEventListener('click', openGuide);

    // 결과 영역 내 목록/최저가 전환 및 정렬 처리
    resultsContainer.addEventListener('click', (e) => {
        // floor select 자체 클릭은 상위 click 위임 로직에서 제외
        if (e.target.closest('[data-floor-select]') || e.target.closest('.floor-filter-select-wrap')) {
            return;
        }

        const typeBtn = e.target.closest('[data-listing-type]');
        if (typeBtn) {
            const selectedType = typeBtn.getAttribute('data-listing-type');

            currentChartType = selectedType;
            currentDetailView = 'list';   // 핵심: 타입 버튼 누르면 무조건 목록으로 복귀
            currentFloorFilter = '전체';   // 타입 바뀌면 층 필터도 초기화

            if (lastAnalysisData) {
                displayResults(lastAnalysisData);
                displayAreaChart(lastAnalysisData);
            }
            return;
        }

        const modeBtn = e.target.closest('[data-detail-mode]');
        if (modeBtn) {
            const nextMode = modeBtn.getAttribute('data-detail-mode');

            // 최저가매물은 매매에서만 동작
            if (nextMode === 'cheapest') {
                if (currentChartType !== '매매') {
                    return;
                }
                currentDetailView = 'cheapest';
            }

            if (lastAnalysisData) {
                displayResults(lastAnalysisData);
            }
            return;
        }

        const sortBtn = e.target.closest('[data-sort-field]');
        if (sortBtn) {
            const field = sortBtn.getAttribute('data-sort-field');

            if (currentListSort.field === field) {
                currentListSort.direction = currentListSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentListSort.field = field;
                currentListSort.direction = 'asc';
            }

            if (lastAnalysisData) {
                displayResults(lastAnalysisData);
            }
        }
    });

    // 층 필터 변경은 click이 아닌 change 이벤트로 처리 (select 요소의 고유 이벤트)
    resultsContainer.addEventListener('change', (e) => {
        const floorSelect = e.target.closest('[data-floor-select]');
        if (floorSelect) {
            e.stopPropagation();

            currentFloorFilter = floorSelect.value || '전체';
            currentDetailView = 'list';

            if (lastAnalysisData) {
                displayResults(lastAnalysisData);
                displayAreaChart(lastAnalysisData);
            }
        }
    });

    // 분석 메뉴 외부 클릭 시 메뉴 닫기 및 메뉴 버튼 클릭 시 해당 메뉴 열기
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.tool-dropdown')) {
            realAuctionMenu?.classList.add('hidden');
        }

        const menuBtn = e.target.closest('[data-analysis-menu]');
        if (!menuBtn) return;

        const menuType = menuBtn.getAttribute('data-analysis-menu');
        realAuctionMenu?.classList.add('hidden');

        if (menuType === 'realdeal') {
            openLandRealAuctionPopupFromPanel();
        } else if (menuType === 'commercial') {
            openCommericalAreaPopupFromPanel();
        } else if (menuType === 'statistics') {
            openLandRealStatisticsPopupFromPanel();
        }
    });

    // 실시간 분석 업데이트 리스트
    chrome.runtime.onMessage.addListener((message) => {
        if (message.type === 'AUTO_ANALYSIS_UPDATE' && message.data) {
            console.log('실시간 업데이트 수신:', message.data.totalCount, '개 매물');
            handleAutoUpdate(message.data);
        }
    });
});


// 1. 평수 차트 렌더링 함수 (listings 배열을 직접 받아 처리)
function renderAreaChart(listings, type = '월세') {
    const chartContainer = document.getElementById('area-chart');
    const chartTitle = document.getElementById('chart-title');

    if (!chartContainer || !chartTitle) return;

    // 제목 업데이트, 해당 타입(매매/월세)만 필터링
    const floorLabel = currentFloorFilter || '전체';
    chartTitle.textContent = `✏️ ${type} 평수 분포(${floorLabel})`;

    const typeFilteredListings = (listings || []).filter(l => l.type === type);
    const filteredListings = filterListingsByFloor(typeFilteredListings, floorLabel);

    if (filteredListings.length === 0) {
        chartContainer.innerHTML = `<div class="empty-msg" style="padding:20px; color:#999; text-align:center;">${type} ${floorLabel} 데이터가 없습니다.</div>`;
        return;
    }

    // displayAreaChart와 동일한 구간 기준으로 통일
    const areaGroups = {
        '10': 0, '20': 0, '30': 0, '40': 0, '50': 0,
        '60': 0, '70': 0, '80': 0, '90': 0, '100+': 0
    };

    filteredListings.forEach(l => {
        const area = Number(l.area) || 0;
        if (area < 20) areaGroups['10']++;
        else if (area < 30) areaGroups['20']++;
        else if (area < 40) areaGroups['30']++;
        else if (area < 50) areaGroups['40']++;
        else if (area < 60) areaGroups['50']++;
        else if (area < 70) areaGroups['60']++;
        else if (area < 80) areaGroups['70']++;
        else if (area < 90) areaGroups['80']++;
        else if (area < 100) areaGroups['90']++;
        else areaGroups['100+']++;
    });

    const maxCount = Math.max(...Object.values(areaGroups), 1);
    const barColor = type === '매매' ? '#2196f3' : '#e91e63';

    const barsHTML = Object.entries(areaGroups).map(([range, count]) => {
        const heightPx = maxCount > 0 ? (count / maxCount) * 80 : 2;
        const label = range === '100+' ? '100+평' : `${range}평`;
        const barHeight = Math.max(heightPx, 2);

        return `
            <div class="bar-container" style="display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100px;">
                <div class="bar-count" style="font-size:11px; margin-bottom:2px; color:${barColor}; font-weight:bold;">${count > 0 ? count : ''}</div>
                <div class="bar" style="
                    width: 20px;
                    height: ${barHeight}px;
                    background-color: ${barColor};
                    opacity: ${count > 0 ? 1 : 0.1};
                    border-radius: 2px 2px 0 0;
                    transition: height 0.3s ease;"></div>
                <div class="bar-label" style="font-size:10px; margin-top:4px; color:#666;">${label}</div>
            </div>
        `;
    }).join('');

    chartContainer.innerHTML = barsHTML;
}


/**
 * 로그인 정보를 스토리지에서 가져와 UI 업데이트
 */
function updateUserSession() {
    const userInfoBar = document.getElementById('user-info-bar');
    const loginMsg = document.getElementById('login-needed-msg');

    chrome.storage.local.get(['access_token', 'nickname', 'sms_count'], (items) => {
        if (items.access_token) {
            // 로그인 상태
            document.getElementById('nickname').textContent = items.nickname || '사용자';
            document.getElementById('sms-count').textContent = items.sms_count || '0';

            userInfoBar?.classList.remove('hidden');
            loginMsg?.classList.add('hidden');
        } else {
            // 비로그인 상태
            userInfoBar?.classList.add('hidden');
            loginMsg?.classList.remove('hidden');

            // 로그인 안되어 있으면 분석 버튼 비활성화 등의 처리 가능
            // analyzeBtn.disabled = true;
        }
    });
}

/**
 * 실시간 분석 업데이트 처리
 */
async function handleAutoUpdate(data) {
    lastAnalysisData = data;

    // 분석 데이터에 포함된 지역정보를 바로 반영
    applyRegionLabelFromAnalysisData(data);

    displayResults(data);
    displayAreaChart(data);
    displayTopAgencies(data);

    // 분석 완료 안내 메시지 표시
    const wolseCount = data.listings?.filter(l => l.type === '월세').length || 0;
    const maemaeCount = data.listings?.filter(l => l.type === '매매').length || 0;
    showAnalysisCount(wolseCount, maemaeCount);

    // 상태바 업데이트
    setStatus('ready', `실시간 분석 중 (${data.totalCount || 0}개)`);
}

/**
 * 네이버 부동산 상가 페이지 열기
 */
function openNaverLand() {
    chrome.tabs.create({ url: NAVER_LAND_URL });
}

/**
 * 사용가이드 페이지 열기
 */
function openGuide() {
    const guideUrl = chrome.runtime.getURL('tools/guide.html');
    chrome.tabs.create({ url: guideUrl });
}

/*
 * 로그인 관련 적용처리
 */
async function loginForPanel() {
    return new Promise((resolve) => {
        chrome.storage.local.get(
            ["access_token", "is_subscribed", "apt_key", "villa_key", "sanga_key"],
            async (items) => {
                const accessToken = items.access_token || '';
                const subscribed = items.is_subscribed || '';

                if (!accessToken) {
                    alert('로그인(회원가입) 후 사용바랍니다.');
                    return resolve({ ok: false });
                }

                if (subscribed !== 'active') {
                    alert('구독승인 후 사용바랍니다.');
                    return resolve({ ok: false });
                }

                try {
                    const response = await fetch(BASE_URL +'/api/user/subscribe_check', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${accessToken}`
                        }
                    });

                    const result = await response.json();

                    if (result.result === 'Success') {
                        return resolve({
                            ok: true,
                            access_token: accessToken,
                            apt_key: items.apt_key || '',
                            villa_key: items.villa_key || '',
                            sanga_key: items.sanga_key || ''
                        });
                    }

                    alert(result.message || '구독(갱신)후 사용바랍니다.');
                    return resolve({ ok: false });
                } catch (error) {
                    console.error('subscribe_check 오류:', error);
                    alert('로그인 확인 중 오류가 발생했습니다.');
                    return resolve({ ok: false });
                }
            }
        );
    });
}

async function loginValidForPanel() {
    const result = await loginForPanel();
    return result;
}

/**
 * 실거래, 업종분석, 통계분석 열기
 */
// 분석 메뉴 토글
function toggleAnalysisMenu(e) {
    e.stopPropagation();
    realAuctionMenu?.classList.toggle('hidden');
}

// 실거래 팝업 열기 (패널에서 지역정보 전달)
async function openLandRealAuctionPopupFromPanel() {
    // 로그인 및 구독 상태 체크
    const auth = await loginValidForPanel();
    if (!auth.ok) return;

    const regions = getCurrentRegionsString() || "경기도,김포시,운양동";
    const menu = 'sanga_real_deal';
    const extUrl = `${BASE_URL}/api/ext_tool?menu=${menu}&regions=${encodeURIComponent(regions)}&tk=${encodeURIComponent(auth.access_token)}`;

    const popupWidth = 950;
    const popupHeight = 840;
    const left = (screen.width - popupWidth) / 2;
    const top = (screen.height - popupHeight) / 2;

    window.open(
        extUrl,
        "realDataPopup",
        `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`
    );
}

// 업종분석 팝업 열기 (패널에서 지역정보 전달)
async function openCommericalAreaPopupFromPanel() {
    const auth = await loginValidForPanel();
    if (!auth.ok) return;

    try {
        const region = currentRegionInfo?.region || '';
        const sigungu = currentRegionInfo?.sigungu || '';
        const umdNm = currentRegionInfo?.umdNm || '';

        if (!region || !sigungu || !umdNm) {
            throw new Error('지역 선택값이 올바르지 않습니다.');
        }

        // landcore.js와 동일하게 lawName 구성
        const lawdCd = '';
        const lawName = `${region} ${sigungu} ${umdNm}`;
        console.log(`업종상권분석 호출 - lawdCd: ${lawdCd}, lawName: ${lawName}`);

        // 상권정보 원본 조회
        const commercialItems = await fetchCommercialAreaInfoForPanel(
            lawdCd,
            lawName,
            auth.access_token
        );

        if (!commercialItems || !commercialItems.length) {
            alert('해당 지역의 상권정보가 없습니다.');
            return;
        }

        // 지도팝업으로 전달할 payload 구성
        const payload = {
            options: [{
                region: lawName,
                floor: "전체",
                area: "전체"
            }],
            addresses: [{
                type: "region",
                address: lawName,
                buildingName: lawName,
                latitude: 0,
                longitude: 0
            }],
            commercialAreaItems: Array.isArray(commercialItems) ? commercialItems : []
        };

        console.log("Commercial area payload for popup:", payload);

        const popupWidth = 1200;
        const popupHeight = 1100;
        const left = window.screenX + (window.outerWidth - popupWidth) / 2;
        const top = window.screenY + (window.outerHeight - popupHeight) / 2 - 100;

        const popup = window.open(
            `${BASE_URL}/api/ext_tool/map?menu=map_popup`,
            'commercialAreaMapPopup',
            `width=${popupWidth},height=${popupHeight},top=${top},left=${left},resizable=yes,scrollbars=yes`
        );

        if (!popup) {
            alert('팝업이 차단되었습니다. 팝업 허용 후 다시 시도해주세요.');
            return;
        }

        const sendPayload = () => {
            try {
                popup.postMessage(payload, new URL(BASE_URL).origin);
            } catch (e) {
                console.error('상권분석 payload 전송 실패:', e);
            }
        };

        popup.onload = sendPayload;
        setTimeout(sendPayload, 800);

    } catch (err) {
        console.error('업종상권분석 처리 실패:', err);
        alert(`업종상권분석 처리 중 오류가 발생했습니다.\n${err.message || err}`);
    }
}

// 상권정보 조회 API 호출 (패널에서 지역정보 전달)
async function fetchCommercialAreaInfoForPanel(lawdCd, lawName, accessToken = '') {
    const url = new URL(`${BASE_URL}/api/sanga/commerical_area_info`);

    if (lawdCd) url.searchParams.set('lawd_cd', lawdCd);
    if (lawName) url.searchParams.set('lawd_name', lawName);

    const headers = {};
    if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const response = await fetch(url.toString(), {
        method: 'GET',
        headers
    });

    if (!response.ok) {
        throw new Error(`상권정보 조회 실패 (${response.status})`);
    }

    const result = await response.json();
    return Array.isArray(result?.records) ? result.records : [];
}

// 통계분석 팝업 열기 (패널에서 지역정보 전달)
async function openLandRealStatisticsPopupFromPanel() {
    // 로그인 및 구독 상태 체크
    const auth = await loginValidForPanel();
    if (!auth.ok) return;

    const regions = getCurrentRegionsString() || "경기도,김포시,운양동";

    const urlParams = new URLSearchParams({
        menu: 'sanga',
        type: 'public',
        regions,
        tk: auth.access_token
    });

    const extUrl = `${BASE_URL}/api/trade/statistics?${urlParams.toString()}`;

    const popupWidth = 1390;
    const popupHeight = 1180;
    const left = (screen.width - popupWidth) / 2;
    const top = (screen.height - popupHeight) / 2;

    window.open(
        extUrl,
        "statisticsAnalysisPopup",
        `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`
    );
}

/**
 * 매물 메모장 열기
 * 현재 열린 매물 상세정보를 추출하여 메모 페이지에 전달
 */
async function openMemo() {
    let params = new URLSearchParams();

    try {
        // 상세정보 팝업에서 데이터 추출
        const response = await chrome.runtime.sendMessage({ type: 'GET_MEMO_DATA' });

        if (response?.success && response.data) {
            const data = response.data;

            // URL 파라미터로 전달
            if (data.propertyName) params.set('propertyName', data.propertyName);
            if (data.price) params.set('price', data.price);
            if (data.rent) params.set('rent', data.rent);
            if (data.area) params.set('area', data.area);
            if (data.floor) params.set('floor', data.floor);
            if (data.address) params.set('address', data.address);
            if (data.features) params.set('features', data.features);
            if (data.propertyNo) params.set('propertyNo', data.propertyNo);
            if (data.agencyName) params.set('agencyName', data.agencyName);
            if (data.agencyPhone) params.set('agencyPhone', data.agencyPhone);
            if (data.agencyMobile) params.set('agencyMobile', data.agencyMobile);
            if (data.agencyAddress) params.set('agencyAddress', data.agencyAddress);
        }
    } catch (error) {
        console.warn('상세정보 추출 실패, 빈 메모장 열기:', error);
    }

    // 메모 페이지 열기
    const memoUrl = chrome.runtime.getURL('tools/memo.html');
    const fullUrl = params.toString() ? `${memoUrl}?${params}` : memoUrl;
    chrome.tabs.create({ url: fullUrl });
}

/**
 * 배후분석 열기
 */
async function openBaehu() {
    const popupWidth = 550;  // 원하는 팝업 너비
    const popupHeight= 950;  // 원하는 팝업 높이
    const left = (screen.width - popupWidth) / 2;
    const top = (screen.height - popupHeight) / 2;
    window.open("https://myfranchise.kr/map", "analyzeCatchmentDemand",
      `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`);
}
/**
 * 수익률 계산기 실행 (토큰 및 구독 상태 체크 포함)
 */
async function openCalculator(tabGubun = "sanga", extraParams = {}) {
    // 로그인 및 구독 상태 체크
    const auth = await loginValidForPanel();
    if (!auth.ok) return;

    // 1. 저장소에서 데이터 가져오기 (비동기)
    chrome.storage.local.get(["access_token", "is_subscribed", "apt_key", "villa_key", "sanga_key"], (items) => {
        const { access_token, is_subscribed } = items;

        // 2. 권한 검사
        // if (!access_token) {
        //     alert('로그인(회원가입) 후 사용바랍니다.');
        //     return;
        // }

        if (is_subscribed !== 'active') {
            alert('구독승인 후 사용바랍니다.');
            return;
        }

        // 3. 탭 구분(상가/일반)에 따른 기본 설정
        let menu = '';
        let popupWidth = 950;
        let popupHeight = 970;
        let regions = getCurrentRegionsString() || "경기도,김포시,운양동";

        if (tabGubun === 'sanga') {
            menu = 'sanga_profit';
            popupWidth = 970;
            popupHeight = 790;
        } else {
            menu = 'general_profit';
            popupWidth = 620;
            popupHeight = 780;
        }

        // 4. 파라미터 통합 (기본값 + 토큰 + 외부 주입값)
        const finalParams = {
            menu: menu,
            regions: regions,
            tk: access_token, // 스토리지에서 가져온 토큰 주입
            ...extraParams    // 외부에서 넘긴 데이터(aptNm, price 등) 병합
        };

        // 5. URL 생성
        const urlParams = new URLSearchParams();
        // 값이 있는 경우만 파라미터에 추가
        Object.entries(finalParams).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                urlParams.append(key, value);
            }
        });

        const extUrl = `${BASE_URL}/api/ext_tool?${urlParams.toString()}`;

        // 6. 팝업 실행
        const left = (screen.width - popupWidth) / 2;
        const top = (screen.height - popupHeight) / 2;

        window.open(
            extUrl,
            "analyzeProfit",
            `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`
        );
    });
}


/**
 * 패널 초기화(리셋)
 */
function resetPanel() {
    resultsContainer.innerHTML = '<div class="empty-state">분석 버튼을 눌러 시작하세요</div>';
    if (areaChartContainer) areaChartContainer.innerHTML = '';
    const agencySection = document.getElementById('top-agencies');
    if (agencySection) agencySection.innerHTML = '';
    const countEl = document.getElementById('analysis-count');
    if (countEl) countEl.classList.add('hidden');
    lastAnalysisData = null;
    if (currentRegionLabel) {
        analyzeBtn.textContent = `${currentRegionLabel} 매물분석하기`;
    } else {
        analyzeBtn.textContent = '매물 분석하기';
    }
    //
    currentChartType = '월세';
    const chartTitle = document.getElementById('chart-title');
    if (chartTitle) {
        chartTitle.textContent = '✏️ 월세 평수 분포';
    }
    //
    currentDetailView = 'list';
    currentListSort = {
        field: 'pricePerPyeong',
        direction: 'asc'
    };
    //
    currentFloorFilter = '전체';
}

/**
 * 현재 탭 상태 확인
 */
async function checkCurrentTab() {
    try {
        const response = await chrome.runtime.sendMessage({ type: 'GET_TAB_INFO' });
        if (response?.isNaverLand) {
            setStatus('ready', '분석 준비 완료');
        } else {
            // 네이버 부동산이 아니면 경고 표시 후 자동으로 페이지 이동
            setStatus('warning', '네이버 부동산으로 이동합니다...');
            //setStatus('warning', '네이버 부동산 페이지를 열어주세요');
            setTimeout(() => {
                //openNaverLand(); // 정의된 NAVER_LAND_URL로 이동
            }, 800); // 사용자 인지를 위해 1초 후 이동
        }
    } catch (error) {
        setStatus('error', '탭 정보를 가져올 수 없습니다');
    }
}

function setStatus(type, text) {
    statusBar.textContent = text;
    statusBar.className = `status-bar status-${type}`;
}

/**
 * 분석 시작
 */
async function startAnalysis() {
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = '[분석 중...]';
    resultsContainer.innerHTML = '<div class="empty-state">데이터를 가져오는 중입니다...</div>';

    try {
        const response = await chrome.runtime.sendMessage({ type: 'START_ANALYSIS' });

        if (response?.success) {
            lastAnalysisData = response.data;

            displayResults(response.data);
            displayAreaChart(response.data);
            displayTopAgencies(response.data);
            saveToHistory(response.data);
            //
            // 분석 응답에 포함된 지역정보를 바로 반영
            applyRegionLabelFromAnalysisData(response.data);
            analyzeBtn.disabled = false;

            // 분석 완료 안내 메시지 표시
            const wolseCount = response.data.listings?.filter(l => l.type === '월세').length || 0;
            const maemaeCount = response.data.listings?.filter(l => l.type === '매매').length || 0;
            showAnalysisCount(wolseCount, maemaeCount);

            // 매물 목록에 평당가/평수 배지 표시
            chrome.runtime.sendMessage({ type: 'SHOW_BADGES' }).catch(() => { });
        } else {
            throw new Error(response?.error || '분석 실패');
        }
    } catch (error) {
        console.error(error);
        resultsContainer.innerHTML = `<div class="empty-state">오류: ${error.message}</div>`;
        analyzeBtn.textContent = '매물 분석하기';
        analyzeBtn.disabled = false;
    }
}

/**
 * 분석 완료 안내 메시지 표시 (숫자 강조 및 색상 구분 적용)
 */
function showAnalysisCount(wolseCount, maemaeCount) {
    const countEl = document.getElementById('analysis-count');
    if (countEl) {
        const total = wolseCount + maemaeCount;

        // 공통 스타일: 글자 크기 12px, 진하게(bold)
        const baseStyle = "font-size: 14px; font-weight: bold;";

        // 숫자 스타일: 검정색
        const numStyle = `${baseStyle} color: #000;`;
        // 월세 스타일: 빨간색 (엑셀 테이블의 월세 색상과 매칭)
        const wolseStyle = `${baseStyle} color: #e91e63;`;
        // 매매 스타일: 파란색 (엑셀 테이블의 매매 색상과 매칭)
        const maemaeStyle = `${baseStyle} color: #2196f3;`;

        // innerHTML을 사용하여 각각의 span에 스타일 적용
        countEl.innerHTML = `
            <span style="${numStyle}">총 ${total}개 분석:</span> 
            <span style="${wolseStyle}">월세 ${wolseCount}개</span>, 
            <span style="${maemaeStyle}">매매 ${maemaeCount}개</span>
        `;

        countEl.classList.remove('hidden');
    }
}

/**
 * 결과 표시 (엑셀 테이블 스타일)
 */
function displayResults(data) {
    if (!data || !data.stats) {
        resultsContainer.innerHTML = '<div class="empty-state">데이터를 불러올 수 없습니다.</div>';
        return;
    }

    const { stats } = data;
    const byFloor = stats.byFloor || {};
    const floors = ['1층', '2층', '상층'];

    const wolseRowHTML = floors.map(floorKey => {
        const stat = byFloor[floorKey]?.wolse || { count: 0, trimmedAvg: 0 };
        const price = stat.count > 0 ? stat.trimmedAvg.toFixed(1) : '-';
        return `
            <td class="data-cell">
                <div class="cell-header">${floorKey}(${stat.count})</div>
                <div class="cell-value">${price}</div>
            </td>
        `;
    }).join('');

    const maemaeRowHTML = floors.map(floorKey => {
        const stat = byFloor[floorKey]?.maemae || { count: 0, trimmedAvg: 0 };
        const price = stat.count > 0 ? formatNumber(Math.round(stat.trimmedAvg)) : '-';
        return `
            <td class="data-cell">
                <div class="cell-header">${floorKey}(${stat.count})</div>
                <div class="cell-value">${price}</div>
            </td>
        `;
    }).join('');

    const detailSectionHTML = getListingDetailSectionHTML(data.listings, currentChartType, currentDetailView);

    const tableHTML = `
        <table class="excel-table">
            <tr class="row-wolse">
                <td class="row-header">월세</td>
                ${wolseRowHTML}
            </tr>
            <tr class="row-maemae">
                <td class="row-header">매매</td>
                ${maemaeRowHTML}
            </tr>
        </table>
        <div class="table-note">* 위 표는 최소값 최대값 제외 후 나머지 평균</div>
        ${detailSectionHTML}
    `;

    resultsContainer.innerHTML = tableHTML;
}

function getListingDetailSectionHTML(listings, selectedType, detailView) {
    const filteredListings = (listings || []).filter(l => l.type === selectedType);
    const typeClass = selectedType === '매매' ? 'is-maemae' : 'is-wolse';
    const typeLabel = selectedType === '매매' ? '매매' : '월세';

    const wolseActiveClass = selectedType === '월세' && detailView === 'list' ? 'active' : '';
    const maemaeActiveClass = selectedType === '매매' && detailView === 'list' ? 'active' : '';
    const cheapestActiveClass = selectedType === '매매' && detailView === 'cheapest' ? 'active' : '';
    const cheapestDisabledClass = selectedType !== '매매' ? 'disabled' : '';

    const floorSelectHTML = detailView === 'list'
        ? getFloorFilterSelectHTML(filteredListings)
        : '';

    let bodyHTML = '';

    if (selectedType === '매매' && detailView === 'cheapest') {
        bodyHTML = getCheapestMaemaeHTML(listings);
    } else {
        bodyHTML = getListingTableHTML(filteredListings, selectedType);
    }

    return `
        <div class="listing-detail-section ${typeClass}">
            <div class="listing-detail-header">
                <div class="listing-detail-left">
                    <div class="listing-detail-title-row">
                        <div class="listing-detail-title">📋 ${typeLabel} 상세</div>
                        ${floorSelectHTML}
                    </div>
                </div>

                <div class="listing-detail-toolbar">
                    <div class="listing-type-selector">
                        <button type="button" class="detail-mode-btn ${wolseActiveClass}" data-listing-type="월세">월세</button>
                        <button type="button" class="detail-mode-btn ${maemaeActiveClass}" data-listing-type="매매">매매</button>
                    </div>

                    <div class="listing-detail-controls">
                        <button type="button" class="detail-mode-btn cheapest-btn ${cheapestActiveClass} ${cheapestDisabledClass}" data-detail-mode="cheapest">최저가매물</button>
                    </div>
                </div>
            </div>

            <div class="listing-detail-body">
                ${bodyHTML}
            </div>
        </div>
    `;
}

// 층 필터 옵션 생성 함수
function getFloorFilterSelectHTML(listings) {
    const options = getFloorFilterOptions(listings);

    return `
        <div class="floor-filter-select-wrap">
            <select class="floor-filter-select" data-floor-select>
                ${options.map(label => `
                    <option value="${label}" ${currentFloorFilter === label ? 'selected' : ''}>
                        ${label}
                    </option>
                `).join('')}
            </select>
        </div>
    `;
}

// 층 정보에서 숫자와 유형(지하/저층/상층 등)을 추출하는 함수
function getFloorFilterOptions(listings) {
    const floorMap = new Map();

    (listings || []).forEach(item => {
        const info = extractFloorInfo(item.floor);
        if (!info) return;

        if (info.type === 'basement') {
            floorMap.set(info.label, { type: 'basement', order: -1, label: info.label });
        } else if (info.type === 'number') {
            floorMap.set(info.label, { type: 'number', order: info.num, label: info.label });
        }
    });

    const floorItems = Array.from(floorMap.values()).sort((a, b) => a.order - b.order);

    return [
        '전체',
        '저층',
        '상층',
        ...floorItems.map(item => item.label)
    ];
}

function extractFloorInfo(floorText) {
    if (!floorText) return null;

    const text = String(floorText).trim().toUpperCase();

    // 예: B1, B2
    const basementMatch = text.match(/^B(\d+)/);
    if (basementMatch) {
        return {
            type: 'basement',
            num: -parseInt(basementMatch[1], 10),
            label: `B${basementMatch[1]}`
        };
    }

    // 예: 1/7, 2/6, 3/10 -> 앞 숫자만 층으로 사용
    const slashMatch = text.match(/^(\d+)\s*\/\s*\d+$/);
    if (slashMatch) {
        const floorNum = parseInt(slashMatch[1], 10);
        return {
            type: 'number',
            num: floorNum,
            label: `${floorNum}층`
        };
    }

    // 예: 1층, 2층, 5층
    const floorMatch = text.match(/^(\d+)\s*층?$/);
    if (floorMatch) {
        const floorNum = parseInt(floorMatch[1], 10);
        return {
            type: 'number',
            num: floorNum,
            label: `${floorNum}층`
        };
    }

    return null;
}

function filterListingsByFloor(listings, selectedFilter) {
    if (!listings || !listings.length) return [];

    if (!selectedFilter || selectedFilter === '전체') {
        return listings;
    }

    return listings.filter(item => {
        const info = extractFloorInfo(item.floor);
        if (!info) return false;

        if (selectedFilter === '저층') {
            return info.type === 'basement' || (info.type === 'number' && info.num <= 2);
        }

        if (selectedFilter === '상층') {
            return info.type === 'number' && info.num >= 3;
        }

        return info.label === selectedFilter;
    });
}


function getListingTableHTML(listings, selectedType) {
    const floorFiltered = filterListingsByFloor(listings, currentFloorFilter);

    if (!floorFiltered || floorFiltered.length === 0) {
        return `<div class="empty-hint">${selectedType} 목록이 없습니다.</div>`;
    }

    const sorted = sortListingsForDetailTable(
        floorFiltered,
        currentListSort.field,
        currentListSort.direction
    );

    const rowsHTML = sorted.map(item => {
        return `
            <tr>
                <td>${formatFloorDisplay(item.floor)}</td>
                <td>${item.direction || '-'}</td>
                <td>${formatPricePerPyeong(item.pricePerPyeong)}</td>
                <td>${formatAreaDisplay(item.area)}</td>
                <td>${formatListingPrice(item)}</td>
            </tr>
        `;
    }).join('');

    return `
        <div class="listing-table-wrap">
            <table class="listing-detail-table">
                <thead>
                    <tr>
                        <th class="sortable ${getSortClass('floor')}" data-sort-field="floor">층</th>
                        <th>향</th>
                        <th class="sortable ${getSortClass('pricePerPyeong')}" data-sort-field="pricePerPyeong">평당가</th>
                        <th class="sortable ${getSortClass('area')}" data-sort-field="area">면적</th>
                        <th>가격</th>
                    </tr>
                </thead>
                <tbody>
                    ${rowsHTML}
                </tbody>
            </table>
        </div>
    `;
}

function sortListingsForDetailTable(listings, field, direction) {
    const sorted = [...listings];

    sorted.sort((a, b) => {
        let av = 0;
        let bv = 0;

        if (field === 'floor') {
            av = getFloorSortValue(a.floor);
            bv = getFloorSortValue(b.floor);
        } else if (field === 'pricePerPyeong') {
            av = Number(a.pricePerPyeong) || 0;
            bv = Number(b.pricePerPyeong) || 0;
        } else if (field === 'area') {
            av = Number(a.area) || 0;
            bv = Number(b.area) || 0;
        }

        if (av < bv) return direction === 'asc' ? -1 : 1;
        if (av > bv) return direction === 'asc' ? 1 : -1;
        return 0;
    });

    return sorted;
}

function getSortClass(field) {
    if (currentListSort.field !== field) return '';
    return currentListSort.direction === 'asc' ? 'sort-asc' : 'sort-desc';
}

function getFloorSortValue(floorText) {
    if (!floorText) return 9999;

    const text = String(floorText).trim();

    if (text.includes('지하')) {
        const num = parseInt(text.replace(/[^\d-]/g, ''), 10);
        return isNaN(num) ? -1 : -Math.abs(num);
    }

    if (text.includes('상층')) return 300;
    if (text.includes('중층')) return 200;
    if (text.includes('고층')) return 400;
    if (text.includes('저층')) return 100;

    const num = parseInt(text.replace(/[^\d]/g, ''), 10);
    return isNaN(num) ? 9999 : num;
}

function formatFloorDisplay(floor) {
    const info = extractFloorInfo(floor);
    return info ? info.label : (floor || '-');
}

function formatAreaDisplay(area) {
    const n = Number(area);
    return Number.isFinite(n) && n > 0 ? `${n.toFixed(1)}평` : '-';
}

function formatPricePerPyeong(value) {
    const n = Number(value);
    return Number.isFinite(n) && n > 0 ? `${formatNumber(Math.round(n))}만` : '-';
}

function setCurrentRegionInfo(data) {
    const info = data?.regionInfo || {};

    currentRegionInfo = {
        region: info.region || '',
        sigungu: info.sigungu || '',
        umdNm: info.umdNm || ''
    };
}

function getCurrentRegionsString() {
    const parts = [
        currentRegionInfo.region,
        currentRegionInfo.sigungu,
        currentRegionInfo.umdNm
    ].filter(Boolean);

    return parts.join(',');
}

function getCurrentRegionDisplayText() {
    const label = currentFloorFilter || '전체';
    return label;
}

function formatListingPrice(item) {
    if (item?.fullPrice) return item.fullPrice;

    if (item?.type === '월세') {
        const deposit = Number(item.deposit) || 0;
        const monthlyRent = Number(item.monthlyRent) || 0;

        if (deposit > 0 || monthlyRent > 0) {
            return `${formatNumber(deposit)}/${formatNumber(monthlyRent)}`;
        }
    }

    const salePrice = Number(item?.price) || Number(item?.salePrice) || 0;
    if (salePrice > 0) {
        return `${formatNumber(salePrice)}만`;
    }

    return '-';
}

/**
 * 매매 최저가 매물 HTML 생성
 */
function getCheapestMaemaeHTML(listings) {
    if (!listings || !Array.isArray(listings)) return '';

    // 매매 매물만 필터링
    const maemaeListings = listings.filter(l => l.type === '매매');
    if (maemaeListings.length === 0) return '';

    // 평당가 기준 최저가 찾기
    const cheapest = maemaeListings.reduce((prev, curr) =>
        prev.pricePerPyeong < curr.pricePerPyeong ? prev : curr
    );

    // 중개사 표시 처리
    let agencyDisplay = '-';
    if (cheapest.agencyCount > 1) {
        agencyDisplay = `중개사 ${cheapest.agencyCount}곳`;
    } else if (cheapest.agencyName) {
        agencyDisplay = cheapest.agencyName;
    }

    return `
        <div class="cheapest-section">
            <div class="cheapest-header">★ 매매 최저가 매물</div>
            <div class="cheapest-details">
                <div class="detail-row">
                    <span class="detail-label">가격</span>
                    <span class="detail-value">${cheapest.fullPrice}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">평단가</span>
                    <span class="detail-value">${formatNumber(cheapest.pricePerPyeong)}만/평</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">면적</span>
                    <span class="detail-value">${cheapest.area?.toFixed(1)}평</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">층/향</span>
                    <span class="detail-value">${cheapest.floor} / ${cheapest.direction}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">중개사</span>
                    <span class="detail-value">${agencyDisplay}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">확인일</span>
                    <span class="detail-value">${cheapest.verificationDate || '-'}</span>
                </div>
            </div>
        </div>
    `;
}

/**
 * 평수 분포 차트 (월세 전용) => 차후 중복데이타 제거요망
 */
function displayAreaChart(data) {
    // 안전 체크
    if (!data || !data.listings || !Array.isArray(data.listings)) {
        if (areaChartContainer) {
            areaChartContainer.innerHTML = '';
        }
        return;
    }
    // 현재 선택된 차트 타입(월세/매매)에 따라 데이터를 필터링하여
    renderAreaChart(data.listings, currentChartType);
}

/**
 * 부동산 TOP 3 표시
 */
function displayTopAgencies(data) {
    const agencySection = document.getElementById('top-agencies');
    if (!agencySection) return;

    if (!data || !data.listings || !Array.isArray(data.listings)) {
        agencySection.innerHTML = '';
        return;
    }

    // 중개사별 월세/매매 각각 카운트
    const agencyCounts = {};
    data.listings.forEach(l => {
        if (l.agencyName && l.agencyName !== '-' && l.agencyName.length > 1) {
            if (!agencyCounts[l.agencyName]) {
                agencyCounts[l.agencyName] = { wolse: 0, maemae: 0 };
            }
            if (l.type === '월세') {
                agencyCounts[l.agencyName].wolse++;
            } else if (l.type === '매매') {
                agencyCounts[l.agencyName].maemae++;
            }
        }
    });

    // 총 매물 수 기준 TOP 3 추출
    const top3 = Object.entries(agencyCounts)
        .map(([name, counts]) => ({
            name,
            wolse: counts.wolse,
            maemae: counts.maemae,
            total: counts.wolse + counts.maemae
        }))
        .sort((a, b) => b.total - a.total)
        .slice(0, 3);

    if (top3.length === 0) {
        agencySection.innerHTML = '';
        return;
    }

    // 헤더는 HTML에 있으므로 리스트만 생성
    const agencyHTML = `
        <div class="agency-list">
            ${top3.map((agency, idx) => `
                <div class="agency-item">
                    <span class="agency-rank">${idx + 1}</span>
                    <span class="agency-name">${agency.name}</span>
                    <span class="agency-count">월세 ${agency.wolse}개 / 매매 ${agency.maemae}개</span>
                </div>
            `).join('')}
        </div>
    `;

    agencySection.innerHTML = agencyHTML;
}

/**
 * 히스토리 저장
 */
function saveToHistory(data) {
    if (!data || !data.stats) return;

    chrome.storage.local.get(['analysisHistory'], (result) => {
        const history = result.analysisHistory || [];
        const newEntry = {
            timestamp: new Date().toISOString(),
            total: data.stats.total,
            wolseCount: data.stats.wolse?.count || 0,
            maemaeCount: data.stats.maemae?.count || 0
        };

        history.unshift(newEntry);
        if (history.length > 10) history.pop();

        chrome.storage.local.set({ analysisHistory: history });
        loadHistory();
    });
}

/**
 * 히스토리 로드
 */
function loadHistory() {
    chrome.storage.local.get(['analysisHistory'], (result) => {
        const history = result.analysisHistory || [];

        if (history.length === 0) {
            historyList.innerHTML = '<div class="empty-history">분석 기록이 없습니다</div>';
            return;
        }

        const historyHTML = history.slice(0, 5).map(entry => {
            const date = new Date(entry.timestamp);
            const dateStr = `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
            return `
                <div class="history-item">
                    <span class="history-date">${dateStr}</span>
                    <span class="history-stats">총 ${entry.total}개 (월세 ${entry.wolseCount}, 매매 ${entry.maemaeCount})</span>
                </div>
            `;
        }).join('');

        historyList.innerHTML = historyHTML;
    });
}

/**
 * 숫자 포맷 (천 단위 콤마)
 */
function formatNumber(num) {
    if (typeof num !== 'number' || isNaN(num)) return '-';
    return num.toLocaleString('ko-KR');
}


/**
 * 분석 응답 데이터 안의 지역정보를 panel 상단에 바로 반영
 * 우선순위:
 * 1. data.regionLabel
 * 2. data.fullRegionText + " 매물분석"
 * 3. data.regionInfo(region/sigungu/umdNm) 조합
 * 4. 기본값 "매물분석"
 */
function applyRegionLabelFromAnalysisData(data) {
    const regionLabelEl = document.getElementById('region-analysis-label');

    // 기본은 "기존 값 유지"
    let label = currentRegionLabel || '';

    if (data?.regionInfo) {
        const region = data.regionInfo.region || '';
        const sigungu = data.regionInfo.sigungu || '';
        const umdNm = data.regionInfo.umdNm || '';

        // regionInfo에 실제 값이 있을 때만 새 라벨 생성
        if (region && sigungu && umdNm) {
            //label = `${region}>${sigungu}>${umdNm}`;
            label = `${sigungu}>${umdNm}`;
        } else if (sigungu && umdNm) {
            label = `${sigungu}>${umdNm}`;
        } else if (sigungu) {
            label = sigungu;
        } else if (region) {
            label = region;
        }
    }

    // 그래도 비어 있으면 최종 기본값
    if (!label) {
        label = '매물분석';
    }

    setCurrentRegionInfo(data);
    currentRegionLabel = label;

    // region-analysis-label 이 있을 때만 표시
    if (regionLabelEl) {
        regionLabelEl.textContent = label;
    }
    //
    if (analyzeBtn) {
        analyzeBtn.textContent = `${currentRegionLabel} 매물분석하기`;
    }
}