
    document.addEventListener("DOMContentLoaded", function () {
        document.getElementById("api-link").addEventListener("click", function () {

            let spanText = document.getElementById("api-link").innerText.trim(); // span의 텍스트 값 가져오기
            if (spanText === "아파트") {
                apiKeyPopup('apt');
            } else if (spanText === "빌라") {
                apiKeyPopup('villa');
            } else if (spanText === "상가") {
                apiKeyPopup('sanga');
            } else  {
                apiKeyPopup('sanga');
                return;
            }
        });
    });

    // 상가,아파트,빌라 국토부 키체크
    function apiKeyPopup(type) {
        const popupWidth = 590; // 기존 팝업 크기 조정
        const popupHeight = 400;
        const left = (screen.width - popupWidth) / 2;
        const top = (screen.height - popupHeight) / 2;
        window.open(`realdata_pop_key.html?type=${type}`, "popupWindow", `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=no,scrollbars=no`);
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

    function formatNumber(num) {
      return num.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    // 숫자금액 한글금액으로 변환
    function convertToKoreanAmount(amount) {
      let amt = Number(amount.replace(/,/g, ""));
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

    // 한글금액 숫자금액으로 변환
    function convertKoreanToNumber(koreanAmount) {
        if (!koreanAmount) return 0;

        let amount = koreanAmount.replace(/,/g, "").trim(); // 콤마 제거 및 공백 제거
        let total = 0;
        let current = 0;

        const units = { "억": 100000000, "천": 10000000, "백": 1000000 };

        let match = amount.match(/(\d+)(억|천|백)?/g);

        if (!match) return isNaN(Number(amount)) ? 0 : Number(amount); // 숫자만 있을 경우 변환

        match.forEach(part => {
            let num = parseInt(part.replace(/[^0-9]/g, ""), 10); // 숫자만 추출
            let unit = part.replace(/[0-9]/g, ""); // 단위만 추출

            if (unit in units) {
                total += num * units[unit];
            } else {
                current += num; // 단위 없는 경우 누적
            }
        });

        return total + current;
    }

    // 평형계산
    function calcPyeong(area) {
      let a = Number(area);
      if (isNaN(a) || a === 0) return "";
      return (a / 3.3).toFixed(1);
    }
