
    //BASE_URL = 'http://192.168.45.167:5002';
    //BASE_URL = 'http://192.168.45.167:8081';
    BASE_URL = 'http://localhost:8080';

    // 자동완성 공통필드
    let selectedLawdCd = "";
    let selectedUmdNm = "";
    let selectedIndex = -1;

    // 검색기준년 및 데이타 저장소
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth();
    window.rowDataArray = [];
    window.allFetchedItems = [];

    // 로그인시 처리로 사용안함
    // document.addEventListener("DOMContentLoaded", function () {
    //     document.getElementById("api-link").addEventListener("click", function () {
    //
    //         let spanText = document.getElementById("api-link").innerText.trim(); // span의 텍스트 값 가져오기
    //         if (spanText === "아파트") {
    //             apiKeyPopup('apt');
    //         } else if (spanText === "빌라") {
    //             apiKeyPopup('villa');
    //         } else if (spanText === "상가") {
    //             apiKeyPopup('sanga');
    //         } else  {
    //             apiKeyPopup('sanga');
    //             return;
    //         }
    //     });
    // });

    // 상가,아파트,빌라 국토부 키체크
    function apiKeyPopup() {
        const popupWidth = 590; // 기존 팝업 크기 조정
        const popupHeight = 400;
        const left = (screen.width - popupWidth) / 2;
        const top = (screen.height - popupHeight) / 2;
        window.open(`/api/menu?menu=api_key`, "popupWindow", `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=no,scrollbars=no`);
    }

    //  function openMap(address) {
    //   const width = 1900;
    //   const height = 1280;
    //   const left = (screen.width - width) / 2;
    //   const top = (screen.height - height) / 2;
    //   window.open('https://www.google.com/maps/search/?api=1&query=' + address, '_blank', 'width=' + width + ',height=' + height + ',left=' + left + ',top=' + top);
    // }

    function openMap(address) {
      const width = 1900;
      const height = 1280;
      const left = (screen.width - width) / 2;
      const top = (screen.height - height) / 2;
      // 네이버맵 URL은 "https://map.naver.com/v5/search/" 뒤에 인코딩된 주소를 붙여서 사용합니다.
      window.open('https://map.naver.com/v5/search/' + encodeURIComponent(address), '_blank', 'width=' + width + ',height=' + height + ',left=' + left + ',top=' + top);
    }

    // function formatNumber(num) {
    //   return num.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    // }
    /**
     * 문자열로 된 숫자에서 쉼표(,)를 모두 제거하고 숫자로 변환하여 반환합니다.
     * @param {string} str - 쉼표가 포함된 숫자 문자열 (예: "1,012,800,000")
     * @returns {number} 쉼표가 제거된 숫자 (예: 1012800000)
     */
    function parseNumberWithCommas(str) {
      if (typeof str !== 'string') {
        throw new TypeError('입력값은 문자열이어야 합니다.');
      }
      // 모든 쉼표를 제거한 뒤 숫자로 변환
      const cleaned = str.replace(/,/g, '');
      const num = Number(cleaned);
      if (Number.isNaN(num)) {
        throw new Error(`유효한 숫자 문자열이 아닙니다: "${str}"`);
      }
      return num;
    }

    function formatNumber(num = 0) {
        // num이 undefined 혹은 null일 경우 0으로 처리
        const safeNum = (num === undefined || num === null) ? 0 : num;
        return safeNum
            .toString()
            .replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    // 숫자금액 한글금액으로 변환 => 1,600,000 -> "1천6백만원"
    function convertToKoreanAmount(amount) {
      let amt = Number(amount.toString().replace(/,/g, ""));
      if (isNaN(amt)) return "";
      let result = "";
      if (amt >= 10000) {
        let eok = Math.floor(amt / 10000);
        let remainder = amt % 10000;
        result = eok + "억";
        if (remainder >= 1000) {
          let chun = Math.floor(remainder / 1000);
          result += chun + "천";
        }
      } else if (amt >= 1000) {
        let chun = Math.floor(amt / 1000);
        let remainder = amt % 1000;
        result = chun + "천";
        if (remainder >= 100) {
          let baek = Math.floor(remainder / 100);
          result += baek + "백";
        }
      } else if (amt >= 100) {
        result = Math.floor(amt / 100) + "백";
      } else {
        result = amt.toString();
      }
      return result;
    }

    // 한글금액 숫자금액으로 변환(예: "1억 5,000" -> 16000000)
    function convertKoreanToNumber(koreanAmount) {
        // 1) null/undefined 처리
        if (koreanAmount === null || koreanAmount === undefined) {
            return 0;
        }

        // 콤마 제거 및 좌우 공백 제거
        let amount = koreanAmount.replace(/,/g, "").trim();

        // 한글 단위(억, 천, 백, 십만)가 없으면 만원 단위로 간주하여 10000을 곱함
        if (!/(억|천|백|십만)/.test(amount)) {
            return Number(amount) * 10000;
        }

        let total = 0;
        // 단위별 곱할 값 설정
        const units = {
            "억": 100000000,
            "천": 10000000,
            "백": 1000000,
            "십만": 100000
        };

        // 정규식: 숫자와 선택적 단위 (십만은 두 글자) 매칭
        let match = amount.match(/(\d+)(억|천|백|십만)?/g);
        if (!match) return isNaN(Number(amount)) ? 0 : Number(amount);

        match.forEach(part => {
            let num = parseInt(part.replace(/[^0-9]/g, ""), 10); // 숫자만 추출
            let unit = part.replace(/[0-9]/g, "");                // 단위만 추출

            if (unit) {
                if (unit in units) {
                    total += num * units[unit];
                }
            } else {
                // 단위가 없는 경우 만원 단위로 간주
                total += num * 10000;
            }
        });

        return total;
    }


    /**
     * 숫자를 한글 단위 또는 천 단위 콤마 형식으로 변환합니다.
     * - 억 단위(>=100,000,000): “1억 6,000” 형식
     * - 그 외: 천 단위 이하 혹은 백 단위는 “5,000”, “100” 등 콤마만 붙여서 반환
     * - null 또는 undefined 입력 시 “0” 반환
     */
    function convertNumberToKorean(amount) {
        // 1) null/undefined 처리
        if (amount === null || amount === undefined) {
            return "0";
        }

        // 2) 입력을 숫자로 파싱 (문자열인 경우 콤마 제거)
        const num = typeof amount === "string"
            ? parseInt(amount.replace(/,/g, ""), 10)
            : amount;

        if (isNaN(num)) {
            return "0";
        }

        // 3) 억 단위 처리
        if (num >= 100_000_000) {
            const eok = Math.floor(num / 100_000_000);
            const wan = Math.floor((num % 100_000_000) / 10_000);

            // 만 단위(=wan)를 천 단위 콤마 형식으로
            const wanStr = wan
                .toString()
                .replace(/\B(?=(\d{3})+(?!\d))/g, ",");

            return wan > 0
                ? `${eok}억 ${wanStr}`
                : `${eok}억`;
        }

        // 4) 그 외: 그냥 천 단위 콤마 붙이기
        return num
            .toString()
            .replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }


    // 평형계산
    function calcPyeong(area) {
      let a = Number(area);
      if (isNaN(a) || a === 0) return "";
      return (a / 3.3).toFixed(1);
    }

    //===========================================
    function getCurrentYear() {
        return new Date().getFullYear();
    }

    function getCurrentDate() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0'); // 월은 0부터 시작하므로 +1
        const day = String(now.getDate()).padStart(2, '0');

        return `${year}-${month}-${day}`;
    }

    function loadYears() {
        let currentYear = getCurrentYear();
        let yearSelect = $('#sale_year');
        for (let i = 0; i <= 3; i++) {
            yearSelect.append(`<option value="${currentYear - i}">${currentYear - i}</option>`);
        }
    }
