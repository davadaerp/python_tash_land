/**
 * 기능:
 * 1. new/fin.naver.com 매물 목록에 평당가/평수 배지 자동 표시
 * 2. 매물 상세정보 팝업에서 매매가, 면적, 보증금/월세 등 핵심 정보 추출
 * 3. 네이버 자동 스크롤 및 Side Panel 에서 분석 요청 시 데이터 제공
 * ============================================
 */

console.log('🏢 랜드코어 부동산 분석기 - Content Script 로드됨');

/**
 * 신 버전(fin.land.naver.com) 여부 감지
 */
function isNewVersion() {
    return location.hostname === 'fin.land.naver.com';
}

function isNaverDomain() {
    const host = location.hostname || '';
    return host === 'new.land.naver.com' || host === 'fin.land.naver.com';
}

function isSupportedAnalysisPage() {
    return isNaverDomain() || isTankAuctionListPage() || isTankAuctionDetailPage() ||
        isAuction1DetailPage() || isGGAuctionDetailPage() || isDooinAuctionDetailPage();
}

// 탱크옥션 리스트 및 상세페이지
function isTankAuctionListPage() {
    return location.href.startsWith('https://www.tankauction.com/ca/caList.php') ||
           location.href.startsWith('https://www.tankauction.com/pa/paList.php');
}

function isTankAuctionDetailPage() {
    return location.href.startsWith('https://www.tankauction.com/ca/caView.php') ||
           location.href.startsWith('https://www.tankauction.com/pa/paView.php');
}

// [추가] 옥션원 상세 페이지 판별 (사용자 요청 URL 대응)
function isAuction1DetailPage() {
    return location.href.startsWith('https://www.auction1.co.kr/auction/ca_view.php');
}

// [추가] 지지옥션 상세 페이지 판별 (사용자 요청 URL 대응)
function isGGAuctionDetailPage() {
    return location.href.startsWith('https://web.ggi.co.kr/detail/km');
}

// [추가] 두인옥션 상세 페이지 판별 (사용자 요청 URL 대응)
function isDooinAuctionDetailPage() {
    return location.href.startsWith('https://www.dooinauction.com/ca/caView.php');
}

// ===== SPA 대응 자동 분석 시스템 =====
// 핵심: document.body를 항상 감시하여 어떤 SPA 네비게이션에서도 동작
let analysisDebounceTimer = null;
let badgeDebounceTimer = null;
let lastUrl = location.href;
//
let mapListSortDebounceTimer = null;
let lastSortedSignature = '';
//
let autoExpandDebounceTimer = null;
let isAutoExpandingListings = false;
let lastExpandedListKey = '';

// 1. 초기 로드 대기 후 시작
setTimeout(() => {
    if (isTankAuctionListPage()) {
        console.log('🏛️ 탱크옥션 목록 감시 시작');
        extractPropertyInfoTank();
        //observeMutationsTank();
        return;
    }

    if (isTankAuctionDetailPage()) {
        console.log('🏛️ 탱크옥션 상세 처리 시작');
        extractPropertyInfoDetailTank();
        return;
    }

    // [추가] 옥션원 상세 처리 시작
    if (isAuction1DetailPage()) {
        console.log('🏛️ 옥션원 상세 처리 시작');
        extractPropertyInfoDetailAuctionOne(); // 하단에 정의할 추출 함수 호출
        return;
    }

    // [추가] GG옥션 상세 처리 시작
    if (isGGAuctionDetailPage()) {
        console.log('🏛️  지지옥션 상세 처리 시작');
        extractPropertyInfoDetailGGAuction(); // 하단에 정의할 추출 함수 호출
        return;
    }

    // [추가] 두인옥션 상세 처리 시작
    if (isDooinAuctionDetailPage()) {
        console.log('🏛️  두인옥션 상세 처리 시작');
        extractPropertyInfoDetailDooinAuction(); // 하단에 정의할 추출 함수 호출
        return;
    }

    if (!isNaverDomain()) {
        console.log('[landcore_panel] naver.com 페이지가 아니므로 자동 감시를 실행하지 않습니다:', location.href);
        return;
    }

    // 일반 네이버 부동산 페이지
    startPersistentWatcher();
}, 1500);

/**
 * 영구 감시 시스템 (SPA 네비게이션 대응)
 * - document.body를 항상 감시
 * - 배지 없는 매물 발견 시 즉시 처리
 * - URL 변경 감지하여 재분석
 */
function startPersistentWatcher() {
    console.log('🏷️ 영구 감시 시스템 시작');

    // 초기 배지 표시
    const count = addBadgesToListings();
    if (count > 0) {
        console.log(`✅ 초기 ${count}개 매물에 배지 표시`);
        sendAnalysisToPanel();
    }

    // === body 레벨 MutationObserver (절대 끊기지 않음) ===
    const observer = new MutationObserver((mutations) => {
        // 상세 패널(#article_detail) 내부 변경은 무시 (평/m² 토글 등)
        // → 토글 시 analyzeCurrentPage() 호출을 방지하여 메시지 채널 보호
        let hasRelevantChange = false;
        for (const m of mutations) {
            if (m.addedNodes.length > 0) {
                // 상세 패널 내부인지 확인
                const isInsideDetail = m.target.closest?.('#article_detail, [class*="ArticleDetail"]');
                if (!isInsideDetail) {
                    hasRelevantChange = true;
                    break;
                }
            }
        }
        if (!hasRelevantChange) return;

        // 배지 표시 (디바운스 300ms - 연속 DOM 변경 시 한 번만)
        clearTimeout(badgeDebounceTimer);
        badgeDebounceTimer = setTimeout(() => {
            const added = addBadgesToListings();
            if (added > 0) {
                console.log(`🏷️ ${added}개 매물에 배지 추가`);
            }
        }, 300);

        // 목록이 새로 열렸는데 총건수보다 적게 렌더링되면 자동 전체 펼치기
        clearTimeout(autoExpandDebounceTimer);
        autoExpandDebounceTimer = setTimeout(async () => {
            if (shouldAutoExpandListings()) {
                await ensureListingsFullyLoaded('mutation');
            } else {
                sendAnalysisToPanel();
            }
        }, 700);
        //
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    console.log('👁️ body MutationObserver 활성화 - 영구 감시 중');

    // === URL 변경 감지 (SPA pushState/replaceState) ===
    // SPA에서 지도 이동/건물 클릭 시 URL이 바뀌지만 페이지 리로드 없음
    setInterval(() => {
        if (location.href !== lastUrl) {
            console.log('🔄 URL 변경 감지:', lastUrl, '→', location.href);
            lastUrl = location.href;
            // URL 변경 후 DOM 업데이트 대기
            setTimeout(async () => {
                const added = addBadgesToListings();
                if (added > 0) {
                    console.log(`🏷️ URL 변경 후 ${added}개 배지 추가`);
                }

                if (shouldAutoExpandListings()) {
                    await ensureListingsFullyLoaded('url-change');
                } else {
                    sendAnalysisToPanel();
                }
            }, 1000);
        }
    }, 500);
}

/**
 * 분석 결과를 사이드패널로 자동 전송
 */
function sendAnalysisToPanel() {
    if (!isNaverDomain()) {
        console.log('[landcore_panel] naver.com 페이지가 아니므로 AUTO_ANALYSIS_UPDATE 전송을 건너뜁니다.');
        return;
    }

    try {
        const payload = buildAnalysisResponseData();
        chrome.runtime.sendMessage({
            type: 'AUTO_ANALYSIS_UPDATE',
            data: payload
        }).catch(() => {
            // 사이드패널이 열려있지 않은 경우 무시
        });
        console.log('📊 실시간 분석 전송:', payload.totalCount, '개 매물');
    } catch (error) {
        //console.warn('자동 분석 실패:', error);
        console.log('자동 분석 실패:', error);
    }
}


// 실거래조회시 지도위치(경.공매연동시) 가져오기
function getWishlistSelectedLocationFromPage() {
    const body = document.body;
    if (!body) return null;

    const latitude = parseFloat(body.dataset.wishlistSelectedLat || '0');
    const longitude = parseFloat(body.dataset.wishlistSelectedLng || '0');
    const address = (body.dataset.wishlistSelectedAddress || '').trim();
    // 근린상가, 다가구, 다세대, 연립빌라등등
    const objectType = (body.dataset.wishlistSelectedObjectType || '').trim();

    if (!latitude || !longitude) {
        return null;
    }

    return {
        latitude,
        longitude,
        address,
        objectType
    };
}

/**
 * 메시지 리스너 - Side Panel에서 분석 요청 시에만 동작
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // START_ANALYSIS: 현재 화면의 매물 분석 (스크롤 없음 - 법적 안전)
    if (message.type === 'START_ANALYSIS') {
        if (!isSupportedAnalysisPage()) {
            sendResponse({ success: false, error: '지원 페이지가 아닙니다. 네이버부동산 또는 탱크옥션에서만 분석 가능합니다.' });
            return true;
        }

        if (!isNaverDomain() && !isTankAuctionListPage() && !isTankAuctionDetailPage()) {
            sendResponse({ success: false, error: '지원 페이지가 아닙니다.' });
            return true;
        }

        console.log('📊 분석 시작 요청 수신');

        (async () => {
            try {
                await autoScrollToLoadAllListings();

                const payload = buildAnalysisResponseData();
                console.log('✅ 분석 완료, 응답 전송');
                sendResponse({ success: true, data: payload });
            } catch (error) {
                console.error('❌ 분석 오류:', error);
                sendResponse({ success: false, error: error.message || '분석 실패' });
            }
        })();

        return true;
    }

    // GET_LISTING_DETAIL: 현재 열린 상세정보 팝업에서 데이터 추출
    if (message.type === 'GET_LISTING_DETAIL') {
        if (!isNaverDomain()) {
            sendResponse({ success: false, error: '네이버부동산 페이지에서만 상세정보 추출이 가능합니다.' });
            return true;
        }

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

    // SHOW_BADGES: 매물 목록에 평당가/평수 배지 표시
    if (message.type === 'SHOW_BADGES') {
        if (!isNaverDomain()) {
            sendResponse({ success: false, error: '네이버부동산 페이지에서만 배지 표시가 가능합니다.' });
            return true;
        }

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

    // 관심물건 지도위치 가져오기
    if (message.type === 'GET_WISHLIST_SELECTED_LOCATION') {
        try {
            const locationData = getWishlistSelectedLocationFromPage();

            sendResponse({
                success: true,
                data: locationData
            });
        } catch (error) {
            console.error('❌ 관심물건 선택 좌표 조회 오류:', error);
            sendResponse({
                success: false,
                error: error.message || '관심물건 좌표 조회 실패'
            });
        }
        return true;
    }

    // [수정] 특정 중개사/가격 매물 상세 조회
    if (message.type === 'GET_AGENCY_DETAIL_BY_NAME') {
        const mode = message.mode || 'agencyName';
        const targetName = normalizeAgencyNameForCompare(message.agencyName);
        const targetItem = message.listingItem || null;

        console.log('[GET_AGENCY_DETAIL_BY_NAME] 요청:', {
            mode,
            agencyName: message.agencyName,
            targetItem
        });

        (async () => {
            try {
                const items = findListingItems();

                for (const item of items) {
                    const listingData = parseListingItem(item);
                    if (!listingData) continue;

                    let matched = false;

                    // 월세,매매목록 상세 구분없이 매물정보로 비교하여 매칭 여부 판단
                    if (mode === 'listingItem') {
                        matched = isSameListingItemForDetail(listingData, targetItem);

                        console.log('[GET_AGENCY_DETAIL_BY_NAME][PRICE_MATCH_CHECK]', {
                            matched,
                            parsed: listingData,
                            target: targetItem
                        });
                    } else {
                        if (!listingData.agencyName) continue;

                        const currentName = normalizeAgencyNameForCompare(listingData.agencyName);
                        matched = currentName === targetName;

                        console.log('[GET_AGENCY_DETAIL_BY_NAME][AGENCY_MATCH_CHECK]', {
                            matched,
                            currentName,
                            targetName,
                            parsed: listingData
                        });
                    }

                    if (!matched) continue;

                    const memoData = await extractMemoDataFromListingItem(item, listingData);

                    sendResponse({
                        success: true,
                        data: memoData
                    });

                    return;
                }

                console.warn('[GET_AGENCY_DETAIL_BY_NAME] 매칭 매물 없음:', {
                    mode,
                    targetName,
                    targetItem
                });

                sendResponse({ success: false });

            } catch (e) {
                console.error('[GET_AGENCY_DETAIL_BY_NAME] 오류:', e);
                sendResponse({ success: false, error: e.message || String(e) });
            }
        })();

        return true;
    }

    return false;
});

function normalizeAgencyNameForCompare(name) {
    if (!name) return '';

    return name
        .replace(/\s+/g, '')
        .replace(/공인중개사사무소|중개사사무소|중개사무소/g, '')
        .trim();
}

function normalizeListingCompareValue(value) {
    return String(value ?? '')
        .replace(/\s+/g, '')
        .replace(/,/g, '')
        .trim();
}

function isNearlySameNumber(a, b, tolerance = 0.15) {
    const na = Number(a) || 0;
    const nb = Number(b) || 0;

    if (!na && !nb) return true;
    if (!na || !nb) return false;

    return Math.abs(na - nb) <= tolerance;
}

function isSameListingItemForDetail(parsed, target) {
    if (!parsed || !target) return false;

    const sameType = normalizeListingCompareValue(parsed.type) === normalizeListingCompareValue(target.type);
    const sameFloor = normalizeListingCompareValue(parsed.floor) === normalizeListingCompareValue(target.floor);
    const samePrice = normalizeListingCompareValue(parsed.fullPrice) === normalizeListingCompareValue(target.fullPrice);
    const sameArea = isNearlySameNumber(parsed.area, target.area, 0.2);
    const samePydanga = isNearlySameNumber(parsed.pricePerPyeong, target.pricePerPyeong, 0.2);

    const parsedAgency = normalizeAgencyNameForCompare(parsed.agencyName || '');
    const targetAgency = normalizeAgencyNameForCompare(target.agencyName || '');
    const sameAgency = !targetAgency || parsedAgency === targetAgency;

    // 핵심 비교: 구분 + 층 + 가격 + 평수 + 평당가
    // 중개사명은 있으면 같이 비교, 없으면 제외
    return sameType && sameFloor && samePrice && sameArea && samePydanga && sameAgency;
}

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
        hasRentInfo: false,  // 임대 정보 존재 여부
        areaInPyeong: false  // 면적이 이미 평 단위인지 여부
    };

    // 신 버전: #article_detail
    if (isNewVersion()) {
        // 매번 최신 DOM을 참조 (토글 등으로 재렌더링될 수 있으므로)
        const getDetailPanel = () => document.querySelector('#article_detail, [class*="ArticleDetail"]');

        const detailPanel = getDetailPanel();
        if (!detailPanel) {
            console.warn('⚠️ 신 버전 상세정보 패널을 찾을 수 없습니다.');
            return extractFromText(document.body.innerText);
        }

        console.log('📋 신 버전 상세정보 패널 발견, 데이터 추출 시작');

        // 신 버전 라벨-값 검색 헬퍼 (매번 최신 DOM 텍스트 사용)
        const getFieldValue = (labelKeyword) => {
            const panel = getDetailPanel();
            if (!panel) return null;
            const allText = panel.innerText;
            const lines = allText.split('\n').map(l => l.trim()).filter(l => l);
            for (let i = 0; i < lines.length; i++) {
                if (lines[i].includes(labelKeyword)) {
                    // 같은 줄에 라벨과 값이 있는 경우
                    const parts = lines[i].split(labelKeyword);
                    const afterLabel = parts[parts.length - 1].trim();
                    if (afterLabel && /\d/.test(afterLabel)) return afterLabel;
                    // 다음 줄에 값이 있는 경우
                    if (i + 1 < lines.length) {
                        return lines[i + 1].trim();
                    }
                }
            }
            return null;
        };

        // 1. 매매가/월세 추출 (상단 텍스트에서)
        const panelText = getDetailPanel()?.innerText || '';
        const salePriceMatch = panelText.match(/매매\s*(\d{1,3}억(?:\s*\d{1,4}(?:,\d{3})?)?|[\d,]+만)/);
        if (salePriceMatch) {
            result.salePrice = parseKoreanPrice(salePriceMatch[1].replace(/\s+/g, ''));
            console.log('💰 매매가 추출:', salePriceMatch[1], '→', result.salePrice, '만원');
        }

        // 월세 패턴: "월세 1억/420" 또는 "월세 5,000/400"
        const rentPriceMatch = panelText.match(/월세\s*([\d,억천]+)\s*\/\s*([\d,]+)/);
        if (rentPriceMatch) {
            result.deposit = parseKoreanPrice(rentPriceMatch[1].replace(/\s+/g, ''));
            result.monthlyRent = parseInt(rentPriceMatch[2].replace(/,/g, '')) || 0;
            result.hasRentInfo = true;
            console.log('🏠 월세 추출: 보증금', result.deposit, '만원, 월세', result.monthlyRent, '만원');
        }

        // 매매 물건의 기보증금/기월세액 추출 (매매인데 현재 임차인이 있는 경우)
        // 주의: innerText에서 "3,000" 과 "/180만원"이 별도 줄로 분리됨
        // → 공백/줄바꿈 제거 후 전체 텍스트에서 패턴 매칭
        if (!result.hasRentInfo) {
            const collapsed = panelText.replace(/\s+/g, '');
            // "기보증금/기월세액3,000/180만원" 또는 "기보증금/기월세액1,000/60만원"
            const rentMatch = collapsed.match(/기보증금\/기월세액([\d,]+)\/([\d,]+)/);
            if (rentMatch) {
                result.deposit = parseInt(rentMatch[1].replace(/,/g, '')) || 0;
                result.monthlyRent = parseInt(rentMatch[2].replace(/,/g, '')) || 0;
                result.hasRentInfo = true;
                console.log('🏠 기보증금/기월세 추출: 보증금', result.deposit, '만원, 월세', result.monthlyRent, '만원');
            }
        }

        // 2. 면적 추출 (단위 감지: m² vs 평)
        const contractAreaText = getFieldValue('계약면적');
        const exclusiveAreaText = getFieldValue('전용면적');

        // 단위 감지: "18.14평" (숫자 바로 뒤 평) vs "60m²"
        // 주의: "60m² ☛ 평" 처럼 전환 버튼 텍스트에도 '평'이 포함됨
        if (contractAreaText && /[\d.]평/.test(contractAreaText)) {
            result.areaInPyeong = true;
        }

        if (contractAreaText) {
            const caMatch = contractAreaText.match(/([\d.]+)/);
            if (caMatch) result.contractArea = parseFloat(caMatch[1]);
        }
        if (exclusiveAreaText) {
            const eaMatch = exclusiveAreaText.match(/([\d.]+)/);
            if (eaMatch) result.exclusiveArea = parseFloat(eaMatch[1]);
        }

        // 폴백 1: 아파트형 "계약88.24㎡ (전용88)"
        if (result.exclusiveArea === 0) {
            const summaryMatch = panelText.match(/계약\s*[\d.]+[㎡m평]\S*\s*\(?전용\s*([\d.]+)/);
            if (summaryMatch) result.exclusiveArea = parseFloat(summaryMatch[1]);
        }
        if (result.contractArea === 0) {
            const summaryMatch = panelText.match(/계약\s*([\d.]+)/);
            if (summaryMatch) result.contractArea = parseFloat(summaryMatch[1]);
        }

        // 폴백 2: 빌라형 "공급94.9㎡ (전용70.39)"
        if (result.exclusiveArea === 0) {
            const supplyExclusiveMatch = panelText.match(/공급\s*[\d.]+[㎡m평]\S*\s*\(?전용\s*([\d.]+)/);
            if (supplyExclusiveMatch) {
                result.exclusiveArea = parseFloat(supplyExclusiveMatch[1]);
            }
        }
        if (result.contractArea === 0) {
            const supplyContractMatch = panelText.match(/공급\s*([\d.]+)/);
            if (supplyContractMatch) {
                result.contractArea = parseFloat(supplyContractMatch[1]);
            }
        }

        // 폴백 3: 단독/다가구형 "대지94.9㎡ (연면적70.39)"
        if (result.exclusiveArea === 0) {
            const grossMatch = panelText.match(/연면적\s*([\d.]+)/);
            if (grossMatch) {
                result.exclusiveArea = parseFloat(grossMatch[1]);
            }
        }
        if (result.contractArea === 0) {
            const landMatch = panelText.match(/대지\s*([\d.]+)/);
            if (landMatch) {
                result.contractArea = parseFloat(landMatch[1]);
            }
        }
        console.log('📐 면적 추출:', result.contractArea, '/', result.exclusiveArea, 'm²');

        return result;
    }

    // ===== 구 버전 (new.land.naver.com) =====
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

    // ===== 신 버전 (fin.land.naver.com) =====
    if (isNewVersion()) {
        const detailPanel = document.querySelector('#article_detail, [class*="ArticleDetail"]');
        if (!detailPanel) {
            console.warn('⚠️ 신 버전 상세정보 패널을 찾을 수 없습니다.');
            return result;
        }

        console.log('📝 신 버전 메모 데이터 추출 시작...');
        const panelText = detailPanel.innerText;
        const lines = panelText.split('\n').map(l => l.trim()).filter(l => l);

        // 라벨 다음 줄에 값이 있는 구조에서 값 추출
        const getFieldValue = (labelKeyword) => {
            for (let i = 0; i < lines.length; i++) {
                if (lines[i] === labelKeyword || lines[i].startsWith(labelKeyword)) {
                    // 같은 줄에 값이 있는 경우
                    const afterLabel = lines[i].replace(labelKeyword, '').trim();
                    if (afterLabel) return afterLabel;
                    // 다음 줄에 값이 있는 경우
                    if (i + 1 < lines.length) return lines[i + 1].trim();
                }
            }
            return null;
        };

        // 1. 매물명 (상단 "정자동 일반상가" 등)
        // 첫 몇 줄에서 상가 유형 추출
        for (const line of lines.slice(0, 5)) {
            if (line.includes('상가') || line.includes('사무실') || line.includes('건물')) {
                result.propertyName = line;
                break;
            }
        }

        // 2. 가격
        const priceMatch = panelText.match(/매매\s*(\d{1,3}억(?:\s*\d{1,4}(?:,\d{3})?)?|[\d,]+만)/);
        if (priceMatch) result.price = '매매 ' + priceMatch[1];
        const rentMatch = panelText.match(/월세\s*([\d,억천]+\s*\/\s*[\d,]+)/);
        if (rentMatch) {
            result.price = '월세 ' + rentMatch[1];
            result.rent = rentMatch[1];
        }

        // 기보증금/기월세액 추출 (매매 물건에 임차인이 있는 경우)
        if (!result.rent) {
            const collapsed = panelText.replace(/\s+/g, '');
            const rentFieldMatch = collapsed.match(/기보증금\/기월세액([\d,]+)\/([\d,]+)/);
            if (rentFieldMatch) {
                result.rent = `${rentFieldMatch[1]}/${rentFieldMatch[2]}만원`;
            }
        }

        // 3. 면적 - 상세 필드(계약면적/전용면적)에서 추출 (요약줄은 네이버가 내림한 값이라 부정확)
        const contractAreaText = getFieldValue('계약면적') || '';
        const exclusiveAreaText = getFieldValue('전용면적') || '';
        const cNum = contractAreaText.match(/([\d.]+)/);
        const eNum = exclusiveAreaText.match(/([\d.]+)/);
        if (cNum && eNum) {
            const cVal = parseFloat(cNum[1]);
            const eVal = parseFloat(eNum[1]);
            const isAlreadyPyeong = /[\d.]평/.test(contractAreaText);
            const cPy = isAlreadyPyeong ? cVal.toFixed(1) : (cVal * 0.3025).toFixed(1);
            const ePy = isAlreadyPyeong ? eVal.toFixed(1) : (eVal * 0.3025).toFixed(1);
            result.area = `${cPy}평/${ePy}평`;
        }

        // 4. 층수
        result.floor = getFieldValue('해당층/총층') || '';

        // 5. 주소 (건축물 정보 > 위치)
        result.address = getFieldValue('위치') || getFieldValue('소재지') || '';

        // 6. 매물특징
        const featuresVal = getFieldValue('매물소개');
        if (featuresVal) result.features = featuresVal;

        // 7. 매물번호
        result.propertyNo = getFieldValue('매물번호') || '';

        // 8. 중개사 정보
        // 전화번호 추출
        const phoneMatches = panelText.match(/\d{2,4}-\d{3,4}-\d{4}/g) || [];
        if (phoneMatches.length > 0) result.agencyPhone = phoneMatches[0];
        if (phoneMatches.length > 1) result.agencyMobile = phoneMatches[1];

        // 중개사명 추출
        for (const line of lines) {
            if (line.includes('공인중개사') || line.includes('부동산사무소')) {
                result.agencyName = line;
                break;
            }
        }

        // 중개사 위치 (등록번호 근처)
        const agencyLocVal = getFieldValue('위치');
        // 두번째 "위치" 값이 중개사 주소
        let locationCount = 0;
        for (let i = 0; i < lines.length; i++) {
            if (lines[i] === '위치' || lines[i].startsWith('위치')) {
                locationCount++;
                if (locationCount === 2 && i + 1 < lines.length) {
                    result.agencyAddress = lines[i + 1].trim();
                    break;
                }
            }
        }

        console.log('📝 신 버전 메모 데이터 추출 완료:', result);
        return result;
    }

    // ===== 구 버전 (new.land.naver.com) =====
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


// 중개사 관련 데이터만 정리하는 함수
async function extractMemoDataFromListingItem(item, listingData = null) {
    const parsed = listingData || parseListingItem(item);
    const prevSignature = getCurrentDetailPanelSignature();

    triggerListingItemDetailOpen(item);

    const changed = await waitForDetailPanelChange(prevSignature, 5000);
    if (!changed) {
        console.warn('상세 패널 열기/변경 대기 실패, 목록 기준 보조값 사용');
    }

    await sleep(180);

    // 상세내역 데이타 추출
    const memoData = extractMemoData();

    return {
        propertyName: memoData.propertyName || parsed?.propertyType || '',
        agencyName: memoData.agencyName || parsed?.agencyName || (parsed?.agencyCount > 1 ? `중개사 ${parsed.agencyCount}곳` : ''),
        agencyPhone: memoData.agencyPhone || '',
        agencyMobile: memoData.agencyMobile || '',
        agencyAddress: memoData.agencyAddress || ''
    };
}

// =============================
// 상세패널 관련 유틸 함수 START
// =============================

// 단순 sleep
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 현재 열린 상세 패널 DOM 반환
function getCurrentDetailPanelElement() {
    if (isNewVersion()) {
        return document.querySelector('#article_detail, [class*="ArticleDetail"]');
    } else {
        return document.querySelector('.detail_panel');
    }
}

// 상세 패널 변경 여부 판단용 시그니처
function getCurrentDetailPanelSignature() {
    const panel = getCurrentDetailPanelElement();
    if (!panel) return '';

    // 매물번호 + 텍스트 일부 조합 (변경 감지용)
    const text = panel.innerText || '';
    return text.slice(0, 200); // 앞부분만 비교 (속도 최적화)
}

function triggerListingItemDetailOpen(item) {
    if (!item) return;

    let clickable = null;

    if (isNewVersion()) {
        /**
         * fin.land 신버전
         * 핵심:
         * - ArticleCard_button-expand 는 중개사 묶음 펼침 버튼이라 클릭하면 안 됨
         * - ArticleCard_link 계열만 클릭해서 상세패널만 열기
         */
        clickable =
            item.querySelector('[class*="ArticleCard_link"]') ||
            item.querySelector('a[href*="article"]') ||
            item.querySelector('a');

        if (!clickable) {
            console.warn('[AgencyDetail] 상세 링크를 찾지 못했습니다. 펼침 버튼은 클릭하지 않습니다.', item);
            return;
        }
    } else {
        /**
         * new.land 구버전
         * 기존 방식 유지
         */
        clickable =
            item.querySelector('.item_link') ||
            item.querySelector('a') ||
            item;
    }

    clickable.dispatchEvent(new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
        view: window
    }));
}

// 상세 패널 변경 대기
async function waitForDetailPanelChange(prevSignature, timeoutMs = 5000) {
    const start = Date.now();

    while (Date.now() - start < timeoutMs) {
        await sleep(120);

        const currentSignature = getCurrentDetailPanelSignature();

        if (currentSignature && currentSignature !== prevSignature) {
            return true;
        }
    }

    return false;
}
// =============================
// 상세패널 관련 유틸 함수 END
// =============================


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
 * 탭구분 즉 아파트, 빌라, 상가 추출
 * 지역정보를 포함한 분석 응답 데이터 생성
 */
function buildAnalysisResponseData() {
    const analysisResult = analyzeCurrentPage();
    const regionInfo = getSelectedRegionInfo();
    const tabGubun = getSelectedTabGubun();

    return {
        ...analysisResult,
        regionInfo: {
            region: regionInfo?.region || null,
            sigungu: regionInfo?.sigungu || null,
            umdNm: regionInfo?.umdNm || null
        },
        tabGubun: tabGubun || null
    };
}

/**
 * 매물 아이템 요소 찾기
 * ⚠️ 읽기만 수행
 */
function findListingItems() {
    // 신 버전 (fin.land.naver.com)
    if (isNewVersion()) {
        // ArticleCard 링크 + 그룹 카드(중개사 다중 등록) 모두 포함
        // 링크: ArticleCard_link (투명 오버레이), 그룹: ArticleCard_button-expand
        const cardElements = document.querySelectorAll(
            '[class*="ArticleCard_link"], [class*="ArticleCard_button-expand"]'
        );
        if (cardElements.length > 0) {
            const parents = new Set();
            cardElements.forEach(el => {
                // 부모 요소가 카드 컨테이너
                const parent = el.parentElement;
                if (parent) parents.add(parent);
            });
            return Array.from(parents);
        }

        // 방법 2: #article_list 내 직접 자식 요소들
        const listContainer = document.querySelector('#article_list');
        if (listContainer) {
            // 스크롤 컨테이너의 자식들 중 실제 카드 요소만 필터링
            const scrollContainer = listContainer.querySelector('[class*="ScrollBox_scroller"]') || listContainer;
            const children = scrollContainer.children;
            const items = [];
            for (const child of children) {
                // 텍스트가 있는 의미있는 카드만 포함
                if (child.innerText && child.innerText.includes('매') && child.innerText.length > 20) {
                    items.push(child);
                }
            }
            if (items.length > 0) return items;
        }

        return [];
    }

    // 구 버전 (new.land.naver.com)
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
    // 매물 유형 추출
    const propertyType = extractPropertyTypeFromListingText(text);

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
        propertyType: propertyType,     // 매물유형 (아파트, 상가점포, 빌라 등)
        category: floorInfo.category,    // 1층, 2층, 상층, 지하
        floor: floorInfo.raw,           // 층 정보 원본
        direction: direction,            // 향
        pricePerPyeong: pricePerPyeong, // 평당가
        area: areaInfo.pyeong,          // 면적 (평)
        fullPrice: priceInfo.fullPrice, // 원본 가격 문자열(매매 2억, 월세 1,000/70)
        price: priceInfo.price,         // 가격 (만원 단위)
        agencyName: agencyInfo.name,    // 공인중개사 이름
        agencyCount: agencyInfo.count,  // 중개사 수
        verificationDate: verificationDate // 확인 날짜
    };
}

/**
 * 매물 카드 텍스트에서 매물유형 추출
 * 예: 아파트, 오피스텔, 빌라, 원룸, 단독/다가구, 전원주택, 상가주택, 재개발,
 *     상가점포, 상가, 사무실, 건물, 공장/창고, 지식산업센터
 */
function extractPropertyTypeFromListingText(text) {
    const normalized = (text || '').replace(/\s+/g, '').trim();

    // 긴 문자열/구체 유형 우선
    const typeKeywords = [
        '아파트',
        '오피스텔',
        '재개발',
        '아파트분양권',
        '빌라',
        '원룸',
        '연립',
        '단독',
        '다가구',
        '전원주택',
        '상가주택',
        '상가점포',
        '사무실',
        '상가건물',
        '빌딩',
        '지식산업센터',
        '공장',
        '창고',
        '토지'
    ];

    for (const keyword of typeKeywords) {
        const keywordNormalized = keyword.replace(/\s+/g, '');
        if (normalized.includes(keywordNormalized)) {
            // 공장/창고 통합 처리
            if (keyword === '공장' || keyword === '창고') {
                return '공장/창고';
            }
            return keyword;
        }
    }

    return '';
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
    // "확인매물 2026.03.19" 패턴 (YYYY.MM.DD 형식 - 신 버전)
    const matchFull = text.match(/확인매물\s*(\d{4}\.\d{2}\.\d{2})/);
    if (matchFull) {
        return matchFull[1];
    }
    // "확인매물 26.01.07" 패턴 (YY.MM.DD 형식 - 구 버전)
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
 * 면적 정보 추출
 *
 * 지원 패턴:
 * 1. 구버전: "/38m²", "/63㎡"
 * 2. 신버전 아파트/오피스텔: "계약123.95㎡ (전용62.97)"
 * 3. 신버전 빌라/연립/다가구: "공급94.9㎡ (전용70.39)"
 * 4. 단독/다가구/건물형: "대지94.9㎡ (연면적70.39)"
 */
function extractArea(text) {
    const normalized = (text || '').replace(/\s+/g, ' ').trim();

    // ==================================================
    // 1) 구버전 형식 우선
    // 예: "상가· 76/38m²", "/63㎡"
    // ==================================================
    const legacyMatch = normalized.match(/\/\s*([\d.]+)\s*[m㎡][²2]?/i);
    if (legacyMatch) {
        const squareMeters = parseFloat(legacyMatch[1]);
        if (!isNaN(squareMeters) && squareMeters > 0) {
            return {
                squareMeters,
                pyeong: squareMeters * 0.3025
            };
        }
    }

    // ==================================================
    // 2) 신버전 아파트/오피스텔
    // 예: "계약123.95㎡ (전용62.97)"
    //     "계약35평 (전용35)"
    // ==================================================
    const contractMatch = normalized.match(/계약\s*([\d.]+)\s*([㎡m평])[^\d]*(?:\(\s*)?전용\s*([\d.]+)/i);
    if (contractMatch) {
        const unitValue = parseFloat(contractMatch[3]);   // 전용값 사용
        const unitType = contractMatch[2];

        if (!isNaN(unitValue) && unitValue > 0) {
            if (unitType === '평') {
                return {
                    squareMeters: unitValue / 0.3025,
                    pyeong: unitValue
                };
            }
            return {
                squareMeters: unitValue,
                pyeong: unitValue * 0.3025
            };
        }
    }

    // ==================================================
    // 3) 신버전 빌라/연립/다가구
    // 예: "공급94㎡ (전용70)"
    //     "공급94.9㎡ (전용70.39)"
    // ==================================================
    const supplyExclusiveMatch = normalized.match(/공급\s*([\d.]+)\s*[㎡m평][^\d]*(?:\(\s*)?전용\s*([\d.]+)/i);
    if (supplyExclusiveMatch) {
        const exclusive = parseFloat(supplyExclusiveMatch[2]);
        if (!isNaN(exclusive) && exclusive > 0) {
            return {
                squareMeters: exclusive,
                pyeong: exclusive * 0.3025
            };
        }
    }

    // ==================================================
    // 4) 단독/다가구/건물형
    // 예: "대지94.9㎡ (연면적70.39)"
    // 연면적을 실사용 분석용 면적으로 간주
    // ==================================================
    const landGrossMatch = normalized.match(/대지\s*([\d.]+)\s*[㎡m평][^\d]*(?:\(\s*)?연면적\s*([\d.]+)/i);
    if (landGrossMatch) {
        const grossArea = parseFloat(landGrossMatch[2]);
        if (!isNaN(grossArea) && grossArea > 0) {
            return {
                squareMeters: grossArea,
                pyeong: grossArea * 0.3025
            };
        }
    }

    // ==================================================
    // 5) 추가 폴백
    // 예: "전용70.39", "연면적70.39"
    // 설명문 오매칭을 줄이기 위해 카드 텍스트 전체에서 마지막 보조 처리
    // ==================================================
    const exclusiveFallback = normalized.match(/전용\s*([\d.]+)/i);
    if (exclusiveFallback) {
        const exclusive = parseFloat(exclusiveFallback[1]);
        if (!isNaN(exclusive) && exclusive > 0) {
            return {
                squareMeters: exclusive,
                pyeong: exclusive * 0.3025
            };
        }
    }

    const grossFallback = normalized.match(/연면적\s*([\d.]+)/i);
    if (grossFallback) {
        const grossArea = parseFloat(grossFallback[1]);
        if (!isNaN(grossArea) && grossArea > 0) {
            return {
                squareMeters: grossArea,
                pyeong: grossArea * 0.3025
            };
        }
    }

    return null;
}

/**
 * 평당가 계산
 */
function calculatePricePerPyeong(type, price, pyeong) {
    if (type === '매매') {
        // 매매는 보통 만원 단위로 딱 떨어지게 반올림
        return Math.round(price / pyeong);
    } else {
        // 월세는 4.49 -> 4.5가 되도록 소수점 첫째 자리에서 반올림
        // (price / pyeong) 결과에 10을 곱하고 반올림 후 다시 10으로 나눔
        return Math.round((price / pyeong) * 10) / 10;
    }
}

/**
 * 층 정보 추출
/**
 * 층 정보 추출
 * - category: 통계 분류용 (1층, 2층, 상층, 지하)
 * - raw: 표시용 최종 문자열도 사람이 보기 좋게 "1층", "2층", "3층", "지하" 형태로 반환
 */
function extractFloorInfo(text) {
    let raw = '-';
    let category = '기타';

    const normalized = (text || '').replace(/\s+/g, ' ').trim();

    // ==================================================
    // 0) fin.land 우선 처리
    // 예: 1/2층, 1 / 2층, 1/-층, 1 / - 층, 1/-
    // -> 모두 1층으로 처리
    // ==================================================
    const firstFloorAnyTotalMatch = normalized.match(/(^|\s)1\s*\/\s*(\d+|-)\s*층?/);
    if (firstFloorAnyTotalMatch) {
        raw = '1층';
        category = '1층';
        return { raw, category };
    }

    // ==================================================
    // 1) 지하 패턴
    // ==================================================
    const basementWithFloorMatch = normalized.match(/B(\d+)\s*\/\s*(\d+)\s*층/i);
    if (basementWithFloorMatch) {
        category = '지하';
        raw = `지하${basementWithFloorMatch[1]}층`;
        return { raw, category };
    }

    const basementWithTotalMatch = normalized.match(/B(\d+)\s*\/\s*(\d+)/i);
    if (basementWithTotalMatch) {
        category = '지하';
        raw = `지하${basementWithTotalMatch[1]}층`;
        return { raw, category };
    }

    const jihaWithTotalMatch = normalized.match(/지하\s*(\d+)\s*\/\s*(\d+)/);
    if (jihaWithTotalMatch) {
        category = '지하';
        raw = `지하${jihaWithTotalMatch[1]}층`;
        return { raw, category };
    }

    const basementOnlyMatch = normalized.match(/B(\d+)(?!\s*\/)/i);
    if (basementOnlyMatch) {
        category = '지하';
        raw = `지하${basementOnlyMatch[1]}층`;
        return { raw, category };
    }

    const jihaMatch = normalized.match(/지하\s*(\d+)/);
    if (jihaMatch) {
        category = '지하';
        raw = `지하${jihaMatch[1]}층`;
        return { raw, category };
    }

    if (normalized.includes('지하')) {
        category = '지하';
        raw = '지하';
        return { raw, category };
    }

    // ==================================================
    // 2) 일반 층/총층
    // 예: 2/5층, 3/15층
    // ==================================================
    const floorMatch = normalized.match(/(\d+)\s*\/\s*(\d+)\s*층/);
    if (floorMatch) {
        const floor = parseInt(floorMatch[1], 10);
        raw = `${floor}층`;
        category = getFloorCategory(floor);
        return { raw, category };
    }

    // ==================================================
    // 3) 총층 미표기 패턴
    // 예: 2/-층, 3/-, 4 / -
    // ==================================================
    const floorUnknownTotalMatch = normalized.match(/(\d+)\s*\/\s*-\s*층?/);
    if (floorUnknownTotalMatch) {
        const floor = parseInt(floorUnknownTotalMatch[1], 10);
        raw = `${floor}층`;
        category = getFloorCategory(floor);
        return { raw, category };
    }

    // ==================================================
    // 4) 층/총층 (층 생략)
    // 예: 2/5, 3/15
    // ==================================================
    const floorWithoutSuffixMatch = normalized.match(/(\d+)\s*\/\s*(\d+)(?![.\d])/);
    if (floorWithoutSuffixMatch) {
        const floor = parseInt(floorWithoutSuffixMatch[1], 10);
        raw = `${floor}층`;
        category = getFloorCategory(floor);
        return { raw, category };
    }

    // ==================================================
    // 5) 단일 층
    // 예: 5층
    // ==================================================
    const singleFloorMatch = normalized.match(/(\d+)\s*층/);
    if (singleFloorMatch) {
        const floor = parseInt(singleFloorMatch[1], 10);
        raw = `${floor}층`;
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
        return {
            count: 0,
            avg: 0,
            min: 0,
            max: 0,
            trimmedAvg: 0,
            minItem: null,
            maxItem: null
        };
    }

    const prices = items
        .map(i => Number(i.pricePerPyeong) || 0)
        .sort((a, b) => a - b);

    const count = prices.length;

    // 최소/최대 매물 객체
    const minItem = items.reduce((prev, curr) =>
        prev.pricePerPyeong < curr.pricePerPyeong ? prev : curr
    );
    const maxItem = items.reduce((prev, curr) =>
        prev.pricePerPyeong > curr.pricePerPyeong ? prev : curr
    );

    // 화면 표시용 최소/최대 숫자
    const min = Number(minItem?.pricePerPyeong) || 0;
    const max = Number(maxItem?.pricePerPyeong) || 0;

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
        min: Math.round(min * 10) / 10,
        max: Math.round(max * 10) / 10,
        minItem,
        maxItem
    };
}

/**
 * 매물 목록에 평당가/평수 배지 표시
 * "월세 1,000/135 (15평/@10.3만)" 형식
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
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-left: 6px;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 700;
                line-height: 1;
                vertical-align: middle;
                white-space: nowrap;
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

    items.forEach(item => {
        // 이미 배지가 있으면 스킵
        if (item.querySelector('.naverbu-badge')) return;

        try {
            const listingData = parseListingItem(item);
            if (!listingData) return;

            // 배지 생성
            const badge = document.createElement('span');
            const isWolse = listingData.type === '월세';

            // 기본 평당가 텍스트 (예: 44.5평/@4.5만)
            let badgeText = `${listingData.area.toFixed(1)}평/@${listingData.pricePerPyeong}만`;

            // 월세인 경우 환산 매매가 추가 여부 판단
            const currentTabGubun = getSelectedTabGubun();
            const showConvertedPrice = shouldShowWolseConvertedPrice(currentTabGubun);
            if (isWolse && showConvertedPrice) {
                // 🔥 층 정보 기반 수익률 적용
                const floorInfo = extractFloorInfo(listingData.floor);

                // 기본 6% (200)
                let multiplier = 200;

                // 🔥 1층, 2층 → 5% 적용 (240)
                if (floorInfo && (floorInfo.category === '1층' || floorInfo.category === '2층')) {
                    multiplier = 240;
                }

                // 🔥 환산가 계산
                const convertedPrice = listingData.price * multiplier;

                let priceLabel = "";

                // 2. '2.4억' 또는 '9,000만' 형태로 포맷팅
                if (convertedPrice >= 10000) {
                    const ukValue = convertedPrice / 10000;
                    priceLabel = `${Number(ukValue.toFixed(2))}억`;
                } else {
                    priceLabel = `${formatNumber(convertedPrice)}만`;
                }

                // 3. 상가 탭에서만 표시
                badgeText += ` >> ${priceLabel}`;
            }

            // 1. 배지 텍스트 생성을 위한 변수 설정
            badge.className = `naverbu-badge naverbu-badge--${isWolse ? 'wolse' : 'maemae'}`;
            badge.textContent = badgeText;

            // 배지 삽입 위치 결정
            if (isNewVersion()) {
                // 신 버전: 가격 텍스트(매매/월세)를 포함하는 요소 찾아서 그 옆에 삽입
                let priceEl = null;

                // 방법 1: 카드 내 모든 요소 중 가격 패턴을 가진 요소 찾기
                const allElements = item.querySelectorAll('*');
                for (const el of allElements) {
                    // 자식 요소 없이 직접 텍스트만 가진 요소 중 가격 패턴 매칭
                    if (el.children.length === 0 || el.childNodes.length <= 3) {
                        const text = el.textContent.trim();
                        if (/^(매매|월세)\s/.test(text) && text.length < 30) {
                            priceEl = el;
                            break;
                        }
                    }
                }

                // 방법 2: 텍스트 노드에서 직접 찾기
                if (!priceEl) {
                    const walker = document.createTreeWalker(item, NodeFilter.SHOW_TEXT);
                    while (walker.nextNode()) {
                        const text = walker.currentNode.textContent.trim();
                        if (/^(매매|월세)/.test(text)) {
                            priceEl = walker.currentNode.parentElement;
                            break;
                        }
                    }
                }

                if (priceEl) {
                    // 가격 범위(~)가 있으면 스킵 (중개사별 다른 가격)
                    if (priceEl.textContent.includes('~')) return;
                    // 가격 요소 옆에 배지 삽입 (inline으로)
                    priceEl.style.display = priceEl.style.display || '';
                    priceEl.appendChild(badge);
                    addedCount++;
                }
            } else {
                // 구 버전: .price_line, .item_price, .price 요소
                const priceEl = item.querySelector('.price_line, .item_price, .price');
                if (priceEl) {
                    priceEl.appendChild(badge);
                    addedCount++;
                }
            }
        } catch (e) {
            console.warn('배지 추가 실패:', e);
        }
    });

    return addedCount;
}


function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function getExpectedArticleCount() {
    // fin.land 기준: "매물 101개"
    const titleCandidates = document.querySelectorAll(
        '.ArticleList_title___lkQ8, [class*="ArticleList_title"], h2, h3'
    );

    for (const el of titleCandidates) {
        const text = (el.textContent || '').trim();
        const match = text.match(/매물\s*([\d,]+)\s*개/);
        if (match) {
            return parseInt(match[1].replace(/,/g, ''), 10) || 0;
        }
    }

    return 0;
}


function shouldAutoExpandListings() {
    if (!isNewVersion()) return false;
    if (isAutoExpandingListings) return false;

    const expectedCount = getExpectedArticleCount();
    const currentItems = findListingItems().length;

    // 총건수가 확인되고, 실제 렌더링 수가 더 적으면 자동 펼치기 필요
    if (expectedCount > 0 && currentItems > 0 && currentItems < expectedCount) {
        return true;
    }

    return false;
}

async function ensureListingsFullyLoaded(triggerReason = 'unknown') {
    if (!isNewVersion()) return;
    if (isAutoExpandingListings) return;

    const expectedCount = getExpectedArticleCount();
    const currentCount = findListingItems().length;

    if (!(expectedCount > 0 && currentCount > 0 && currentCount < expectedCount)) {
        return;
    }

    // 같은 목록에 대해 중복 실행 방지
    const listKey = `${location.href}|${expectedCount}`;
    if (lastExpandedListKey === listKey && currentCount >= expectedCount) {
        return;
    }

    console.log(`📂 자동 전체 펼치기 시작 [${triggerReason}] ${currentCount}/${expectedCount}`);

    isAutoExpandingListings = true;
    try {
        await autoScrollToLoadAllListings();

        const finalCount = findListingItems().length;
        console.log(`✅ 자동 전체 펼치기 완료: ${finalCount}/${expectedCount}`);

        if (finalCount >= expectedCount) {
            lastExpandedListKey = listKey;
        }

        // 펼친 뒤 다시 배지/분석 갱신
        const added = addBadgesToListings();
        if (added > 0) {
            console.log(`🏷️ 자동 펼치기 후 ${added}개 배지 추가`);
        }
        sendAnalysisToPanel();
    } catch (e) {
        console.warn('자동 전체 펼치기 실패:', e);
    } finally {
        isAutoExpandingListings = false;
    }
}


// 매물 목록이 동적으로 로딩되는 경우, 자동으로 스크롤하여 전체 매물 로딩 유도
async function autoScrollToLoadAllListings() {
    console.log('🔄 전체 매물 로딩용 자동 스크롤 시작');

    let scrollContainer =
        document.querySelector('#article_list [class*="ScrollBox_scroller"]') ||
        document.querySelector('#article_list');

    if (!scrollContainer) {
        scrollContainer =
            document.querySelector('.item_list.item_list--article') ||
            document.querySelector('.list_contents') ||
            document.scrollingElement ||
            document.documentElement;
    }

    if (!scrollContainer) {
        console.warn('⚠️ 스크롤 컨테이너를 찾지 못했습니다.');
        return;
    }

    const expectedCount = getExpectedArticleCount();
    let prevCount = 0;
    let stableCount = 0;
    let prevScrollTop = -1;

    const maxRounds = 80;
    const waitMs = 400;

    for (let i = 0; i < maxRounds; i++) {
        const itemsBefore = findListingItems();
        const currentCount = itemsBefore.length;

        console.log(`📦 현재 매물 수: ${currentCount}${expectedCount ? '/' + expectedCount : ''} / round=${i + 1}`);

        // 목표치 도달 시 종료
        if (expectedCount > 0 && currentCount >= expectedCount) {
            console.log(`✅ 목표 매물 수 도달: ${currentCount}/${expectedCount}`);
            break;
        }

        const loader = document.querySelector('.loader');
        if (loader) {
            loader.scrollIntoView({ behavior: 'auto', block: 'center' });
        } else {
            scrollContainer.scrollTop = scrollContainer.scrollHeight;

            const items = findListingItems();
            const lastItem = items[items.length - 1];
            if (lastItem) {
                lastItem.scrollIntoView({ behavior: 'auto', block: 'end' });
            }
        }

        await delay(waitMs);

        const itemsAfter = findListingItems();
        const newCount = itemsAfter.length;
        const newScrollTop = scrollContainer.scrollTop;

        if (newCount === prevCount && newScrollTop === prevScrollTop) {
            stableCount += 1;
        } else {
            stableCount = 0;
        }

        prevCount = newCount;
        prevScrollTop = newScrollTop;

        if (expectedCount > 0) {
            if (newCount >= expectedCount) {
                console.log(`✅ 전체 매물 로딩 완료: ${newCount}/${expectedCount}`);
                break;
            }

            if (stableCount >= 4) {
                console.log(`⚠️ 안정화 종료: ${newCount}/${expectedCount}`);
                break;
            }
        } else {
            if (stableCount >= 3) {
                console.log(`✅ 전체 매물 로딩 완료 추정: ${newCount}개`);
                break;
            }
        }
    }

    // 목록 상단 복귀
    scrollContainer.scrollTop = 0;
    const firstItem = findListingItems()[0];
    if (firstItem) {
        firstItem.scrollIntoView({ behavior: 'auto', block: 'start' });
    }

    await delay(300);
}

/**
 * 숫자 포맷팅 (천단위 콤마)
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * 현재 선택 지역 추출
 * 우선순위:
 * 1. 기존 new.land 스타일: .filter_region_inner span.area.is-selected
 * 2. 선택 chip / breadcrumb / aria-selected 요소
 */
function getSelectedRegionInfo() {
    let regions = [];
    // 신 버전: fin.land.naver.com - 선택된 지역 정보는 breadcrumb 또는 chip 형태로 존재할 수 있음
    if (isNewVersion()) {
        //regions = ['경기도', '김포시', '구래동'];
        const el = document.querySelector('.ChipsItem-module_text__NCP3f > div');
        if (el) {
            const text = el.textContent.trim(); // "김포시 운양동"
            const [sigungu, umdNm] = text.split(' ');

            return {
                region: '',   // 필요시 따로 처리
                sigungu,
                umdNm
            };
        }
    } else {
        // 구 버전: new.land.naver.com - .filter_region_inner 내 .area.is-selected 클래스
        const container = document.querySelector('.filter_region_inner');
        if (!container) {
            console.error('filter_region_inner 요소를 찾을 수 없습니다.');
            return { region: null, sigungu: null, umName: null };
        }

        // .area.is-selected 클래스를 가진 모든 span 요소 선택
        const spans = container.querySelectorAll('span.area.is-selected');

        // 각 span에서 첫 번째 텍스트 노드(아이콘 등 제외)를 가져옵니다.
        regions = Array.from(spans).map(span => {
            // textContent 사용 시 자식 요소의 텍스트까지 모두 포함되므로
            // childNodes[0]를 이용하여 첫 번째 텍스트 노드만 취득합니다.
            const textNode = span.childNodes[0];
            return textNode ? textNode.nodeValue.trim() : "";
        });
    }

  return {
    region: regions[0] || null,
    sigungu: regions[1] || null,
    umdNm: regions[2] || null
  };
}

/**
 * 신버전(fin.land) 매물 목록의 propertyType 기준으로 탭 구분 집계
 * 리턴 예:
 * {
 *   apt: 10,
 *   villa: 3,
 *   sanga: 7
 * }
 */
function getFinPropertyTypeTabGubunCounts() {
    const counts = {
        apt: 0,
        villa: 0,
        sanga: 0
    };

    const items = findListingItems();
    if (!items || items.length === 0) {
        return counts;
    }

    items.forEach(item => {
        try {
            const listingData = parseListingItem(item);
            if (!listingData || !listingData.propertyType) return;

            const detected = detectTabGubunFromText(listingData.propertyType);
            if (detected && counts.hasOwnProperty(detected)) {
                counts[detected] += 1;
            }
        } catch (e) {
            // 개별 파싱 실패는 무시
        }
    });

    return counts;
}

/**
 * count 집계 결과에서 탭 구분 1개 선택
 * 1차 단순 우선순위: sanga -> villa -> apt
 */
function pickSingleTabGubunFromCounts(counts) {
    if (counts.sanga > 0) return 'sanga';
    if (counts.villa > 0) return 'villa';
    if (counts.apt > 0) return 'apt';
    return '';
}

/**
 * 현재 선택된 부동산 탭 구분 추출
 * 리턴값: 'apt' | 'villa' | 'sanga' | ''
 */
function getSelectedTabGubun() {
    // ==================================================
    // 1) 구버전(new.land.naver.com)
    // 기존 탭 DOM 기준 처리
    // ==================================================
    if (!isNewVersion()) {
        const oldTabs = document.querySelectorAll('.lnb_wrap .lnb_item');

        for (const tab of oldTabs) {
            if (tab.getAttribute('aria-selected') === 'true') {
                const controls = tab.getAttribute('aria-controls');
                const text = (tab.textContent || '').trim();

                switch (controls) {
                    case 'tab1':
                        return 'apt';
                    case 'tab2':
                        return 'villa';
                    case 'tab4':
                        return 'sanga';
                    default: {
                        const detected = detectTabGubunFromText(text);
                        if (detected) return detected;
                    }
                }
            }
        }

        // 구버전 URL 기반 보조 판별
        const url = location.href.toLowerCase();
        const path = location.pathname.toLowerCase();

        if (path.startsWith('/complexes') || url.includes('/complex/')) {
            return 'apt';
        }
        if (path.startsWith('/houses') || url.includes('/house/')) {
            return 'villa';
        }
        if (path.startsWith('/offices') || url.includes('/office/')) {
            return 'sanga';
        }

        return '';
    }

    // ==================================================
    // 2) 신버전(fin.land.naver.com)
    // parseListingItem() 에서 구한 propertyType 기준 처리
    // ==================================================
    const finCounts = getFinPropertyTypeTabGubunCounts();
    console.log('== fin propertyType group counts:', finCounts);

    /**
     * count 집계 결과에서 탭 구분 1개 선택
     * 1차 단순 우선순위: sanga -> villa -> apt
     */
    const picked = pickSingleTabGubunFromCounts(finCounts);
    if (picked) {
        return picked;
    }

    return '';
}

/**
 * 탭 문자열을 보고 apt / villa / sanga 판별
 */
function detectTabGubunFromText(text) {
    const normalized = (text || '').replace(/\s+/g, '').toLowerCase();

    // 아파트 계열
    if (
        normalized.includes('아파트') ||
        normalized.includes('오피스텔') ||
        normalized.includes('아파트분양권') ||
        normalized.includes('apt') ||
        normalized.includes('officetel') ||
        normalized.includes('complex')
    ) {
        return 'apt';
    }

    // 빌라/주택 계열
    if (
        normalized.includes('빌라') ||
        normalized.includes('연립') ||
        normalized.includes('빌라/연립') ||
        normalized.includes('다세대') ||
        normalized.includes('단독') ||
        normalized.includes('다가구') ||
        normalized.includes('단독/다가구') ||
        normalized.includes('원룸') ||
        normalized.includes('전원주택') ||
        normalized.includes('상가주택') ||
        normalized.includes('다중주택') ||
        normalized.includes('villa') ||
        normalized.includes('house')
    ) {
        return 'villa';
    }

    // 상가 계열
    if (
        normalized.includes('상가') ||
        normalized.includes('상가점포') ||
        normalized.includes('사무실') ||
        normalized.includes('공장') ||
        normalized.includes('창고') ||
        normalized.includes('지식산업센터') ||
        normalized.includes('건물') ||
        normalized.includes('상가건물') ||
        normalized.includes('빌딩') ||
        normalized.includes('토지') ||
        normalized.includes('office') ||
        normalized.includes('factory') ||
        normalized.includes('warehouse') ||
        normalized.includes('sanga')
    ) {
        return 'sanga';
    }

    return '';
}



/**
 * 월세 배지에 환산가(>> 2.4억)를 붙일지 여부
 * - apt  : 제거
 * - villa: 제거
 * - sanga: 유지
 */
function shouldShowWolseConvertedPrice(tabGubun) {
    return tabGubun === 'sanga';
}

// 탱크옥션 페이지 내 매물 정보 변경 감지하여 자동 분석 트리거 (300ms 디바운스)
function observeMutationsTank() {
    const targetNode = document.body;
    if (!targetNode) return;

    const config = { childList: true, subtree: true };

    const callback = function(mutationsList) {
        for (const mutation of mutationsList) {
            if (mutation.type === 'childList') {
                clearTimeout(analysisDebounceTimer);
                analysisDebounceTimer = setTimeout(() => {
                    extractPropertyInfoTank();
                }, 300);
                break;
            }
        }
    };

    const observer = new MutationObserver(callback);
    observer.observe(targetNode, config);
}

// 탱크옥션 페이지에서 매물 정보 추출하여 평당가 계산 후 DOM에 표시
function extractPropertyInfoTank() {
    const tbody = document.querySelector('#lsTbody');
    if (!tbody) return;

    const propertyItems = tbody.querySelectorAll('tr');
    if (!propertyItems.length) return;

    propertyItems.forEach((item) => {
        let areaPy = 0;

        const areaElements = item.querySelectorAll('.blue, .blue.f12');
        areaElements.forEach(el => {
            const areaText = el.textContent.trim();

            const buildingMatch = areaText.match(/건물[^㎡]*\d+\.?\d*㎡\((\d+\.?\d*)평\)/);
            if (buildingMatch && !areaPy) {
                areaPy = parseFloat(buildingMatch[1]);
            }

            const landMatch = areaText.match(/토지[^㎡]*\d+\.?\d*㎡\((\d+\.?\d*)평\)/);
            if (landMatch && !areaPy) {
                areaPy = parseFloat(landMatch[1]);
            }
        });

        if (!areaPy) return;

        const price1Element = item.querySelector('[id^="apslAmt_"]');
        const price2Element = item.querySelector('[id^="minbAmt"]');

        if (!price1Element || !price2Element) return;
        if (price1Element.dataset.highlighted) return;

        const price1Text = price1Element.textContent.trim().replace(/,/g, '');
        const price2Text = price2Element.textContent.trim().replace(/,/g, '');

        const price1num = parseInt(price1Text, 10);
        const price2num = parseInt(price2Text, 10);

        if (!price1num || !price2num) return;

        const pydanga1 = parseInt(price1num / (areaPy * 10000), 10);
        const pydanga2 = parseInt(price2num / (areaPy * 10000), 10);

        const lineBreakSpan = document.createElement('span');
        lineBreakSpan.innerHTML = '<br>';

        const lineBreakSpan2 = document.createElement('span');
        lineBreakSpan2.innerHTML = '<br>';

        const pydanga1Span = document.createElement('span');
        pydanga1Span.textContent = `@${pydanga1}만원`;
        pydanga1Span.style.opacity = '0.5';
        pydanga1Span.style.color = 'red';

        const pydanga2Span = document.createElement('span');
        pydanga2Span.textContent = `@${pydanga2}만원`;
        pydanga2Span.style.opacity = '0.5';
        pydanga2Span.style.color = 'green';

        price1Element.appendChild(lineBreakSpan);
        price1Element.appendChild(pydanga1Span);

        price2Element.appendChild(lineBreakSpan2);
        price2Element.appendChild(pydanga2Span);

        price1Element.dataset.highlighted = 'true';
    });
}

// 탱크옥션 페이지에서 매물 정보 변경 감지하여 평당가 자동 계산 트리거 (300ms 디바운스)
// 경매와 공매를 구분해서 적용처리함.
function extractPropertyInfoDetailTank() {
    console.log('🏛️ 탱크옥션 상세분석 및 데이터 전송 로직 시작');

    let areaPy = 0;
    let appraisalPrice = ""; // 감정가 저장용
    let minimumPrice = "";   // 최저가 저장용

    const tbody = document.querySelector('.Btbl_list');
    if (!tbody) return;

    const thList = tbody.querySelectorAll('th');
    console.log('[TankAuction] thList count:', thList.length);

    // 1. 면적 추출 (평당가 계산용)
    for (const headerCell of thList) {
        const isLand = headerCell.textContent.includes('토지면적');
        const isBuilding = headerCell.textContent.includes('건물면적');

        if (isLand || isBuilding) {
            const areaEl = headerCell.nextElementSibling;
            if (!areaEl) continue;

            const content = areaEl.innerHTML.trim();
            const lines = content.split(/<br\s*\/?>/i);
            const regex = /\((\d+\.\d+)평\)/;

            lines.forEach(part => {
                const match = part.match(regex);
                if (match) areaPy = parseFloat(match[1]);
            });
        }
    }

    // 2. 가격 정보 추출 및 화면 표시
    for (const headerCell of thList) {
        // 감정가 추출
        if (headerCell.textContent.includes('감정가')) {
            const price1Element = headerCell.nextElementSibling;
            if (!price1Element) continue;

            appraisalPrice = price1Element.textContent.trim().replace(/[,원]/g, '');

            if (!price1Element.dataset.highlighted) {
                const price1num = parseInt(appraisalPrice, 10);
                if (areaPy > 0) {
                    const pydanga1 = parseInt(price1num / (areaPy * 10000), 10);
                    price1Element.innerHTML += `<br><span style="opacity:0.5; color:red;">@${pydanga1}만원</span>`;
                }
                price1Element.dataset.highlighted = 'true';
            }
        }

        // 최저가 추출
        if (headerCell.textContent.includes('최저가')) {
            const price2Element = headerCell.nextElementSibling;
            if (!price2Element) continue;

            minimumPrice = price2Element.textContent.trim().replace(/\(\d+%\)\s*/g, '').replace(/[,원]/g, '');

            if (!price2Element.dataset.priceCalculated) {
                const price2num = parseInt(minimumPrice, 10);
                if (areaPy > 0) {
                    const pydanga2 = parseInt(price2num / (areaPy * 10000), 10);
                    price2Element.innerHTML += `<br><span style="opacity:0.5; color:green;">@${pydanga2}만원</span>`;
                }
                price2Element.dataset.priceCalculated = 'true';
            }
        }
    }

    // 3. 물건종류 추출
    let objectType = "";
    const objectTypeSpan = document.querySelector('span.viewobject');
    if (objectTypeSpan) {
        objectType = objectTypeSpan.textContent.trim();
    }

    // 4. 경매/공매 구분
    const viewTitle = document.querySelector('#lyCnt_num .viewtitle.clear, .viewtitle.clear');
    const viewTitleText = viewTitle ? viewTitle.textContent.replace(/\s+/g, ' ').trim() : "";
    const isPublicSale = viewTitleText.includes('공매');
    const isAuction = viewTitleText.includes('경매');

    console.log('[TankAuction] viewTitleText:', viewTitleText);
    console.log('[TankAuction] isAuction:', isAuction, 'isPublicSale:', isPublicSale);

    let addrDiv = null;
    let addrSpan = null;
    let existingBtn = null;
    let fullAddr = "";
    let searchAddr = "";
    let newAddr = "";

    // =========================
    // 4-1. 경매 주소 처리
    // =========================
    if (isAuction) {
        addrDiv = document.querySelector('div[style*="padding:5px 0 10px"]');
        console.log('[TankAuction] auction addrDiv:', addrDiv);

        if (!addrDiv) return;

        addrSpan = addrDiv.querySelector('span.bold');
        console.log('[TankAuction] auction addrSpan:', addrSpan);

        if (!addrSpan) return;

        fullAddr = addrSpan.textContent.trim();
        searchAddr = fullAddr.split(',')[0].trim();

        const roadAddrSpan = Array.from(addrDiv.querySelectorAll('span')).find(span =>
            span.textContent.includes('도로명주소:')
        );

        if (roadAddrSpan) {
            const match = roadAddrSpan.textContent.match(/도로명주소:\s*([^)]+)/);
            if (match) {
                newAddr = match[1].trim();
            }
        }

        existingBtn = addrDiv.querySelector('.button');
    }

    // =========================
    // 4-2. 공매 주소 처리
    // =========================
    else if (isPublicSale) {
        const lyCntNum = document.querySelector('#lyCnt_num');
        console.log('[TankAuction] public sale lyCntNum:', lyCntNum);

        if (!lyCntNum) return;

        const candidateDivs = Array.from(lyCntNum.querySelectorAll('div'));
        addrDiv = candidateDivs.find(div => {
            const text = div.textContent.replace(/\s+/g, ' ').trim();
            return text.includes('도로명주소:') && !text.includes('매각일자');
        });

        console.log('[TankAuction] public sale addrDiv:', addrDiv);

        if (!addrDiv) return;

        const spans = addrDiv.querySelectorAll('span');
        addrSpan = Array.from(spans).find(span => {
            const text = span.textContent.replace(/\s+/g, ' ').trim();
            return text && !text.includes('도로명주소:');
        });

        console.log('[TankAuction] public sale addrSpan:', addrSpan);

        if (!addrSpan) return;

        fullAddr = addrSpan.textContent.trim();
        searchAddr = fullAddr.split(',')[0].trim();

        const roadAddrSpan = Array.from(spans).find(span =>
            span.textContent.includes('도로명주소:')
        );

        if (roadAddrSpan) {
            const match = roadAddrSpan.textContent.match(/도로명주소:\s*([^\]]+)/);
            if (match) {
                newAddr = match[1].trim();
            } else {
                newAddr = roadAddrSpan.textContent
                    .replace('[', '')
                    .replace(']', '')
                    .replace('도로명주소:', '')
                    .trim();
            }
        }

        existingBtn = addrSpan;
    } else {
        console.log('[TankAuction] 경매/공매 구분 실패');
        return;
    }

    console.log('[TankAuction] fullAddr:', fullAddr);
    console.log('[TankAuction] searchAddr:', searchAddr);
    console.log('[TankAuction] newAddr:', newAddr);

    // 중복 추가 방지
    if (addrDiv.querySelector('.naver-forward-btn')) return;

    const naverBtn = document.createElement('span');
    naverBtn.className = 'button btn_small btn_white naver-forward-btn';
    naverBtn.style.cssText = 'margin-left:5px; cursor:pointer; color:#03cf5d; font-weight:bold;';
    naverBtn.textContent = '랜드코어 이동';

    // 5. 클릭 이벤트: 추출된 모든 정보를 파라미터로 전달
    naverBtn.onclick = function() {
        const serverUrl = `https://www.landcore.co.kr/api/ext_tool/forward-map`;

        const form = document.createElement('form');
        form.method = 'POST';
        form.action = serverUrl;
        form.target = '_blank';
        form.acceptCharset = "UTF-8";

        const data = {
            address: searchAddr,
            addressRoad: newAddr,
            objectType: objectType,
            appraisalPrice: appraisalPrice,
            minimumPrice: minimumPrice
        };
        console.log("== extractPropertyInfoDetailTank data", data);

        for (const key in data) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = data[key];
            form.appendChild(input);
        }

        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
    };

    // 버튼 삽입
    if (isAuction) {
        if (existingBtn) {
            existingBtn.parentNode.insertBefore(naverBtn, existingBtn.nextSibling);
        } else {
            addrSpan.insertAdjacentElement('afterend', naverBtn);
        }
    } else if (isPublicSale) {
        addrSpan.insertAdjacentElement('afterend', naverBtn);
    }
}


/**
 * [추가] 옥션원 상세페이지 정보 추출 함수
 * 탱크옥션의 extractPropertyInfoDetailTank 로직을 참조함
 */
function extractPropertyInfoDetailAuctionOne() {
    const auctionContainer = document.getElementById('auction_container');
    if (!auctionContainer) return;

    // ------------------------------------------------------------------
    // 1. 물건종별 추출 : "물건종별" th 다음 td 에서 값 읽기
    // ------------------------------------------------------------------
    let objectType = "";
    const thList = auctionContainer.querySelectorAll('th');

    thList.forEach((th) => {
        const thText = th.textContent.replace(/\s+/g, '').trim();

        if (thText === '물건종별') {
            const td = th.nextElementSibling;
            if (td) {
                // 전체 텍스트를 가져온 뒤 괄호()나 대괄호[] 및 그 안의 내용을 모두 제거
                let rawType = td.textContent.replace(/\s+/g, ' ').trim();

                // 정규식 설명:
                // 1. [\(|\[].*?[\)|\]] : ( ) 또는 [ ]로 감싸진 모든 문자를 찾아 제거
                // 2. .trim() : 앞뒤 공백 제거
                objectType = rawType.replace(/[\(|\[].*?[\)|\]]/g, '').trim();
            }
        }
    });

    // ------------------------------------------------------------------
    // 2. 감정가 추출 : "감 정 가" th 다음 td
    // ------------------------------------------------------------------
    let appraisalPrice = "";

    thList.forEach((th) => {
        const thText = th.textContent.replace(/\s+/g, '').trim();
        if (thText === '감정가') {
            const td = th.nextElementSibling;
            if (td) {
                const raw = td.textContent;
                appraisalPrice = extractPriceOnly(raw);
            }
        }
    });

    // ------------------------------------------------------------------
    // 3. 최저가 추출 : "최 저 가" th 다음 td
    // ------------------------------------------------------------------
    let minimumPrice = "";

    thList.forEach((th) => {
        const thText = th.textContent.replace(/\s+/g, '').trim();
        if (thText === '최저가') {
            const td = th.nextElementSibling;
            if (td) {
                const raw = td.textContent;
                minimumPrice = extractPriceOnly(raw);
            }
        }
    });

        // ------------------------------------------------------------------
    // 5. 새주소 문자열 추출
    // ------------------------------------------------------------------
    let searchAddr = "";

    // "소 재 지" th 찾기
    thList.forEach((th) => {
        const thText = th.textContent.replace(/\s+/g, '').trim();

        if (thText === '소재지') {
            const td = th.nextElementSibling;
            if (td) {
                // addr_view_1 중 첫번째만
                const addrSpan = td.querySelector('.addr_view_1');
                if (addrSpan) {
                    searchAddr = addrSpan.textContent.trim();
                }
            }
        }
    });

    // ------------------------------------------------------------------
    // 4. "새 주소" 행 찾기
    // ------------------------------------------------------------------
    let newAddr = "";
    let newAddressTd = null;
    thList.forEach((th) => {
        const thText = th.textContent.replace(/\s+/g, '').trim();

        if (thText === '새주소') {
            newAddressTd = th.nextElementSibling;
            if (newAddressTd) {
                // addr_view_1 중 첫번째만
                const addrSpan = newAddressTd.querySelector('.addr_view_1');
                if (addrSpan) {
                    newAddr = addrSpan.textContent.trim();
                }
            }
        }
    });

    // ------------------------------------------------------------------
    // 5. 버튼 삽입 위치 찾기 (주소복사 버튼 뒤)
    // ------------------------------------------------------------------
    // HTML에 있는 <button class="copyBtn" title="주소복사"> 를 찾습니다.
    const copyBtn = auctionContainer.querySelector('.copyBtn');

    // ------------------------------------------------------------------
    // 7. 버튼 생성
    // ------------------------------------------------------------------
    const naverBtn = document.createElement('span');
    naverBtn.className = 'button btn_small btn_white naver-forward-btn';
    naverBtn.style.cssText = 'margin-left:5px; cursor:pointer; color:#03cf5d; font-weight:bold;';
    naverBtn.textContent = '랜드코어 이동';

    // ------------------------------------------------------------------
    // 8. 클릭 이벤트
    // ------------------------------------------------------------------
    naverBtn.onclick = function () {
        const serverUrl = 'https://www.landcore.co.kr/api/ext_tool/forward-map';

        const form = document.createElement('form');
        form.method = 'POST';
        form.action = serverUrl;
        form.target = '_blank';
        form.acceptCharset = "UTF-8";

        // address: 지번주소, address_road: 새주소
        const data = {
            address: searchAddr,
            address_road: newAddr,
            objectType: objectType,
            appraisalPrice: appraisalPrice,
            minimumPrice: minimumPrice
        };

        console.log("== extractPropertyInfoDetailAuctionOne data", data)

        for (const key in data) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = data[key];
            form.appendChild(input);
        }

        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
    };

    // ------------------------------------------------------------------
    // 8. 주소복사 버튼 바로 뒤에 버튼 추가
    // ------------------------------------------------------------------
    if (copyBtn) {
        // copyBtn의 부모 안에서 copyBtn 다음 형제 요소로 삽입
        copyBtn.parentNode.insertBefore(naverBtn, copyBtn.nextSibling);
    }

    // ------------------------------------------------------------------
    // 9. 새주소 뒤에 버튼 추가 (이거하면 위 버튼도 안나옴 ㅠ.ㅠ)
    // ------------------------------------------------------------------
    // if (newAddressTd) {
    //     newAddressTd.appendChild(naverBtn);
    // }
}

/**
 * [추가] GG옥션 상세페이지 정보 추출 함수
 */
function extractPropertyInfoDetailGGAuction() {
    console.log('[GGAuction] start');

    // ------------------------------------------------------------
    // 0. 기준 DOM 찾기
    // auction_container 가 아니라 courtInfo_btn 이 들어있는 table 기준
    // ------------------------------------------------------------
    const courtInfoBtn = document.querySelector('#courtInfo_btn');
    console.log('[GGAuction] courtInfoBtn:', courtInfoBtn);

    if (!courtInfoBtn) {
        console.warn('[GGAuction] courtInfoBtn not found');
        return false;
    }

    const rootTable = courtInfoBtn.closest('table');
    console.log('[GGAuction] rootTable:', rootTable);

    if (!rootTable) {
        console.warn('[GGAuction] rootTable not found');
        return false;
    }

    const thList = rootTable.querySelectorAll('th');
    console.log('[GGAuction] thList count:', thList.length);

    // ------------------------------------------------------------
    // 공통 유틸
    // ------------------------------------------------------------
    const normalize = (text) => (text || '').replace(/\s+/g, '').trim();
    const cleanText = (text) => (text || '').replace(/\s+/g, ' ').trim();

    const getTdByThText = (label) => {
        const target = normalize(label);
        console.log(`[GGAuction] getTdByThText start: ${label}`);

        for (const th of thList) {
            const currentTh = normalize(th.textContent);
            if (currentTh === target) {
                console.log(`[GGAuction] getTdByThText found: ${label}`, th.nextElementSibling);
                return th.nextElementSibling;
            }
        }

        console.warn(`[GGAuction] getTdByThText not found: ${label}`);
        return null;
    };

    // "44,541,117,000원(25.03.18)" -> "44,541,117,000"
    const extractPriceWithoutWon = (raw) => {
        if (!raw) {
            console.warn('[GGAuction] extractPriceWithoutWon raw empty');
            return '';
        }

        const text = cleanText(raw);
        const match = text.match(/[\d,]+(?=원)/);
        const result = match ? match[0] : '';
        console.log('[GGAuction] extractPriceWithoutWon:', { raw, cleaned: text, result });
        return result;
    };

    // ------------------------------------------------------------
    // 1. 소재지
    // ------------------------------------------------------------
    console.log('[GGAuction] 소재지 step start');

    let searchAddr = '';
    const sojajiTd = getTdByThText('소재지');
    console.log('[GGAuction] 소재지 td:', sojajiTd);

    if (sojajiTd) {
        const addrEl =
            sojajiTd.querySelector('span.mr-4') ||
            sojajiTd.querySelector('span');

        console.log('[GGAuction] 소재지 addrEl:', addrEl);

        if (addrEl) {
            searchAddr = cleanText(addrEl.textContent);
        } else {
            searchAddr = cleanText(sojajiTd.textContent);
        }
    }

    console.log('[GGAuction] 소재지 result:', searchAddr);

    // ------------------------------------------------------------
    // 2. 도로명주소 -> 새주소
    // ------------------------------------------------------------
    console.log('[GGAuction] 도로명주소 step start');

    let newAddr = '';
    const roadAddrTd = getTdByThText('도로명주소');
    console.log('[GGAuction] 도로명주소 td:', roadAddrTd);

    if (roadAddrTd) {
        newAddr = cleanText(roadAddrTd.textContent);
    }

    console.log('[GGAuction] 도로명주소 result:', newAddr);

    // ------------------------------------------------------------
    // 3. 용도 -> objectType
    // ------------------------------------------------------------
    console.log('[GGAuction] 용도 step start');

    let objectType = '';
    const objectTypeTd = getTdByThText('용도');
    console.log('[GGAuction] 용도 td:', objectTypeTd);

    if (objectTypeTd) {
        objectType = cleanText(objectTypeTd.textContent)
            .replace(/[\(\[].*?[\)\]]/g, '')
            .trim();
    }

    console.log('[GGAuction] 용도 result:', objectType);

    // ------------------------------------------------------------
    // 4. 감정가
    // ------------------------------------------------------------
    console.log('[GGAuction] 감정가 step start');

    let appraisalPrice = '';
    const appraisalTd = getTdByThText('감정가');
    console.log('[GGAuction] 감정가 td:', appraisalTd);

    if (appraisalTd) {
        const priceEl =
            appraisalTd.querySelector('span.font-bold') ||
            appraisalTd.querySelector('span');

        console.log('[GGAuction] 감정가 priceEl:', priceEl);

        appraisalPrice = extractPriceWithoutWon(
            priceEl ? priceEl.textContent : appraisalTd.textContent
        );
    }

    console.log('[GGAuction] 감정가 result:', appraisalPrice);

    // ------------------------------------------------------------
    // 5. 최저가
    // ------------------------------------------------------------
    console.log('[GGAuction] 최저가 step start');

    let minimumPrice = '';
    const minimumTd = getTdByThText('최저가');
    console.log('[GGAuction] 최저가 td:', minimumTd);

    if (minimumTd) {
        const priceEl = minimumTd.querySelector('span.font-bold, .font-bold');
        const percentEl = minimumTd.querySelector('.rounded-20');

        console.log('[GGAuction] 최저가 priceEl:', priceEl);
        console.log('[GGAuction] 최저가 percentEl:', percentEl);

        const price = extractPriceWithoutWon(
            priceEl ? priceEl.textContent : minimumTd.textContent
        );
        const percent = cleanText(percentEl ? percentEl.textContent : '');

        console.log('[GGAuction] 최저가 parsed:', { price, percent });

        if (percent && price) {
            minimumPrice = `(${percent}) ${price}`;
        } else if (price) {
            minimumPrice = price;
        }
    }

    console.log('[GGAuction] 최저가 result:', minimumPrice);

    // ------------------------------------------------------------
    // 6. 버튼 중복 방지
    // ------------------------------------------------------------
    console.log('[GGAuction] 버튼 중복체크 step start');

    if (rootTable.querySelector('#landcore_naver_forward_btn')) {
        console.warn('[GGAuction] button already exists');
        return true;
    }

    // ------------------------------------------------------------
    // 7. 버튼 생성
    // ------------------------------------------------------------
    console.log('[GGAuction] 버튼 생성 step start');

    const naverForwardBtn = document.createElement('button');
    naverForwardBtn.type = 'button';
    naverForwardBtn.id = 'landcore_naver_forward_btn';

    naverForwardBtn.className =
        'px-8 disabled:bg-secondary-5 disabled:text-font-disabled print:hidden h-24 rounded-4 body-12r';

    naverForwardBtn.textContent = '랜드코어 이동';

    // 🔥 핵심: 강제 스타일
    naverForwardBtn.style.backgroundColor = '#03C75A';
    naverForwardBtn.style.color = '#ffffff';
    naverForwardBtn.style.border = 'none';
    naverForwardBtn.style.fontWeight = 'bold';

    console.log('[GGAuction] 버튼 생성 완료:', naverForwardBtn);

    // ------------------------------------------------------------
    // 8. 클릭 이벤트
    // ------------------------------------------------------------
    naverForwardBtn.onclick = function () {
        console.log('[GGAuction] 랜드코어 이동 버튼 클릭');

        const serverUrl = 'https://www.landcore.co.kr/api/ext_tool/forward-map';

        const form = document.createElement('form');
        form.method = 'POST';
        form.action = serverUrl;
        form.target = '_blank';
        form.acceptCharset = 'UTF-8';

        const data = {
            address: searchAddr,             // 소재지
            address_road: newAddr,          // 도로명주소
            objectType: objectType,         // 용도
            appraisalPrice: appraisalPrice, // 감정가
            minimumPrice: minimumPrice      // 최저가
        };

        console.log('[GGAuction] 클릭시 전송 data:', data);

        Object.keys(data).forEach((key) => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = data[key] || '';
            form.appendChild(input);

            console.log('[GGAuction] hidden input append:', {
                key,
                value: data[key] || ''
            });
        });

        document.body.appendChild(form);
        console.log('[GGAuction] form appended, submit start');

        form.submit();

        console.log('[GGAuction] form submitted');
        document.body.removeChild(form);
        console.log('[GGAuction] form removed');
    };

    // ------------------------------------------------------------
    // 9. 관할법원 버튼 뒤에 삽입
    // ------------------------------------------------------------
    console.log('[GGAuction] 버튼 삽입 step start');

    courtInfoBtn.parentNode.insertBefore(naverForwardBtn, courtInfoBtn.nextSibling);

    console.log('[GGAuction] 버튼 삽입 완료');
    console.log('[GGAuction] end success', {
        searchAddr,
        newAddr,
        objectType,
        appraisalPrice,
        minimumPrice
    });

    return true;
}


/**
 * [추가] 두인옥션 상세페이지 정보 추출 함수
 */
function extractPropertyInfoDetailDooinAuction() {
    console.log('[DooinAuction] start');

    // ------------------------------------------------------------
    // 0. 기준 DOM 찾기
    // 두인경매 DOM: #lyCnt_base 내부 ViewTblBase 기준
    // ------------------------------------------------------------
    const root = document.querySelector('#lyCnt_base');
    console.log('[DooinAuction] root:', root);

    if (!root) {
        console.warn('[DooinAuction] #lyCnt_base not found');
        return false;
    }

    const rootTable = root.querySelector('table.ViewTblBase');
    console.log('[DooinAuction] rootTable:', rootTable);

    if (!rootTable) {
        console.warn('[DooinAuction] table.ViewTblBase not found');
        return false;
    }

    const trList = Array.from(rootTable.querySelectorAll('tr'));
    console.log('[DooinAuction] trList count:', trList.length);

    // ------------------------------------------------------------
    // 공통 유틸
    // ------------------------------------------------------------
    const normalize = (text) => (text || '').replace(/\s+/g, '').trim();
    const cleanText = (text) => (text || '').replace(/\s+/g, ' ').trim();

    const getTdByThText = (label) => {
        const target = normalize(label);
        console.log(`[DooinAuction] getTdByThText start: ${label}`);

        for (const tr of trList) {
            const thList = Array.from(tr.querySelectorAll('th'));
            for (const th of thList) {
                const currentTh = normalize(th.textContent);
                if (currentTh === target) {
                    const td = th.nextElementSibling;
                    console.log(`[DooinAuction] getTdByThText found: ${label}`, td);
                    return td;
                }
            }
        }

        console.warn(`[DooinAuction] getTdByThText not found: ${label}`);
        return null;
    };

    const getRowByThText = (label) => {
        const target = normalize(label);
        console.log(`[DooinAuction] getRowByThText start: ${label}`);

        for (const tr of trList) {
            const thList = Array.from(tr.querySelectorAll('th'));
            for (const th of thList) {
                const currentTh = normalize(th.textContent);
                if (currentTh === target) {
                    console.log(`[DooinAuction] getRowByThText found: ${label}`, tr);
                    return tr;
                }
            }
        }

        console.warn(`[DooinAuction] getRowByThText not found: ${label}`);
        return null;
    };

    // "2,963,427,520" / "2,963,427,520원" / "(24%) 711,518,000" -> 숫자만 추출
    const extractPrice = (raw) => {
        if (!raw) {
            console.warn('[DooinAuction] extractPrice raw empty');
            return '';
        }

        const text = cleanText(raw);
        const match = text.match(/[\d,]+/g);
        const result = match ? match[match.length - 1] : '';

        console.log('[DooinAuction] extractPrice:', { raw, cleaned: text, result });
        return result;
    };

    const extractPercent = (raw) => {
        if (!raw) return '';

        const text = cleanText(raw);
        const match = text.match(/\((\d+%)\)/);
        const result = match ? match[1] : '';

        console.log('[DooinAuction] extractPercent:', { raw, cleaned: text, result });
        return result;
    };

    // ------------------------------------------------------------
    // 1. 소재지 + 도로명검색 버튼
    // 핵심: 도로명주소는 별도 행이 아니라 버튼의 data-addr 에서 추출
    // ------------------------------------------------------------
    console.log('[DooinAuction] 소재지 step start');

    let searchAddr = '';
    let newAddr = '';
    let roadSearchBtn = null;

    const sojajiRow = getRowByThText('소재지');
    const sojajiTd = getTdByThText('소재지');

    console.log('[DooinAuction] 소재지 row:', sojajiRow);
    console.log('[DooinAuction] 소재지 td:', sojajiTd);

    if (sojajiTd) {
        const addrEl = sojajiTd.querySelector('span.bold');
        console.log('[DooinAuction] 소재지 addrEl:', addrEl);

        if (addrEl) {
            searchAddr = cleanText(addrEl.textContent);
        } else {
            searchAddr = cleanText(sojajiTd.textContent);
        }

        roadSearchBtn = sojajiTd.querySelector('.btn-gotoAddr[data-addr]');
        console.log('[DooinAuction] 도로명검색 버튼:', roadSearchBtn);

        if (roadSearchBtn) {
            newAddr = cleanText(roadSearchBtn.getAttribute('data-addr'));
        }
    }

    console.log('[DooinAuction] 소재지 result:', searchAddr);
    console.log('[DooinAuction] 도로명주소(data-addr) result:', newAddr);

    // ------------------------------------------------------------
    // 2. 물건종류 -> objectType
    // 기존 "용도"가 아니라 두인경매 DOM에서는 "물건종류"
    // ------------------------------------------------------------
    console.log('[DooinAuction] 물건종류 step start');

    let objectType = '';
    const objectTypeTd = getTdByThText('물건종류');
    console.log('[DooinAuction] 물건종류 td:', objectTypeTd);

    if (objectTypeTd) {
        // mobileTitle(물건종류) 문구 제외하고 실제 값만 추출
        const clonedTd = objectTypeTd.cloneNode(true);
        clonedTd.querySelectorAll('.show-mobile.mobileTitle').forEach((el) => el.remove());

        objectType = cleanText(clonedTd.textContent)
            .replace(/[\(\[].*?[\)\]]/g, '')
            .trim();
    }

    console.log('[DooinAuction] 물건종류 result:', objectType);

    // ------------------------------------------------------------
    // 3. 감정가
    // ------------------------------------------------------------
    console.log('[DooinAuction] 감정가 step start');

    let appraisalPrice = '';
    const appraisalTd = getTdByThText('감정가');
    console.log('[DooinAuction] 감정가 td:', appraisalTd);

    if (appraisalTd) {
        const priceEl = appraisalTd.querySelector('span.bold') || appraisalTd;
        console.log('[DooinAuction] 감정가 priceEl:', priceEl);

        appraisalPrice = extractPrice(priceEl.textContent);
    }

    console.log('[DooinAuction] 감정가 result:', appraisalPrice);

    // ------------------------------------------------------------
    // 4. 최저가
    // 두인경매 DOM은 "(24%) 711,518,000" 형태
    // ------------------------------------------------------------
    console.log('[DooinAuction] 최저가 step start');

    let minimumPrice = '';
    const minimumTd = getTdByThText('최저가');
    console.log('[DooinAuction] 최저가 td:', minimumTd);

    if (minimumTd) {
        const rawText = cleanText(minimumTd.textContent);
        const price = extractPrice(rawText);
        const percent = extractPercent(rawText);

        console.log('[DooinAuction] 최저가 parsed:', { rawText, price, percent });

        if (percent && price) {
            minimumPrice = `(${percent}) ${price}`;
        } else if (price) {
            minimumPrice = price;
        }
    }

    console.log('[DooinAuction] 최저가 result:', minimumPrice);

    // ------------------------------------------------------------
    // 5. 버튼 중복 방지
    // ------------------------------------------------------------
    console.log('[DooinAuction] 버튼 중복체크 step start');

    if (rootTable.querySelector('#landcore_naver_forward_btn')) {
        console.warn('[DooinAuction] button already exists');
        return true;
    }

    // ------------------------------------------------------------
    // 6. 버튼 생성
    // ------------------------------------------------------------
    console.log('[DooinAuction] 버튼 생성 step start');

    const naverForwardBtn = document.createElement('button');
    naverForwardBtn.type = 'button';
    naverForwardBtn.id = 'landcore_naver_forward_btn';
    naverForwardBtn.textContent = '랜드코어 이동'; 

    naverForwardBtn.style.display = 'inline-flex';
    naverForwardBtn.style.alignItems = 'center';
    naverForwardBtn.style.justifyContent = 'center';
    naverForwardBtn.style.height = '28px';
    naverForwardBtn.style.padding = '0 10px';
    naverForwardBtn.style.marginLeft = '6px';
    naverForwardBtn.style.border = '1px solid #03C75A';
    naverForwardBtn.style.borderRadius = '4px';
    naverForwardBtn.style.backgroundColor = '#03C75A';
    naverForwardBtn.style.color = '#ffffff';
    naverForwardBtn.style.fontSize = '12px';
    naverForwardBtn.style.fontWeight = '700';
    naverForwardBtn.style.lineHeight = '1';
    naverForwardBtn.style.cursor = 'pointer';
    naverForwardBtn.style.verticalAlign = 'middle';

    console.log('[DooinAuction] 버튼 생성 완료:', naverForwardBtn);

    // ------------------------------------------------------------
    // 7. 클릭 이벤트
    // ------------------------------------------------------------
    naverForwardBtn.onclick = function () {
        console.log('[DooinAuction] 랜드코어 이동 버튼 클릭');

        const serverUrl = 'https://www.landcore.co.kr/api/ext_tool/forward-map';

        const form = document.createElement('form');
        form.method = 'POST';
        form.action = serverUrl;
        form.target = '_blank';
        form.acceptCharset = 'UTF-8';

        const data = {
            address: searchAddr,             // 소재지
            address_road: newAddr,          // 도로명검색 버튼 data-addr
            objectType: objectType,         // 물건종류
            appraisalPrice: appraisalPrice, // 감정가
            minimumPrice: minimumPrice      // 최저가
        };

        console.log('[DooinAuction] 클릭시 전송 data:', data);

        Object.keys(data).forEach((key) => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = data[key] || '';
            form.appendChild(input);

            console.log('[DooinAuction] hidden input append:', {
                key,
                value: data[key] || ''
            });
        });

        document.body.appendChild(form);
        console.log('[DooinAuction] form appended, submit start');

        form.submit();

        console.log('[DooinAuction] form submitted');
        document.body.removeChild(form);
        console.log('[DooinAuction] form removed');
    };

    // ------------------------------------------------------------
    // 8. 소재지 row 의 도로명 검색 버튼 뒤에 삽입
    // ------------------------------------------------------------
    console.log('[DooinAuction] 버튼 삽입 step start');

    if (roadSearchBtn && roadSearchBtn.parentNode) {
        roadSearchBtn.insertAdjacentElement('afterend', naverForwardBtn);
        console.log('[DooinAuction] 도로명 검색 버튼 뒤에 삽입 완료');
    } else if (sojajiTd) {
        sojajiTd.appendChild(naverForwardBtn);
        console.log('[DooinAuction] 소재지 td 마지막에 fallback 삽입 완료');
    } else {
        console.warn('[DooinAuction] 버튼 삽입 위치를 찾지 못함');
        return false;
    }

    console.log('[DooinAuction] end success', {
        searchAddr,
        newAddr,
        objectType,
        appraisalPrice,
        minimumPrice
    });

    return true;
}

//
function extractPriceOnly(text) {
    if (!text) return "";

    text = text.replace(/\s+/g, ' ').trim();

    // (17%) 포함된 경우
    const matchWithRate = text.match(/\(\d+%\)\s*[0-9,]+/);
    if (matchWithRate) {
        return matchWithRate[0].trim();
    }

    // 일반 금액
    const matchPrice = text.match(/[0-9,]+/);
    if (matchPrice) {
        return matchPrice[0].trim();
    }

    return "";
}