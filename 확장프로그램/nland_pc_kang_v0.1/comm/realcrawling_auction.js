        //
        let selectedLawdCd = "";
        let selectedUmdNm = "";
        let selectedIndex = -1;
        window.allFetchedItems = [];

        $(document).ready(function() {

            let sortHouseAscending = true;
            let sortBuildingAscending = true;
            let sortFloorAscending = true;
            let sortBuildingAreaAscending = true;
            let sortPriceAscending = true;

            // "종류(아파트,빌라등)" 정렬
            $('#sortHouse').click(function() {
                 window.currentFilteredItems.sort((a, b) => {
                    let buildingA = a.구분 ? a.구분.toString() : ""; // 문자열 변환 및 예외 처리
                    let buildingB = b.구분 ? b.구분.toString() : "";

                    return sortHouseAscending
                        ? buildingA.localeCompare(buildingB, 'ko-KR')
                        : buildingB.localeCompare(buildingA, 'ko-KR');
                });
                sortHouseAscending = !sortHouseAscending;
                updateSortIcons();
                renderTable(window.currentFilteredItems);
            });

            // "동" 정렬
            $('#sortBuilding').click(function() {
                window.currentFilteredItems.sort((a, b) => {
                    let buildingA = parseInt(a.동) || 0;
                    let buildingB = parseInt(b.동) || 0;
                    return sortBuildingAscending ? buildingA - buildingB : buildingB - buildingA;
                });
                sortBuildingAscending = !sortBuildingAscending;
                updateSortIcons();
                renderTable(window.currentFilteredItems);
            });

            // "층" 정렬
            $('#sortFloor').click(function() {
                window.currentFilteredItems.sort((a, b) => {
                    let buildingA = parseInt(a.층) || 0;
                    let buildingB = parseInt(b.층) || 0;
                    return sortFloorAscending ? buildingA - buildingB : buildingB - buildingA;
                });
                sortFloorAscending = !sortFloorAscending;
                updateSortIcons();
                renderTable(window.currentFilteredItems);
            });

            // 건물평수 정렬
            $('#sortBuildingArea').click(function() {
                window.currentFilteredItems.sort((a, b) => {
                    let areaA = parseFloat(a.건물평수) || 0;
                    let areaB = parseFloat(b.건물평수) || 0;
                    return sortBuildingAreaAscending ? areaA - areaB : areaB - areaA;
                });
                sortBuildingAreaAscending = !sortBuildingAreaAscending;
                updateSortIcons();
                renderTable(window.currentFilteredItems);
            });

            // 매각금액 정렬
            $('#sortPrice').click(function() {
                window.currentFilteredItems.sort((a, b) => {
                    let priceA = parseFloat(a.매각금액.replace(/,/g, "")) || 0;
                    let priceB = parseFloat(b.매각금액.replace(/,/g, "")) || 0;
                    return sortPriceAscending ? priceA - priceB : priceB - priceA;
                });
                sortPriceAscending = !sortPriceAscending;
                updateSortIcons();
                renderTable(window.currentFilteredItems);
            });

            function updateSortIcons() {
                $('#sortHouse').text(sortHouseAscending ? '구분 ▲' : '구분 ▼');
                $('#sortBuilding').text(sortBuildingAscending ? '동 ▲' : '동 ▼');
                $('#sortFloor').text(sortFloorAscending ? '층 ▲' : '층 ▼');
                $('#sortBuildingArea').text(sortBuildingAreaAscending ? '건물평수 ▲' : '건물평수 ▼');
                $('#sortPrice').text(sortPriceAscending ? '매각금액 ▲' : '매각금액 ▼');
            }

            // 단지명 검색 이벤트 처리
            // document.addEventListener("DOMContentLoaded", function() {
            //     document.getElementById("aptNm").addEventListener("keydown", applyFilters);
            // });
            // 단지명 검색 이벤트 처리 - 적용 위치 변경
            $("#aptNm").on("keydown", applyFilters);

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

            let categoryOptions = [];
            function loadCategories() {
                $.ajax({
                    url: 'http://192.168.45.167:5002/api/categories',
                    method: 'GET',
                    dataType: 'json',
                    success: function(data) {
                        categoryOptions = data;
                        // main-category추가함
                        populateMainCategory(categoryOptions);
                    }
                });
            }

            function fetchData() {
                //
                document.getElementById("result-amt").textContent = "평균금액/단가: 0/0";
                document.getElementById("result-count").textContent = "건수: 0건";
                document.getElementById("aptNm").value = "";

                let searchTerm = $('#locatadd_nm').val();
                let saleYear = $('#sale_year').val();
                let saleMonth = $('#sale_month').val();
                let mainCategory = $('#main-category').val();
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
                        saleYear: saleYear,
                        saleMonth: saleMonth,
                        mainCategory: mainCategory,
                        category: category,
                        dangiName: dangiName
                    },
                    dataType: 'json',
                    timeout: 5000,  // 5초 타임아웃 설정
                    beforeSend: function() {
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

             function renderTable(data) {
                let tableBody = $('#dataBody');
                tableBody.empty();
                data.forEach((item, index) => {
                    let fullAddress = `${item.지역} ${item.시군구} ${item.법정동}`.trim();
                    tableBody.append(`<tr>
                        <td class="center-align">${item.매각일자}</td>
                        <td class="center-align">${item.사건번호}</td>
                        <td class="center-align">${item.구분}</td>
                        <td class="center-align">${item.동}</td>
                        <td class="center-align">${item.층}</td>
                        <!--
                        <td>${fullAddress}</td>
                        --->
                        <td class="center-align">${item.건물평수}</td>
                        <td class="center-align">${item.대지평수}</td>
                        <td class="right-align">${formatNumber(item.감정금액)}</td>
                        <td class="right-align">${formatNumber(item.최저금액)}<br><span class="center-align">(${item.최저퍼센트})</span></td>
                        <td class="highlight right-align">${formatNumber(item.매각금액)}<br><span class="highlight center-align">(${item.매각퍼센트})</span></td>
                        <td class="center-align">${item.단지명}</td>
                        <!--
                        <td class="center-align">${formatNumber(item.감정금액평단가)}만/${formatNumber(item.최저금액평단가)}만/${formatNumber(item.매각금액평단가)}만</td>
                        -->
                        <td class="center-align"><button class="map-btn" data-address="${item.주소1}">지도</button></td>
                        <td><button class="detail-btn" data-index="${index}">상세</button></td>
                    </tr>`);
                });

                // 전체 거래금액과 전체 건물면적(평) 계산
                let totalDealAmount = 0;
                let totalArea = 0;
                data.forEach(item => {
                  let amount = Number(item.매각금액.replace(/,/g, "")) / 10000;
                  totalDealAmount += amount;
                  let area = parseFloat(item.건물평수);
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

                // '지도 보기' 버튼에 이벤트 리스너 추가
                document.querySelectorAll('.map-btn').forEach(button => {
                    button.addEventListener('click', function() {
                        let address = this.getAttribute('data-address');
                        openMap(address);
                    });
                });

                // 상세 보기 버튼 이벤트 리스너 추가
                document.querySelectorAll('.detail-btn').forEach(button => {
                    button.addEventListener('click', function() {
                        let index = this.getAttribute('data-index');
                        openDetailPopup(data[index]); // 인덱스도 함께 전달
                    });
                });
            }

            // 상세 보기 버튼 종료 이벤트 리스너 추가
            document.querySelectorAll('.close-btn').forEach(button => {
                button.addEventListener('click', function() {
                    $('#detailPopup').hide();
                });
            });

            function openMap(address) {
              const width = 1900;
              const height = 1280;
              const left = (screen.width - width) / 2;
              const top = (screen.height - height) / 2;
              // 네이버맵 URL은 "https://map.naver.com/v5/search/" 뒤에 인코딩된 주소를 붙여서 사용합니다.
              window.open('https://map.naver.com/v5/search/' + encodeURIComponent(address), '_blank', 'width=' + width + ',height=' + height + ',left=' + left + ',top=' + top);
            }

            function openDetailPopup(item) {
                let fullRowData = {
                    "매각일자": item.매각일자 || "",
                    "사건번호": item.사건번호 || "",
                    "구분": item.구분 || "",
                    "주소1": item.주소1 || "",
                    "법정동": item.법정동 || "",
                    "건물면적(m2)": item.건물m2 || "",
                    "건물면적(평)": item.건물평수 || "",
                    "대지면적(m2)": item.대지m2 || "",
                    "대지면적(평)": item.대지평수 || "",
                    "감정금액": formatNumber(item.감정금액) || "",
                    "최저금액": formatNumber(item.감정금액) || "",
                    "매각금액": formatNumber(item.매각금액) || "",
                    "최저퍼센트": item.최저퍼센트 || "",
                    "매각퍼센트": item.매각퍼센트 || "",
                    "감정금액 평단가": formatNumber(item.감정금액평단가) || "만",
                    "최저금액 평단가": formatNumber(item.최저금액평단가) || "만",
                    "매각금액 평단가": formatNumber(item.매각금액평단가) || "만"
                };
                let detailContent = `<ul>`;
                for (let key in fullRowData) {
                    detailContent += `<li><strong>${key}:</strong> ${fullRowData[key]}</li>`;
                }
                detailContent += `</ul>`;

                $('#detailContent').html(detailContent);
                $('#detailPopup').show(); // 팝업 표시
            }

            // 검색 버튼 클릭 이벤트 수정 (입력 체크 추가)
            $('#search-btn').click(function() {
                let searchTerm = $('#locatadd_nm').val().trim(); // 검색어 가져오기
                if (!searchTerm) { // 검색어가 없을 경우 경고 메시지
                    alert("법정동명을 입력하세요.");
                    $('#locatadd_nm').focus(); // 입력란에 포커스 이동
                    return;
                }
                fetchData(); // 검색어가 존재하면 데이터 검색 실행
            });
            //
            loadCategories();
            loadYears();

            //=========================================================
            // 메인카테고리 서버읽어와서 처리
            function populateMainCategory(categories) {
                let $mainCategory = $("#main-category");
                //$mainCategory.empty(); // 기존 옵션 초기화

                // JSON 데이터의 1레벨 키 값을 main-category의 옵션으로 추가
                Object.keys(categories).forEach(function (key) {
                    $mainCategory.append(`<option value="${key}">${key}</option>`);
                });
            }

            // 메인카테고리 선택시
            document.getElementById('main-category').addEventListener('change', function() {
                let selectedMain = this.value;
                let categorySelect = document.getElementById('category');
                categorySelect.innerHTML = '';

                if (categoryOptions[selectedMain]) {
                    categoryOptions[selectedMain].forEach(option => {
                        let opt = document.createElement('option');
                        opt.value = option === "전체" ? "" : option;
                        opt.textContent = option;
                        categorySelect.appendChild(opt);
                    });
                } else {
                    let opt = document.createElement('option');
                    opt.value = '';
                    opt.textContent = '전체';
                    categorySelect.appendChild(opt);
                }
            });

            // 조건선택 및 단지명입력 목록 처리
            function applyFilters() {
              let selAptNm = document.getElementById("aptNm").value;
              console.log(selAptNm);
              let filteredItems = window.allFetchedItems.filter(item => {
                let ok = true;
                if (selAptNm.trim() !== "") {
                  ok = ok && item.단지명 && item.단지명.includes(selAptNm.trim());
                }
                return ok;
              });
              renderTable(filteredItems);
              // 현재 필터된 데이터 저장 (정렬 시 사용)
              window.currentFilteredItems = filteredItems;
            }
        });