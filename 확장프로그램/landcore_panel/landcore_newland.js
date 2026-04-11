/**
 * 기능:
 * 1. new.naver.com(구네이버부동산) 매물 목록에 평당가/평수 배지 자동 표시
 * 2. 매물 상세정보 팝업에서 매매가, 면적, 보증금/월세 등 핵심 정보 추출
 * 3. 네이버 자동 스크롤 및 Side Panel 에서 분석 요청 시 데이터 제공
 * ============================================
 */
let observer; // observer를 외부에서 선언
let isScheduled = false; // 함수 호출이 예약되었는지 여부를 나타내는 플래그(중복실행방지)
//
let tabGubun = '';
let access_token = ""
let apt_key = "";
let villa_key = "";
let sanga_key = "";

// config으로 만들 부분
let autoScroll = true;
let dangaAsc = true;

// ============ 상가/빌라 ==============
function loadSangaItems() {
    //
    let loadingStack = null;
	if (autoScroll) {
		loadingStack = document.querySelector('.loader');
        // loadingStack is null 이면 로딩이 다 완료되었다는 의미로 처리함.
		console.log(loadingStack);
		if (loadingStack) {
			// 해당 영역으로 스크롤
			loadingStack.scrollIntoView({ behavior: 'auto', block: 'center' });
		}
	}
    //
    const propertyItems = document.querySelectorAll('.item_inner:not(.is-loading)'); // 'is-loading' 클래스를 제외한 요소 선택
    console.log('전체 propertyItems:', propertyItems);
    if (propertyItems.length > 0) {
        // loadingStack is null => 모든게 로딩이 완료되었으면 품목소트후 재정렬처리(단가순)
        if (loadingStack == null) {
            sortSangaItems();
        }
    }
}

// div 요소들끼리 정리하는 부분
function sortSangaItems() {
    //
    const propertyLists = document.querySelectorAll('div.item.false'); // 'is-loading' 클래스를 제외한 요소 선택
    //console.log(propertyLists);
    const divs = Array.from(propertyLists); // 어레이에 맞게 정렬

    if(divs.length >0) { // 요소가 존재하는지 확인
        if (dangaAsc === true) {
            //div 요소들을 내부 텍스트 기준으로 내림차순 정렬
            divs.sort((a, b) => {
              const numA = parseFloat(a.textContent.match(/@([\d.]+)만/)?.[1] || 0);
              const numB = parseFloat(b.textContent.match(/@([\d.]+)만/)?.[1] || 0);
              return numA - numB;
            });
        } else{
            //div 요소들을 내부 텍스트 기준으로 오름차순 정렬
            divs.sort((a, b) => {
              const numA = parseFloat(a.textContent.match(/@([\d.]+)만/)?.[1] || '0');
              const numB = parseFloat(b.textContent.match(/@([\d.]+)만/)?.[1] || '0');
              return numB - numA;
            });
        }
        //
        const container = propertyLists[0].parentElement;
        container.innerHTML = ''; // 부모 요소 비우기
        //
        //리스트 패널이 완전히 로딩되었으면, 해당 패널의 스크롤 위치를 0으로 설정
        divs.forEach(div => {
            container.appendChild(div);
        });
        // 정렬된 리스트의 첫 번째 요소(0번째 위치)로 스크롤 이동
        if(divs[0]) {
            divs[0].scrollIntoView({ behavior: "smooth", block: "start" });
        }
    } else {
        console.log('no elements sorted');
    }
}

// 아파트 아이템 로드
function loadAptItems() {
    console.log('loadAptItems.. start');

    let loadingStack = null;
	if (autoScroll) {
		loadingStack = document.querySelector('.loader');
        // loadingStack is null 이면 로딩이 다 완료되었다는 의미로 처리함.
		console.log(loadingStack);
		if (loadingStack) {
			// 해당 영역으로 스크롤
			loadingStack.scrollIntoView({ behavior: 'auto', block: 'center' });
		}
	}
    //
    const propertyItems = document.querySelectorAll('.item_inner:not(.is-loading)'); // 'is-loading' 클래스를 제외한 요소 선택
    console.log('전체 propertyItems:', propertyItems);
    if (propertyItems.length > 0) {
        //sortAptItems(propertyItems);
    }
}

//============ 아파트 ==============
// div 요소들끼리 정리하는 부분
function sortAptItems(propertyItems) {
    // 1) Copy into a true Array
    const divs = Array.from(propertyItems);
    if (divs.length === 0) return;

    // 2) Define the type priority
    const typeOrder = { '매매': 0, '전세': 1, '월세': 2 };

    // 3) Helper: extract numeric amount for sorting
    function parseAmountForSort(elem) {
        const type = elem.querySelector('.price_line .type')?.textContent.trim() || '';
        const price = elem.querySelector('.price_line .price')?.textContent.trim() || '';
        const beforeParen = price.split('(')[0];
        const parts = beforeParen.split('/').map(s => s.trim());

        if (type === '매매' || type === '전세') {
          const sale = parts[0];
          const m = sale.match(/(\d+)\s*억(?:\s*([\d,]+))?/);
          if (m) {
            return parseInt(m[1],10)*10000 + (m[2] ? parseInt(m[2].replace(/,/g,''),10) : 0);
          }
          return parseFloat(sale.replace(/[^0-9.]/g,'')) || 0;
        }
        if (type === '월세') {
          const rent = parts[1] ? parts[1].replace(/[^0-9]/g,'') : '0';
          return parseInt(rent,10) || 0;
        }
        return 0;
    }

    // 4) Sort according to type priority first, then amount
    divs.sort((a, b) => {
        const tA = a.querySelector('.price_line .type')?.textContent.trim() || '';
        const tB = b.querySelector('.price_line .type')?.textContent.trim() || '';
        const pA = typeOrder[tA] ?? 99;
        const pB = typeOrder[tB] ?? 99;
        if (pA !== pB) return pA - pB;
        return parseAmountForSort(a) - parseAmountForSort(b);
    });

    // 5) Re‐append into the original container
    const container = divs[0].parentElement;
    container.innerHTML = '';
    divs.forEach(div => {
        container.appendChild(div);
    });

    // 6) Scroll first into view
    divs[0].scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function detectTabGubunFromText(text) {
    const normalized = (text || '').replace(/\s+/g, '').toLowerCase();

    if (
        normalized.includes('아파트') ||
        normalized.includes('오피스텔') ||
        normalized.includes('apt') ||
        normalized.includes('officetel') ||
        normalized.includes('complex')
    ) {
        return 'apt';
    }

    if (
        normalized.includes('빌라') ||
        normalized.includes('연립') ||
        normalized.includes('단독') ||
        normalized.includes('다가구') ||
        normalized.includes('전원주택') ||
        normalized.includes('상가주택') ||
        normalized.includes('villa') ||
        normalized.includes('house')
    ) {
        return 'villa';
    }

    if (
        normalized.includes('상가') ||
        normalized.includes('사무실') ||
        normalized.includes('공장') ||
        normalized.includes('창고') ||
        normalized.includes('지식산업센터') ||
        normalized.includes('건물') ||
        normalized.includes('office') ||
        normalized.includes('store') ||
        normalized.includes('factory') ||
        normalized.includes('warehouse') ||
        normalized.includes('sanga')
    ) {
        return 'sanga';
    }

    return '';
}

// 리스트목록 처리
function extractPropertyInfo() {
	const tabs = document.querySelectorAll('.lnb_wrap .lnb_item, [role="tab"], button[aria-selected], a[aria-current="page"]');

	tabs.forEach(tab => {
	    const isSelected =
            tab.getAttribute('aria-selected') === 'true' ||
            tab.getAttribute('aria-current') === 'page' ||
            tab.classList.contains('selected') ||
            tab.classList.contains('is_selected');

        if (!isSelected) return;

		const controls = tab.getAttribute('aria-controls');
        const tabText = (tab.textContent || '').trim();

		switch (controls) {
		  case 'tab1':
			console.log('아파트/오피스텔 탭이 선택되었습니다.');
	  		tabGubun = 'apt';
			break;

		  case 'tab2':
			console.log('빌라/주택 탭이 선택되었습니다.');
		  	tabGubun = 'villa';
			break;

		  case 'tab4':
			console.log('상가/업무/공장/토지 탭이 선택되었습니다.');
			tabGubun = 'sanga';
			loadSangaItems();
			break;

		  default: {
            const detected = detectTabGubunFromText(tabText);
            if (detected) {
                tabGubun = detected;
                console.log('텍스트 기반 탭 판별:', tabText, '->', tabGubun);

                if (tabGubun === 'sanga' || tabGubun === 'villa') {
                    loadSangaItems();
                }
            } else {
			    console.log('알 수 없는 탭이 선택되었습니다.');
            }
          }
		}

        console.log('tabGubun: ' + tabGubun);
	});
}

// 아파트 MutationObserver 감시도 async로!
async function observeMutations() {
    console.log("observeMutations() called");
    try {
        const targetNode = await waitForElement('.item_list.item_list--article');
        const config = { childList: true, subtree: true };

        const observer = new MutationObserver(async (mutationsList, obs) => {
            if (!isScheduled) {
                isScheduled = true;
                obs.disconnect(); // 중단
                console.log('새 항목 감지됨 → 로드 실행');

                  if (tabGubun === 'sanga' || tabGubun === 'villa') {
                        // 상가 및 빌라 아이템 로드
                        loadSangaItems(); // 추가 아이템 로드
                  } else {
                        // 아파트 아이템 로드(1차로 전세부문 처리 차후로 미룸)
                        loadAptItems();
                  }
                try {
                    const newTarget = await waitForElement('.item_list.item_list--article');
                    obs.observe(newTarget, config); // 다시 감시
                    isScheduled = false;
                } catch (err) {
                    console.error("재감시 실패:", err);
                }
            }
        });
        observer.observe(targetNode, config);
    } catch (err) {
        console.error("초기 감시 대상 노드 탐색 실패:", err);
    }
}

// 비동기 DOM 요소 대기 함수
async function waitForElement(selector, timeout = 10000) {
    return new Promise((resolve, reject) => {
        const element = document.querySelector(selector);
        if (element) return resolve(element);

        const observer = new MutationObserver(() => {
            const el = document.querySelector(selector);
            if (el) {
                observer.disconnect();
                resolve(el);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        setTimeout(() => {
            observer.disconnect();
            reject(new Error(`Timeout: ${selector} not found within ${timeout}ms`));
        }, timeout);
    });
}

function isNaverLandPage() {
    const host = window.location.hostname || '';
    const href = window.location.href || '';

    return (
        host.endsWith('naver.com') &&
        (
            href.startsWith('https://new.land.naver.com/offices') ||
            href.startsWith('https://new.land.naver.com/houses') ||
            href.startsWith('https://new.land.naver.com/complexes') ||
            href.startsWith('https://fin.land.naver.com/')
        )
    );
}

// 페이지가 로드되면 실행
window.addEventListener('load', function() {
        if (!isNaverLandPage()) {
            console.log('[landcore_newland] naver.com 페이지가 아니므로 DOM 감시를 실행하지 않습니다.');
            return;
        }
        setTimeout(extractPropertyInfo,50);
        observeMutations(); // DOM 변경 감시 시작
});