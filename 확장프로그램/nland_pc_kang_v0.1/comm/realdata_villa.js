
    let currentYear = new Date().getFullYear();
    window.rowDataArray = [];
    window.allFetchedItems = [];
    // 전역 변수: 평형 및 거래일자 정렬 토글 상태 (초기 오름차순)
    let sortDealDateAscending = true;
    let sortBuildingYearAscending = true;
    let sortPyeongAscending = true;
    let sortFloorAscending = true;

    let selectedLawdCd = "";
    let selectedUmdNm = "";
    let selectedIndex = -1;

    document.addEventListener('DOMContentLoaded', function() {
        const yearSelect = document.getElementById("year");
        yearSelect.innerHTML = '<option value="all">전체</option>';

        // 거래일자 헤더 정렬 이벤트 추가
        document.getElementById("sortDealDate").addEventListener("click", function() {
          if (window.currentFilteredItems) {
            window.currentFilteredItems.sort((a, b) => {
              let da = a.dealDate;
              let db = b.dealDate;
              return sortDealDateAscending ? da.localeCompare(db) : db.localeCompare(da);
            });
            sortDealDateAscending = !sortDealDateAscending;
            updateSortIcons();
            renderTable(window.currentFilteredItems);
          }
        });

        // 건축년도 헤더 정렬 이벤트 추가
        document.getElementById("sortBuildYear").addEventListener("click", function() {
          if (window.currentFilteredItems) {
            window.currentFilteredItems.sort((a, b) => {
              let yearA = parseInt(a.buildYear) || 0;
              let yearB = parseInt(b.buildYear) || 0;
              return sortBuildingYearAscending ? (yearA - yearB) : (yearB - yearA);
            });
            sortBuildingYearAscending = !sortBuildingYearAscending;
            updateSortIcons();
            renderTable(window.currentFilteredItems);
          }
        });

        // 평형 헤더(건물면적(평))에 토글 정렬 이벤트 추가
        document.getElementById("sortPyeong").addEventListener("click", function() {
          if (window.currentFilteredItems) {
            window.currentFilteredItems.sort((a, b) => {
              let pa = parseFloat(a.excluUseArPyeong);
              let pb = parseFloat(b.excluUseArPyeong);
              return sortPyeongAscending ? (pa - pb) : (pb - pa);
            });
            sortPyeongAscending = !sortPyeongAscending;
            updateSortIcons();
            renderTable(window.currentFilteredItems);
          }
        });

        // 층 헤더(층) 정렬 이벤트 추가
        document.getElementById("sortFloor").addEventListener("click", function() {
          if (window.currentFilteredItems) {
            window.currentFilteredItems.sort((a, b) => {
              let floorA = parseInt(a.floor) || 0;
              let floorB = parseInt(b.floor) || 0;
              return sortFloorAscending ? (floorA - floorB) : (floorB - floorA);
            });
            sortFloorAscending = !sortFloorAscending;
            updateSortIcons();
            renderTable(window.currentFilteredItems);
          }
        });
        // 초기 아이콘 업데이트
        updateSortIcons();

         // 검색 버튼 클릭 이벤트 수정 (입력 체크 추가)
        document.getElementById("search-btn").addEventListener("click", function() {
            let searchTerm = $('#locatadd_nm').val().trim(); // 검색어 가져오기
            if (!searchTerm) { // 검색어가 없을 경우 경고 메시지
                alert("법정동명을 입력하세요.");
                $('#locatadd_nm').focus(); // 입력란에 포커스 이동
                return;
            }
            fetchData(); // 검색어가 존재하면 데이터 검색 실행
        });
    });

    // 아이콘 업데이트
    function updateSortIcons() {
      document.getElementById("sortDealDate").textContent = sortDealDateAscending ? "거래일자 ▲" : "거래일자 ▼";
      document.getElementById("sortBuildYear").textContent = sortBuildingYearAscending ? "건축년도 ▲" : "건축년도 ▼";
      document.getElementById("sortPyeong").textContent = sortPyeongAscending ? "건물면적 ▲" : "건물면적 ▼";
      document.getElementById("sortFloor").textContent = sortFloorAscending ? "층 ▲" : "층 ▼";
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

    async function fetchData() {
      //
      // 상가,아파트,빌라 국토부 키체크
      const existingKey = localStorage.getItem(`villa_key`);
      if (!existingKey) {
        if (confirm(`빌라 키가 없습니다. 등록하시겠습니까?`)) {
          apiKeyPopup('villa');
        }
      } else {
        document.getElementById("result-amt").textContent = "평균단가/금액: 0/0";
        document.getElementById("result-count").textContent = "건수: 0";
        document.getElementById("mhouseNm").value = "";
        //
        const dataContainer = document.getElementById("data-container");
        dataContainer.innerHTML = `<div class="loading-overlay">데이터를 불러오는 중입니다...</div>`;
        const selectedYear = document.getElementById("year").value;
        const selectedMonth = document.getElementById("month").value;
        const lawdCd = selectedLawdCd;
        const umdNm = selectedUmdNm;
        const url = "https://apis.data.go.kr/1613000/RTMSDataSvcRHTrade/getRTMSDataSvcRHTrade";
        //const serviceKey = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA==";
        const serviceKey = existingKey;
        let allItems = [];
        try {
          const yearsToFetch = selectedYear === "all"
                  ? Array.from({length: 3}, (_, i) => currentYear - i)
                  : [selectedYear];
          for (const year of yearsToFetch) {
            const monthsToFetch = selectedMonth === "all"
                    ? Array.from({length: 12}, (_, i) => (i + 1).toString().padStart(2, "0"))
                    : [selectedMonth];
            for (const month of monthsToFetch) {
              const params = {
                serviceKey: serviceKey,
                LAWD_CD: lawdCd,
                DEAL_YMD: `${year}${month}`,
                pageNo: 1,
                numOfRows: 500
              };
              const response = await fetch(`${url}?${new URLSearchParams(params)}`);
              if (!response.ok) {
                throw new Error(`API 요청 실패: ${response.status}`);
              }
              const text = await response.text();
              const parser = new DOMParser();
              const xmlDoc = parser.parseFromString(text, "text/xml");
              const items = xmlDoc.querySelectorAll("item");
              if (items.length === 0) {
                console.log(`${year}년 ${month}월: 검색된 데이터가 없습니다.`);
                continue;
              }
              items.forEach(item => {
                const itemData = {};
                item.childNodes.forEach(node => {
                  if (node.nodeType === 1) {
                    itemData[node.nodeName] = node.textContent;
                  }
                });
                if (!umdNm || itemData.umdNm === umdNm) {
                  itemData.dealDate = `${itemData.dealYear}-${itemData.dealMonth.padStart(2, "0")}-${itemData.dealDay.padStart(2, "0")}`;
                  itemData.excluUseArPyeong = calcPyeong(itemData.excluUseAr);
                  itemData.convertedDealAmount = convertToKoreanAmount(itemData.dealAmount);
                  allItems.push(itemData);
                }
              });
            }
          }
          window.allFetchedItems = allItems;
          renderTable(allItems);

          // 연도, 월 select 업데이트 (중복 제거)
          let yearSet = new Set();
          let monthSet = new Set();
          allItems.forEach(item => {
            if (item.dealDate) {
              yearSet.add(item.dealDate.substring(0, 4));
              monthSet.add(item.dealDate.substring(5, 7));
            }
          });
          const yearSelectElem = document.getElementById("year");
          yearSelectElem.innerHTML = '<option value="all">전체</option>';
          Array.from(yearSet).sort((a, b) => b - a).forEach(yr => {
            const opt = document.createElement("option");
            opt.value = yr;
            opt.textContent = yr + "년";
            yearSelectElem.appendChild(opt);
          });
          const monthSelectElem = document.getElementById("month");
          monthSelectElem.innerHTML = '<option value="all">전체</option>';
          Array.from(monthSet).sort().forEach(mo => {
            const opt = document.createElement("option");
            opt.value = mo;
            opt.textContent = parseInt(mo) + "월";
            monthSelectElem.appendChild(opt);
          });
          //
        } catch (error) {
          console.error("오류 발생:", error);
          dataContainer.innerHTML = `<p>오류 발생: ${error.message}</p>`;
        }
      }
    }

    function renderTable(items) {
      const dataContainer = document.getElementById("data-container");
      if (items.length === 0) {
        dataContainer.innerHTML = '<div class="no-data-message">검색된 데이터가 없습니다.</div>';
        document.getElementById("result-count").textContent = "건수: 0";
        return;
      }
      let tableHTML = `<table>
        ${items.map((item, index) => {
          let fullRowData = {
            "순번": index + 1,
            "주소(법정코드)": selectedLawdCd,
            "시군구명": item.sggNm || "",
            "거래일자": item.dealDate || "",
            "건축년도": item.buildYear || "",
            "층": item.floor || "",
            "건물면적(m2)": item.excluUseAr || "",
            "전용면적(평)": item.excluUseArPyeong || "",
            "대지면적": item.landAr || "",
            "단지명": item.mhouseNm || "",
            "매수구분": item.buyerGbn || "",
            "거래금액": item.dealAmount || "",
            "거래금액(한글)": item.convertedDealAmount || "",
            "지번": item.jibun || "",
            "토지이용": item.landUse || "",
            "읍면동명": item.umdNm || ""
          };
          window.rowDataArray.push(fullRowData);
          const currentIndex = window.rowDataArray.length - 1;

          // 평단가 계산
          let computedUnitPrice = "";
          // 문자열에 콤마가 있을 경우 제거 후 숫자로 변환
          let tradeAmountNum = parseFloat((item.dealAmount || "0").replace(/,/g, ""));
          let areaNum = parseFloat((item.excluUseArPyeong || "0").replace(/,/g, ""));
          if (!isNaN(tradeAmountNum) && !isNaN(areaNum) && areaNum > 0) {
            let unitPrice = tradeAmountNum / areaNum;
            // 소수점 없이 표시하거나 원하는 형식으로 변환 가능
            //computedUnitPrice = formatNumber(unitPrice.toFixed(0).toString());
            computedUnitPrice = unitPrice.toFixed(0).toString();
          } else {
            computedUnitPrice = "N/A";
          }

          // 거래금액(한글)과 평단가를 결합해서 표시 (예: "거래금액/@평단가")
          // 거래금액은 파란색, 평단가는 빨간색으로 표시
          let priceDisplay = `${item.convertedDealAmount || ""}/<span style="color: red;">@${computedUnitPrice}</span>`;
          // 평처리
          let computExcluUseAr = parseFloat(item.excluUseAr).toFixed(2).toString();
          let pyeongDisplay = `${item.excluUseArPyeong || ""} / <span style="color: blue;">${computExcluUseAr}</span>`;

          // 리스트에 표시할 데이터 배열: 순번, 거래일자, 전용(평), 거래금액/평단가, 건축년도, 건물용도
          let listRowData = [
            index + 1,
            item.dealDate || "",
            item.buildYear || "",
            item.floor || "",
            pyeongDisplay || "",
            priceDisplay,
            item.mhouseNm || ""
          ];

         // 각 셀을 index에 따라 정렬 처리: 4번째 셀은 오른쪽, 나머지는 중앙 정렬
          const cellStyles = [
            "text-align: center; width: 5%;",    // 순번: 중앙정렬, 너비 5%
            "text-align: center; width: 12%;",   // 거래일자: 중앙정렬, 너비 20%
            "text-align: center; width: 10%;",   // 건축년도: 중앙정렬, 너비 20%
            "text-align: center; width: 7%;",   // 건물층
            "text-align: center; width: 15%;",   // 건물면적(평): 중앙정렬, 너비 20%
            "text-align: right; width: 15%;",    // 거래금액(한글): 오른쪽 정렬, 너비 20%
            "text-align: center; width: 17%;"    // 건물용도: 중앙정렬, 너비 15%
          ];

          const cellsHTML = listRowData
            .map((cell, idx) => `<td style="${cellStyles[idx]}">${cell}</td>`)
            .join("");
          // 지도 버튼과 상세보기 버튼 생성 (각각 고유 id 부여)
          const mapBtnHTML = `<td><button id="map-btn-${currentIndex}" style="padding:4px 8px; font-size:12px;">지도</button></td>`;
          const detailBtnHTML = `<td><button id="detail-btn-${currentIndex}" style="padding:4px 8px; font-size:12px;">상세</button></td>`;

          return `<tr>${cellsHTML}${mapBtnHTML}${detailBtnHTML}</tr>`;
        }).join("")}
      </table>`;
      dataContainer.innerHTML = tableHTML;

      // 전체 거래금액과 전체 건물면적(평) 계산
        let totalDealAmount = 0;
        let totalArea = 0;
        items.forEach(item => {
          let amount = Number(item.dealAmount.replace(/,/g, ""));
          totalDealAmount += amount;
          let area = parseFloat(item.excluUseArPyeong);
          if (!isNaN(area)) {
            totalArea += area;
          }
        });
        // 평균금액: 전체 거래금액 / 거래건수
        let avgDealAmount = items.length > 0 ? totalDealAmount / items.length : 0;
        // 평균단가: 전체 거래금액 / 전체 건물면적(평)
        let avgUnitPrice = totalArea > 0 ? totalDealAmount / totalArea : 0;

        // 평균금액은 한글 형식으로 변환, 평균단가는 천단위 콤마 처리
        let avgDealAmountFormatted = convertToKoreanAmount(avgDealAmount.toFixed(0));
        let avgUnitPriceFormatted = formatNumber(avgUnitPrice.toFixed(0));

        // result-amt 에 평균금액(총건수 기준) 및 평균단가(평 기준) 출력, result-count 에 건수를 출력
        document.getElementById("result-amt").innerHTML = `평균금액/단가: ${avgDealAmountFormatted}/<span style="color: red;">@${avgUnitPriceFormatted}</span>`;
        document.getElementById("result-count").textContent = `건수: ${items.length}`;

        // 렌더링 완료 후, 각 버튼에 대해 id를 이용해 이벤트 리스너 등록
        for (let i = 0; i < window.rowDataArray.length; i++) {
          // 지도 버튼 이벤트: 해당 행의 "시군구명", "읍면동명", "지번"을 조합하여 지도 검색
          let mapBtn = document.getElementById("map-btn-" + i);
          if (mapBtn) {
            mapBtn.addEventListener("click", function() {
              let rowData = window.rowDataArray[i];
              let mapAddress = (rowData["시군구명"] || "") + " " + (rowData["읍면동명"] || "") + " " + (rowData["지번"] || "");
              openMap(mapAddress);
            });
          }
          // 상세보기 버튼 이벤트: showDetailPopupRow 함수 호출
          let detailBtn = document.getElementById("detail-btn-" + i);
          if (detailBtn) {
            detailBtn.addEventListener("click", function() {
              showDetailPopupRow(i);
            });
          }
        }
    }

    document.addEventListener("DOMContentLoaded", function() {
      document.getElementById("year").addEventListener("change", applyFilters);
      document.getElementById("month").addEventListener("change", applyFilters);
      document.getElementById("pyeon").addEventListener("change", function() {
          document.getElementById("pyeonSu").value = '';
          applyFilters()
      });
      // 평형및 단지명 검색
      document.getElementById("pyeonSu").addEventListener("keyup", function() {
          document.getElementById("pyeon").value = 'all';
          applyFilters()
      });
      document.getElementById("mhouseNm").addEventListener("keyup", applyFilters);
    });

    function showDetailPopup(rowData) {
        let headerRect = document.getElementById("header-container").getBoundingClientRect();
        let topPos = headerRect.bottom + (window.innerHeight - headerRect.bottom) / 2 - 150;
        let detailHTML = `<h2>상세 정보</h2>
          <table style="width:90%; margin:auto; border-collapse:collapse;">
        `;
        for (const key in rowData) {
          detailHTML += `<tr>
            <th style="border:1px solid #ddd; padding:8px; background:#f2f2f2; text-align:left; width:40%;">${key}</th>
            <td style="border:1px solid #ddd; padding:8px; text-align:left; width:60%;">${rowData[key]}</td>
          </tr>`;
        }
        detailHTML += `</table>`;
        // 인라인 이벤트 제거하고 id 부여
        detailHTML += `<button class="close-btn" id="close-btn">X</button>`;

        let popupContent = document.getElementById("detailPopup").querySelector(".popup-content");
        popupContent.innerHTML = detailHTML;

        // 이벤트 리스너 등록
        document.getElementById("close-btn").addEventListener("click", hideDetailPopup);

        popupContent.style.top = "50%";
        popupContent.style.left = "50%";
        popupContent.style.transform = "translate(-50%, -50%)";
        document.getElementById("detailPopup").style.display = "block";
    }

    function showDetailPopupRow(index) {
      showDetailPopup(window.rowDataArray[index]);
    }

    function hideDetailPopup() {
      document.getElementById("detailPopup").style.display = "none";
    }

    // 조건선택 및 단지명입력 목록 처리
    function applyFilters() {
      let selYear = document.getElementById("year").value;
      let selMonth = document.getElementById("month").value;
      let selPyeon = document.getElementById("pyeon").value;
      let selPyeonSu = document.getElementById("pyeonSu").value;
      let selHouseNm = document.getElementById("mhouseNm").value;
      let filteredItems = window.allFetchedItems.filter(item => {
        let ok = true;
        if (selYear !== "all") {
          ok = ok && item.dealDate && item.dealDate.substring(0,4) === selYear;
        }
        if (selMonth !== "all") {
          ok = ok && item.dealDate && item.dealDate.substring(5,7) === selMonth;
        }
        if (selPyeon !== "all") {
          let p = parseFloat(item.excluUseArPyeong);
          if (isNaN(p)) return false;
          if (selPyeon === "9") {
            ok = ok && (p >= 1 && p < 10);
          } else if (selPyeon === "10") {
            ok = ok && (p >= 10 && p < 20);
          } else if (selPyeon === "20") {
            ok = ok && (p >= 20 && p < 30);
          } else if (selPyeon === "30") {
            ok = ok && (p >= 30 && p < 40);
          } else if (selPyeon === "40") {
            ok = ok && (p >= 40 && p < 50);
          } else if (selPyeon === "50") {
            ok = ok && (p >= 50 && p < 70);
          } else if (selPyeon === "70") {
            ok = ok && (p >= 70 && p < 100);
          } else if (selPyeon === "100") {
            ok = ok && (p >= 100);
          }
        } else if (selPyeonSu.trim() !== "") {
          // selPyeon이 "all"이고 selPyeonSu가 입력되었을 경우,
          // 예: 15평이면 15.0 이상 16.0 미만으로 필터링
          let p = parseFloat(item.excluUseArPyeong);
          if (isNaN(p)) return false;
          let custom = parseFloat(selPyeonSu);
          ok = ok && (p >= custom && p < (custom + 1));
        }
        if (selHouseNm.trim() !== "") {
          ok = ok && item.mhouseNm && item.mhouseNm.includes(selHouseNm.trim());
        }
        return ok;
      });
      renderTable(filteredItems);
      // 현재 필터된 데이터 저장 (정렬 시 사용)
      window.currentFilteredItems = filteredItems;
    }