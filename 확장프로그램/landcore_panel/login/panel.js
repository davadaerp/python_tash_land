/**
 * landcore - Excel Style Panel JS
 * 1. 실시간 분석 업데이트 수신 및 처리
 * 2. 분석도구 제공으로 실거래, 업종분석, 통계분석, 매물검색 팝업 열기
 */
// DOM Elements (초기에는 null 상태)
let analyzeBtn;
let resetBtn;
let resetBtnIcon;
let realAuctionBtn;
let realAuctionMenu;
let calculatorBtn;
let smsBtn;
let imjangAnalysisMenu;
let imjangAnalysisBtn;
let nplBtn;
let baehuBtn;
let naverLandBtn;
let guideBtn;
let statusBar;
let resultsContainer;
let areaChartContainer;
let historyList;
//
let siteShortcutBtn;
let siteShortcutMenu;
// 상위목록 중개사 섹션
let topAgenciesToggle;
let topAgenciesSection;

// API Base URL => landcore.js에 이미 정의되어 있으므로 주석 처리 (중복 정의 방지) 차후 landcore
const LANDCORE_URL = "https://www.landcore.co.kr";
//const LANDCORE_URL = 'http://127.0.0.1:5000';

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
    field: 'pricePerPyeong',   // 'floor' | 'pricePerPyeong' | 'area' | 'price'
    direction: 'asc'           // 'asc' | 'desc'
};
// 현재 층 필터 상태 (예: '전체', '1층', '2층', '상층')
let currentFloorFilter = '전체';

let currentRegionInfo = {
    region: '',
    sigungu: '',
    umdNm: '',
    lawdCd: '',     // 법정동코드 (예: 41135000)
    lawdName: '',   // 경기도 김포시 운양동
    regions: '',    // 경기도,김포시,운양동
    tabGubun: ''    // apt | villa | sanga
};

// 초기화
document.addEventListener('DOMContentLoaded', async () => {
    // 로그인 상태 업데이트
    //updateUserSession();

    console.log('Panel Initialized');
    // 여기 정의하면 팝업식으로 열릴때 계속실행되어버림 ㅠ.ㅠ
    // 패널이 처음 열릴 때 현재 활성 탭이 지원 페이지가 아니면
    // 네이버부동산 탭을 자동으로 보장
    const activeTabUrl = await getActiveTabUrl();
    if (!isSupportedAnalysisUrl(activeTabUrl)) {
        await ensureNaverLandTabOnPanelOpen();
    }

    // 🔥 여기서 DOM 요소 가져오기 (핵심)
    analyzeBtn = document.getElementById('analyze-btn');
    resetBtn = document.getElementById('reset-btn');
    resetBtnIcon = document.getElementById('reset-btn-icon');
    realAuctionBtn = document.getElementById('real-auction-btn');
    realAuctionMenu = document.getElementById('real-auction-menu');
    calculatorBtn = document.getElementById('calculator-btn');
    smsBtn = document.getElementById('sms-btn');
    imjangAnalysisMenu = document.getElementById('imjang-analysis-menu');
    imjangAnalysisBtn = document.getElementById('imjang-analysis-btn');
    nplBtn = document.getElementById('npl-btn');
    baehuBtn = document.getElementById('baehu-btn');
    naverLandBtn = document.getElementById('naver-land-btn');
    guideBtn = document.getElementById('guide-btn');
    statusBar = document.getElementById('status-bar');
    resultsContainer = document.getElementById('results-container');
    areaChartContainer = document.getElementById('area-chart');
    historyList = document.getElementById('history-list');

    siteShortcutBtn = document.getElementById('site-shortcut-btn');
    siteShortcutMenu = document.getElementById('site-shortcut-menu');
    // 상위목록 중개사 섹션
    topAgenciesToggle = document.getElementById('top-agencies-toggle');
    topAgenciesSection = document.getElementById('top-agencies');

    analyzeBtn?.addEventListener('click', startAnalysis);
    resetBtn?.addEventListener('click', resetPanel);
    realAuctionBtn?.addEventListener('click', toggleAnalysisMenu);
    calculatorBtn?.addEventListener('click', openCalculator);
    baehuBtn?.addEventListener('click', openBaehu);
    smsBtn?.addEventListener('click', openSmsSendFromPanel);
    imjangAnalysisBtn?.addEventListener('click', toggleImjangAnalysisMenu);
    nplBtn?.addEventListener('click', openNplSearchFromPanel);
    //memoBtn.addEventListener('click', openMemo);
    naverLandBtn?.addEventListener('click', openNaverLand);
    guideBtn?.addEventListener('click', (e) => {
        e.preventDefault();
        openGuide();
    });
    //
    siteShortcutBtn?.addEventListener('click', toggleSiteShortcutMenu);
    topAgenciesToggle?.addEventListener('click', toggleTopAgenciesSection);

    // ✅ 상위 중개사 클릭 이벤트 (부동산명 클릭)
    topAgenciesSection?.addEventListener('click', (e) => {
        const agencyLink = e.target.closest('[data-agency-name]');
        if (!agencyLink) return;

        e.preventDefault();

        const agencyName = agencyLink.getAttribute('data-agency-name') || '';
        showAgencyDetailByName(agencyName);
    });

    // 초기화 아이콘 업데이트
    updateResetButtonIcon(getCurrentTabGubun());

    // 결과 영역 내 목록/최저가 전환 및 정렬 처리
    resultsContainer?.addEventListener('click', (e) => {
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
    resultsContainer?.addEventListener('change', (e) => {
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
            imjangAnalysisMenu?.classList.add('hidden');
        }

        if (!e.target.closest('.tools-header-shortcut')) {
            siteShortcutMenu?.classList.add('hidden');
        }

        // 데이터분석 메뉴버튼
        const menuBtn = e.target.closest('[data-analysis-menu]');
        if (menuBtn) {
            const menuType = menuBtn.getAttribute('data-analysis-menu');
            realAuctionMenu?.classList.add('hidden');

            if (menuType === 'realdeal') {
                //openLandRealAuctionPopupFromPanel();
                openLandCoreFromPanel("wishlist")
            } else if (menuType === 'commercial') {
                //openCommericalAreaPopupFromPanel();
                openLandCoreFromPanel("commerical")
            } else if (menuType === 'statistics') {
                openLandRealStatisticsPopupFromPanel();
            } else if (menuType === 'propertySearch') {
                // 네이버매물검색
                openPropertySearchPopupFromPanel();
            }
            return;
        }

        // 임장분석 메뉴버튼
        const imjangMenuBtn = e.target.closest('[data-imjang-menu]');
        if (imjangMenuBtn) {
            const menuType = imjangMenuBtn.getAttribute('data-imjang-menu');
            imjangAnalysisMenu?.classList.add('hidden');

            if (menuType === 'checklist') {
                openChecklistFromPanel();
            } else if (menuType === 'formDownload') {
                openFormDownloadFromPanel();
            }
            return;
        }

        // 사이트바로가기 메뉴버튼
        const siteBtn = e.target.closest('[data-site-url]');
        if (siteBtn) {
            const url = siteBtn.getAttribute('data-site-url');
            siteShortcutMenu?.classList.add('hidden');

            if (url) {
                chrome.tabs.create({ url });
            }
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
    const typeFilteredListings = (listings || []).filter(l => l.type === type);
    const filteredListings = filterListingsByFloor(typeFilteredListings, floorLabel);
    const selectedCount = filteredListings.length || 0;

    chartTitle.textContent = `✏️ ${type} 평수 분포(${floorLabel}/${selectedCount}건)`;

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
 * 실시간 분석 업데이트 처리
 */
async function handleAutoUpdate(data) {
    lastAnalysisData = data;

    // 지역 + 탭구분 반영
    setCurrentRegionInfo(data);

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
 * - 이미 열려있으면 alert
 * - 없으면 현재 활성 탭을 네이버부동산으로 이동
 */
function openNaverLand() {
    chrome.tabs.query({ currentWindow: true }, async (tabs) => {
        if (chrome.runtime.lastError) {
            alert('탭 조회 중 오류 발생');
            return;
        }

        // 이미 열려 있는 네이버부동산 탭 찾기
        const exists = tabs.find(tab => {
            const url = tab.url || '';
            return url.includes('land.naver.com');
        });

        if (exists) {
            alert('네이버부동산 사이트가 이미 열려있습니다.');
            return;
        }

        // 현재 활성 탭 찾기
        const activeTab = tabs.find(tab => tab.active);
        if (!activeTab?.id) {
            alert('현재 활성 탭을 찾을 수 없습니다.');
            return;
        }

        const activeUrl = activeTab.url || '';

        // 기본값 (없으면 기존처럼)
        let targetUrl = NAVER_LAND_URL;


        // 현재 열린 landcore 관심물건 지도 페이지에서 선택된 좌표 조회
        const selectedLocation = await getWishlistSelectedLocationFromActiveTab();

        const latitude = selectedLocation?.latitude || null;
        const longitude = selectedLocation?.longitude || null;
        const objectType = selectedLocation?.objectType || '';
        const lat = latitude || null;
        const lon = longitude || null;
        // 차후 objectType(근린상가,다가구,아파트등) 위치이동정의

        // 좌표 있으면 네이버 지도 위치 이동 URL로 변경
        // 구네이버: https://new.land.naver.com/offices?ms=${lat},${lon},17&a=SG&b=A1:B2&e=RETAIL
        // 신네이버: https://fin.land.naver.com/map?center=127.01767432382815-37.59265013737151&zoom=16&tradeTypes=A1-B2&realEstateTypes=D02-D03-D04-E01-Z00-D01
        if (lat && lon) {
            targetUrl = `https://new.land.naver.com/offices?ms=${lat},${lon},17&a=SG&b=A1:B2&e=RETAIL`;
        }
        console.log('targetUrl:', targetUrl, {
            latitude,
            longitude,
            objectType
        });

        // 현재 활성 탭이 landcore.co.kr 이면 새 탭으로 열기
        if (activeUrl.includes('landcore.co.kr')) {
            chrome.tabs.create({ url: targetUrl });
            setStatus('ready', '네이버부동산을 새 탭으로 열었습니다.');
            return;
        }

        try {
            const response = await chrome.runtime.sendMessage({
                type: 'MOVE_TAB_TO_NAVER_LAND',
                tabId: activeTab.id,
                url: targetUrl
            });

            if (!response?.success) {
                alert(response?.error || '네이버부동산 이동 실패');
                return;
            }

            setStatus('ready', '현재 탭을 네이버부동산으로 이동했습니다.');
        } catch (error) {
            console.error('openNaverLand MOVE_TAB_TO_NAVER_LAND 오류:', error);
            alert('네이버부동산 이동 중 오류가 발생했습니다.');
        }

        // 없으면 새로 열기 => 이전버전
        //chrome.tabs.create({ url: NAVER_LAND_URL });
    });
}

/**
 * 사용가이드 페이지 열기
 */
function openGuide() {
    //const guideUrl = chrome.runtime.getURL('guide/UserGuide.html');
    const guideUrl = `${LANDCORE_URL}/api/form_guide?menu=guide`;
    chrome.tabs.create({ url: guideUrl });
}

/*
 * 로그인 관련 적용처리
 */
async function loginForPanel() {
    return new Promise((resolve) => {
        chrome.storage.local.get(
            ["access_token", "is_subscribed"],
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
                    const response = await fetch(LANDCORE_URL +'/api/user/subscribe_check', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${accessToken}`
                        }
                    });

                    const result = await response.json();

                    if (result.result === 'Success') {
                        return resolve({
                            ok: true,
                            access_token: accessToken
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

// 사이트 바로가기 메뉴 토글
function toggleSiteShortcutMenu(e) {
    e.stopPropagation();
    siteShortcutMenu?.classList.toggle('hidden');
}

// 상위목록 중개사 섹션 토글
function toggleTopAgenciesSection() {
    if (!topAgenciesSection || !topAgenciesToggle) return;

    const isHidden = topAgenciesSection.classList.contains('hidden');

    if (isHidden) {
        topAgenciesSection.classList.remove('hidden');
        topAgenciesToggle.setAttribute('aria-expanded', 'true');
    } else {
        topAgenciesSection.classList.add('hidden');
        topAgenciesToggle.setAttribute('aria-expanded', 'false');
    }

    syncTopAgenciesToggleIcon();
}

function syncTopAgenciesToggleIcon() {
    const iconEl = document.getElementById('top-agencies-toggle-icon');
    if (!iconEl || !topAgenciesSection) return;

    const isExpanded = !topAgenciesSection.classList.contains('hidden');
    iconEl.textContent = isExpanded ? '▲' : '▼';
}

async function showAgencyDetailByName(agencyName) {
    if (!agencyName) {
        alert('부동산명이 없습니다.');
        return;
    }

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const activeTab = tabs?.[0];

        if (!activeTab?.id) {
            alert('현재 활성 탭을 찾을 수 없습니다.');
            return;
        }

        chrome.tabs.sendMessage(
            activeTab.id,
            {
                type: 'GET_AGENCY_DETAIL_BY_NAME',
                agencyName
            },
            (response) => {
                if (chrome.runtime.lastError) {
                    alert('네이버부동산 탭에서 중개사 정보를 가져올 수 없습니다.');
                    return;
                }

                if (!response?.success || !response.data) {
                    alert(`${agencyName}\n\n해당 부동산명의 상세 매물을 찾지 못했습니다.`);
                    return;
                }

                const d = response.data;

                // alert(
                //     `부동산명: ${d.agencyName || agencyName}\n` +
                //     `전화번호: ${d.agencyPhone || '-'}\n` +
                //     `휴대폰: ${d.agencyMobile || '-'}\n` +
                //     `주소: ${d.agencyAddress || '-'}`
                // );
            }
        );
    });
}

/**
 * 실거래, 업종분석, 통계분석 열기
 */
// 분석 메뉴 토글
function toggleAnalysisMenu(e) {
    e.stopPropagation();
    realAuctionMenu?.classList.toggle('hidden');
}

// 실거래 팝업방식 열기 (패널에서 지역정보 전달) => 사용안함
async function openLandRealAuctionPopupFromPanel_old() {
    // 로그인 및 구독 상태 체크
    const auth = await loginValidForPanel();
    if (!auth.ok) return;

    // 외부에서 탭 구분이 명확히 넘어오면 그걸 우선, 그렇지 않으면 현재 탭 상태에서 구분, 둘 다 없으면 기본값 'sanga'로 설정
    const selectedTabGubun = getCurrentTabGubun() || 'sanga';

    // 테스트용 확인
    //alert(`현재 탭 구분: ${selectedTabGubun}`);

    let menu = "sanga_real_deal";
    if (selectedTabGubun === 'sanga') {
        menu = 'sanga_real_deal';
    } else if (selectedTabGubun === 'villa') {
        menu = 'villa_real_deal';
    } else if (selectedTabGubun === 'apt') {
        menu = 'apt_real_deal';
    }

    // 🔥 여기 수정
    const regionInfo = await getCurrentRegionsString(auth.access_token);
    const regions = regionInfo.regions || "경기도,김포시,운양동";
    const extUrl = `${LANDCORE_URL}/api/ext_tool?menu=${menu}&regions=${encodeURIComponent(regions)}&tk=${encodeURIComponent(auth.access_token)}`;

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

// 실거래(관심물건포함) 검색 브라우져상 새탭으로 열기 (POST 방식)
// param_menu => wishlist:관심물건및 실거래분석, commerical: 업종분석, npl: NPL물건검색
async function openLandCoreFromPanel(param_menu = 'wishlist') {
    const auth = await loginValidForPanel();
    if (!auth || !auth.ok) return;

    try {
        console.log("== openLandCoreFromPanel (Requesting map2): ", currentRegionInfo);
        // 1. 법정동 정보 확인 (서버의 get_lawd_by_name 처리를 위해 address 필수)
        if (!currentRegionInfo) {
            throw new Error('법정동 정보(주소)가 비어 있습니다.');
        }
        //
        const address = currentRegionInfo.region + ' ' + currentRegionInfo.sigungu  + ' ' + currentRegionInfo.umdNm ;
        // apt,villa,sanga
        const propertyType = currentRegionInfo.tabGubun;
        console.log("== openLandCoreFromPanel (Requesting map): ", address, propertyType);

        // 2. 서버 설정에 맞춘 타겟 URL 수정 (map -> map2)
        const targetUrl = `${LANDCORE_URL}/api/ext_tool/map_panel`;

        // 3. 숨겨진 form 엘리먼트 생성
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = targetUrl;
        form.target = '_blank'; // 새 탭에서 열기

        // 4. 전송할 데이터 구성 (서버의 request.form.get 항목과 일치시킴)
        const data = {
            menu: param_menu,          // wishlist, commercial, npl 등
            tk: auth.access_token,     // 서버의 access_token 변수로 매핑됨
            propertyType: propertyType,
            address: address           // 서버의 get_lawd_by_name의 인자로 사용됨

        };

        // 5. 데이터를 hidden input으로 추가
        for (const key in data) {
            if (data.hasOwnProperty(key)) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = key;
                input.value = data[key];
                form.appendChild(input);
            }
        }

        // 6. body에 붙여서 제출 후 즉시 제거
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);

    } catch (err) {
        console.error('실거래분석 처리 실패:', err);
        alert(`실거래분석 처리 중 오류가 발생했습니다.\n${err.message || err}`);
    }
}

// NPL 검색 브라우져상 새탭으로 열기 (POST 방식)
async function openNplSearchFromPanel() {
    //
    openLandCoreFromPanel("npl");
}


// 통계분석 팝업 열기 (패널에서 지역정보 전달)
async function openLandRealStatisticsPopupFromPanel() {
    // 로그인 및 구독 상태 체크
    const auth = await loginValidForPanel();
    if (!auth.ok) return;

    // 외부에서 탭 구분이 명확히 넘어오면 그걸 우선, 그렇지 않으면 현재 탭 상태에서 구분, 둘 다 없으면 기본값 'sanga'로 설정
    const selectedTabGubun = getCurrentTabGubun() || 'sanga';

    // 테스트용 확인
    console.log(`현재 탭 구분: ${selectedTabGubun}`);

    if (selectedTabGubun === 'apt') {
        alert('아파트 통계분석은 준비중입니다.');
        return;
    }

    const regionInfo = await getCurrentRegionsString(auth.access_token);
    const regions = regionInfo.regions;     // 경기도,김포시,운양동

    const urlParams = new URLSearchParams({
        menu: selectedTabGubun,
        type: 'public',
        regions,
        tk: auth.access_token
    });

    const extUrl = `${LANDCORE_URL}/api/trade/statistics?${urlParams.toString()}`;

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

// 매물검색 팝업 열기 (패널에서 지역정보 전달)
async function openPropertySearchPopupFromPanel() {
    // 로그인 및 구독 상태 체크
    const auth = await loginValidForPanel();
    if (!auth.ok) return;

    alert('준비중입니다.')
    return;

    const regionInfo = await getCurrentRegionsString(auth.access_token);
    const regions = regionInfo?.regions || "경기도,김포시,운양동";

    // menu => apt_search, sanga_search
    const urlParams = new URLSearchParams({
        menu: 'sanga_search',
        regions: regions,
        tk: auth.access_token,
        customTag: 'propertySearch'
    });

    const extUrl = `${LANDCORE_URL}/api/ext_tool?${urlParams.toString()}`;

    const popupWidth = 1480;
    const popupHeight = 1200;
    const left = (screen.width - popupWidth) / 2;
    const top = (screen.height - popupHeight) / 2;

    window.open(
        extUrl,
        "propertySearchPopup",
        `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`
    );
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
async function openCalculator(extraParams = {}) {
    // 로그인 및 구독 상태 체크
    const auth = await loginValidForPanel();
    if (!auth.ok) return;

    // 1. 저장소에서 데이터 가져오기 (비동기)
    chrome.storage.local.get(["access_token", "is_subscribed", "apt_key", "villa_key", "sanga_key"], async (items) => {
        const {access_token, is_subscribed} = items;

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
        const regionInfo = await getCurrentRegionsString(auth.access_token);
        const regions = regionInfo.regions || "경기도,김포시,운양동";

        // 외부에서 탭 구분이 명확히 넘어오면 그걸 우선, 그렇지 않으면 현재 탭 상태에서 구분, 둘 다 없으면 기본값 'sanga'로 설정
        const selectedTabGubun = getCurrentTabGubun() || 'sanga';

        // 테스트용 확인
        // alert(`현재 탭 구분: ${selectedTabGubun}`);
        console.log(`현재 탭 구분: ${selectedTabGubun}`);

        if (selectedTabGubun === 'sanga') {
            menu = 'sanga_profit';
            popupWidth = 980;
            popupHeight = 840;
        } else {
            menu = 'general_profit';
            popupWidth = 640;
            popupHeight = 775;
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

        const extUrl = `${LANDCORE_URL}/api/ext_tool?${urlParams.toString()}`;

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

// SMS 발송 페이지 열기 (토큰 및 구독 상태 체크 포함)
async function openSmsSendFromPanel() {
    const auth = await loginValidForPanel();
    if (!auth.ok) return;

    const regionInfo = await getCurrentRegionsString(auth.access_token);
    const regions = regionInfo.regions || "경기도,김포시,운양동";

    const urlParams = new URLSearchParams({
        menu: 'realtor',
        regions,
        tk: auth.access_token,
        customTag: 'sms'
    });

    const extUrl = `${LANDCORE_URL}/api/ext_tool?${urlParams.toString()}`;

    const popupWidth = 1000;
    const popupHeight = 1180;
    const left = (screen.width - popupWidth) / 2;
    const top = (screen.height - popupHeight) / 2;

    window.open(
        extUrl,
        "smsSendSearch",
        `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`
    );
}

// 임장분석 메뉴열기
function toggleImjangAnalysisMenu(e) {
    e.stopPropagation();
    imjangAnalysisMenu?.classList.toggle('hidden');
    realAuctionMenu?.classList.add('hidden');
}

// 투자체크리스트 새탭에서 열기
async function openChecklistFromPanel() {
    const auth = await loginValidForPanel();
    if (!auth.ok) return;

    const guideUrl = `${LANDCORE_URL}/api/form_guide?menu=checklist`;
    chrome.tabs.create({ url: guideUrl });
}

// 매물 분석 양식 다운로드 페이지 열기 (토큰 및 구독 상태 체크 포함)
async function openFormDownloadFromPanel() {
    const auth = await loginValidForPanel();
    if (!auth.ok) return;

    console.log("== openFormDownloadFromPanel: ", currentRegionInfo);
    if (!currentRegionInfo) {
        throw new Error('법정동 정보(주소)가 비어 있습니다.');
    }
    //
    const regions = currentRegionInfo.region + ',' + currentRegionInfo.sigungu  + ',' + currentRegionInfo.umdNm ;
    console.log("== openLandCoreFromPanel regions: ", regions);

    const urlParams = new URLSearchParams({
        menu: 'form_down',
        regions,
        tk: auth.access_token,
        customTag: 'form'
    });

    const extUrl = `${LANDCORE_URL}/api/ext_tool?${urlParams.toString()}`;

    const popupWidth = 500;
    const popupHeight = 450;
    const left = (screen.width - popupWidth) / 2;
    const top = (screen.height - popupHeight) / 2;

    window.open(
        extUrl,
        "formDownload",
        `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`
    );
}

/**
 * 새 분석 시작 전에 이전 분석 UI를 0 기준으로 초기화
 */
function resetAnalysisUiForNewRun() {
    // 분석 상태 초기화
    currentChartType = '월세';
    currentDetailView = 'list';
    currentFloorFilter = '전체';
    currentListSort = {
        field: 'pricePerPyeong',
        direction: 'asc'
    };

    // 결과 영역은 로딩 메시지로 교체
    resultsContainer.innerHTML = '<div class="empty-state">데이터를 가져오는 중입니다...</div>';

    // 평수 분포 초기화
    if (areaChartContainer) {
        areaChartContainer.innerHTML = '<div class="empty-msg" style="padding:20px; color:#999; text-align:center;">월세 전체 데이터가 없습니다.</div>';
    }

    const chartTitle = document.getElementById('chart-title');
    if (chartTitle) {
        chartTitle.textContent = '✏️ 월세 평수 분포(전체/0건)';
    }

    // 분석 건수 0으로 초기화
    const countEl = document.getElementById('analysis-count');
    if (countEl) {
        countEl.innerHTML = `
            <span style="font-size: 14px; font-weight: bold; color: #000;">총 0개 분석:</span> 
            <span style="font-size: 14px; font-weight: bold; color: #e91e63;">월세 0개</span>, 
            <span style="font-size: 14px; font-weight: bold; color: #2196f3;">매매 0개</span>
        `;
        countEl.classList.remove('hidden');
    }

    // 상태바 0 기준으로 초기화
    setStatus('loading', '분석 준비 중 (0개)');

    // TOP 중개사 초기화
    const agencySection = document.getElementById('top-agencies');
    if (agencySection) {
        agencySection.innerHTML = '';
        agencySection.classList.add('hidden');
    }
    if (topAgenciesToggle) {
        topAgenciesToggle.setAttribute('aria-expanded', 'false');
    }
    syncTopAgenciesToggleIcon();
}

/**
 * 패널 초기화(리셋)
 */
function resetPanel() {
    resultsContainer.innerHTML = '<div class="empty-state">분석 버튼을 눌러 시작하세요</div>';
    if (areaChartContainer) areaChartContainer.innerHTML = '';
    //
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
    // 상위목록 중개사 초기화
    const agencySection = document.getElementById('top-agencies');
    if (agencySection) {
        agencySection.innerHTML = '';
        agencySection.classList.add('hidden');
    }
    if (topAgenciesToggle) {
        topAgenciesToggle.setAttribute('aria-expanded', 'false');
    }
    syncTopAgenciesToggleIcon();
    //
    currentDetailView = 'list';
    currentListSort = {
        field: 'pricePerPyeong',
        direction: 'asc'
    };
    //
    currentFloorFilter = '전체';

    // 초기화 아이콘 설정
    updateResetButtonIcon(getCurrentTabGubun());
}

/**
 * 현재 탭 상태 확인--네이버부동산 탭이면 분석 준비, 아니면 경고 및 네이버부동산으로 이동
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

function isSupportedAnalysisUrl(url = '') {
    return (
        url.includes('new.land.naver.com') ||
        url.includes('fin.land.naver.com') ||
        url.includes('www.tankauction.com/ca/caList.php') ||
        url.includes('www.tankauction.com/pa/paList.php') ||
        url.includes('www.tankauction.com/ca/caView.php') ||
        url.includes('www.tankauction.com/pa/paView.php')
    );
}

async function getActiveTabUrl() {
    return new Promise((resolve) => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (chrome.runtime.lastError || !tabs || !tabs.length) {
                resolve('');
                return;
            }
            resolve(tabs[0]?.url || '');
        });
    });
}

// 관심물거 지도위치 가져오기
async function getWishlistSelectedLocationFromActiveTab() {
    return new Promise((resolve) => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (chrome.runtime.lastError || !tabs || !tabs.length || !tabs[0]?.id) {
                resolve(null);
                return;
            }

            const activeTab = tabs[0];

            chrome.tabs.sendMessage(
                activeTab.id,
                { type: 'GET_WISHLIST_SELECTED_LOCATION' },
                (response) => {
                    if (chrome.runtime.lastError) {
                        resolve(null);
                        return;
                    }

                    if (!response?.success || !response?.data) {
                        resolve(null);
                        return;
                    }

                    resolve(response.data);
                }
            );
        });
    });
}

function setStatus(type, text) {
    if (!statusBar) {
        console.warn('[setStatus] status-bar 요소가 없습니다.', { type, text });
        return;
    }

    statusBar.textContent = text;
    statusBar.className = `status-bar status-${type}`;
}

/**
 * 패널이 열릴 때 네이버부동산 탭을 보장
 * 1) 현재 윈도우에 네이버부동산 탭이 있으면 그 탭으로 이동
 * 2) 없으면 네이버부동산 새 탭 생성
 */
async function ensureNaverLandTabOnPanelOpen() {
    try {
        setStatus('loading', '네이버부동산 탭 확인 중...');

        const response = await chrome.runtime.sendMessage({
            type: 'ENSURE_NAVER_LAND_TAB',
            url: NAVER_LAND_URL
        });

        if (response?.success) {
            if (response.action === 'focus') {
                setStatus('ready', '기존 네이버부동산 탭으로 이동했습니다.');
            } else if (response.action === 'create') {
                setStatus('ready', '네이버부동산 탭을 새로 열었습니다.');
            } else {
                setStatus('ready', '분석 준비 완료');
            }
        } else {
            setStatus('error', response?.error || '네이버부동산 탭 확인 실패');
        }
    } catch (error) {
        console.error('ensureNaverLandTabOnPanelOpen 오류:', error);
        setStatus('error', '네이버부동산 탭 확인 중 오류 발생');
    }
}

/**
 * 분석 시작
 */
async function startAnalysis() {

    // 현재 탭이 fin/new/tankauction 분석 지원 페이지가 아니면 그때만 네이버 탭 보장
    const activeTabUrl = await getActiveTabUrl();
    if (!isSupportedAnalysisUrl(activeTabUrl)) {
        await ensureNaverLandTabOnPanelOpen();
    }

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = '[분석 중...]';
    resultsContainer.innerHTML = '<div class="empty-state">데이터를 가져오는 중입니다...</div>';

    // 새 분석 시작 전 이전 결과를 0 기준으로 초기화
    resetAnalysisUiForNewRun();

    try {
        const response = await chrome.runtime.sendMessage({ type: 'START_ANALYSIS' });

        if (response?.success) {
            lastAnalysisData = response.data;

            // 지역 + 탭구분 반영
            setCurrentRegionInfo(response.data);

            displayResults(response.data);
            displayAreaChart(response.data);
            displayTopAgencies(response.data);
            //saveToHistory(response.data);

            // 분석 응답에 포함된 지역정보를 바로 반영
            applyRegionLabelFromAnalysisData(response.data);

            analyzeBtn.disabled = false;

            // 분석 완료 안내 메시지 표시
            const wolseCount = response.data.listings?.filter(l => l.type === '월세').length || 0;
            const maemaeCount = response.data.listings?.filter(l => l.type === '매매').length || 0;
            showAnalysisCount(wolseCount, maemaeCount);

            // 매물 목록에 평당가/평수 배지 표시
            chrome.runtime.sendMessage({ type: 'SHOW_BADGES' }).catch(() => {});
        } else {
            throw new Error(response?.error || '분석 실패');
        }
    } catch (error) {
        console.error(error);
        resultsContainer.innerHTML = `<div class="empty-state">오류: ${error.message}</div>`;
        setStatus('error', '분석 실패 (0개)');
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

    const formatStatValue = (value, typeKey) => {
        const num = Number(value);
        if (!Number.isFinite(num) || num <= 0) return '-';

        if (typeKey === 'wolse') {
            return num.toFixed(1);
        }
        return formatNumber(Math.round(num));
    };

    const buildRows = (typeKey, typeLabel, typeClass) => {
        return floors.map((floorKey, idx) => {
            const stat = byFloor[floorKey]?.[typeKey] || {
                count: 0,
                trimmedAvg: 0,
                min: 0,
                max: 0
            };

            const minText = stat.count > 0 ? formatStatValue(stat.min, typeKey) : '-';
            const avgText = stat.count > 0 ? formatStatValue(stat.trimmedAvg, typeKey) : '-';
            const maxText = stat.count > 0 ? formatStatValue(stat.max, typeKey) : '-';

            return `
                <tr class="summary-row ${typeClass}">
                    ${idx === 0 ? `<td class="summary-type-cell" rowspan="3">${typeLabel}</td>` : ''}
                    <td class="summary-floor-cell">${floorKey}</td>
                    <td class="summary-min-cell">${minText}</td>
                    <td class="summary-avg-cell">${avgText}</td>
                    <td class="summary-max-cell">${maxText}</td>
                    <td class="summary-count-cell">${stat.count}</td>
                </tr>
            `;
        }).join('');
    };

    const tableHTML = `
        <div class="summary-table-section">
            <table class="summary-result-table">
                <thead>
                    <tr>
                        <th>구분</th>
                        <th>층</th>
                        <th>최소</th>
                        <th>평균</th>
                        <th>최대</th>
                        <th>건수</th>
                    </tr>
                </thead>
                <tbody>
                    ${buildRows('wolse', '월세', 'row-wolse')}
                    ${buildRows('maemae', '매매', 'row-maemae')}
                </tbody>
            </table>
        </div>
    `;

    const detailSectionHTML = getListingDetailSectionHTML(
        data.listings,
        currentChartType,
        currentDetailView
    );

    resultsContainer.innerHTML = `
        ${tableHTML}
        ${detailSectionHTML}
    `;
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
                <td class="listing-price-cell" style="min-width: 170px; white-space: nowrap;">${formatListingPrice(item)}</td>
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
                        <th class="sortable ${getSortClass('price')}" data-sort-field="price">가격</th>
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
        } else if (field === 'price') {
            av = getListingPriceSortValue(a);
            bv = getListingPriceSortValue(b);
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
    const nextTabGubun = data?.tabGubun || '';

    const nextRegion = info.region || '';
    const nextSigungu = info.sigungu || '';
    const nextUmdNm = info.umdNm || '';

    const changed =
        currentRegionInfo.region !== nextRegion ||
        currentRegionInfo.sigungu !== nextSigungu ||
        currentRegionInfo.umdNm !== nextUmdNm;

    currentRegionInfo = {
        region: nextRegion,
        sigungu: nextSigungu,
        umdNm: nextUmdNm,
        lawdCd: changed ? '' : (currentRegionInfo.lawdCd || ''),
        lawdName: changed ? '' : (currentRegionInfo.lawdName || ''),
        regions: changed ? '' : (currentRegionInfo.regions || ''),
        tabGubun: nextTabGubun || currentRegionInfo.tabGubun || ''
    };

    // 초기화 아이콘 설정
    updateResetButtonIcon(currentRegionInfo.tabGubun);
}

// 현재 탭 구분 반환 (예: 'sanga', 'apt', 'villa')
function getCurrentTabGubun() {
    return currentRegionInfo?.tabGubun || 'sanga';
}

function getResetBaseSvg() {
    return `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" class="reset-base-svg">
            <path d="M12 5V1L7 6L12 11V7C15.31 7 18 9.69 18 13C18 16.31 15.31 19 12 19C9.33 19 7.07 17.36 6.24 15H4.17C5.06 18.39 8.26 21 12 21C16.42 21 20 17.42 20 13C20 8.58 16.42 5 12 5Z" fill="currentColor"/>
        </svg>
    `;
}

function getTabTypeIconHtml(tabGubun = '') {
    switch (tabGubun) {
        case 'sanga':
            return `<span class="reset-tab-type-icon reset-tab-type-icon-sanga">🏪</span>`;
        case 'villa':
            return `<span class="reset-tab-type-icon reset-tab-type-icon-villa">🏘️</span>`;
        case 'apt':
            return `<span class="reset-tab-type-icon reset-tab-type-icon-apt">🏢</span>`;
        default:
            return `<span class="reset-tab-type-icon reset-tab-type-icon-default">📌</span>`;
    }
}

function updateResetButtonIcon(tabGubun = '') {
    if (!resetBtnIcon) return;

    resetBtnIcon.innerHTML = `
        <span class="reset-btn-icon-inner reset-type-${tabGubun || 'default'}">
            ${getTabTypeIconHtml(tabGubun)}
            ${getResetBaseSvg()}
        </span>
    `;

    // 툴립관련 수정함
    let title = '초기화'; // default

    if (tabGubun === 'sanga') {
        title = '상가초기화';
    } else if (tabGubun === 'villa') {
        title = '빌라초기화';
    } else if (tabGubun === 'apt') {
        title = '아파트초기화';
    }

    resetBtn.setAttribute('title', title);
}

// 현재 지역 정보를 문자열로 반환 (예: "경기도,김포시,운양동")
async function getCurrentRegionsString(accessToken = '') {

    // 이미 currentRegionInfo 안에 값이 있으면 재호출 없이 반환
    if (currentRegionInfo.lawdCd) {
        return {
            lawdCd: currentRegionInfo.lawdCd,
            lawdName: currentRegionInfo.lawdName,
            regions: currentRegionInfo.regions
        };
    }

    const region = currentRegionInfo.region || '';
    const sigungu = currentRegionInfo.sigungu || '';
    const umdNm = currentRegionInfo.umdNm || '';
    const queryLawdName = [region, sigungu, umdNm].filter(Boolean).join(' ').trim();

    console.log('==== getCurrentRegionsString - queryLawdName: ' + queryLawdName);

    const url = new URL(`${LANDCORE_URL}/api/lawdcd/single`);
    url.searchParams.set('lawd_name', queryLawdName);

    const headers = {};
    if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const response = await fetch(url.toString(), {
        method: 'GET',
        headers
    });

    if (!response.ok) {
        throw new Error(`법정동 조회 실패 (${response.status})`);
    }

    const result = await response.json();
    if (result?.result !== 'Success') {
        throw new Error(result?.message || '법정동 조회 실패');
    }

    // lawdName: 경기도 김포시 운양동 => regions: "경기도,김포시,운양동"
    console.log('==== getCurrentRegionsString: ' + result)

    return {
        lawdCd: result.lawd_cd,
        lawdName: result.lawd_name,
        umdName: umdNm,
        regions: result.regions
    };
}

function getCurrentRegionDisplayText() {
    const label = currentFloorFilter || '전체';
    return label;
}

function formatListingPrice(item) {
    if (item?.fullPrice) {
        const fullPriceText = String(item.fullPrice);

        // 월세일 때만 "=> 환산가" 추가
        if (item?.type === '월세' && fullPriceText.includes('/')) {
            const price = Number(item.price) || 0;

            // 🔥 층 정보 파싱
            const floorInfo = extractFloorInfo(item.floor);
            let multiplier = 200; // 기본 6% (기존)

            // 🔥 1층, 2층 → 5% 적용 (240)
            if (floorInfo && floorInfo.type === 'number' && floorInfo.num <= 2) {
                multiplier = 240; // 5% 수익률
            }

            // 🔥 환산가 계산
            const converted = price * multiplier;
            const convertedText = `${(converted / 10000).toFixed(1).replace('.0','')}억`;

            return `${fullPriceText} <span style="color:#d32f2f; font-weight:800;">&gt; ${convertedText}</span>`;
        }

        return fullPriceText;
    }

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

// 가격 정렬을 위한 값 계산 함수
function getListingPriceSortValue(item) {
    if (!item) return 0;

    // 월세: "보증금/월세" 형식에서는 월세금액을 우선 기준으로 정렬
    // 예: 1,500/70, 3,000/60 이면 70이 60보다 크므로 1,500/70이 뒤로 감
    // 같은 월세금액일 때만 보증금을 2차 기준으로 사용
    if (item.type === '월세') {
        let deposit = Number(item.deposit);
        let monthlyRent = Number(item.monthlyRent);

        // deposit / monthlyRent 값이 비어있을 수 있으므로 fullPrice에서도 보조 파싱
        if ((!Number.isFinite(deposit) || !Number.isFinite(monthlyRent)) && item.fullPrice) {
            const parts = String(item.fullPrice)
                .replace(/\s/g, '')
                .split('/');

            if (parts.length >= 2) {
                deposit = Number(String(parts[0]).replace(/,/g, ''));
                monthlyRent = Number(String(parts[1]).replace(/,/g, ''));
            }
        }

        deposit = Number.isFinite(deposit) ? deposit : 0;
        monthlyRent = Number.isFinite(monthlyRent) ? monthlyRent : 0;

        // 월세 우선 + 보증금 보조 정렬
        return (monthlyRent * 100000000) + deposit;
    }

    // 매매: 매매가 기준 정렬
    const salePrice = Number(item.price) || Number(item.salePrice) || 0;
    return salePrice;
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
            <div class="cheapest-header">
               💰 <span style="color:#ff9800; font-weight:bold;">최저가 매물</span>(매매)
            </div>
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
 * 부동산 상위목록 표시
 */
function displayTopAgencies(data) {
    const agencySection = document.getElementById('top-agencies');
    if (!agencySection) return;

    if (!data || !data.listings || !Array.isArray(data.listings)) {
        agencySection.innerHTML = '';
        agencySection.classList.add('hidden');
        if (topAgenciesToggle) {
            topAgenciesToggle.setAttribute('aria-expanded', 'false');
        }
        syncTopAgenciesToggleIcon();
        return;
    }

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
        agencySection.innerHTML = '<div class="empty-hint">표시할 부동산 정보가 없습니다.</div>';
        agencySection.classList.add('hidden');
        if (topAgenciesToggle) {
            topAgenciesToggle.setAttribute('aria-expanded', 'false');
        }
        syncTopAgenciesToggleIcon();
        return;
    }

    const rowsHTML = top3.map((agency, idx) => {
        return `
            <tr>
                <td class="top-agency-rank-cell">${idx + 1}</td>
                <td class="top-agency-name-cell">
                    <button type="button"
                            class="top-agency-name-link"
                            data-agency-name="${agency.name}"
                            title="중개사 상세정보 보기">
                        ${agency.name}
                    </button>
                </td>
                <td class="top-agency-wolse-count">${agency.wolse}</td>
                <td class="top-agency-maemae-count">${agency.maemae}</td>
                <td class="top-agency-total-count">${agency.total}</td>
            </tr>
        `;
    }).join('');

    agencySection.innerHTML = `
        <div class="listing-detail-section top-agencies-detail-section">
            <div class="listing-detail-body">
                <div class="listing-table-wrap">
                    <table class="listing-detail-table top-agencies-table">
                        <thead>
                            <tr>
                                <th>순위</th>
                                <th>부동산명</th>
                                <th>월세</th>
                                <th>매매</th>
                                <th>총계</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rowsHTML}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;

    // 기본은 펼침 유지
    agencySection.classList.remove('hidden');
    if (topAgenciesToggle) {
        topAgenciesToggle.setAttribute('aria-expanded', 'true');
    }
    syncTopAgenciesToggleIcon();
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
        analyzeBtn.innerHTML = `<span class="region-highlight">${currentRegionLabel}</span> 매물분석하기`;
    }
}