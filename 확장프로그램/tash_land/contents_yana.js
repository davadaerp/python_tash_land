
let oldItems;
let observer; // observer를 외부에서 선언
let isScheduled = false; // 함수 호출이 예약되었는지 여부를 나타내는 플래그(중복실행방지)
//
let tableData = []; // 테이블 만들 데이터 { key: data, key2: data2} 형식으로 저장
let tabGubun = '';
let BASE_URL = "https://erp-dev.bacchuserp.com";
let currSelectedType = 'all';
let isLoggedInStatus = false;
let apt_key = "";
let villa_key = "";
let sanga_key = "";

// config으로 만들 부분
let autoScroll = true;
let contiStatus = false;
let dangaAsc = true;
let summaryListShowStatus = false;
let percentMargin = 6;
let onoffstatus = true;
// config으로 만들 부분 끝

// 가격에 평당가및 기타 부문추가함
function sangaItemRowModify(item, type, area, pdanga, price) {

    const priceElement = item.querySelector('.price'); // 금액정보
    if (type === '매매') {
        // 매매 정보를 붉은색으로 표시
        if (!priceElement.dataset.highlighted) {
            const priceSpan = document.createElement('span');
            priceSpan.textContent = `(${area}평 @${pdanga}만)`;
            priceSpan.style.opacity = 0.5; // 50% opacity
            priceSpan.style.color = 'green';
            priceSpan.style.fontSize = '11pt';
            priceElement.appendChild(priceSpan);
            priceElement.dataset.highlighted = true; // 한 번만 실행되도록 표시
        }
    }
    if (type === '월세') {
        // 월세 정보를 붉은색으로 표시
        if (!priceElement.dataset.highlighted) {
            const priceSpan = document.createElement('span');
            priceSpan.textContent = `(${area}평 @${pdanga}만`;
            priceSpan.style.opacity = 0.5; // 50% opacity
            priceSpan.style.color = 'red';
            priceSpan.style.fontSize = '11pt';

            const priceSpan2 = document.createElement('span');
            priceSpan2.textContent = `  >>${price}억)`;
            priceSpan2.style.opacity = 0.5; // 50% opacity
            priceSpan2.style.color = 'violet';
            priceSpan2.style.fontSize = '13pt';

            priceElement.appendChild(priceSpan);
            priceElement.appendChild(priceSpan2);

            priceElement.dataset.highlighted = true; // 한 번만 실행되도록 표시
        }
    }
    // 불필요한 요소 숨김 처리(위 삭제하면 동일묶음에서 에러발생)
    ['.tag_area', '.cp_area', '.label_area'].forEach(selector => {
        const element = item.querySelector(selector);
        //if (element) element.remove();
        if (element) element.style.display = 'none';
    });
    // class="banner type_performance" 포함 요소 삭제
    const bannerElement = item.querySelector('.banner.type_performance');
    if (bannerElement) bannerElement.remove();
}

// innerHTML에서 데이터를 추출하여 tableitem 객체를 반환하는 함수
function extractSangaItemFromHTML(item) {

    // console.log('로드된 item:', item);
    // console.log('innerHTML:', item.innerHTML);
    // console.log('innerText:', item.innerText);

      // 임시 컨테이너 생성 후 innerHTML 삽입
      const container = document.createElement("div");
      container.innerHTML =  item.innerHTML;

      // 1. 형태(type): price_line 내의 .type 텍스트 (예: "월세" 또는 "매매")
      const typeEl = container.querySelector(".price_line .type");
      const type = typeEl ? typeEl.textContent.trim() : "";

      // 2. 구분(title): item_title 내의 .text (예: "일반사무실")
      const titleEl = container.querySelector(".item_title .text");
      const title = titleEl ? titleEl.textContent.trim() : "";

      // 3. spec 파싱: 첫번째 spec에 "분양면적/전용면적, 해당층/전체층, 향" 정보가 포함됨
      // 예: "42/33m², 1/1층, 동향"
      let saleArea = "", exclusiveArea = "", cfloor = "", tfloor = "", direction = "";
      const specEls = container.querySelectorAll(".info_area .spec");
      let specText = "";
      if (specEls && specEls.length > 0) {
        specText = specEls[0].textContent.trim();
      }
      // spec를 콤마(,) 기준으로 분리
      const parts = specText.split(",");
      if (parts.length >= 1) {
        // 첫번째 부분: 분양면적/전용면적 (예: "42/33m²")
        const areaPart = parts[0].trim().replace("m²", "");
        const areaParts = areaPart.split("/");
        if (areaParts.length >= 2) {
          const areaPrts1 = parseInt(areaParts[0].trim()) * 0.3025;
          const areaPrts2 = parseInt(areaParts[1].trim()) * 0.3025;
          // 분양면적,전용면적
          saleArea = areaPrts1.toFixed(2);
          exclusiveArea = areaPrts2.toFixed(2);
        }
      }
      if (parts.length >= 2) {
        // 두번째 부분: 해당층/전체층 (예: "1/1층")
        const floorPart = parts[1].trim().replace("층", "");
        const floorParts = floorPart.split("/");
        if (floorParts.length >= 2) {
          cfloor = floorParts[0].trim();
          tfloor = floorParts[1].trim();
        }
      }
      if (parts.length >= 3) {
        // 세번째 부분: 향 (예: "동향")
        direction = parts[2].trim();
      }

      // 4. 가격(price): price_line 내의 .price (예: "300/30")
      const priceEl = container.querySelector(".price_line .price");
      const price = priceEl ? priceEl.textContent.trim() : "";
      //console.log('price:', price);

      // 5. 기타(etc): 두번째 spec(있다면)와 tag_area의 태그들을 모두 연결하여 구성
      let etc = "";
      if (specEls && specEls.length > 1) {
        etc += specEls[1].textContent.trim();
      }
      const tagEls = container.querySelectorAll(".tag_area .tag");
      tagEls.forEach(tag => {
        etc += " " + tag.textContent.trim();
      });
      etc = etc.trim();

      // 6. 평당가(pdanga): 가격에서 첫번째 숫자를 전용면적으로 나눈 값 (숫자일 경우)
      let pdanga = "";
      // 먼저 '(' 앞까지만 잘라냄 => "3,000/30(106.18평 @6.1만)";
      const priceBeforeParen = price.split('(')[0];
      // '/' 기준으로 보증금과 월세 분리
      const priceParts = priceBeforeParen.split('/');
      let calcPrice = 0;
      let calcRentSalePrice = 0;    // 월세기반 매매가계산
      //
      if (type === '매매' || type === '전세')  {
              // calcPrice 문자열에서 억, 천 단위 정보를 추출하여 price와 pdanga 계산
            const salePrice = priceParts[0].trim(); // 예: "2억" 또는 "2억 5,000"
            const regex = /(\d+)\s*억(?:\s*([\d,]+))?/; // 첫 번째 그룹: 억 단위, 두 번째 그룹(선택): 천 단위
            const match = salePrice.match(regex);

            if (match) {
                // 억 단위는 1억당 10000 단위로 변환
                const billionPart = parseInt(match[1], 10) * 10000;
                // 천 단위가 있으면 콤마 제거 후 숫자로 변환, 없으면 0
                const thousandPart = match[2] ? parseInt(match[2].replace(/,/g, ''), 10) : 0;
                calcPrice = billionPart + thousandPart;
            } else {
                // 정규식 매칭에 실패하면, salePrice를 숫자만 추출하여 처리 (예외 처리)
                calcPrice = parseFloat(salePrice.replace(/[^0-9.]/g, ''));
            }
            pdanga = (calcPrice / parseFloat(exclusiveArea)).toFixed(0);
      }
      //
      if (type === '월세')  {
            const savePrice = priceParts[0].replace(/[^0-9]/g, '');    // 보증금
            const rentPrice = priceParts[1].replace(/[^0-9]/g, '');    // 월세
            calcPrice = savePrice + '/' + rentPrice;
            pdanga = (parseInt(rentPrice) / parseFloat(exclusiveArea)).toFixed(1);
            // 월세기반 매매가계산
            //const percentMargin = document.getElementById("percentMargin").value;
            calcRentSalePrice = parseInt(rentPrice) * 12 * 100 / percentMargin / 10000;
      }

      // tableitem 객체 구성 (분양면적과 전용면적은 각각 saleArea, exclusiveArea로 할당)
      const tableitem = {
        "구분": title,
        "형태": type,
        "해당층": cfloor,
        "전체층": tfloor,
        "향": direction,
        "평당가": pdanga,
        "분양면적": saleArea,
        "전용면적": exclusiveArea,
        "가격": calcPrice,
        "기타": etc
      };
      //데이터를 배열화
      tableData.push(tableitem);

      //console.log(tableitem);

      // 목록상태수정(월세/매매,전용평,평당가,월세기반매매가-수익율기준)
      sangaItemRowModify(item, type, exclusiveArea, pdanga, calcRentSalePrice);
}

// div 요소들끼리 정리하는 부분
function sortItems() {
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

// 요약목록 테이블
function summaryTable() {
    const mapWrap = document.querySelector('.map_wrap'); // .map_wrap 클래스를 가진 요소 선택
    if (mapWrap) {
        console.log('mapWrap Start..');
        // 1. newBox를 찾아서 없으면 생성
        let newBox = mapWrap.querySelector('.new-box');
        if (!newBox) {
            newBox = document.createElement('div');
            newBox.classList.add('new-box');
            mapWrap.appendChild(newBox);
        }
        // newBox 스타일 옵션 추가
        newBox.style.width = '400px';
        newBox.style.height = tabGubun === 'sanga' ? '80px' : '95px';
        newBox.style.padding = '5px';
        newBox.style.backgroundColor = '#ffffff';
        newBox.style.zIndex = '9999';
        newBox.style.position = 'absolute';
        newBox.style.top = '0px';
        newBox.style.left = '0px';
        //newBox.style.border = '1px solid #ccc'; // newBox에 테두리 추가

        // 2. tableData에서 평당가 데이터를 이용하여 통계 계산
        function computeStats(dataArray, isSale) {
            if (dataArray.length === 0) return { min: '-', avg: '-', max: '-', count: 0 };
            const min = Math.min(...dataArray);
            const max = Math.max(...dataArray);
            const sum = dataArray.reduce((acc, val) => acc + val, 0);
            const avg = (sum / dataArray.length).toFixed(isSale ? 0 : 1);
            return { min, avg, max, count: dataArray.length };
        }

        // tableData 필터링: 월세, 전세, 매매 데이터 각각
        const 월세Data = tableData.filter(item => item["형태"] === '월세').map(item => parseFloat(item["평당가"]));
        const 전세Data = tableData.filter(item => item["형태"] === '전세').map(item => parseFloat(item["가격"]));
        const 매매Data = tableData.filter(item => item["형태"] === '매매').map(item => parseFloat(item["가격"]));
        const stats월세 = computeStats(월세Data, false);
        const stats전세 = computeStats(전세Data, true);
        const stats매매 = computeStats(매매Data, true);

        // tabGubun이 'villa' 또는 'apt'인 경우 전세 행 추가
        let 전세RowHTML = '';
        if (tabGubun === 'villa' || tabGubun === 'apt') {
            전세RowHTML = `
                          <tr>
                              <td style="background-color: #eeffe6; text-align: center;">전세</td>
                              <td>${formatCurrency('전세',stats전세.min)}</td>
                              <td>${formatCurrency('전세',stats전세.avg)}</td>
                              <td>${formatCurrency('전세',stats전세.max)}</td>
                              <td>${stats전세.count}</td>
                          </tr>
            `;
        }

        // 3. 왼쪽: 통계 테이블, 오른쪽: 컨트롤(요약표 버튼, 수익율(%) 레이블, 수익율 input)을
        //    위에서 아래로 나열하는 테이블 형식으로 배치하고, outer table 높이를 newBox 높이에 맞춤
        const combinedHTML = `
            <table border="0" style="width: 100%; height: 100%; border-collapse: collapse; text-align: center;">
              <tr>
                <!-- 왼쪽 통계 테이블 -->
                <td style="vertical-align: top; width: 85%; padding-left: 5px;">
                  <table border="1" style="width: 100%; height: 100%; border-collapse: collapse;">
                      <thead style="background-color: #e0f7ff;">
                          <tr>
                              <th>구분</th>
                              <th>최소</th>
                              <th>평균</th>
                              <th>최대</th>
                              <th>건수</th>
                          </tr>
                      </thead>
                      <tbody>
                          <tr>
                              <td style="background-color: #ffe6e6; text-align: center;">월세</td>
                              <td>${formatCurrency('월세', stats월세.min)}</td>
                              <td>${formatCurrency('월세', stats월세.avg)}</td>
                              <td>${formatCurrency('월세', stats월세.max)}</td>
                              <td>${stats월세.count}</td>
                          </tr>
                          ${전세RowHTML}
                          <tr>
                              <td style="background-color: #ADD8E6; text-align: center;">매매</td>
                              <td>${formatCurrency('매매', stats매매.min)}</td>
                              <td>${formatCurrency('매매', stats매매.avg)}</td>
                              <td>${formatCurrency('매매', stats매매.max)}</td>
                              <td>${stats매매.count}</td>
                          </tr>
                      </tbody>
                  </table>
                </td>
                <!-- 오른쪽 컨트롤 영역 -->
                <td style="vertical-align: top; padding-left: 5px; width: 17%;">
                  <table border="0" style="height: 100%; border-collapse: collapse;">
                     <tr>
                        <td style="padding-bottom: 5px;">
                           <button id="summaryBtn" style="border: 1px solid #555555; border-radius:5px; padding:2px 5px;">요약표</button>
                        </td>
                     </tr>
                     <tr>
                        <td style="padding-bottom: 2px; border: 1px solid #ccc;">
                           <label for="percentMargin">수익율</label>
                        </td>
                     </tr>
                     <tr>
                        <td style="border: 1px solid #ccc;">
                           <input type="text" id="percentMargin" value="6%" style="width:40px; background-color:#f0f0f0; text-align: center;">
                        </td>
                     </tr>
                  </table>
                </td>
              </tr>
            </table>
        `;

        // newBox 안에 결합된 HTML 삽입
        newBox.innerHTML = combinedHTML;

        // 4. 요약표 버튼에 클릭 이벤트 등록 (클릭 시 sangaSummaryList() 실행)
        const summaryBtn = newBox.querySelector('#summaryBtn');
        if (summaryBtn) {
            summaryBtn.addEventListener('click', function() {
                // 로그인여부 체크
                loginValid().then(valid => {
                    if (!valid) return;   // 로그인 실패 시 여기서 중단
                    //
                    summaryListShowStatus = true;
                    if(tabGubun === 'sanga') {
                        sangaSummaryList();
                    } else {
                        villaSummaryList();
                    }
                });
            });
        }
    }
}

// 요약목록 리스트 헤더
function summaryListHeader() {
    // 1. 새로운 박스(newBox2) 생성 (summaryBtn을 눌렀을 때 new-box 오른쪽에 위치)
      const mapWrap = document.querySelector('.map_wrap');
      if (!mapWrap) return;
      // 검색후 삭제함.
      let newBox2 = document.getElementById("sum-list-box")
      if (newBox2) {
          newBox2.remove();
      }
      newBox2 = document.createElement('div');
      newBox2.classList.add('new-box2'); // 클래스 이름은 점(.) 없이 사용
      mapWrap.appendChild(newBox2);
      //
      newBox2.id = "sum-list-box";
      newBox2.style.width = '400px';
      newBox2.style.height = '690px';
      newBox2.style.padding = '10px';
      newBox2.style.backgroundColor = '#ffffff';
      newBox2.style.zIndex = '9999';
      newBox2.style.position = 'absolute';
      newBox2.style.top = '0px';
      newBox2.style.left = '403px';
      newBox2.style.overflowY = 'auto';

      // 2. 상단 영역 - select 박스와 버튼들 생성
      // 2.1 구분(selectBox): tableData에서 "형태" 값(예: 월세, 전세, 매매) 고유값 구하기
      let types = Array.from(new Set(tableData.map(item => item["형태"])));
      const fixedOrder = ["월세", "전세", "매매"];
      types.sort((a, b) => fixedOrder.indexOf(a) - fixedOrder.indexOf(b));
      let typeOptions = `<option value="all" ${currSelectedType === 'all' ? 'selected' : ''}>전체</option>`;
      types.forEach(t => {
        typeOptions += `<option value="${t}" ${currSelectedType === t ? 'selected' : ''}>${t}</option>`;
      });

      // 2.2 층(selectBox): tableData에서 "해당층" 값 고유값 구하기
      let floors = Array.from(new Set(tableData.map(item => item["해당층"])));
      floors.sort((a, b) => a - b);
      let floorOptions = `
          <option value="all">전체</option>
          <option value="low">저층</option>
          <option value="high">상층</option>`;
      floors.forEach(f => {
        floorOptions += `<option value="${f}">${f}층</option>`;
      });

      // 2.3 상단 버튼들 (평형분석, 실거래, 배후분석, 닫기)
      let topBarHTML = `
          <div class="top-bar" style="display:flex; align-items:center; justify-content:space-between; margin-bottom:5px;">
            <div class="select-group" style="display:flex; align-items:center;">
              <select id="selectGroup" style="margin-left:2px; margin-right:5px; background-color:red; outline:1px solid #555555; height:24px; padding:2px 5px; border-radius:4px; font-size:14px;">${typeOptions}</select>
              <select id="selectFloor" style="margin-right:5px; background-color:blue; color:#ffffff; outline:1px solid #555555; height:24px; padding:2px 5px; border-radius:4px; font-size:14px;">${floorOptions}</select>
            </div>
            <div class="button-group" style="display:flex; align-items:center;">
              <button id="pyeongButton" style="border:1px solid #555555; margin-left:3px; margin-right:3px; border-radius:5px; padding:2px 5px;">평형분석</button>
              <button id="realButton" style="border:1px solid #555555; margin-left:3px; margin-right:3px; border-radius:5px; padding:2px 5px;">실거래분석</button>
              <button id="baehuButton" style="border:1px solid #555555; margin-left:3px; margin-right:3px; border-radius:5px; padding:2px 5px;">배후분석</button>
              <button id="closeButton" style="border:1px solid #555555; margin-left:3px; margin-right:3px; border-radius:5px; padding:2px 5px;">닫기</button>
            </div>
          </div>
    ` ;
      newBox2.innerHTML = topBarHTML;
      // 테이블 업데이트를 위한 컨테이너 생성
      const tableContainer = document.createElement('div');
      tableContainer.id = "tableContainer";
      newBox2.appendChild(tableContainer);

      // 6. 버튼 이벤트 등록
      const pyeongButton = newBox2.querySelector('#pyeongButton');
      if (pyeongButton) {
        pyeongButton.addEventListener('click', () => {
            sangaPyeongPopup(); // 평형분석 팝업 호출 (정의되어 있어야 함)
        });
      }
      const realButton = newBox2.querySelector('#realButton');
      if (realButton) {
        realButton.addEventListener('click', () => {
            // 실거래분석(국토부및경매데이터)
            analyzeRealdealDemand();
        });
      }
      const baehuButton = newBox2.querySelector('#baehuButton');
      if (baehuButton) {
        baehuButton.addEventListener('click', () => {
            // 배후분석(마이프차접속)
            analyzeCatchmentDemand();
        });
      }
      const closeButton = newBox2.querySelector('#closeButton');
      if (closeButton) {
        closeButton.addEventListener('click', () => {
          //newBox2.style.display = 'none';
            summaryListShowStatus = false;
            newBox2.remove();
        });
      }
}

// 상가 요약목록 리스트
function sangaSummaryList() {

    // 헤더정의
    summaryListHeader();

    // 3. 데이터 중복 제거: 구분(형태), 평당가, 면적(전용면적), 가격이 동일하면 1개만 남김
    // let uniqueDataMap = {};
    // tableData.forEach(item => {
    //   const key = item["형태"] + "_" + item["평당가"] + "_" + item["전용면적"] + "_" + item["가격"];
    //   uniqueDataMap[key] = item;
    // });
    let uniqueDataMap = tableData;

    // 전역 변수: 평당가 정렬 순서 (true: 오름차순, false: 내림차순)
    let pdangaSortAsc = true;

    // 4. 테이블 업데이트 함수 (필터 조건에 따라 통계표와 상세 리스트 재생성)
    function updateTables() {
        // 4.1 선택된 구분 및 층 값 읽기 (구분은 uniqueDataMap의 데이터를 필터링)
        const selectedType = document.getElementById('selectGroup').value;
        const selectedFloor = document.getElementById('selectFloor').value;
        let filteredData = Object.values(uniqueDataMap);
        if (selectedType !== "all") {
          filteredData = filteredData.filter(item => item["형태"] === selectedType);
        }
        if (selectedFloor !== "all") {
          filteredData = filteredData.filter(item => {
            const floor = item["해당층"];
            if (selectedFloor === "low") {
              return ["B1", "B2", "B3", "1", "2"].includes(floor);
            } else if (selectedFloor === "high") {
              const floorNumber = parseInt(floor);
              return !isNaN(floorNumber) && floorNumber >= 3;
            } else {
              return floor === selectedFloor;
            }
          });
        }
        currSelectedType = selectedType;

        // 4.2 첫 번째 테이블 - 통계표 생성 (구분별, 층별 통계)
        function getFloorGroup(cfloor) {
          const num = parseFloat(cfloor);
          if (isNaN(num)) return "기타";
          if (num === 1) return "1층";
          else if (num === 2) return "2층";
          else if (num >= 3) return "상층";
          else return num + "층";
        }
        let summaryGroups = {};
        filteredData.forEach(item => {
          const type = item["형태"];
          const floorGroup = getFloorGroup(item["해당층"]);
          let value = (type === "월세") ? parseFloat(item["평당가"]) : parseFloat(item["가격"]);
          if (!summaryGroups[type]) summaryGroups[type] = {};
          if (!summaryGroups[type][floorGroup]) summaryGroups[type][floorGroup] = [];
          if (!isNaN(value)) {
            summaryGroups[type][floorGroup].push(value);
          }
        });
        function computeStatsForGroup(arr, isSale) {
          if (arr.length === 0) return { min: '-', avg: '-', max: '-', count: 0 };
          const min = Math.min(...arr);
          const max = Math.max(...arr);
          const sum = arr.reduce((acc, cur) => acc + cur, 0);
          const avg = (sum / arr.length).toFixed(isSale ? 0 : 2);
          return { min, avg, max, count: arr.length };
        }
        //
        let summaryStatsHTML = `
          <table border="1" style="width:100%; border-collapse:collapse; text-align:center; margin-bottom:10px;">
            <thead style="background-color:#e0f7ff;">
              <tr>
                <th>구분</th>
                <th>층</th>
                <th>최소</th>
                <th>평균</th>
                <th>최대</th>
                <th>건수</th>
              </tr>
            </thead>
            <tbody>
        `;
        // selectGroup의 현재 선택값 가져오기
        const selectedGroup = document.getElementById("selectGroup").value;
        // 선택값에 따라 타입 배열 구성
        let groupTypes = [];
        if (selectedGroup === "all") {
          groupTypes = ["월세", "매매"];
        } else {
          groupTypes = [selectedGroup];
        }
        groupTypes.forEach((type, typeIdx) => {
          const isSale = (type === "매매");
          const floorOrder = ["1층", "2층", "상층"];
          floorOrder.forEach((floor, floorIdx) => {
            let stats = { min: '-', avg: '-', max: '-', count: 0 };
            if (summaryGroups[type] && summaryGroups[type][floor]) {
              stats = computeStatsForGroup(summaryGroups[type][floor], isSale);
            }

            // 마지막 행 체크: 표시되는 마지막 행에 굵은 하단 테두리
            const isLastRow = (type === "월세" && floorIdx === floorOrder.length - 1);
            const borderBottomStyle = isLastRow ? "border-bottom:1px solid #000;" : "";
            const avgStyle = type === "월세" ? "color:red; font-weight:bold;" : "";
            const typeStyle = type === "매매" ? "color:blue;" : "";
            const countStyle = type === "매매" ? "color:blue;" : "";

            summaryStatsHTML += `
              <tr style="${borderBottomStyle}">
                <td style="${typeStyle}">${type}</td>
                <td>${floor}</td>
                <td>${formatCurrency(type, stats.min)}</td>
                <td style="${avgStyle}>">${formatCurrency(type, stats.avg)}</td>
                <td>${formatCurrency(type, stats.max)}</td>
                <td style="${countStyle}">${stats.count}</td>
              </tr>
            `;
          });
        });
        summaryStatsHTML += `</tbody></table>`;

        // 4.3 두 번째 테이블 - 상세 리스트 생성
        // 평당가 헤더에 id="sortPdanga"와 현재 정렬 순서 화살표 표시
        const arrowSymbol = pdangaSortAsc ? "▲" : "▼";
        // 형태별 그룹 정렬: 월세가 먼저 나오고, 같은 그룹 내에서 평당가를 정렬
        let sortedUniqueData = filteredData.slice().sort((a, b) => {
          if (a["형태"] !== b["형태"]) {
            return a["형태"] === "월세" ? -1 : 1;
          } else {
            const pdA = parseFloat(a["평당가"]) || 0;
            const pdB = parseFloat(b["평당가"]) || 0;
            return pdangaSortAsc ? pdA - pdB : pdB - pdA;
          }
        });
        let detailTableHTML = `
          <table border="1" style="width:100%; border-collapse:collapse; text-align:center; margin-bottom:10px;">
            <thead style="background-color:#e0f7ff;">
              <tr>
                <th>구분</th>
                <th>층</th>
                <th>향</th>
                <th id="sortPdanga" style="cursor:pointer;">평당가 ${arrowSymbol}</th>
                <th>면적</th>
                <th>가격</th>
              </tr>
            </thead>
            <tbody>
        `;
        sortedUniqueData.forEach(item => {
          const floorDisplay = item["해당층"] + "/" + item["전체층"];
          const typeStyle = item["형태"] === "매매" ? "color:blue;" : "";
          detailTableHTML += `
            <tr>
              <td style="${typeStyle}">${item["형태"]}</td>
              <td>${floorDisplay}</td>
              <td>${item["향"]}</td>
              <td>${item["평당가"]}</td>
              <td>${item["전용면적"]}</td>
              <td>${formatCurrency(item["형태"],item["가격"])}</td>
            </tr>
          `;
        });
        detailTableHTML += `</tbody></table>`;

        // 4.4 두 테이블 결합하여 테이블 컨테이너 업데이트
        tableContainer.innerHTML = summaryStatsHTML + detailTableHTML;

        // 4.5 평당가 헤더 클릭 시 정렬 순서 토글 및 테이블 재갱신
        const sortHeader = document.getElementById('sortPdanga');
        if (sortHeader) {
          sortHeader.onclick = () => {
            pdangaSortAsc = !pdangaSortAsc;
            updateTables();
          };
        }
    } // end updateTables

    // 초기 테이블 업데이트 호출
    updateTables();

    // 5. select 박스 값 변경 시 테이블 업데이트 (구분, 층 모두)
    const selectGroup = document.getElementById('selectGroup');
    const selectFloor = document.getElementById('selectFloor');
    if (selectGroup) {
        selectGroup.addEventListener('change', updateTables);
    }
    if (selectFloor) {
        selectFloor.addEventListener('change', updateTables);
    }
}


// 빌라 요약목록 리스트
function villaSummaryList() {

    // 헤더정의
    summaryListHeader();

    // 3. 데이터 중복 제거: 구분(형태), 평당가, 면적(전용면적), 가격이 동일하면 1개만 남김
    let uniqueDataMap = tableData;

    // 전역 변수: 평당가 정렬 순서 (true: 오름차순, false: 내림차순)
    let pdangaSortAsc = true;

    // 4. 테이블 업데이트 함수 (필터 조건에 따라 통계표와 상세 리스트 재생성)
    function updateTables() {
        // 4.1 선택된 구분 및 층 값 읽기 (구분은 uniqueDataMap의 데이터를 필터링)
        const selectedType = document.getElementById('selectGroup').value;
        const selectedFloor = document.getElementById('selectFloor').value;
        let filteredData = Object.values(uniqueDataMap);
        if (selectedType !== "all") {
          filteredData = filteredData.filter(item => item["형태"] === selectedType);
        }
        if (selectedFloor !== "all") {
          filteredData = filteredData.filter(item => {
            const floor = item["해당층"];
            if (selectedFloor === "low") {
              return ["B1", "B2", "B3", "1", "2"].includes(floor);
            } else if (selectedFloor === "high") {
              const floorNumber = parseInt(floor);
              return !isNaN(floorNumber) && floorNumber >= 3;
            } else {
              return floor === selectedFloor;
            }
          });
        }
        currSelectedType = selectedType;

        // 4.2 첫 번째 테이블 - 통계표 생성 (형태별 통계)
        function computeStatsForGroup(arr, isSale) {
          if (arr.length === 0) return { min: '-', avg: '-', max: '-', count: 0 };
          const min = Math.min(...arr);
          const max = Math.max(...arr);
          const sum = arr.reduce((acc, cur) => acc + cur, 0);
          const avg = (sum / arr.length).toFixed(isSale ? 0 : 2);
          return { min, avg, max, count: arr.length };
        }
        let summaryStatsHTML = `
          <table border="1" style="width:100%; border-collapse:collapse; text-align:center; margin-bottom:10px;">
            <thead style="background-color:#e0f7ff;">
              <tr>
                <th>구분</th>
                <th>최소</th>
                <th>평균</th>
                <th>최대</th>
                <th>건수</th>
              </tr>
            </thead>
            <tbody>
        `;
        // 항상 월세, 전세, 매매 순서대로 출력 (전세는 녹색, 매매는 파란색)
        const typesOrder = ["월세", "전세", "매매"];
        typesOrder.forEach(type => {
            let values = filteredData.filter(item => item["형태"] === type).map(item => {
                return type === "월세" ? parseFloat(item["평당가"]) : parseFloat(item["가격"]);
            }).filter(val => !isNaN(val));
            const isSale = (type !== "월세");
            let stats = computeStatsForGroup(values, isSale);
            let typeStyle = "";
            if (type === "매매") {
                typeStyle = "color:blue;";
            } else if (type === "전세") {
                typeStyle = "color:green;";
            }
            summaryStatsHTML += `
              <tr>
                <td style="${typeStyle}">${type}</td>
                <td>${formatCurrency(type,stats.min)}</td>
                <td>${formatCurrency(type,stats.avg)}</td>
                <td>${formatCurrency(type,stats.max)}</td>
                <td style="${typeStyle}">${stats.count}</td>
              </tr>
            `;
        });
        summaryStatsHTML += `</tbody></table>`;

        // 4.3 두 번째 테이블 - 상세 리스트 생성
        // 평당가 헤더에 id="sortPdanga"와 현재 정렬 순서 화살표 표시
        const arrowSymbol = pdangaSortAsc ? "▲" : "▼";
        // 형태별 정렬: 월세, 전세, 매매 순서대로 정렬하고, 같은 그룹 내에서 평당가 순 정렬
        const orderMap = { "월세": 1, "전세": 2, "매매": 3 };
        let sortedUniqueData = filteredData.slice().sort((a, b) => {
          if (a["형태"] !== b["형태"]) {
            return orderMap[a["형태"]] - orderMap[b["형태"]];
          } else {
            const pdA = parseFloat(a["평당가"]) || 0;
            const pdB = parseFloat(b["평당가"]) || 0;
            return pdangaSortAsc ? pdA - pdB : pdB - pdA;
          }
        });
        let detailTableHTML = `
          <table border="1" style="width:100%; border-collapse:collapse; text-align:center; margin-bottom:10px;">
            <thead style="background-color:#e0f7ff;">
              <tr>
                <th>구분</th>
                <th>층</th>
                <th>향</th>
                <th id="sortPdanga" style="cursor:pointer;">평당가 ${arrowSymbol}</th>
                <th>면적</th>
                <th>가격</th>
              </tr>
            </thead>
            <tbody>
        `;
        sortedUniqueData.forEach(item => {
          const floorDisplay = item["해당층"] + "/" + item["전체층"];
          let typeStyle = "";
          if (item["형태"] === "매매") {
              typeStyle = "color:blue;";
          } else if (item["형태"] === "전세") {
              typeStyle = "color:green;";
          }
          detailTableHTML += `
            <tr>
              <td style="${typeStyle}">${item["형태"]}</td>
              <td>${floorDisplay}</td>
              <td>${item["향"]}</td>
              <td>${item["평당가"]}</td>
              <td>${item["전용면적"]}</td>
              <td>${formatCurrency(item["형태"], item["가격"])}</td>
            </tr>
          `;
        });
        detailTableHTML += `</tbody></table>`;

        // 4.4 두 테이블 결합하여 테이블 컨테이너 업데이트
        tableContainer.innerHTML = summaryStatsHTML + detailTableHTML;

        // 4.5 평당가 헤더 클릭 시 정렬 순서 토글 및 테이블 재갱신
        const sortHeader = document.getElementById('sortPdanga');
        if (sortHeader) {
          sortHeader.onclick = () => {
            pdangaSortAsc = !pdangaSortAsc;
            updateTables();
          };
        }
    } // end updateTables

    // 초기 테이블 업데이트 호출
    updateTables();

    // 5. select 박스 값 변경 시 테이블 업데이트 (구분, 층 모두)
    const selectGroup = document.getElementById('selectGroup');
    const selectFloor = document.getElementById('selectFloor');
    if (selectGroup) {
        selectGroup.addEventListener('change', updateTables);
    }
    if (selectFloor) {
        selectFloor.addEventListener('change', updateTables);
    }
}

// 평형분석(상가및 빌라,아파트)
function sangaPyeongPopup() {
  // 0. select 값 가져오기 (sangaSummaryList()에서 생성한 select 박스: id="selectGroup", "selectFloor")
  const typeSelectValue = document.getElementById('selectGroup').value;
  const floorSelectValue = document.getElementById('selectFloor').value;
  const typeValue = typeSelectValue == 'all' ? "전체" : typeSelectValue;
  // 전체는 평형처리 안함
  if (typeSelectValue === 'all') {
      alert('월세/전세/매매를 선택해주세요');
      return;
  }
  let floorValue = "";
  if (floorSelectValue === 'all') {
      floorValue = "전체";
  } else if (floorSelectValue === 'low') {
      floorValue = "저층";
  } else if (floorSelectValue === 'high') {
      floorValue = "상층";
  } else {
      floorValue = floorSelectValue;  // 예: "1", "2", "3" 같은 일반 숫자층
  }
  const headerText = `${typeValue} > ${floorValue} (중복제거함)`;

  // 1. tableData에서 중복 제거
  // (구분, 해당층, 향, 평당가, 전용면적, 가격이 동일하면 하나로 처리하며, 해당층이 falsy인 항목은 제외)
  const dedupedData = [];
  const seen = new Set();
  tableData.forEach(item => {
    if (!item["해당층"]) return; // 해당층이 없으면 건너뜀
    const key = item["형태"] + "_" + item["평당가"] + "_" + item["전용면적"] + "_" + item["가격"];
    if (!seen.has(key)) {
      seen.add(key);
      dedupedData.push(item);
    }
  });

  const selectedType = document.getElementById('selectGroup').value;
  const selectedFloor = document.getElementById('selectFloor').value;
  let filteredData = Object.values(dedupedData);
  if (selectedType !== "all") {
      filteredData = filteredData.filter(item => item["형태"] === selectedType);
  }
  if (selectedFloor !== "all") {
      filteredData = filteredData.filter(item => {
        const floor = item["해당층"];
        if (selectedFloor === "low") {
          return ["B1", "B2", "B3", "1", "2"].includes(floor);
        } else if (selectedFloor === "high") {
          const floorNumber = parseInt(floor);
          return !isNaN(floorNumber) && floorNumber >= 3;
        } else {
          return floor === selectedFloor;
        }
      });
  }

  // 2. 그룹화: 각 항목에서 층과 전용면적 그룹화
  // 층: "해당층"에서 "/" 앞 숫자를 이용하여 1층, 2층, 3층 이상은 "상층"으로 구분
  // 면적 그룹: 전용면적이 10미만이면 "9평", 10이상이면 Math.floor(area/10)*10 + "평"
  const groups = {};
  filteredData.forEach(item => {
    const floorExtract = item["해당층"].split('/')[0];
    let floorCategory;
    const floorNum = Number(floorExtract);
    if (floorNum === 1) floorCategory = "1층";
    else if (floorNum === 2) floorCategory = "2층";
    else if (floorNum >= 3) floorCategory = "상층";
    else floorCategory = item["해당층"];

    const area = parseFloat(item["전용면적"]);
    if (isNaN(area)) return;
    const areaGroup = area < 10 ? "9평" : `${Math.floor(area / 10) * 10}평`;

    if (!groups[floorCategory]) {
      groups[floorCategory] = {};
    }
    // 평당가를 사용: 형태가 "월세"이면 평당가, 그렇지 않으면 가격 사용
    const value = (item["형태"] === "월세") ? parseFloat(item["평당가"]) : parseFloat(item["가격"]);
    if (!isNaN(value)) {
      if (!groups[floorCategory][areaGroup]) {
        groups[floorCategory][areaGroup] = { count: 0, sum: 0, min: value, max: value };
      }
      groups[floorCategory][areaGroup].count += 1;
      groups[floorCategory][areaGroup].sum += value;
      groups[floorCategory][areaGroup].min = Math.min(groups[floorCategory][areaGroup].min, value);
      groups[floorCategory][areaGroup].max = Math.max(groups[floorCategory][areaGroup].max, value);
    }
  });

  // 3. 각 floor 그룹별 총합 계산 (건수, 평균, 최소, 최대)
  const floorTotals = {};
  Object.keys(groups).forEach(floorCat => {
    let totalCount = 0, totalSum = 0;
    let floorMin = Infinity, floorMax = -Infinity;
    Object.values(groups[floorCat]).forEach(group => {
      totalCount += group.count;
      totalSum += group.sum;
      floorMin = Math.min(floorMin, group.min);
      floorMax = Math.max(floorMax, group.max);
    });
    floorTotals[floorCat] = {
      count: totalCount,
      avg: totalCount > 0 ? (totalSum / totalCount).toFixed(1) : 0,
      min: floorMin === Infinity ? 0 : floorMin.toFixed(1),
      max: floorMax === -Infinity ? 0 : floorMax.toFixed(1)
    };
  });

  // 4. 팝업 컨테이너 생성
  const popupDiv = document.createElement("div");
  popupDiv.id = "pyeongPopup";
  popupDiv.style.cssText =
    "position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);" +
    "width: 600px; background-color: #fff; border: 2px solid #007bff; border-radius: 8px;" +
    "box-shadow: 0 4px 8px rgba(0,0,0,0.2); padding: 10px; overflow-y: auto; z-index: 10000;";

  // 4.1 헤더 생성 (선택된 값 표시)
  const headerDiv = document.createElement("div");
  headerDiv.style.textAlign = "left";
  headerDiv.style.marginBottom = "10px";
  headerDiv.style.fontSize = "14px";
  headerDiv.style.fontWeight = "bold";
  headerDiv.textContent = headerText;
  popupDiv.appendChild(headerDiv);

  // 헤더 드래그 가능하게 처리
  headerDiv.style.cursor = "move";
  headerDiv.onmousedown = function(event) {
    let shiftX = event.clientX - popupDiv.getBoundingClientRect().left;
    let shiftY = event.clientY - popupDiv.getBoundingClientRect().top;
    function moveAt(pageX, pageY) {
      popupDiv.style.left = pageX - shiftX + "px";
      popupDiv.style.top = pageY - shiftY + "px";
    }
    moveAt(event.pageX, event.pageY);
    function onMouseMove(event) {
      moveAt(event.pageX, event.pageY);
    }
    document.addEventListener("mousemove", onMouseMove);
    document.onmouseup = function() {
      document.removeEventListener("mousemove", onMouseMove);
      document.onmouseup = null;
    };
  };
  headerDiv.ondragstart = function() { return false; };

  // 5. 통계 테이블 생성
  const table = document.createElement("table");
  table.style.width = "100%";
  table.style.borderCollapse = "collapse";
  table.style.textAlign = "center";

  // colgroup 생성 (innerHTML 이용)
  const colgroupHTML = `
    <colgroup>
      <col style="width: 10%;">
      <col style="width: 15%;">
      <col style="width: 15%;">
      <col style="width: 15%;">
      <col style="width: 15%;">
      <col style="width: 15%;">
      <col style="width: 15%;">
    </colgroup>
  `;
  // 기존 innerHTML에 colgroup 추가
  table.innerHTML = colgroupHTML;

  // 테이블 헤더 생성 (innerHTML 이용한 리스트 형식)
  const headerHTML = `
    <thead>
      <tr style="text-align: center; background-color: #f2f2f2;">
        <th style="border: 1px solid #ccc;">순번</th>
        <th style="border: 1px solid #ccc;">구분</th>
        <th style="border: 1px solid #ccc;">평형</th>
        <th style="border: 1px solid #ccc;">건수</th>
        <th style="border: 1px solid #ccc;">최소</th>
        <th style="border: 1px solid #ccc;">평균</th>
        <th style="border: 1px solid #ccc;">최대</th>
      </tr>
    </thead>
  `;
  // 기존 내용 뒤에 헤더 추가
  table.innerHTML += headerHTML;

  // 테이블 바디 생성 (동적 생성)
  const tbody = document.createElement("tbody");
  const floorOrder = ["1층", "2층", "상층"];
  const floorColors = { "1층": "#ffe0e0", "2층": "#e0f7ff", "상층": "#e0ffe0" };

  floorOrder.forEach(floorCat => {
    if (groups[floorCat]) {
      let groupRowIndex = 1;
      const sortedAreaKeys = Object.keys(groups[floorCat]).sort((a, b) => {
        const numA = parseInt(a.replace("평", ""), 10);
        const numB = parseInt(b.replace("평", ""), 10);
        return numA - numB;
      });
      sortedAreaKeys.forEach((areaGroup, index) => {
        const { count, sum, min, max } = groups[floorCat][areaGroup];
        const avg = (sum / count).toFixed(1);
        const tr = document.createElement("tr");
        tr.style.backgroundColor = floorColors[floorCat] || "#fff";
        tr.style.textAlign = "center";
        tr.style.borderBottom = "1px solid #eee";

        // 순번 셀
        const tdIndex = document.createElement("td");
        tdIndex.textContent = groupRowIndex;
        tdIndex.style.border = "1px solid #ccc";
        tr.appendChild(tdIndex);
        groupRowIndex++;

        // 구분 셀: 같은 floor 그룹의 첫 행에만 표시 (rowspan 적용)
        if (index === 0) {
          const tdFloor = document.createElement("td");
          tdFloor.textContent = floorCat;
          tdFloor.rowSpan = sortedAreaKeys.length + 1;
          tdFloor.style.border = "1px solid #ccc";
          tdFloor.style.backgroundColor = floorColors[floorCat] || "#fff";
          tdFloor.style.fontWeight = "bold";
          tr.appendChild(tdFloor);
        }

        // 평형 셀 (면적 그룹)
        const tdArea = document.createElement("td");
        tdArea.textContent = areaGroup;
        tdArea.style.border = "1px solid #ccc";
        tr.appendChild(tdArea);

        // 건수 셀
        const tdCount = document.createElement("td");
        tdCount.textContent = count;
        tdCount.style.border = "1px solid #ccc";
        tr.appendChild(tdCount);

        // 최소 셀
        const tdMin = document.createElement("td");
        tdMin.textContent = formatCurrency(selectedType, Number(min).toFixed(1));
        tdMin.style.border = "1px solid #ccc";
        tr.appendChild(tdMin);

        // 평균 셀
        const tdAvg = document.createElement("td");
        tdAvg.textContent = formatCurrency(selectedType, avg);
        tdAvg.style.border = "1px solid #ccc";
        tr.appendChild(tdAvg);

        // 최대 셀
        const tdMax = document.createElement("td");
        tdMax.textContent = formatCurrency(selectedType, Number(max).toFixed(1));
        tdMax.style.border = "1px solid #ccc";
        tr.appendChild(tdMax);

        tbody.appendChild(tr);
      });
      // 총합(합계) 행 추가
      const floorTotal = floorTotals[floorCat];
      const totalRow = document.createElement("tr");
      totalRow.style.textAlign = "center";
      totalRow.style.backgroundColor = "#f9f9f9";

      // 순번 셀 (빈 셀)
      const tdEmpty = document.createElement("td");
      tdEmpty.textContent = "";
      tdEmpty.style.border = "1px solid #ccc";
      totalRow.appendChild(tdEmpty);

      // 구분 셀 ("합계")
      const tdLabel = document.createElement("td");
      tdLabel.textContent = "합계";
      tdLabel.style.border = "1px solid #ccc";
      tdLabel.style.fontWeight = "bold";
      totalRow.appendChild(tdLabel);

      // 건수 셀
      const tdTotalCount = document.createElement("td");
      tdTotalCount.textContent = floorTotal.count;
      tdTotalCount.style.border = "1px solid #ccc";
      tdTotalCount.style.fontWeight = "bold";
      totalRow.appendChild(tdTotalCount);

      // 최소 셀
      const tdTotalMin = document.createElement("td");
      tdTotalMin.textContent = formatCurrency(selectedType, floorTotal.min);
      tdTotalMin.style.border = "1px solid #ccc";
      tdTotalMin.style.fontWeight = "bold";
      totalRow.appendChild(tdTotalMin);

      // 평균 셀
      const tdTotalAvg = document.createElement("td");
      tdTotalAvg.textContent = formatCurrency(selectedType, floorTotal.avg);
      tdTotalAvg.style.border = "1px solid #ccc";
      tdTotalAvg.style.fontWeight = "bold";
      totalRow.appendChild(tdTotalAvg);

      // 최대 셀
      const tdTotalMax = document.createElement("td");
      tdTotalMax.textContent = formatCurrency(selectedType, floorTotal.max);
      tdTotalMax.style.border = "1px solid #ccc";
      tdTotalMax.style.fontWeight = "bold";
      totalRow.appendChild(tdTotalMax);

      tbody.appendChild(totalRow);
    }
  });
  table.appendChild(tbody);
  popupDiv.appendChild(table);

  // 6. 팝업 하단 중앙에 닫기 버튼 생성
  const closeDiv = document.createElement("div");
  closeDiv.style.textAlign = "center";
  closeDiv.style.marginTop = "10px";
  const closeButton = document.createElement("button");
  closeButton.textContent = "닫기";
  closeButton.style.padding = "5px 10px";
  closeButton.style.backgroundColor = "#007bff";
  closeButton.style.color = "#fff";
  closeButton.style.border = "none";
  closeButton.style.borderRadius = "4px";
  closeButton.style.cursor = "pointer";
  closeButton.addEventListener("click", () => {
    document.body.removeChild(popupDiv);
  });
  closeDiv.appendChild(closeButton);
  popupDiv.appendChild(closeDiv);

  // 7. 팝업을 body에 추가하여 표시
  document.body.appendChild(popupDiv);
}


// 네이버 지도에서 선택되어진 주소명가져오기
function getSelectedRegions() {
  const container = document.querySelector('.filter_region_inner');
  if (!container) {
    console.error('filter_region_inner 요소를 찾을 수 없습니다.');
    return { region: null, sigungu: null, umName: null };
  }

  // .area.is-selected 클래스를 가진 모든 span 요소 선택
  const spans = container.querySelectorAll('span.area.is-selected');

  // 각 span에서 첫 번째 텍스트 노드(아이콘 등 제외)를 가져옵니다.
  const regions = Array.from(spans).map(span => {
    // textContent 사용 시 자식 요소의 텍스트까지 모두 포함되므로
    // childNodes[0]를 이용하여 첫 번째 텍스트 노드만 취득합니다.
    const textNode = span.childNodes[0];
    return textNode ? textNode.nodeValue.trim() : "";
  });

  return {
    region: regions[0] || null,
    sigungu: regions[1] || null,
    umdNm: regions[2] || null
  };
}

// 실거래분석(국토부및경매데이터)
function analyzeRealdealDemand() {
    // 지역선택 가져오기
    const {region, sigungu, umdNm} = getSelectedRegions();
    //alert(region + ',' + sigungu + ',' + umdNm);
    // '경기도,김포시,구래동'
    const regions = region + ',' + sigungu + ',' + umdNm;

    // 확장툴url
    let ext_url = '';
    if (tabGubun === 'sanga') {
        ext_url = BASE_URL + "/api/ext_tool?menu=sanga_real_deal&regions=" + regions ;
    } else {
         ext_url = BASE_URL + "/api/ext_tool?menu=villa_real_deal&regions=" + regions ;
    }
    //
    const popupWidth = 950;  // 원하는 팝업 너비
    const popupHeight= 840;  // 원하는 팝업 높이
    const left = (screen.width - popupWidth) / 2;
    const top = (screen.height - popupHeight) / 2;
    window.open(ext_url , "analyzeCatchmentDemand",
      `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`);
}

// 배후분석(마이프차접속)
function analyzeCatchmentDemand() {
    //
    const popupWidth = 550;  // 원하는 팝업 너비
    const popupHeight= 950;  // 원하는 팝업 높이
    const left = (screen.width - popupWidth) / 2;
    const top = (screen.height - popupHeight) / 2;
    window.open("https://myfranchise.kr/map", "analyzeCatchmentDemand",
      `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`);
}

// 네이버 매물검색 처리
function searchNaverListings() {
  // 기본 컨트롤 박스 가져오기
  const onoffPanel = document.querySelector('.filter_area');
  onoffPanel.style.display = 'inline-block'; // 줄 바꿈 방지

  // 네이버매물검색 버튼 생성
  const naverSearch = document.createElement('span');
  naverSearch.id = 'naverSearch'; // id 지정
  naverSearch.textContent = tabGubun === 'sanga' ? '매물검색' : '실거래검색';
  naverSearch.style.marginTop = '15px';
  naverSearch.style.marginLeft = '10px'; // 다른 요소와의 간격 조절
  naverSearch.style.backgroundColor = '#007bff'; // 엷은 파란색 배경
  naverSearch.style.color = '#fff'; // 검정색 텍스트
  naverSearch.style.padding = '5px 6px'; // 내부 여백
  naverSearch.style.fontSize = '12px'; // 글씨 크기
  naverSearch.style.borderRadius = '8px'; // 둥근 모서리
  naverSearch.style.cursor = 'pointer'; // 커서
  naverSearch.style.transition = 'all 0.3s ease'; // 부드러운 효과
  naverSearch.style.verticalAlign = 'middle'; // 정렬 보정
  naverSearch.style.border = '1px solid #ccc'; // 테두리 추가 (연한 회색)

  // 클릭 시 지정 URL을 새 팝업창으로 엽니다.
  naverSearch.addEventListener('click', function() {
    // 로그인여부 체크
    loginValid().then(valid => {
        if (!valid) return;   // 로그인 실패 시 여기서 중단
        //
        // 지역선택 가져오기
        const {region, sigungu, umdNm} = getSelectedRegions();
        //alert(region + ',' + sigungu + ',' + umdNm);
        // '경기도,김포시,구래동'
        const regions = region + ',' + sigungu + ',' + umdNm;

        let search_menu = "";
        if (tabGubun === 'sanga') {
            search_menu = "menu=sanga_search&regions=" + regions + '&api_key=' + sanga_key;
        } else if (tabGubun === 'villa') {
            search_menu = "menu=villa&regions=" + regions + '&api_key=' + villa_key;
        }  if (tabGubun === 'apt') {
            search_menu = "menu=apt&regions=" + regions + '&api_key=' + sanga_key;
        }
        // 확장툴url
        let ext_url = BASE_URL + "/api/ext_tool?" + search_menu;
        //let ext_url = "http://192.168.45.167:8081/api/ext_tool?" + search_menu;

        const popupWidth = tabGubun === 'sanga' ? 1490 : 1100;   // 원하는 팝업 너비
        const popupHeight = 1200;  // 원하는 팝업 높이
        const left = (screen.width - popupWidth) / 2;
        const top = (screen.height - popupHeight) / 2;
        // window.open(ext_url, "realDataPopup",
        //   `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`);
        window.open(
              ext_url,
              "realDataPopup",
              `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes,location=no,menubar=no,toolbar=no,status=no`
            );
    });
  });

  // onoffPanel에 실거래검색 버튼 추가
  onoffPanel.appendChild(naverSearch);
}

// NPL 매물검색 처리
function nplSearchListings() {

  // 실거래검색 버튼 요소 가져오기
  const naverSearch = document.getElementById("naverSearch");

  // NPL매물검색 버튼 생성
  const nplSearch = document.createElement('span');
  nplSearch.id = 'nplSearch'; // id 지정
  nplSearch.textContent = 'NPL검색';
  nplSearch.style.marginTop = '15px';
  nplSearch.style.marginLeft = '10px'; // 다른 요소와의 간격 조절
  nplSearch.style.backgroundColor = '#ffb700'; // 엷은 파란색 배경
  nplSearch.style.color = '#fff'; // 검정색 텍스트
  nplSearch.style.padding = '5px 6px'; // 내부 여백
  nplSearch.style.fontSize = '12px'; // 글씨 크기
  nplSearch.style.borderRadius = '8px'; // 둥근 모서리
  nplSearch.style.cursor = 'pointer'; // 커서
  nplSearch.style.transition = 'all 0.3s ease'; // 부드러운 효과
  nplSearch.style.verticalAlign = 'middle'; // 정렬 보정
  nplSearch.style.border = '1px solid #ccc'; // 테두리 추가 (연한 회색)

  // 클릭 시 지정 URL을 새 팝업창으로 엽니다.
  nplSearch.addEventListener('click', function() {

    // 로그인여부 체크
    loginValid().then(valid => {
        if (!valid) return;   // 로그인 실패 시 여기서 중단

        // 지역선택 가져오기
        const {region, sigungu, umdNm} = getSelectedRegions();
        //alert(region + ',' + sigungu + ',' + umdNm);
        // '경기도,김포시,구래동'
        const regions = region + ',' + sigungu + ',' + umdNm;

        let search_menu = "menu=npl_search&regions=" + regions + '&api_key=' + sanga_key;

        // 확장툴url
        let ext_url = BASE_URL + "/api/ext_tool?" + search_menu;
        //let ext_url = "http://192.168.45.167:8081/api/ext_tool?" + search_menu;

        const popupWidth = 1490;   // 원하는 팝업 너비
        const popupHeight = 1200;  // 원하는 팝업 높이
        const left = (screen.width - popupWidth) / 2;
        const top = (screen.height - popupHeight) / 2;
        // window.open(ext_url, "realDataPopup",
        //   `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`);
        window.open(
              ext_url,
              "nplDataPopup",
              `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes,location=no,menubar=no,toolbar=no,status=no`
            );
    });
  });

  // 네이버매물검색 버튼 바로 뒤에 NPL검색 버튼 추가
  naverSearch.parentNode.insertBefore(nplSearch, naverSearch.nextSibling);
}

// 수익율분석 처리
function analyzeProfitDemand() {
  // 실거래검색 버튼 요소 가져오기
  const nplSearch = document.getElementById("nplSearch");

  // 수익율분석 버튼 생성
  const analyzeProfit = document.createElement('span');
  analyzeProfit.id = 'analyzeProfit'; // id 지정
  analyzeProfit.textContent = '수익율분석';
  analyzeProfit.style.marginLeft = '10px'; // 실거래검색 버튼과 간격
  analyzeProfit.style.backgroundColor = 'lightyellow'; // 엷은 노란색 배경
  analyzeProfit.style.color = '#000'; // 검정색 텍스트
  analyzeProfit.style.padding = '5px 6px'; // 내부 여백
  analyzeProfit.style.fontSize = '12px'; // 글씨 크기
  analyzeProfit.style.borderRadius = '8px'; // 둥근 모서리
  analyzeProfit.style.cursor = 'pointer'; // 커서
  analyzeProfit.style.transition = 'all 0.3s ease'; // 부드러운 효과
  analyzeProfit.style.display = 'inline-block'; // 옆으로 배치되도록 설정
  analyzeProfit.style.verticalAlign = 'middle'; // 정렬 보정
  analyzeProfit.style.border = '1px solid #ccc'; // 테두리 추가 (연한 회색)

  // 클릭 시 지정 URL을 새 팝업창으로 엽니다.
  analyzeProfit.addEventListener('click', function() {
    // 로그인여부 체크
    loginValid().then(valid => {
        if (!valid) return;   // 로그인 실패 시 여기서 중단

        // 지역선택 가져오기
        const {region, sigungu, umdNm} = getSelectedRegions();
        const regions = region + ',' + sigungu + ',' + umdNm;

        // 확장툴url => sanga:상가수익율표, general:아파트/발라 수익율표
        let ext_url = "";
        if (tabGubun === 'sanga') {
            ext_url = BASE_URL + "/api/ext_tool?menu=sanga_profit&regions=" + regions;
        } else {
            ext_url = BASE_URL + "/api/ext_tool?menu=general_profit&regions=" + regions;
        }
        //
        const popupWidth = 970;
        const popupHeight = 790;
        const left = (screen.width - popupWidth) / 2;
        const top = (screen.height - popupHeight) / 2;
        window.open(ext_url, "analyzeProfit",
            `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`);
    });
  });

  // NPL매물검색 버튼 바로 뒤에 수익율분석 버튼 추가
  nplSearch.parentNode.insertBefore(analyzeProfit, nplSearch.nextSibling);
}

// 문자보내기(중개사및 대출상담사) 처리
function smsSend() {
  // 수익율분석 버튼 요소 가져오기
  const analyzeProfit = document.getElementById("analyzeProfit");

  // 문자보내기 버튼 생성
  const smsSendSearch = document.createElement('span');
  smsSendSearch.id = 'smsSendSearch'; // id 지정
  smsSendSearch.textContent = '문자보내기';
  smsSendSearch.style.marginLeft = '10px'; // 실거래검색 버튼과 간격
  smsSendSearch.style.backgroundColor = 'lightyellow'; // 엷은 노란색 배경
  smsSendSearch.style.color = '#000'; // 검정색 텍스트
  smsSendSearch.style.padding = '5px 6px'; // 내부 여백
  smsSendSearch.style.fontSize = '12px'; // 글씨 크기
  smsSendSearch.style.borderRadius = '8px'; // 둥근 모서리
  smsSendSearch.style.cursor = 'pointer'; // 커서
  smsSendSearch.style.transition = 'all 0.3s ease'; // 부드러운 효과
  smsSendSearch.style.display = 'inline-block'; // 옆으로 배치되도록 설정
  smsSendSearch.style.verticalAlign = 'middle'; // 정렬 보정
  smsSendSearch.style.border = '1px solid #ccc'; // 테두리 추가 (연한 회색)

  // 클릭 시 지정 URL을 새 팝업창으로 엽니다.
  smsSendSearch.addEventListener('click', function() {
    // 로그인여부 체크
    loginValid().then(valid => {
        if (!valid) return;   // 로그인 실패 시 여기서 중단

        // 지역선택 가져오기
        const {region, sigungu, umdNm} = getSelectedRegions();
        const regions = region + ',' + sigungu + ',' + umdNm;
        //
        // 확장툴url
        let ext_url = BASE_URL + "/api/ext_tool?menu=realtor&regions=" + regions;
        //
        const popupWidth = 1000;
        const popupHeight = 1180;
        const left = (screen.width - popupWidth) / 2;
        const top = (screen.height - popupHeight) / 2;
        window.open(ext_url, "smsSendSearch",
            `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`);
    });
  });

  // 수익율분석 버튼 바로 뒤에 추가
  analyzeProfit.parentNode.insertBefore(smsSendSearch, analyzeProfit.nextSibling);
}

// 양식다운로드 처리
function formDownload() {
  // 문자검색 버튼 요소 가져오기
  const smsSendSearch = document.getElementById("smsSendSearch");

  // 수익율분석 버튼 생성
  const formDownload = document.createElement('span');
  formDownload.id = 'formDownload'; // id 지정
  formDownload.textContent = '양식다운';
  formDownload.style.marginLeft = '10px'; // 실거래검색 버튼과 간격
  formDownload.style.backgroundColor = 'lightred'; // 엷은 노란색 배경
  formDownload.style.color = '#000'; // 검정색 텍스트
  formDownload.style.padding = '5px 6px'; // 내부 여백
  formDownload.style.fontSize = '12px'; // 글씨 크기
  formDownload.style.borderRadius = '8px'; // 둥근 모서리
  formDownload.style.cursor = 'pointer'; // 커서
  formDownload.style.transition = 'all 0.3s ease'; // 부드러운 효과
  formDownload.style.display = 'inline-block'; // 옆으로 배치되도록 설정
  formDownload.style.verticalAlign = 'middle'; // 정렬 보정
  formDownload.style.border = '1px solid #ccc'; // 테두리 추가 (연한 회색)

  // 클릭 시 지정 URL을 새 팝업창으로 엽니다.
  formDownload.addEventListener('click', function() {
        // 로그인여부 체크
        loginValid().then(valid => {
            if (!valid) return;   // 로그인 실패 시 여기서 중단
            // 지역선택 가져오기
            const {region, sigungu, umdNm} = getSelectedRegions();
            const regions = region + ',' + sigungu + ',' + umdNm;
            //
            // 확장툴url
            let ext_url = BASE_URL + "/api/ext_tool?menu=form_down&regions=" + regions;
            //
            const popupWidth = 500;
            const popupHeight = 450;
            const left = (screen.width - popupWidth) / 2;
            const top = (screen.height - popupHeight) / 2;
            window.open(ext_url, "analyzeProfit",
                `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`);
        });
  });

  // 문자검색 버튼 바로 뒤에 수익율분석 버튼 추가
  smsSendSearch.parentNode.insertBefore(formDownload, smsSendSearch.nextSibling);
}

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
    tableData = [];
    const propertyItems = document.querySelectorAll('.item_inner:not(.is-loading)'); // 'is-loading' 클래스를 제외한 요소 선택
    console.log('전체 propertyItems:', propertyItems);
    if (propertyItems.length > 0) {
        propertyItems.forEach(item => {
            extractSangaItemFromHTML(item);
        });
        // loadingStack is null => 모든게 로딩이 완료되었으면 품목소트후 재정렬처리(단가순)
        if (loadingStack == null) {
            summaryTable();
            //
            sortItems();
            // 요약표가 열려있으면
            if (summaryListShowStatus == true) {
                if (tabGubun === 'sanga') {
                     sangaSummaryList();
                } else {
                     villaSummaryList();
                }
            }
        }
    }
}

function formatCurrency(type, amount) {

    // '-' 또는 null인 경우 0으로 처리
    if (amount === '-' || amount === null) {
        amount = 0;
    }
    // type이 "월세"이고 amount가 문자열이며 슬래시를 포함하면 그대로 반환
    if (type === '월세' && typeof amount === 'string' && amount.indexOf('/') !== -1) {
        return amount;
    }
    // 문자열 등으로 전달된 경우 숫자로 변환
    amount = Number(amount);
    // 숫자가 아니거나 음수이면 0으로 처리
    if (isNaN(amount) || amount < 0) {
        amount = 0;
    }

    if (type === '매매' || type === '전세') {
        // 소수점 이하 제거: 소숫점 이하를 버립니다.
        amount = Math.floor(amount);

        // 만원(10,000) 이상이면 억 단위로 변환합니다.
        if (amount >= 10000) {
            const quotient = Math.floor(amount / 10000); // 억 부분
            const remainder = amount % 10000;            // 나머지 부분
            // 나머지가 0이면 억만 표시, 그렇지 않으면 천 단위 콤마를 추가합니다.
            return remainder ? `${quotient}억${remainder.toLocaleString()}` : `${quotient}억`;
        }
        // 만원 미만이면 단순히 천 단위 콤마 처리합니다.
        return amount.toLocaleString();
    }
    return amount.toString();
}

// 리스트목록 처리
function extractPropertyInfo() {

	// 모든 탭 요소 선택 (lnb_wrap 내부의 .lnb_item)
	const tabs = document.querySelectorAll('.lnb_wrap .lnb_item');

	tabs.forEach(tab => {
	  // 선택된(눌린) 탭인지 확인
	  if (tab.getAttribute('aria-selected') === 'true') {
		// aria-controls 값 가져오기
		const controls = tab.getAttribute('aria-controls');

		// 각 탭에 대해 처리 (필요에 따라 조건문 수정)
		switch (controls) {
		  case 'tab1':
			console.log('아파트/오피스텔 탭이 선택되었습니다.');
			// 아파트적용 프로퍼티 => 매물검색, 수익율분석, 문자보개기
	  		tabGubun = 'apt';
            topButtonCreate();
			break;
		  case 'tab2':
			console.log('빌라/주택 탭이 선택되었습니다.');
			// 빌라적용 프로퍼티 => 매물검색, 수익율분석, 문자보개기
		  	tabGubun = 'villa';
            topButtonCreate();
			//villaPropertyInfo();
			break;
		  case 'tab3':
			console.log('원룸/투룸 탭이 선택되었습니다.');
			// tab3에 대한 추가 처리
			break;
          case 'tab4':
			console.log('상가/업무/공장/토지 탭이 선택되었습니다.');
			// 상가적용 프로퍼티 => 매물검색, 수익율분석, 문자보개기
			tabGubun = 'sanga';
            topButtonCreate();
            //
			loadSangaItems();
			break;
		  case 'tab5':
			console.log('분양 탭이 선택되었습니다.');
			// tab5에 대한 추가 처리
			break;
		  case 'tab6':
			console.log('MY관심 탭이 선택되었습니다.');
			// tab6에 대한 추가 처리
			break;
		  case 'tab7':
			console.log('우리집 탭이 선택되었습니다.');
			// tab7에 대한 추가 처리
			break;
		  default:
			console.log('알 수 없는 탭이 선택되었습니다.');
		}
	  }
      console.log('tabGubun: ' + tabGubun);
	});
}

function topButtonCreate() {
    // 로그인처리(사용안함-비동기문제발생)
    //login();
    // 네이버매물 팝업
    searchNaverListings();
    // NPL 매물검색 처리
    nplSearchListings();
    // 수익율분석 처리
    analyzeProfitDemand();
    // 문자보내기(중개사및 대출상담사) 처리
    smsSend();
    // 양식다운로드 처리
    formDownload();
}

function loginValid() {
    //
    return login().then(isOk => {
        if (!isOk) {
          alert('로그인(회원가입) 후 사용바랍니다.');
          return false;
        }
        return true;
    });
}

// content_yana.js 내 코드
function login() {
    return new Promise((resolve, reject) => {
        chrome.storage.local.get(['access_token', 'apt_key', 'villa_key', 'sanga_key'], function(data) {
            const accessToken = data.access_token;
            apt_key = data.apt_key;
            villa_key = data.villa_key;
            sanga_key = data.sanga_key;

            console.log('accessToken: ' + accessToken);
            if (accessToken === '' || accessToken === null || accessToken === 'undefined') {
                //alert('로그인 후 사용바랍니다.');
                return resolve(false);  // reject 대신 resolve
            }

            $.ajax({
                url: BASE_URL + '/api/login_token',
                method: 'GET',
                headers: {
                    "Authorization": "Bearer " + accessToken
                },
                success: function(response) {
                    if (response.result === "Success") {
                        isLoggedInStatus = true;
                        resolve(true);
                    } else {
                        // alert('로그인 후 사용바랍니다.');
                        isLoggedInStatus = false;
                        resolve(false);
                    }
                },
                error: function() {
                    isLoggedInStatus = false;
                    resolve(false);
                }
            });
        });
    });
}


// **MutationObserver를 활용한 자동 감시**
function observeMutations() {
    const targetNode = document.querySelector('.item_list.item_list--article');
    if (!targetNode) {
        console.error('targetNode not found. 해당 요소가 DOM에 존재하는지 확인하세요.');
        return;
    }
    const config = { childList: true, subtree: true }; // 자식 요소 변경 감시

    const callback = function(mutationsList, observer) {
        if (!isScheduled) {
            isScheduled = true;
            observer.disconnect(); // 감시 중단
            console.log('새로운 아이템 감지됨, 추가 로드 실행');
            loadSangaItems(); // 추가 아이템 로드

            // targetNode가 여전히 존재하는지 확인 후 감시 재개
            const newTargetNode = document.querySelector('.item_list.item_list--article');
            if (newTargetNode) {
                observer.observe(newTargetNode, config);
            } else {
                console.error('재감시를 위한 targetNode를 찾을 수 없습니다.');
            }
            isScheduled = false; // 다시 감시 가능하도록 초기화
        }
    };
    const observer = new MutationObserver(callback);
    observer.observe(targetNode, config);
}

// 탱크옥션 처리
function observeMutationsTank() {
    const targetNode = document.querySelector('body'); // 감시할 노드 선택
    const config = { childList: true, subtree: true }; // 감시할 변경 유형 설정

    const callback = function(mutationsList, observer) {
		// 제거된 부분이 있는지 확인 - 제거가 안되서 문제... 파악다시
        for (let mutation of mutationsList) {
            if (mutation.type === 'childList') {
                setTimeout(extractPropertyInfoTank, 300); // 1초 후에 extractPropertyInfo 함수 실행
            }
        }
    };

    const observer = new MutationObserver(callback);
    observer.observe(targetNode, config);
}

// 옥션원 리스트목록 표시
function extractPropertyInfoTank() {

    // 1. tbody 존재 여부 체크 (3가지 방법)
    const tbody = document.querySelector('#lsTbody');
    const propertyItems = tbody.querySelectorAll('tr');

	propertyItems.forEach((item) => {

        let areaPy = 0;
        // 방법 1 적용: 모든 .blue 클래스 요소 수집
        const areaElements = item.querySelectorAll('.blue, .blue.f12');
        areaElements.forEach(el => {
            const areaText = el.textContent.trim();
            console.log('검색 텍스트:', areaText);

            // 건물 평수 우선 추출
            const buildingMatch = areaText.match(/건물[^㎡]*\d+\.?\d*㎡\((\d+\.?\d*)평\)/);
            if (buildingMatch && !areaPy) { // 아직 값이 없을 때만 할당
                areaPy = parseFloat(buildingMatch[1]);
                console.log(`건물 평수: ${areaPy}평`);
            }

            // 건물 없으면 토지 평수 추출
            const landMatch = areaText.match(/토지[^㎡]*\d+\.?\d*㎡\((\d+\.?\d*)평\)/);
            if (landMatch && !areaPy) {
                areaPy = parseFloat(landMatch[1]);
                console.log(`토지 평수: ${areaPy}평`);
            }
        });
        console.log(`최종 평수: ${areaPy}평`);

		if (areaPy) {
			// 금액1 추출 (auct_iprice_숫자 아이디 내부 텍스트) //auct_jprice_2406369
			const price1Element = item.querySelector('[id^="apslAmt_"]');
			const price1Text = price1Element.textContent.trim().replace(/,/g, '');
			const price1num = parseInt(price1Text);
			console.log(price1num);
			if (!price1Element.dataset.highlighted) {
				// 금액2 추출 (auct_iprice_숫자 아이디 내부 텍스트) //auct_jprice_2406369
				const price2Element = item.querySelector('[id^="minbAmt"]');
				const price2Text = price2Element.textContent.trim().replace(/,/g, '');
				const price2num = parseInt(price2Text);
				console.log(price2num);

				const pydanga1 = parseInt(price1num / (areaPy * 10000));
				const pydanga2 = parseInt(price2num / (areaPy * 10000));
				console.log(pydanga1);

				// Create a new <span> element for the line break
				const lineBreakSpan = document.createElement('span');
				lineBreakSpan.innerHTML = '<br>'; // This will render as an actual line break
				const lineBreakSpan2 = document.createElement('span');
				lineBreakSpan2.innerHTML = '<br>'; // This will render as an actual line break

				const pydanga1Span = document.createElement('span');
				pydanga1Span.textContent = `@${pydanga1}만원`;
				pydanga1Span.style.opacity = 0.5; // 50% opacity
				pydanga1Span.style.color = 'red';

				// Append the line break and the calculated value to the content
				price1Element.appendChild(lineBreakSpan);
				price1Element.appendChild(pydanga1Span);

				const pydanga2Span = document.createElement('span');
				pydanga2Span.textContent = `@${pydanga2}만원`;
				pydanga2Span.style.opacity = 0.5; // 50% opacity
				pydanga2Span.style.color = 'green';

				price2Element.appendChild(lineBreakSpan2);
				price2Element.appendChild(pydanga2Span);

				// 낙찰단가는 창을 모르니까 비워둠
				// const price3Element = item.querySelector('[id^="auct_sprice_"]');

				// if (price3Element) {
					// // 금액3 추출 (auct_iprice_숫자 아이디 내부 텍스트) //auct_sprice_2406369
					// const price3Text = price3Element.textContent.trim().replace(/,/g, '');
					// const price3num = parseInt(price3Text);
					// const pydanga3 = parseInt(price3num / (areaPy * 10000));

					// const lineBreakSpan3 = document.createElement('span');
					// lineBreakSpan3.innerHTML = '<br>'; // This will render as an actual line break

					// const pydanga3Span = document.createElement('span');
					// pydanga3Span.textContent = `@${pydanga3}만원`;
					// pydanga3Span.style.opacity = 0.5; // 50% opacity
					// pydanga3Span.style.color = 'blue';

					// price3Element.appendChild(lineBreakSpan3);
					// price3Element.appendChild(pydanga3Span);
				// }
				price1Element.dataset.highlighted = true;
			}
		} else {
			console.log('면적 없어서 pass');
		}
	});
}


// 탱크 auction 세부조회 적용
function extractPropertyInfoDetailTank() {
	let areaPy;

	const tbody = document.querySelector('.Btbl_list');
	const headerCells = tbody.querySelectorAll('th');
	for (const headerCell of headerCells) {
		if (headerCell.textContent.includes('토지면적')) {
			const areaLand = headerCell.nextElementSibling;
			// const content = areaLand.textContent.trim(); //내용에서 공백 제가
			const content = areaLand.innerHTML.trim(); //내용에서 공백 제가
			const lines = content.split(/<br\s*\/?>/i);
			const regex = /\((\d+\.\d+)\평\)/;

			lines.forEach (part => {
				const match = part.match(regex);
				if (match) {
					areaPy = parseFloat(match [1]);
					console.log(areaPy);
				} else {
					console.log('면적 추출 실패');
				}
			});
		}
	}

	for (const headerCell of headerCells) {
		if (headerCell.textContent.includes('건물면적')) {
			const areaBd = headerCell.nextElementSibling;
			const content = areaBd.innerHTML.trim(); //내용에서 공백 제가
			const lines = content.split(/<br\s*\/?>/i);
			const regex = /\((\d+\.\d+)\평\)/;

			lines.forEach (part => {
				const match = part.match(regex);
				if (match) {
					areaPy = parseFloat(match [1]);
					console.log(areaPy);
				} else {
					console.log('면적 추출 실패');
				}
			});
		}
	}


	for (const headerCell of headerCells) {
		if (headerCell.textContent.includes('감정가')) {
			const price1Element = headerCell.nextElementSibling;
			const price1Text = price1Element.textContent.trim().replace(/,/g, '');
			const price1num = parseInt(price1Text);
			const pydanga1 = parseInt(price1num / (areaPy * 10000));

			// Create a new <span> element for the line break
			const lineBreakSpan = document.createElement('span');
			lineBreakSpan.innerHTML = '<br>'; // This will render as an actual line break

			const pydanga1Span = document.createElement('span');
			pydanga1Span.textContent = `@${pydanga1}만원`;
			pydanga1Span.style.opacity = 0.5; // 50% opacity
			pydanga1Span.style.color = 'red';

			// Append the line break and the calculated value to the content
			price1Element.appendChild(lineBreakSpan);
			price1Element.appendChild(pydanga1Span);

		}
	}


	for (const headerCell of headerCells) {
		if (headerCell.textContent.includes('최저가')) {
			const price2Element = headerCell.nextElementSibling;
			const price2Text1 = price2Element.textContent.trim().replace(/\(\d+%\)\s*/g, '');
			const price2Text = price2Text1.replace(/[,원]/g,'');
			const price2num = parseInt(price2Text);
			console.log(price2num);
			const pydanga2 = parseInt(price2num / (areaPy * 10000));

			// Create a new <span> element for the line break
			const lineBreakSpan2 = document.createElement('span');
			lineBreakSpan2.innerHTML = '<br>'; // This will render as an actual line break

			const pydanga2Span = document.createElement('span');
			pydanga2Span.textContent = `@${pydanga2}만원`;
			pydanga2Span.style.opacity = 0.5; // 50% opacity
			pydanga2Span.style.color = 'green';

			// Append the line break and the calculated value to the content
			price2Element.appendChild(lineBreakSpan2);
			price2Element.appendChild(pydanga2Span);

		}
	}


	for (const headerCell of headerCells) {
		if (headerCell.textContent.includes('매각가')) {
			const price3Element = headerCell.nextElementSibling;
			const price3Text1 = price3Element.textContent.trim().replace(/\(\d+%\)\s*/g, '');
			const price3Text = price3Text1.replace(/[,원]/g,'');
			const price3num = parseInt(price3Text);
			// console.log(price2num);
			const pydanga2 = parseInt(price3num / (areaPy * 10000));

			// Create a new <span> element for the line break
			const lineBreakSpan3 = document.createElement('span');
			lineBreakSpan3.innerHTML = '<br>'; // This will render as an actual line break

			const pydanga3Span = document.createElement('span');
			pydanga3Span.textContent = `@${pydanga2}만원`;
			pydanga3Span.style.opacity = 0.5; // 50% opacity
			pydanga3Span.style.color = 'blue';

			// Append the line break and the calculated value to the content
			price3Element.appendChild(lineBreakSpan3);
			price3Element.appendChild(pydanga3Span);

		}
	}

}

// 페이지가 로드되면 실행
window.addEventListener('load', function() {
    if (window.location.href.startsWith('https://new.land.naver.com/offices') ||
        window.location.href.startsWith('https://new.land.naver.com/houses') ||
        window.location.href.startsWith('https://new.land.naver.com/complexes')) {
        setTimeout(extractPropertyInfo,50);
        observeMutations(); // DOM 변경 감시 시작
    }

    	// Tank Auction 목록조회아이템 적용(경매,공매)
	if (window.location.href.startsWith('https://www.tankauction.com/ca/caList.php') ||
        window.location.href.startsWith('https://www.tankauction.com/pa/paList.php')) {
		setTimeout(extractPropertyInfoTank,50);
		observeMutationsTank();
	}

	// Tank Auction 세부조회아이템 적용
	if (window.location.href.startsWith('https://www.tankauction.com/ca/caView.php') ||
        window.location.href.startsWith('https://www.tankauction.com/pa/paView.php')) {
		extractPropertyInfoDetailTank();
	}

});
