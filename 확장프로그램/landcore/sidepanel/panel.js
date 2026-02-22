/**
 * landcore - Excel Style Panel JS
 */

// DOM Elements
const analyzeBtn = document.getElementById('analyze-btn');
const resetBtn = document.getElementById('reset-btn');
const realAuctionBtn = document.getElementById('real-auction-btn');
const calculatorBtn = document.getElementById('calculator-btn');
//const memoBtn = document.getElementById('memo-btn');
const baehuBtn = document.getElementById('baehu-btn');
const naverLandBtn = document.getElementById('naver-land-btn');
const guideBtn = document.getElementById('guide-btn');
const statusBar = document.getElementById('status-bar');
const resultsContainer = document.getElementById('results-container');
const areaChartContainer = document.getElementById('area-chart');
const historyList = document.getElementById('history-list');

// 네이버 부동산 상가 페이지 URL (마지막 위치 기억)
const NAVER_LAND_URL = 'https://new.land.naver.com/offices?a=SG:SMS&b=A1:B2&e=RETAIL&ad=true';

// State
let lastAnalysisData = null;

// 초기화
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Panel Initialized');
    await checkCurrentTab();
    loadHistory();

    analyzeBtn.addEventListener('click', startAnalysis);
    resetBtn.addEventListener('click', resetPanel);
    realAuctionBtn.addEventListener('click', openRealAuction);
    calculatorBtn.addEventListener('click', openCalculator);
    //memoBtn.addEventListener('click', openMemo);
    baehuBtn.addEventListener('click', openBaehu);
    naverLandBtn.addEventListener('click', openNaverLand);
    guideBtn.addEventListener('click', openGuide);

    // 실시간 분석 업데이트 리스트
    chrome.runtime.onMessage.addListener((message) => {
        if (message.type === 'AUTO_ANALYSIS_UPDATE' && message.data) {
            console.log('실시간 업데이트 수신:', message.data.totalCount, '개 매물');
            handleAutoUpdate(message.data);
        }
    });
});

/**
 * 실시간 분석 업데이트 처리
 */
function handleAutoUpdate(data) {
    lastAnalysisData = data;

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

/**
 * 실거래가 및 경매내역 열기
 */
function openRealAuction() {
    alert("실거래가 및 경매내역 페이지는 현재 준비 중입니다. 추후 업데이트를 기대해주세요!");
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
 * 수익률 계산기 열기
 * 현재 열린 매물 상세정보를 추출하여 계산기에 전달
 */
async function openCalculator_old() {
    let params = new URLSearchParams();

    try {
        // 상세정보 팝업에서 데이터 추출
        const response = await chrome.runtime.sendMessage({ type: 'GET_LISTING_DETAIL' });

        if (response?.success && response.data) {
            const data = response.data;

            // 만원 단위 변환(x 10,000)
            const WON_MULTIPLIER = 10000;

            // 매매가 및 입찰가/매수가 (원 단위로 변환)
            if (data.salePrice > 0) {
                params.set('bidPrice', data.salePrice * WON_MULTIPLIER);
            }

            // 계약면적 및 분양평수 (m2 * 0.3025 = 평)
            if (data.contractArea > 0) {
                const supplyPyeong = (data.contractArea * 0.3025).toFixed(1);
                params.set('supplyArea', supplyPyeong);
            }

            // 전용면적 및 전용평수 (m2 * 0.3025 = 평)
            if (data.exclusiveArea > 0) {
                const exclusivePyeong = (data.exclusiveArea * 0.3025).toFixed(1);
                params.set('exclusiveArea', exclusivePyeong);
            }

            // 계약금 = 매매가의 10% (원 단위)
            if (data.salePrice > 0) {
                const contractDeposit = Math.round(data.salePrice * 0.1 * WON_MULTIPLIER);
                params.set('contractDeposit', contractDeposit);
            }

            // 보증금/월세 (원 단위로 변환)
            if (data.hasRentInfo) {
                if (data.deposit > 0) {
                    params.set('deposit', data.deposit * WON_MULTIPLIER);
                }
                if (data.monthlyRent > 0) {
                    params.set('monthlyRent', data.monthlyRent * WON_MULTIPLIER);
                }
            }

            // 매수중개수수료 체크 기본 활성화
            params.set('purchaseFeeCheck', 'true');
        }
    } catch (error) {
        console.warn('상세정보 추출 실패, 빈 계산기 열기:', error);
    }

    // 확장 프로그램 내부 페이지로 창 열기
    const calculatorUrl = chrome.runtime.getURL('tools/profit-sanga.html');
    const fullUrl = params.toString() ? `${calculatorUrl}?${params}` : calculatorUrl;
    chrome.tabs.create({ url: fullUrl });
}

/**
 * 수익률 계산기 실행 (토큰 및 구독 상태 체크 포함)
 */
function openCalculator(tabGubun = "sanga", extraParams = {}) {
    const BASE_URL = "https://www.landcore.co.kr";

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
        let regions = "경기도,김포시,운양동"; // 기본값 설정

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
            analyzeBtn.textContent = '매물 분석하기';
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
        const baseStyle = "font-size: 12px; font-weight: bold;";

        // 숫자 스타일: 검정색
        const numStyle = `${baseStyle} color: #000;`;
        // 월세 스타일: 빨간색 (엑셀 테이블의 월세 색상과 매칭)
        const wolseStyle = `${baseStyle} color: #e91e63;`;
        // 매매 스타일: 파란색 (엑셀 테이블의 매매 색상과 매칭)
        const maemaeStyle = `${baseStyle} color: #2196f3;`;

        // innerHTML을 사용하여 각각의 span에 스타일 적용
        countEl.innerHTML = `
            총 <span style="${numStyle}">${total}</span>개 분석 : 
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
    // 안전 체크
    if (!data || !data.stats) {
        resultsContainer.innerHTML = '<div class="empty-state">데이터를 불러올 수 없습니다.</div>';
        return;
    }

    const { stats } = data;
    const byFloor = stats.byFloor || {};

    // '지하'를 제외한 층수 배열 정의
    //const floors = ['1층', '2층', '상층', '지하'];
    const floors = ['1층', '2층', '상층'];

    // 월세 행 HTML 생성
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

    // 매매 행 HTML 생성
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

    // 매매 최저가 매물 찾기
    const cheapestMaemaeHTML = getCheapestMaemaeHTML(data.listings);

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
        ${cheapestMaemaeHTML}
    `;

    resultsContainer.innerHTML = tableHTML;
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

    // 월세 매물만 필터링
    const wolseListings = data.listings.filter(l => l.type === '월세');
    if (wolseListings.length === 0) {
        if (areaChartContainer) areaChartContainer.innerHTML = '';
        return;
    }

    // 평수 구간별 카운트
    const areaGroups = {
        '10': 0, '20': 0, '30': 0, '40': 0, '50': 0,
        '60': 0, '70': 0, '80': 0, '90': 0, '100+': 0
    };

    wolseListings.forEach(l => {
        const area = l.area || 0;
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

    const barsHTML = Object.entries(areaGroups).map(([range, count]) => {
        const heightPx = maxCount > 0 ? (count / maxCount) * 80 : 2;
        const label = range === '100+' ? '100+평' : `${range}평`;
        const barHeight = Math.max(heightPx, 2);

        // 🔹 background-color: #007bff (파란색) 추가
        return `
            <div class="bar-container" style="display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100px;">
                <div class="bar-count" style="font-size: 11px; margin-bottom: 2px; color: #007bff; font-weight: bold;">${count > 0 ? count : ''}</div>
                <div class="bar" style="
                    width: 20px; 
                    height: ${barHeight}px; 
                    background-color: #007bff; 
                    opacity: ${count > 0 ? 1 : 0.1}; 
                    border-radius: 2px 2px 0 0;
                    transition: height 0.3s ease;"></div>
                <div class="bar-label" style="font-size: 10px; margin-top: 4px; color: #666;">${label}</div>
            </div>
        `;
    }).join('');

    areaChartContainer.innerHTML = barsHTML;
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