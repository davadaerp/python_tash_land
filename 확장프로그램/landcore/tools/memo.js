/**
 * 매물 메모장 - memo.js
 * 매물 상세정보 + 사용자 메모를 로컬에 저장/검색/삭제
 */

// ============================================
// 전역 변수
// ============================================
let memoList = [];
const STORAGE_KEY = 'naverbu_memos';

// ============================================
// 초기화
// ============================================
document.addEventListener('DOMContentLoaded', function () {
    // URL 파라미터에서 매물 정보 추출
    loadPropertyFromUrl();

    // 평당가 계산
    calculatePerPyeong();

    // 저장된 메모 목록 로드
    loadMemos();

    // 이벤트 리스너
    document.getElementById('save-btn').addEventListener('click', saveMemo);
    document.getElementById('clear-btn').addEventListener('click', clearForm);
    document.getElementById('search-input').addEventListener('input', filterMemos);
});

// ============================================
// URL 파라미터에서 매물 정보 로드
// ============================================
function loadPropertyFromUrl() {
    const params = new URLSearchParams(window.location.search);

    // 매물 정보 필드 매핑
    const fieldMapping = {
        'propertyName': 'property-name',
        'price': 'price',
        'rent': 'rent',
        'area': 'area',
        'floor': 'floor',
        'address': 'address',
        'features': 'features',
        'propertyNo': 'property-no',
        'agencyName': 'agency-name',
        'agencyPhone': 'agency-phone',
        'agencyMobile': 'agency-mobile',
        'agencyAddress': 'agency-address'
    };

    // 파라미터 값 적용
    for (const [paramKey, elementId] of Object.entries(fieldMapping)) {
        const value = params.get(paramKey);
        if (value) {
            const element = document.getElementById(elementId);
            if (element) {
                try {
                    element.value = decodeURIComponent(value);
                } catch (e) {
                    // URI 디코딩 실패 시 원본 값 사용
                    element.value = value;
                }
            }
        }
    }
}

// ============================================
// 평당가 계산 및 표시
// ============================================
function calculatePerPyeong() {
    const areaText = document.getElementById('area').value;
    const priceText = document.getElementById('price').value;
    const rentText = document.getElementById('rent').value;

    // 면적에서 전용평수 추출 (예: "94.7㎡/60.3㎡(전용률64%)" -> 60.3)
    const areaMatch = areaText.match(/[\d.]+㎡\/([\d.]+)㎡/);
    const exclusivePyeong = areaMatch ? parseFloat(areaMatch[1]) : 0;

    if (exclusivePyeong <= 0) return;

    // 매매가격 평당가 계산
    if (priceText) {
        const priceInMan = parseKoreanPriceToMan(priceText);
        if (priceInMan > 0) {
            const pricePerPyeong = Math.round(priceInMan / exclusivePyeong);
            document.getElementById('price-per-pyeong').textContent = formatPriceShort(pricePerPyeong);
        }
    }

    // 월세 평당가 계산
    const rentPerPyeongEl = document.getElementById('rent-per-pyeong');
    if (rentText && rentText !== '-/-') {
        // 예: "6,000/300만원" -> 월세 300
        const rentMatch = rentText.match(/[\d,]+\/([\d,]+)/);
        if (rentMatch) {
            const monthlyRent = parseInt(rentMatch[1].replace(/,/g, ''));
            if (monthlyRent > 0) {
                const rentPerPyeong = (monthlyRent / exclusivePyeong).toFixed(1);
                rentPerPyeongEl.textContent = `${rentPerPyeong}만`;
            } else {
                rentPerPyeongEl.textContent = '-';
            }
        } else {
            rentPerPyeongEl.textContent = '-';
        }
    } else {
        rentPerPyeongEl.textContent = '-';
    }
}

// 한글 가격 -> 만원 단위 변환
function parseKoreanPriceToMan(priceText) {
    let total = 0;
    // "8억" -> 80000, "1억 5,000" -> 15000
    const ukMatch = priceText.match(/(\d+)억/);
    if (ukMatch) {
        total += parseInt(ukMatch[1]) * 10000;
    }
    const manMatch = priceText.match(/(\d{1,4})[,\s]*(\d{3})?(?:만|$)/);
    if (manMatch) {
        let manValue = manMatch[1];
        if (manMatch[2]) manValue += manMatch[2];
        total += parseInt(manValue.replace(/,/g, ''));
    }
    // 숫자만 있는 경우
    if (total === 0) {
        const numMatch = priceText.match(/[\d,]+/);
        if (numMatch) {
            total = parseInt(numMatch[0].replace(/,/g, ''));
        }
    }
    return total;
}

// 만원 단위 간략 표시 (예: 1333만)
function formatPriceShort(priceInMan) {
    if (priceInMan >= 10000) {
        const uk = Math.floor(priceInMan / 10000);
        const man = priceInMan % 10000;
        return man > 0 ? `${uk}억${man}만` : `${uk}억`;
    }
    return `${priceInMan}만`;
}

// ============================================
// 메모 저장
// ============================================
function saveMemo() {
    const address = document.getElementById('address').value;
    const price = document.getElementById('price').value;

    // 필수 입력 체크 (주소 또는 가격이 있어야 함)
    if (!address && !price) {
        showToast('⚠️ 매물 정보가 없습니다. 네이버 부동산에서 매물을 선택해주세요.', 'warning');
        return;
    }

    const memo = {
        id: Date.now(),
        date: new Date().toLocaleString('ko-KR'),
        price: price,
        rent: document.getElementById('rent').value,
        area: document.getElementById('area').value,
        floor: document.getElementById('floor').value,
        address: address,
        features: document.getElementById('features').value,
        propertyNo: document.getElementById('property-no').value,
        agencyName: document.getElementById('agency-name').value,
        agencyPhone: document.getElementById('agency-phone').value,
        agencyMobile: document.getElementById('agency-mobile').value,
        agencyAddress: document.getElementById('agency-address').value,
        userMemo: document.getElementById('user-memo').value
    };

    // 저장
    memoList.unshift(memo); // 최신순 정렬
    saveMemos();
    renderMemoList();

    showToast('✅ 메모가 저장되었습니다');
}

// ============================================
// chrome.storage.local에 저장
// ============================================
function saveMemos() {
    if (typeof chrome !== 'undefined' && chrome.storage) {
        chrome.storage.local.set({ [STORAGE_KEY]: memoList });
    } else {
        // 개발 환경에서는 localStorage 사용
        localStorage.setItem(STORAGE_KEY, JSON.stringify(memoList));
    }
}

// ============================================
// 저장된 메모 불러오기
// ============================================
function loadMemos() {
    if (typeof chrome !== 'undefined' && chrome.storage) {
        chrome.storage.local.get([STORAGE_KEY], (result) => {
            memoList = result[STORAGE_KEY] || [];
            renderMemoList();
        });
    } else {
        // 개발 환경
        const saved = localStorage.getItem(STORAGE_KEY);
        memoList = saved ? JSON.parse(saved) : [];
        renderMemoList();
    }
}

// ============================================
// 메모 목록 렌더링
// ============================================
function renderMemoList(filteredList = null) {
    const list = filteredList || memoList;
    const container = document.getElementById('memo-list');
    const totalCount = document.getElementById('total-count');

    totalCount.textContent = list.length + '건';

    if (list.length === 0) {
        container.innerHTML = `
      <div class="empty-state">
        <p>💡 저장된 메모가 없습니다</p>
      </div>
    `;
        return;
    }

    // 액셀 스타일 테이블
    container.innerHTML = `
    <table class="memo-table">
      <thead>
        <tr>
          <th>날짜</th>
          <th>가격</th>
          <th>평수</th>
          <th>소재지</th>
          <th>메모</th>
          <th>작업</th>
        </tr>
      </thead>
      <tbody>
        ${list.map(memo => `
          <tr>
            <td>${formatDate(memo.date)}</td>
            <td>${memo.price || '-'}</td>
            <td>${getExclusivePyeong(memo.area)}</td>
            <td>${truncate(memo.address || '-', 20)}</td>
            <td>${truncate(memo.userMemo || '-', 20)}</td>
            <td class="actions">
              <button class="btn btn-secondary btn-load" data-id="${memo.id}">불러오기</button>
              <button class="btn btn-danger btn-delete" data-id="${memo.id}">삭제</button>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

    // 이벤트 리스너 추가 (CSP 준수)
    container.querySelectorAll('.btn-load').forEach(btn => {
        btn.addEventListener('click', () => loadMemo(parseInt(btn.dataset.id)));
    });
    container.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', () => deleteMemo(parseInt(btn.dataset.id)));
    });
}

// 전용평수 추출 (예: "94.7㎡/60.3㎡(전용률64%)" -> "60.3평")
function getExclusivePyeong(areaText) {
    if (!areaText) return '-';
    const match = areaText.match(/[\d.]+㎡\/([\d.]+)㎡/);
    return match ? `${match[1]}평` : '-';
}

// 날짜 포맷 (YY.MM.DD)
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const now = new Date();
    const y = String(now.getFullYear()).slice(-2);
    const m = String(now.getMonth() + 1).padStart(2, '0');
    const d = String(now.getDate()).padStart(2, '0');
    return `${y}.${m}.${d}`;
}

// ============================================
// 메모 불러오기
// ============================================
function loadMemo(id) {
    const memo = memoList.find(m => m.id === id);
    if (!memo) return;

    document.getElementById('price').value = memo.price || '';
    document.getElementById('rent').value = memo.rent || '';
    document.getElementById('area').value = memo.area || '';
    document.getElementById('floor').value = memo.floor || '';
    document.getElementById('address').value = memo.address || '';
    document.getElementById('features').value = memo.features || '';
    document.getElementById('property-no').value = memo.propertyNo || '';
    document.getElementById('agency-name').value = memo.agencyName || '';
    document.getElementById('agency-phone').value = memo.agencyPhone || '';
    document.getElementById('agency-mobile').value = memo.agencyMobile || '';
    document.getElementById('agency-address').value = memo.agencyAddress || '';
    document.getElementById('user-memo').value = memo.userMemo || '';

    // 평당가 재계산
    calculatePerPyeong();

    showToast('📂 메모를 불러왔습니다');
}

// ============================================
// 메모 삭제
// ============================================
function deleteMemo(id) {
    if (!confirm('이 메모를 삭제하시겠습니까?')) return;

    memoList = memoList.filter(m => m.id !== id);
    saveMemos();
    renderMemoList();
    showToast('🗑 삭제되었습니다');
}

// ============================================
// 검색 필터링
// ============================================
function filterMemos() {
    const query = document.getElementById('search-input').value.toLowerCase().trim();

    if (!query) {
        renderMemoList();
        return;
    }

    const filtered = memoList.filter(memo => {
        return (
            (memo.price && memo.price.toLowerCase().includes(query)) ||
            (memo.area && memo.area.toLowerCase().includes(query)) ||
            (memo.address && memo.address.toLowerCase().includes(query)) ||
            (memo.features && memo.features.toLowerCase().includes(query)) ||
            (memo.agencyName && memo.agencyName.toLowerCase().includes(query)) ||
            (memo.userMemo && memo.userMemo.toLowerCase().includes(query))
        );
    });

    renderMemoList(filtered);
}

// ============================================
// 전체 삭제 (초기화)
// ============================================
function clearForm() {
    if (memoList.length === 0) {
        showToast('⚠️ 삭제할 메모가 없습니다');
        return;
    }

    if (!confirm(`저장된 메모 ${memoList.length}건을 모두 삭제하시겠습니까?`)) return;

    memoList = [];
    saveMemos();
    renderMemoList();
    showToast('🗑 모든 메모가 삭제되었습니다');
}

// ============================================
// 유틸리티 함수
// ============================================
function truncate(str, maxLength) {
    if (!str) return '';
    return str.length > maxLength ? str.substring(0, maxLength) + '...' : str;
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.background = type === 'warning' ? '#f59e0b' : '#10b981';
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 2500);
}