/**
 *
 * 기능:
 * 1. 매물 목록에 평당가/평수 배지 자동 표시
 * 2. Side Panel에서 분석 요청 시 데이터 제공
 *
 * [버그 수정] 가격/면적 정규식 개선
 * - 문제: 공백 제거 시 숫자가 합쳐져 잘못된 평당가 계산
 *   예: "월세500/55 7평" → "월세500/557평" → 월세 557만원으로 오인식
 * - 해결:
 *   1) 공백을 완전히 제거하지 않고 단일 공백으로 변환
 *   2) 정규식에 공백(\s*) 허용
 *   3) 기존 배지(.naverbu-badge)를 파싱에서 제외
 *
 * [핵심 정규식]
 * - 매매: /매매\s*(\d{1,3}억(?:\s*\d{1,4}(?:,\d{3})?)?|[\d,]+만)/
 * - 월세: /월세\s*([\d,억천]+)\s*\/\s*([\d,]+)/
 * - 확인일: /확인매물\s*(\d{2}\.\d{2}\.\d{2})/
 * ============================================
 */

console.log('🏢 랜드코어 분석기 - Content Script 로드됨');

// 페이지 로드 시 자동으로 배지 표시 및 분석
setTimeout(() => {
    initAutoAnalysis();
}, 1500);

// 디바운스 타이머
let analysisDebounceTimer = null;

/**
 * 자동 분석 초기화
 * - 페이지 로드 시 즉시 배지 표시 및 분석
 * - MutationObserver로 새 매물 감지하여 실시간 업데이트
 */
function initAutoAnalysis() {
    console.log('🏷️ 자동 분석 시작...');

    // 초기 배지 표시
    const count = addBadgesToListings();
    console.log(`✅ 초기 ${count}개 매물에 배지 표시`);

    // 초기 분석 실행 및 사이드패널 업데이트
    sendAnalysisToPanel();

    // 스크롤로 새 매물 로드 시 배지 추가 + 분석 업데이트 (MutationObserver)
    const listContainer = document.querySelector('.item_list, .list_item, .article_list');
    if (listContainer) {
        const observer = new MutationObserver((mutations) => {
            // 새 요소가 추가되면 처리
            let hasNewItems = mutations.some(m => m.addedNodes.length > 0);
            if (hasNewItems) {
                // 배지 표시 (즉시)
                setTimeout(() => addBadgesToListings(), 300);

                // 분석 업데이트 (디바운스 - 500ms)
                clearTimeout(analysisDebounceTimer);
                analysisDebounceTimer = setTimeout(() => {
                    sendAnalysisToPanel();
                }, 500);
            }
        });

        observer.observe(listContainer.parentElement || document.body, {
            childList: true,
            subtree: true
        });
        console.log('👁️ MutationObserver 활성화 - 실시간 분석 중');
    }
}

/**
 * 분석 결과를 사이드패널로 자동 전송
 */
function sendAnalysisToPanel() {
    try {
        const analysisResult = analyzeCurrentPage();
        chrome.runtime.sendMessage({
            type: 'AUTO_ANALYSIS_UPDATE',
            data: analysisResult
        }).catch(() => {
            // 사이드패널이 열려있지 않은 경우 무시
        });
        console.log('📊 실시간 분석 전송:', analysisResult.totalCount, '개 매물');
    } catch (error) {
        console.warn('자동 분석 실패:', error);
    }
}

/**
 * 메시지 리스너 - Side Panel에서 분석 요청 시에만 동작
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // START_ANALYSIS: 현재 화면의 매물 분석 (스크롤 없음 - 법적 안전)
    if (message.type === 'START_ANALYSIS') {
        console.log('📊 분석 시작 요청 수신');

        try {
            const analysisResult = analyzeCurrentPage();
            console.log('✅ 분석 완료, 응답 전송');
            sendResponse({ success: true, data: analysisResult });
        } catch (error) {
            console.error('❌ 분석 오류:', error);
            sendResponse({ success: false, error: error.message || '분석 실패' });
        }
        return true;
    }

    // GET_LISTING_DETAIL: 현재 열린 상세정보 팝업에서 데이터 추출
    if (message.type === 'GET_LISTING_DETAIL') {
        console.log('📋 상세정보 추출 요청 수신');

        try {
            const detailData = extractListingDetail();
            console.log('✅ 상세정보 추출 완료:', detailData);
            sendResponse({ success: true, data: detailData });
        } catch (error) {
            console.error('❌ 상세정보 추출 오류:', error);
            sendResponse({ success: false, error: error.message || '추출 실패' });
        }
        return true;
    }

    // GET_MEMO_DATA: 메모용 상세정보 추출 (주소, 중개사 정보 포함)
    if (message.type === 'GET_MEMO_DATA') {
        console.log('📝 메모용 데이터 추출 요청 수신');

        try {
            const memoData = extractMemoData();
            console.log('✅ 메모용 데이터 추출 완료:', memoData);
            sendResponse({ success: true, data: memoData });
        } catch (error) {
            console.error('❌ 메모용 데이터 추출 오류:', error);
            sendResponse({ success: false, error: error.message || '추출 실패' });
        }
        return true;
    }

    // SHOW_BADGES: 매물 목록에 평당가/평수 배지 표시
    if (message.type === 'SHOW_BADGES') {
        console.log('🏷️ 배지 표시 요청 수신');

        try {
            const count = addBadgesToListings();
            console.log(`✅ ${count}개 매물에 배지 표시 완료`);
            sendResponse({ success: true, count: count });
        } catch (error) {
            console.error('❌ 배지 표시 오류:', error);
            sendResponse({ success: false, error: error.message });
        }
        return true;
    }

    return false;
});

/**
 * 현재 열린 매물 상세정보 팝업에서 데이터 추출
 * ⚠️ 읽기만 수행 - DOM 수정 없음
 */
function extractListingDetail() {
    const result = {
        salePrice: 0,        // 매매가 (만원)
        contractArea: 0,     // 계약면적 (m²)
        exclusiveArea: 0,    // 전용면적 (m²)
        deposit: 0,          // 보증금 (만원)
        monthlyRent: 0,      // 월세 (만원)
        hasRentInfo: false   // 임대 정보 존재 여부
    };

    // 상세정보 팝업 영역 찾기 (.detail_panel이 정확한 셀렉터)
    const detailPanel = document.querySelector('.detail_panel');
    if (!detailPanel) {
        console.warn('⚠️ 상세정보 패널을 찾을 수 없습니다. 페이지 전체에서 검색합니다.');
        return extractFromText(document.body.innerText);
    }

    console.log('📋 상세정보 패널 발견, 데이터 추출 시작');

    // 1. 매매가 추출 (.price 요소에서)
    // ⚠️ innerText가 빈 문자열 반환하므로 textContent 사용
    const priceEl = detailPanel.querySelector('.price');
    if (priceEl) {
        const priceText = (priceEl.textContent || priceEl.innerHTML).replace(/\s+/g, '');
        result.salePrice = parseKoreanPrice(priceText);
        console.log('💰 매매가 추출:', priceText, '→', result.salePrice, '만원');
    }

    // 2. 테이블에서 정보 추출 (th/td 구조)
    const getTableValue = (labelKeyword) => {
        const ths = detailPanel.querySelectorAll('th');
        for (const th of ths) {
            if (th.innerText.includes(labelKeyword)) {
                const td = th.nextElementSibling;
                return td ? td.innerText.trim() : null;
            }
        }
        return null;
    };

    // 3. 면적 추출
    const areaText = getTableValue('계약/전용면적') || getTableValue('면적');
    if (areaText) {
        // "100㎡/63㎡(전용률63%)" 또는 "100m²/63m²" 형식
        const areaMatch = areaText.match(/(\d+(?:\.\d+)?)[㎡m][²2]?\s*\/\s*(\d+(?:\.\d+)?)/);
        if (areaMatch) {
            result.contractArea = parseFloat(areaMatch[1]);
            result.exclusiveArea = parseFloat(areaMatch[2]);
            console.log('📐 면적 추출:', result.contractArea, '/', result.exclusiveArea, 'm²');
        }
    }

    // 4. 보증금/월세 추출
    const rentText = getTableValue('기보증금/월세') || getTableValue('보증금');
    if (rentText) {
        // "1,000/70만원" 또는 "3,000/240" 형식
        const rentMatch = rentText.match(/([,\d]+)\s*\/\s*([,\d]+)/);
        if (rentMatch) {
            result.deposit = parseInt(rentMatch[1].replace(/,/g, '')) || 0;
            result.monthlyRent = parseInt(rentMatch[2].replace(/,/g, '')) || 0;
            result.hasRentInfo = true;
            console.log('🏠 임대정보 추출: 보증금', result.deposit, '만원, 월세', result.monthlyRent, '만원');
        }
    }

    return result;
}

/**
 * 메모용 상세정보 추출
 * 매물명, 가격, 면적, 주소, 중개사 정보 등 모든 정보 추출
 */
function extractMemoData() {
    const result = {
        propertyName: '',   // 매물명 (예: 일반상가 1층)
        price: '',          // 매매가격 (예: 6억)
        rent: '',           // 보증금/월세 (예: 2,000/65만원)
        area: '',           // 면적 (예: 72.68㎡/57.66㎡)
        floor: '',          // 층수 (예: 1/20층)
        address: '',        // 소재지
        features: '',       // 매물특징
        propertyNo: '',     // 매물번호
        agencyName: '',     // 중개사 상호
        agencyPhone: '',    // 전화번호
        agencyMobile: '',   // 휴대폰
        agencyAddress: ''   // 중개사 주소
    };

    const detailPanel = document.querySelector('.detail_panel');
    if (!detailPanel) {
        console.warn('⚠️ 상세정보 패널을 찾을 수 없습니다.');
        return result;
    }

    console.log('📝 메모 데이터 추출 시작...');

    // 헬퍼 함수: th/td 테이블에서 값 추출
    const getTableValue = (labelKeyword) => {
        const ths = detailPanel.querySelectorAll('th');
        for (const th of ths) {
            if (th.innerText.includes(labelKeyword)) {
                const td = th.nextElementSibling;
                return td ? td.innerText.trim() : null;
            }
        }
        return null;
    };

    // 1. 매물명 (상단 타이틀 - 다양한 셀렉터 시도)
    const titleSelectors = ['.detail_header_title', 'h1', '.info_article_title', '.complex_title'];
    for (const selector of titleSelectors) {
        const titleEl = detailPanel.querySelector(selector);
        if (titleEl && titleEl.innerText.trim()) {
            result.propertyName = titleEl.innerText.trim().replace(/\s+/g, ' ');
            console.log('  매물명:', result.propertyName);
            break;
        }
    }

    // 2. 매매가격 (다양한 셀렉터 시도)
    const priceSelectors = ['.price', '.head_price', '.info_price'];
    for (const selector of priceSelectors) {
        const priceEl = detailPanel.querySelector(selector);
        if (priceEl && priceEl.textContent.trim()) {
            result.price = priceEl.textContent.replace(/\s+/g, ' ').trim();
            console.log('  가격:', result.price);
            break;
        }
    }

    // 3. 보증금/월세
    const rentText = getTableValue('기보증금/월세') || getTableValue('보증금') || getTableValue('월세');
    if (rentText) {
        result.rent = rentText;
        console.log('  보증금/월세:', result.rent);
    }

    // 4. 면적 (m² → 평으로 변환)
    const areaText = getTableValue('계약/전용면적') || getTableValue('면적') || getTableValue('전용면적');
    if (areaText) {
        // 숫자 추출: "312.95㎡/199.43㎡(전용률64%)" → [312.95, 199.43]
        const numbers = areaText.match(/[\d.]+/g);
        if (numbers && numbers.length >= 2) {
            const contractPyeong = (parseFloat(numbers[0]) * 0.3025).toFixed(1);
            const exclusivePyeong = (parseFloat(numbers[1]) * 0.3025).toFixed(1);
            // 전용률 추출
            const ratioMatch = areaText.match(/전용률(\d+)%/);
            const ratio = ratioMatch ? `(전용률${ratioMatch[1]}%)` : '';
            result.area = `${contractPyeong}평/${exclusivePyeong}평${ratio}`;
        } else {
            result.area = areaText;
        }
        console.log('  면적:', result.area);
    }

    // 5. 층수
    const floorText = getTableValue('해당층/총층') || getTableValue('층');
    if (floorText) {
        result.floor = floorText;
        console.log('  층수:', result.floor);
    }

    // 6. 소재지
    const addressText = getTableValue('소재지') || getTableValue('주소');
    if (addressText) {
        result.address = addressText;
        console.log('  소재지:', result.address);
    }

    // 7. 매물특징
    const featuresText = getTableValue('매물특징');
    if (featuresText) {
        result.features = featuresText;
        console.log('  매물특징:', result.features);
    }

    // 8. 매물번호
    const propertyNoText = getTableValue('매물번호');
    if (propertyNoText) {
        result.propertyNo = propertyNoText;
        console.log('  매물번호:', result.propertyNo);
    }

    // 9. 중개사 정보 - 테이블의 '중개사' 행에서 추출
    const agencyRow = getTableValue('중개사');
    if (agencyRow) {
        // 중개사 상호 - 첫 줄이나 굵은 텍스트
        const lines = agencyRow.split('\n').map(l => l.trim()).filter(l => l);
        if (lines.length > 0) {
            // '공인중개사' 또는 '부동산'이 포함된 줄 찾기
            for (const line of lines) {
                if (line.includes('공인중개사') || line.includes('부동산') || line.includes('사무소')) {
                    result.agencyName = line.replace(/[↗✓길찾기]/g, '').trim();
                    console.log('  중개사:', result.agencyName);
                    break;
                }
            }
            // 못 찾으면 첫 줄 사용
            if (!result.agencyName && lines[0]) {
                result.agencyName = lines[0].replace(/[↗✓길찾기]/g, '').trim();
                console.log('  중개사:', result.agencyName);
            }
        }

        // 전화번호들 추출
        const phoneMatches = agencyRow.match(/\d{2,4}-\d{3,4}-\d{4}/g) || [];
        if (phoneMatches.length > 0) {
            result.agencyPhone = phoneMatches[0];
            console.log('  전화:', result.agencyPhone);
        }
        if (phoneMatches.length > 1) {
            result.agencyMobile = phoneMatches[1];
            console.log('  휴대폰:', result.agencyMobile);
        }

        // 주소 추출 - 줄 단위로 찾기
        const addrLines = agencyRow.split('\n').map(l => l.trim()).filter(l => l);
        for (const line of addrLines) {
            // 대표/등록번호 포함된 줄 제외
            if (line.includes('대표') || line.includes('등록번호') || line.includes('최근')) continue;
            // 경기/서울/인천 등으로 시작하고 시/구/동 포함된 줄
            if (/^[경서인대부울강세충전라]/.test(line) && /[시군구동읍면로길]/.test(line)) {
                result.agencyAddress = line.replace(/[↗✓길찾기]/g, '').trim();
                console.log('  주소:', result.agencyAddress);
                break;
            }
        }
    } else {
        console.log('  ⚠️ 중개사 정보를 찾을 수 없습니다');
    }

    console.log('📝 메모 데이터 추출 완료:', result);
    return result;
}

/**
 * 텍스트에서 매물 정보 추출
 */
function extractFromText(text) {
    const result = {
        salePrice: 0,
        contractArea: 0,
        exclusiveArea: 0,
        deposit: 0,
        monthlyRent: 0,
        hasRentInfo: false
    };

    // 공백 제거한 버전
    const collapsed = text.replace(/\s+/g, '');

    // 1. 매매가 추출: "매매 1억 7,000" 또는 "매매1억7000" 등
    const salePriceMatch = collapsed.match(/매매(\d+억[\d,]*|\d{1,3}억|[\d,]+만)/);
    if (salePriceMatch) {
        result.salePrice = parseKoreanPrice(salePriceMatch[1]);
    }

    // 2. 면적 추출: "계약/전용면적 100m²/63m²" 또는 "100㎡/63㎡"
    const areaMatch = collapsed.match(/(\d+(?:\.\d+)?)[m㎡][²2]?\/(\d+(?:\.\d+)?)[m㎡][²2]?/);
    if (areaMatch) {
        result.contractArea = parseFloat(areaMatch[1]);
        result.exclusiveArea = parseFloat(areaMatch[2]);
    }

    // 3. 보증금/월세 추출: "기보증금/월세 1,000/70만원" 또는 "1000/70"
    const rentMatch = collapsed.match(/기보증금\/월세[\s:]*([,\d]+)\/([,\d]+)/);
    if (rentMatch) {
        result.deposit = parseInt(rentMatch[1].replace(/,/g, '')) || 0;
        result.monthlyRent = parseInt(rentMatch[2].replace(/,/g, '')) || 0;
        result.hasRentInfo = true;
    } else {
        // 대안 패턴: "보증금 1,000 / 월 70"
        const altRentMatch = text.match(/보증금[\s:]*([,\d]+).*?월[\s:]*([,\d]+)/);
        if (altRentMatch) {
            result.deposit = parseInt(altRentMatch[1].replace(/,/g, '')) || 0;
            result.monthlyRent = parseInt(altRentMatch[2].replace(/,/g, '')) || 0;
            result.hasRentInfo = true;
        }
    }

    return result;
}

/**
 * 한글 가격 문자열을 만원 단위로 변환
 * 예: "1억7,000" -> 17000, "5억" -> 50000
 */
function parseKoreanPrice(priceStr) {
    let total = 0;
    const str = priceStr.replace(/,/g, '');

    if (str.includes('억')) {
        const ukIndex = str.indexOf('억');
        const uk = parseInt(str.substring(0, ukIndex)) || 0;
        const remaining = str.substring(ukIndex + 1).replace(/만/g, '');
        const man = parseInt(remaining) || 0;
        total = uk * 10000 + man;
    } else if (str.includes('만')) {
        total = parseInt(str.replace(/만/g, '')) || 0;
    } else {
        total = parseInt(str) || 0;
    }

    return total;
}

/**
 * 현재 페이지 분석 - 매물 데이터 추출
 * ⚠️ 법적 안전: 스크롤 자동화 없음, 읽기만 수행
 */
function analyzeCurrentPage() {
    const items = findListingItems();
    const data = [];

    items.forEach(item => {
        try {
            const listingData = parseListingItem(item);
            if (listingData) {
                data.push(listingData);
            }
        } catch (e) {
            console.warn('매물 파싱 오류:', e);
        }
    });

    // 통계 계산
    const stats = calculateStatistics(data);

    return {
        listings: data,
        stats: stats,
        timestamp: new Date().toISOString(),
        totalCount: data.length
    };
}

/**
 * 매물 아이템 요소 찾기
 * ⚠️ 읽기만 수행
 */
function findListingItems() {
    const selectors = [
        '.item_inner',
        '.item',
        '.c-item',
        '.article_item',
        '.item_link',
        '.list_item'
    ];

    for (const selector of selectors) {
        const found = document.querySelectorAll(selector);
        if (found.length > 0) {
            // 매물 발견
            // 중개사 묶음의 자식 아이템 제외
            return Array.from(found).filter(item => {
                return !item.classList.contains('item--child') &&
                    !item.closest('.item--child');
            });
        }
    }

    return [];
}

/**
 * 개별 매물 아이템 파싱
 * ⚠️ 읽기만 수행 - DOM 수정 없음
 */
function parseListingItem(item) {
    // 기존 배지가 있으면 텍스트에서 제외 (중복 분석 시 배지 텍스트 포함 방지)
    const clone = item.cloneNode(true);
    const badges = clone.querySelectorAll('.naverbu-badge');
    badges.forEach(b => b.remove());

    // 공백을 완전히 제거하면 "55 7평" → "557평"이 되어 숫자가 합쳐지는 문제 발생
    // 단일 공백으로 변환하여 숫자 분리 유지
    const text = clone.innerText.replace(/\s+/g, ' ');
    const rawText = item.innerText; // 원본 텍스트 (공백 포함)

    // 가격 정보 추출
    const priceInfo = extractPriceInfo(text);
    if (!priceInfo || priceInfo.price === 0) {
        return null;
    }

    // 면적 정보 추출
    const areaInfo = extractArea(text);
    if (!areaInfo) {
        return null;
    }

    // 평당가 계산
    const pricePerPyeong = calculatePricePerPyeong(
        priceInfo.type,
        priceInfo.price,
        areaInfo.pyeong
    );

    // 층 정보 추출
    const floorInfo = extractFloorInfo(text);

    // 향 정보 추출
    const direction = extractDirection(text);

    // 공인중개사 정보 추출 (DOM 우선, 텍스트 폴백)
    const agencyInfo = extractAgencyFromItem(item) || extractAgencyInfo(rawText);

    // 확인 날짜 추출
    const verificationDate = extractVerificationDate(text);

    return {
        type: priceInfo.type,           // 매매 or 월세
        category: floorInfo.category,    // 1층, 2층, 상층, 지하
        floor: floorInfo.raw,           // 층 정보 원본
        direction: direction,            // 향
        pricePerPyeong: pricePerPyeong, // 평당가
        area: areaInfo.pyeong,          // 면적 (평)
        fullPrice: priceInfo.fullPrice, // 원본 가격 문자열
        agencyName: agencyInfo.name,    // 공인중개사 이름
        agencyCount: agencyInfo.count,  // 중개사 수
        verificationDate: verificationDate // 확인 날짜
    };
}

/**
 * DOM 요소에서 직접 중개사 정보 추출
 * 예: "가능동향부동산뱅크제공대우타운중개사사무소" → "대우타운"
 */
function extractAgencyFromItem(item) {
    // 네이버 부동산 매물 카드의 중개사 요소 셀렉터
    const agencySelectors = [
        '.realtor_name',
        '.item_realtor',
        '.realtor',
        '.agent_name',
        '[class*="realtor"]',
        '[class*="agent"]',
        '.info_agent'
    ];

    for (const selector of agencySelectors) {
        const el = item.querySelector(selector);
        if (el) {
            let name = el.innerText.trim();
            let collapsed = name.replace(/\s+/g, '');

            if (collapsed.length < 2) continue;

            // "중개사 N곳" 패턴 체크
            const multiMatch = collapsed.match(/중개사(\d+)곳/);
            if (multiMatch) {
                return { name: null, count: parseInt(multiMatch[1]) };
            }

            // "|" 구분자로 분리하여 첫 번째 부분만 사용
            if (collapsed.includes('|')) {
                collapsed = collapsed.split('|')[0];
            }

            // "제공" 키워드가 있으면 그 뒤에서 찾기
            if (collapsed.includes('제공')) {
                const afterProvider = collapsed.split('제공').pop();

                const p1 = afterProvider.match(/^([가-힣]{2,10})공인중개사사무소/);
                if (p1) return { name: p1[1], count: 1 };

                const p2 = afterProvider.match(/^([가-힣]{2,10})중개사사무소/);
                if (p2) return { name: p2[1], count: 1 };

                const p3 = afterProvider.match(/^([가-힣]{2,10})중개사무소/);
                if (p3) return { name: p3[1], count: 1 };

                continue; // 제공 뒤에 사무소 없으면 다음 셀렉터 시도
            }

            // "제공" 없는 경우 일반 매칭
            const pattern1 = collapsed.match(/([가-힣]{2,10})공인중개사사무소/);
            if (pattern1) return { name: pattern1[1], count: 1 };

            const pattern2 = collapsed.match(/([가-힣]{2,10})중개사사무소/);
            if (pattern2) return { name: pattern2[1], count: 1 };

            const pattern3 = collapsed.match(/([가-힣]{2,10})중개사무소/);
            if (pattern3) return { name: pattern3[1], count: 1 };
        }
    }

    return null; // DOM에서 못 찾으면 null 반환 (텍스트 폴백)
}

/**
 * 공인중개사 정보 추출 (사무소로 끝나는 패턴만)
 * 예: "가능동향부동산뱅크제공대우타운중개사사무소" → "대우타운"
 */
function extractAgencyInfo(rawText) {
    // 공백/줄바꿈 제거한 버전 생성
    const collapsed = rawText.replace(/\s+/g, '');

    // "중개사 N곳" 패턴 검색 (중복 매물)
    const multiMatch = collapsed.match(/중개사(\d+)곳/);
    if (multiMatch) {
        return { name: null, count: parseInt(multiMatch[1]) };
    }

    // "제공" 키워드가 있으면, 그 뒤에서 사무소 패턴 찾기
    // 예: "ㅇㅇ제공대우타운중개사사무소" → "대우타운"
    if (collapsed.includes('제공')) {
        // "제공" 뒤의 텍스트에서 찾기
        const afterProvider = collapsed.split('제공').pop();

        const p1 = afterProvider.match(/^([가-힣]{2,10})공인중개사사무소/);
        if (p1) return { name: p1[1], count: 1 };

        const p2 = afterProvider.match(/^([가-힣]{2,10})중개사사무소/);
        if (p2) return { name: p2[1], count: 1 };

        const p3 = afterProvider.match(/^([가-힣]{2,10})중개사무소/);
        if (p3) return { name: p3[1], count: 1 };

        // 제공 뒤에 사무소 패턴 없으면 제공업체만 있는 것
        return { name: null, count: 0 };
    }

    // "제공" 없는 경우 일반 패턴 매칭 (상호 길이 2~10자로 제한)
    const pattern1 = collapsed.match(/([가-힣]{2,10})공인중개사사무소/);
    if (pattern1) return { name: pattern1[1], count: 1 };

    const pattern2 = collapsed.match(/([가-힣]{2,10})중개사사무소/);
    if (pattern2) return { name: pattern2[1], count: 1 };

    const pattern3 = collapsed.match(/([가-힣]{2,10})중개사무소/);
    if (pattern3) return { name: pattern3[1], count: 1 };

    return { name: null, count: 0 };
}

/**
 * 확인 날짜 추출
 */
function extractVerificationDate(text) {
    // "확인매물 26.01.07" 패턴 (공백 허용, YY.MM.DD 형식)
    const match = text.match(/확인매물\s*(\d{2}\.\d{2}\.\d{2})/);
    if (match) {
        return match[1];
    }
    // "확인매물 01.07" 패턴 (MM.DD 형식)
    const match2 = text.match(/확인매물\s*(\d{1,2}\.\d{1,2})/);
    if (match2) {
        return match2[1];
    }
    return '-';
}

/**
 * 가격 정보 추출 (기존 naverbu 로직 이식)
 */
function extractPriceInfo(text) {
    let type = '';
    let price = 0;
    let fullPrice = '';

    if (text.includes('매매')) {
        type = '매매';
        // 매매 가격 패턴: "매매 5억 8,000" 또는 "매매 5억" 또는 "매매 8,000만"
        // 공백이 유지되므로 정규식에서 공백 허용
        const match = text.match(/매매\s*(\d{1,3}억(?:\s*\d{1,4}(?:,\d{3})?)?|[\d,]+만)/);
        if (match) {
            fullPrice = match[1].replace(/\s+/g, ''); // 공백 제거하여 저장
            const str = fullPrice;

            if (str.includes('억')) {
                const ukIndex = str.indexOf('억');
                const uk = parseInt(str.substring(0, ukIndex)) || 0;
                const remaining = str.substring(ukIndex + 1).replace(/,/g, '');
                const man = parseInt(remaining) || 0;
                price = uk * 10000 + man;
            } else if (str.includes('만')) {
                price = parseInt(str.replace(/[만,]/g, '')) || 0;
            } else {
                price = parseInt(str.replace(/,/g, '')) || 0;
            }
        }
    } else if (text.includes('월세')) {
        type = '월세';
        // 월세 패턴: "월세 7,000/310" 또는 "월세 5억 1,200/2,635"
        // 공백이 유지되므로 정규식에서 공백 허용
        const match = text.match(/월세\s*([\d,억천]+)\s*\/\s*([\d,]+)/);
        if (match) {
            fullPrice = `${match[1]}/${match[2]}`;
            price = parseInt(match[2].replace(/,/g, '')) || 0;
        }
    }

    return price > 0 ? { type, price, fullPrice } : null;
}

/**
 * 면적 정보 추출 (기존 naverbu 로직 이식)
 */
function extractArea(text) {
    const match = text.match(/\/([\d.]+)m²/);
    if (!match) return null;

    const squareMeters = parseFloat(match[1]);
    const pyeong = squareMeters * 0.3025;

    return { squareMeters, pyeong };
}

/**
 * 평당가 계산 (기존 naverbu 로직 이식)
 */
function calculatePricePerPyeong(type, price, pyeong) {
    if (type === '매매') {
        return Math.round(price / pyeong);
    } else {
        return parseFloat((price / pyeong).toFixed(1));
    }
}

/**
 * 층 정보 추출 (기존 naverbu 로직 이식)
 */
function extractFloorInfo(text) {
    let raw = '-';
    let category = '기타';

    // B1/6층 같은 패턴 (지하+총층) - 층 포함
    const basementWithFloorMatch = text.match(/B(\d+)\/(\d+)층/i);
    if (basementWithFloorMatch) {
        category = '지하';
        raw = `B${basementWithFloorMatch[1]}/${basementWithFloorMatch[2]}`;
        return { raw, category };
    }

    // B1/6 같은 패턴 (층 없이)
    const basementWithTotalMatch = text.match(/B(\d+)\/(\d+)/i);
    if (basementWithTotalMatch) {
        category = '지하';
        raw = `B${basementWithTotalMatch[1]}/${basementWithTotalMatch[2]}`;
        return { raw, category };
    }

    // 지하1/6층 같은 한글 패턴
    const jihaWithTotalMatch = text.match(/지하(\d+)\/(\d+)/);
    if (jihaWithTotalMatch) {
        category = '지하';
        raw = `B${jihaWithTotalMatch[1]}/${jihaWithTotalMatch[2]}`;
        return { raw, category };
    }

    // 단독 지하 패턴 (B1, B2 등) - 숫자 뒤에 / 가 아닌 경우
    const basementOnlyMatch = text.match(/B(\d+)(?!\/)/i);
    if (basementOnlyMatch) {
        category = '지하';
        raw = `B${basementOnlyMatch[1]}`;
        return { raw, category };
    }

    // 지하 한글 패턴
    const jihaMatch = text.match(/지하(\d+)/);
    if (jihaMatch) {
        category = '지하';
        raw = `B${jihaMatch[1]}`;
        return { raw, category };
    }

    // 일반 지하 표시
    if (text.includes('지하')) {
        category = '지하';
        raw = '지하';
        return { raw, category };
    }

    // 층/총층 패턴 (예: 3/15층)
    const floorMatch = text.match(/(\d+)\/(\d+)층/);
    if (floorMatch) {
        const floor = parseInt(floorMatch[1]);
        raw = `${floor}/${floorMatch[2]}`;
        category = getFloorCategory(floor);
        return { raw, category };
    }

    // 단일 층 패턴 (예: 5층)
    const singleFloorMatch = text.match(/(\d+)층/);
    if (singleFloorMatch) {
        const floor = parseInt(singleFloorMatch[1]);
        raw = floor.toString();
        category = getFloorCategory(floor);
        return { raw, category };
    }

    return { raw, category };
}

/**
 * 층 카테고리 분류
 */
function getFloorCategory(floor) {
    if (floor < 0) return '지하';
    if (floor === 1) return '1층';
    if (floor === 2) return '2층';
    if (floor >= 3) return '상층';
    return '기타';
}

/**
 * 향 정보 추출
 */
function extractDirection(text) {
    const match = text.match(/(동|서|남|북|남동|남서|북동|북서)향/);
    return match ? match[0] : '-';
}

/**
 * 통계 계산
 */
function calculateStatistics(data) {
    if (data.length === 0) {
        return {
            wolse: { count: 0, avg: 0, min: null, max: null },
            maemae: { count: 0, avg: 0, min: null, max: null },
            byFloor: {},
            total: 0
        };
    }

    // 월세 / 매매 분리
    const wolseItems = data.filter(d => d.type === '월세');
    const maemaeItems = data.filter(d => d.type === '매매');

    // 층별 분류 (매매/월세 각각)
    const floorCategories = ['1층', '2층', '상층', '지하'];
    const byFloor = {};

    floorCategories.forEach(floor => {
        const floorWolse = wolseItems.filter(d => d.category === floor);
        const floorMaemae = maemaeItems.filter(d => d.category === floor);

        byFloor[floor] = {
            wolse: calculateGroupStats(floorWolse),
            maemae: calculateGroupStats(floorMaemae),
            total: floorWolse.length + floorMaemae.length
        };
    });

    return {
        wolse: calculateGroupStats(wolseItems),
        maemae: calculateGroupStats(maemaeItems),
        byFloor: byFloor,
        total: data.length
    };
}

/**
 * 그룹 통계 계산 (절사평균 포함)
 */
function calculateGroupStats(items) {
    if (items.length === 0) {
        return { count: 0, avg: 0, min: null, max: null, trimmedAvg: 0 };
    }

    const prices = items.map(i => i.pricePerPyeong).sort((a, b) => a - b);
    const count = prices.length;

    // 최소/최대
    const min = items.reduce((prev, curr) =>
        prev.pricePerPyeong < curr.pricePerPyeong ? prev : curr
    );
    const max = items.reduce((prev, curr) =>
        prev.pricePerPyeong > curr.pricePerPyeong ? prev : curr
    );

    // 일반 평균
    const avg = prices.reduce((a, b) => a + b, 0) / count;

    // 절사평균 (상하위 10% 제외)
    let trimmedAvg = avg;
    if (count >= 5) {
        const trimCount = Math.floor(count * 0.1);
        const trimmedPrices = prices.slice(trimCount, count - trimCount);
        trimmedAvg = trimmedPrices.reduce((a, b) => a + b, 0) / trimmedPrices.length;
    }

    return {
        count,
        avg: Math.round(avg * 10) / 10,
        trimmedAvg: Math.round(trimmedAvg * 10) / 10,
        min,
        max
    };
}

/**
 * 매물 목록에 평당가/평수 배지 표시
 * 스크린샷 참고: "월세 1,000/135 (10.3만/13평)" 형식
 */
function addBadgesToListings() {
    const items = findListingItems();
    let addedCount = 0;

    // 스타일 주입 (한 번만)
    if (!document.getElementById('naverbu-badge-style')) {
        const style = document.createElement('style');
        style.id = 'naverbu-badge-style';
        style.textContent = `
            .naverbu-badge {
                display: inline-block;
                margin-left: 6px;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 700;
                vertical-align: middle;
            }
            .naverbu-badge--wolse {
                background: #FFF0F0;
                color: #E53935;
                border: 1px solid #FFCDD2;
            }
            .naverbu-badge--maemae {
                background: #E3F2FD;
                color: #1565C0;
                border: 1px solid #BBDEFB;
            }
        `;
        document.head.appendChild(style);
    }

    // 각 매물 아이템에 배지 추가(예를들어 30.25평 @5.6만 >> 3.4억가 6만/30.3평 이리 처리되어짐)
    items.forEach(item => {
        // 이미 배지가 있으면 스킵
        if (item.querySelector('.naverbu-badge')) return;

        try {
            const listingData = parseListingItem(item);
            if (!listingData) return;

            /*
            // landcore.js에 이미 배치처리가 되어져서 여기에서는 블럭처리함.
            //
            // 가격 요소 찾기 (.price_line, .price, 또는 텍스트에서)
            const priceEl = item.querySelector('.price_line, .item_price, .price');
            if (!priceEl) return;

            // 배지 생성
            const badge = document.createElement('span');
            const isWolse = listingData.type === '월세';

            badge.className = `naverbu-badge naverbu-badge--${isWolse ? 'wolse' : 'maemae'}`;
            badge.textContent = `${formatNumber(Math.round(listingData.pricePerPyeong))}만/${listingData.area.toFixed(1)}평`;

            // 배지 삽입
            priceEl.appendChild(badge);
            */
            addedCount++;
        } catch (e) {
            console.warn('배지 추가 실패:', e);
        }
    });

    return addedCount;
}

/**
 * 숫자 포맷팅 (천단위 콤마)
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

