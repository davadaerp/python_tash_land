
        //
        let selectedLawdCd = "";
        let selectedUmdNm = "";
        let selectedIndex = -1;
        window.allFetchedItems = [];

        $(document).ready(function() {

            // 단지명 검색 이벤트 처리
            // document.addEventListener("DOMContentLoaded", function() {
            //     document.getElementById("aptNm").addEventListener("keydown", applyFilters);
            // });
            // 단지명 검색 이벤트 처리 - 적용 위치 변경
            //$("#aptNm").on("keydown", applyFilters);
            $("#trade_type").on("change", applyFilters);
            $("#category").on("change", applyFilters);
            $("#pyeon").on("change", applyFilters);
            $("#sel_floor").on("change", applyFilters);

            //
            // document.addEventListener("DOMContentLoaded", function() {
            //     document.getElementById("trade_type").addEventListener("change", function() {
            //         alert('xxxxx');
            //         applyFilters();
            //     });
            //     // document.getElementById("sale_month").addEventListener("change", applyFilters);
            //     // document.getElementById("pyeon").addEventListener("change", applyFilters);
            // });

            let sortTradeAscending = true;
            let sortCategoryAscending = true;
            let sortFloorAscending = true;
            let sortBuildingAreaAscending = true;
            let sortPriceAscending = true;

            // "매매,월세" 정렬
            $('#sortTrade').click(function () {
                window.currentFilteredItems.sort((a, b) => {
                    let buildingA = a.거래유형 ? a.거래유형.toString() : ""; // 문자열 변환 및 예외 처리
                    let buildingB = b.거래유형 ? b.거래유형.toString() : "";

                    return sortTradeAscending
                        ? buildingA.localeCompare(buildingB, 'ko-KR')
                        : buildingB.localeCompare(buildingA, 'ko-KR');
                });
                sortTradeAscending = !sortTradeAscending;
                updateSortIcons();
                renderTable(window.currentFilteredItems);
            });

            // 물건구분(일반상가,복합상가,사무실등) 정렬
            $('#sortCategory').click(function () {
                window.currentFilteredItems.sort((a, b) => {
                    let buildingA = parseInt(a.구분) || 0;
                    let buildingB = parseInt(b.구분) || 0;
                    return sortCategoryAscending ? buildingA - buildingB : buildingB - buildingA;
                });
                sortCategoryAscending = !sortCategoryAscending;
                updateSortIcons();
                renderTable(window.currentFilteredItems);
            });

            // "층" 정렬
            $('#sortFloor').click(function () {
                window.currentFilteredItems.sort((a, b) => {
                    let buildingA = parseInt(a.층수) || 0;
                    let buildingB = parseInt(b.층수) || 0;
                    return sortFloorAscending ? buildingA - buildingB : buildingB - buildingA;
                });
                sortFloorAscending = !sortFloorAscending;
                updateSortIcons();
                renderTable(window.currentFilteredItems);
            });

            // 건물평수 정렬
            $('#sortBuildingArea').click(function () {
                window.currentFilteredItems.sort((a, b) => {
                    let areaA = parseFloat(a.전용면적평) || 0;
                    let areaB = parseFloat(b.전용면적평) || 0;
                    return sortBuildingAreaAscending ? areaA - areaB : areaB - areaA;
                });
                sortBuildingAreaAscending = !sortBuildingAreaAscending;
                updateSortIcons();
                renderTable(window.currentFilteredItems);
            });

            // 매각금액 정렬
            $('#sortPrice').click(function () {
                window.currentFilteredItems.sort((a, b) => {
                    let priceA = parseFloat(a.가격.replace(/,/g, "")) || 0;
                    let priceB = parseFloat(b.가격.replace(/,/g, "")) || 0;
                    return sortPriceAscending ? priceA - priceB : priceB - priceA;
                });
                sortPriceAscending = !sortPriceAscending;
                updateSortIcons();
                renderTable(window.currentFilteredItems);
            });

            function updateSortIcons() {
                $('#sortTrade').text(sortTradeAscending ? '거래유형 ▲' : '거래유형 ▼');
                $('#sortCategory').text(sortCategoryAscending ? '물건구분 ▲' : '물건구분 ▼');
                $('#sortFloor').text(sortFloorAscending ? '층 ▲' : '층 ▼');
                $('#sortBuildingArea').text(sortBuildingAreaAscending ? '전용면적(평) ▲' : '전용면적(평) ▼');
                $('#sortPrice').text(sortPriceAscending ? '금액 ▲' : '금액 ▼');
            }

            //===========================================
            function getCurrentYear() {
                return new Date().getFullYear();
            }

            function loadYears() {
                let currentYear = getCurrentYear();
                let yearSelect = $('#sale_year');
                for (let i = 0; i <= 3; i++) {
                    yearSelect.append(`<option value="${currentYear - i}">${currentYear - i}</option>`);
                }
            }

            function formatNumber(num) {
                return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
            }


            function fetchData() {
                //
                document.getElementById("result-amt").textContent = "평균금액/단가: 0/0";
                document.getElementById("result-count").textContent = "건수: 0건";
                document.getElementById("aptNm").value = "";

                let searchTerm = $('#locatadd_nm').val();
                let trade_type = $('#trade_type').val();
                let saleYear = $('#sale_year').val();
                let saleMonth = $('#sale_month').val();
                let category = $('#category').val();
                let dangiName = $('#aptNm').val();

                $('#loading').show();
                $('#noData').hide();
                $('table').hide();

                $.ajax({
                    url: 'http://192.168.45.167:5002/api/data',
                    method: 'GET',
                    data: {
                        lawdCd: selectedLawdCd,
                        umdNm: selectedUmdNm,
                        searchTerm: searchTerm,
                        trade_type: trade_type,
                        saleYear: saleYear,
                        saleMonth: saleMonth,
                        category: category,
                        dangiName: dangiName
                    },
                    dataType: 'json',
                    timeout: 5000,  // 5초 타임아웃 설정
                    beforeSend: function () {
                        $('#loading').show();
                        $('#noData').hide();
                        $('#errorMessage').hide();  // 에러 메시지 초기화
                        $('table').hide();
                    },
                    success: function (data) {
                        $('#loading').hide();
                        if (data.length === 0) {
                            $('#noData').show();
                            $('#errorMessage').hide(); // 오류 메시지가 보이지 않도록 설정
                        } else {
                            $('#noData').hide();
                            $('#errorMessage').hide();
                            $('table').show();
                            window.allFetchedItems = data;
                            window.currentFilteredItems = data;
                            renderTable(data);
                            // 층수세팅
                            set_floor(data);
                        }
                    },
                    error: function (xhr, status, error) {
                        $('#loading').hide();
                        if (status === "timeout") {
                            $('#errorMessage').text("서버 응답이 없습니다. 서버가 실행 중인지 확인하세요.").show();
                        } else {
                            $('#errorMessage').text("데이터를 가져오는 중 오류가 발생했습니다: " + error).show();
                        }
                    }
                });
            }

            // 층수를 세팅함
            function set_floor(allItems) {
                // sel_floor 셀렉트 박스 초기화 및 중복 없는 층수 옵션 추가
                const selFloorElem = document.getElementById("sel_floor");
                selFloorElem.innerHTML = '<option value="all">전체</option> <option value="low">저층</option> <option value="high">상층</option>';
                let floorSet = new Set();
                allItems.forEach(item => {
                  if (item.층수) {
                    floorSet.add(item.층수);
                  }
                });
                // 층수 값이 숫자로만 구성되어 있다면 숫자 비교, 그렇지 않으면 문자열 비교로 정렬
                Array.from(floorSet)
                  .sort((a, b) => {
                    let numA = parseFloat(a);
                    let numB = parseFloat(b);
                    if (!isNaN(numA) && !isNaN(numB)) {
                      return numA - numB;
                    }
                    return a.localeCompare(b);
                  })
                  .forEach(floor => {
                    const opt = document.createElement("option");
                    opt.value = floor;
                    opt.textContent = floor + "층";
                    selFloorElem.appendChild(opt);
                  });
            }

            function renderTable(data) {
                let tableBody = $('#dataBody');
                tableBody.empty();
                data.forEach((item, index) => {
                    let pyeongAmt = convertKoreanToNumber(item.가격);
                    let pyeongArea = parseFloat(item.전용면적평);
                    let pyeongPrice= (pyeongAmt / pyeongArea) / 10000;
                    //console.log(pyeongAmt, pyeongArea, pyeongPrice)
                    tableBody.append(`<tr>
                        <td class="center-align">${item.매물일자}</td>
                        <!--
                            <td class="center-align">${item.기사번호}</td>
                        -->
                        <td class="center-align">${item.거래유형.replace(/\s/g, "")}</td>
                        <td class="center-align">${item.구분}</td>
                        <td class="center-align">${item.층수}</td>
                        <td class="center-align">${item.총층수}</td>
                        <td class="center-align">${item.전용면적m2}</td>
                        <td class="center-align" style="color: blue;">${item.전용면적평}</td>
                        <td class="right-align">${formatNumber(item.가격)}/<span style="color: red;">@${formatNumber(pyeongPrice.toFixed(0))}</span></td>
                        <td class="right-align" style="color: green;">${item.월세}</td>
                        <td class="right-align">${item.방향}</td>
                        <td class="center-align">
                          ${item.중개사명.length > 13 ? item.중개사명.substring(0, 13) + '...' : item.중개사명}
                        </td>
                        <td class="center-align"><button class="detail-btn" data-link="${index}">상세링크</button></td>
                        <td><button class="map-btn" data-map="${index}">위치</button></td>
                    </tr>`);
                });

                // 전체 거래금액과 전체 건물면적(평) 계산
                let totalDealAmount = 0;
                let totalArea = 0;
                data.forEach(item => {
                    // let amount = Number(item.가격.replace(/,/g, "")) / 10000;
                    let amount = convertKoreanToNumber(item.가격) / 10000;
                    totalDealAmount += amount;
                    let area = parseFloat(item.전용면적평);
                    if (!isNaN(area)) {
                        totalArea += area;
                    }
                });

                // 평균금액: 전체 거래금액 / 거래건수
                let avgDealAmount = data.length > 0 ? totalDealAmount / data.length : 0;
                // 평균단가: 전체 거래금액 / 전체 건물면적(평)
                let avgUnitPrice = totalArea > 0 ? totalDealAmount / totalArea : 0;

                // 평균금액은 한글 형식으로 변환, 평균단가는 천단위 콤마 처리
                let avgDealAmountFormatted = convertToKoreanAmount(avgDealAmount.toFixed(0));
                let avgUnitPriceFormatted = formatNumber(avgUnitPrice.toFixed(0));

                // result-amt 에 평균금액(총건수 기준) 및 평균단가(평 기준) 출력, result-count 에 건수를 출력
                document.getElementById("result-amt").innerHTML = `평균금액/단가: ${avgDealAmountFormatted}/<span style="color: red;">@${avgUnitPriceFormatted}</span>`;
                document.getElementById("result-count").textContent = `건수: ${data.length}`;

                // 매물상세 보기 버튼 이벤트 리스너 추가
                document.querySelectorAll('.detail-btn').forEach(button => {
                    button.addEventListener('click', function () {
                        let index = this.getAttribute('data-link');
                        openDetailPopup(data[index]); // 인덱스도 함께 전달
                    });
                });

                // '지도 보기' 버튼에 이벤트 리스너 추가
                document.querySelectorAll('.map-btn').forEach(button => {
                    button.addEventListener('click', function () {
                        let index = this.getAttribute('data-map');
                        openMap(data[index]);
                    });
                });
            }

            // 상세 보기 버튼 종료 이벤트 리스너 추가
            document.querySelectorAll('.close-btn').forEach(button => {
                button.addEventListener('click', function () {
                    $('#detailPopup').hide();
                });
            });

            function openDetailPopup(item) {
                const article_no = item.기사번호;
                var url = "https://fin.land.naver.com/articles/" + article_no;
                var width = 900;
                var height = 1200;

                // 화면의 중앙 좌표 계산
                var left = (window.innerWidth - width) / 2 + window.screenX;
                var top = (window.innerHeight - height) / 2 + window.screenY;

                // 새 창 열기 (팝업 창)
                var popupWindow = window.open(url, "popup", `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`);

                // 포커스 이동
                if (popupWindow) {
                    popupWindow.focus();
                }
            }

            function openMap(item) {
                const article_no = item.기사번호;
                var url = "https://m.land.naver.com/near/article/" + article_no + "?poi=SCHOOLPOI";
                var width = 1400;
                var height = 1200;

                // 화면의 중앙 좌표 계산
                var left = (window.innerWidth - width) / 2 + window.screenX;
                var top = (window.innerHeight - height) / 2 + window.screenY;

                // 새 창 열기 (팝업 창)
                var popupWindow = window.open(url, "popup", `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`);

                // 포커스 이동
                if (popupWindow) {
                    popupWindow.focus();
                }
            }

            //
            // function openMap(address) {
            //     const width = 1900;
            //     const height = 1280;
            //     const left = (screen.width - width) / 2;
            //     const top = (screen.height - height) / 2;
            //     // 네이버맵 URL은 "https://map.naver.com/v5/search/" 뒤에 인코딩된 주소를 붙여서 사용합니다.
            //     window.open('https://map.naver.com/v5/search/' + encodeURIComponent(address), '_blank', 'width=' + width + ',height=' + height + ',left=' + left + ',top=' + top);
            // }

            // 검색 버튼 클릭 이벤트 수정 (입력 체크 추가)
            $('#search-btn').click(function () {
                let searchTerm = $('#locatadd_nm').val().trim(); // 검색어 가져오기
                if (!searchTerm) { // 검색어가 없을 경우 경고 메시지
                    alert("법정동명을 입력하세요.");
                    $('#locatadd_nm').focus(); // 입력란에 포커스 이동
                    return;
                }
                fetchData(); // 검색어가 존재하면 데이터 검색 실행
            });
            //
            loadYears();

            //=========================================================
            // 조건선택 목록 처리
            function applyFilters() {
                let trade_type = document.getElementById("trade_type").value;
                let category = document.getElementById("category").value;
                let selYear = document.getElementById("sale_year").value;
                // let selMonth = document.getElementById("sale_month").value;
                let selPyeon = document.getElementById("pyeon").value;
                let selFloor = document.getElementById("sel_floor").value;
                let filteredItems = window.allFetchedItems.filter(item => {
                    let ok = true;

                    if (trade_type !== "all") {
                        ok = ok && item.거래유형 && item.거래유형.includes(trade_type.trim());
                    }
                    if (category !== "all") {
                        ok = ok && item.구분 && item.구분.includes(category.trim());
                    }
                    if (selPyeon !== "all") {
                      let p = parseFloat(item.전용면적평).toFixed(0);
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
                    }
                    if (selFloor !== "all") {
                        let p = item.층수 ? item.층수.toString().trim() : ""; // null 방지 + 문자열 변환
                        if (selFloor === "low") {
                            ok = ok && (p === "B1" || p === "B2" || p === "지하" || Number(p) === 1 || Number(p) === 2);
                        } else if (selFloor === "high") {
                            ok = ok && (Number(p) >= 3);
                        } else {
                            if (isNaN(Number(selFloor))) {
                              ok = ok && (p.toString().trim() === selFloor.toString().trim());
                            } else {
                              ok = ok && (Number(p) === Number(selFloor));
                            }
                        }
                    }
                    return ok;
              });
              console.log("필터링된 항목 개수:", filteredItems.length); // 디버깅용 로그

              renderTable(filteredItems);
              // 현재 필터된 데이터 저장 (정렬 시 사용)
              window.currentFilteredItems = filteredItems;
            }
        });