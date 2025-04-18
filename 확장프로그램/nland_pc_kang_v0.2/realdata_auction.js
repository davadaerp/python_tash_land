
        $(document).ready(function() {

            let sortBuildingAscending = true;
            let sortBuildingAreaAscending = true;
            let sortPriceAscending = true;

            // "동" 정렬
            $('#sortBuilding').click(function() {
                window.currentData.sort((a, b) => {
                    let buildingA = parseInt(a.동) || 0;
                    let buildingB = parseInt(b.동) || 0;
                    return sortBuildingAscending ? buildingA - buildingB : buildingB - buildingA;
                });
                sortBuildingAscending = !sortBuildingAscending;
                updateSortIcons();
                renderTable(window.currentData);
            });

            // 건물평수 정렬
            $('#sortBuildingArea').click(function() {
                window.currentData.sort((a, b) => {
                    let areaA = parseFloat(a.건물평수) || 0;
                    let areaB = parseFloat(b.건물평수) || 0;
                    return sortBuildingAreaAscending ? areaA - areaB : areaB - areaA;
                });
                sortBuildingAreaAscending = !sortBuildingAreaAscending;
                updateSortIcons();
                renderTable(window.currentData);
            });

            // 매각금액 정렬
            $('#sortPrice').click(function() {
                window.currentData.sort((a, b) => {
                    let priceA = parseFloat(a.매각금액.replace(/,/g, "")) || 0;
                    let priceB = parseFloat(b.매각금액.replace(/,/g, "")) || 0;
                    return sortPriceAscending ? priceA - priceB : priceB - priceA;
                });
                sortPriceAscending = !sortPriceAscending;
                updateSortIcons();
                renderTable(window.currentData);
            });

            function updateSortIcons() {
                $('#sortBuilding').text(sortBuildingAscending ? '동 ▲' : '동 ▼');
                $('#sortBuildingArea').text(sortBuildingAreaAscending ? '건물평수 ▲' : '건물평수 ▼');
                $('#sortPrice').text(sortPriceAscending ? '매각금액 ▲' : '매각금액 ▼');
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

            function loadCategories() {
                $.ajax({
                    url: 'http://192.168.45.167:5002/api/categories',
                    method: 'GET',
                    dataType: 'json',
                    success: function(data) {
                        let categorySelect = $('#category');
                        Object.keys(data).forEach(key => {
                            categorySelect.append(`<option value="${data[key]}">${data[key]}</option>`);
                        });
                    }
                });
            }

            function fetchData() {
                let searchTerm = $('#search').val();
                let saleYear = $('#sale_year').val();
                let saleMonth = $('#sale_month').val();
                let category = $('#category').val();

                $('#loading').show();
                $('#noData').hide();
                $('table').hide();

                $.ajax({
                    url: 'http://192.168.45.167:5002/api/data',
                    method: 'GET',
                    data: {
                        searchTerm: searchTerm,
                        saleYear: saleYear,
                        saleMonth: saleMonth,
                        category: category
                    },
                    dataType: 'json',
                    success: function (data) {
                        $('#loading').hide();
                        if (data.length === 0) {
                            $('#noData').show();
                        } else {
                            $('#noData').hide();
                            $('table').show();
                            window.currentData = data;
                            renderTable(data);
                            $('#searchCount').text(`건수: ${data.length}건`);
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
                        <!--
                        <td class="center-align">${formatNumber(item.감정금액평단가)}만/${formatNumber(item.최저금액평단가)}만/${formatNumber(item.매각금액평단가)}만</td>
                        -->
                        <td class="center-align"><button class="map-btn" data-address="${item.주소1}">지도</button></td>
                        <td><button class="detail-btn" data-index="${index}">상세</button></td>
                    </tr>`);
                });

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

            $('#searchBtn').click(fetchData);
            //
            loadCategories();
            loadYears();
            //fetchData();
        });