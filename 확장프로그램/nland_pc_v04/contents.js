// content.js

// config초기화를 위한 부분(개발용)
// chrome.storage.local.remove(['config'], function() {
	// console.log('Config removed from local storage.');
// });

let propertyData = [];
let propertyData2 = [];
let tableData1 = []; // 월세 테이블 만들 데이터 { key: data, key2: data2} 형식으로 저장
let tableData2 = []; // 매매테이블 만들 데이터
let newBox2;
let datalength1 = 0;
let datalength2 = 0;

// config으로 만들 부분
let contiStatus = false;
let floorsorting = true;
let dangaAsc = true;
let autoScroll = false;
let tableshowstatus = false;
let percentMargin = 6.5;
let onoffstatus = true;
// config으로 만들 부분 끝

let oldItems;
let observer; // observer를 외부에서 선언
let timeout; // 타이머를 저장할 변수
let isScheduled = false; // 함수 호출이 예약되었는지 여부를 나타내는 플래그

//
// 테이블 복제처리
let tableData1_copy = []; // 월세 테이블 만들 데이터 { key: data, key2: data2} 형식으로 저장
let tableData2_copy = []; // 매매테이블 만들 데이터

// 기존 테이블 제거 함수
function removeTable() {
	const existingSummaryTable = document.getElementById('summaryTableId'); // Get the table by its ID
  	if (existingSummaryTable) {
    	existingSummaryTable.remove(); // newBox2에서 기존 요약 테이블 제거
  	}
  	//
  	const existingListTable = document.getElementById('listTableId'); // Get the table by its ID
  	if (existingListTable) {
    	existingListTable.remove(); // newBox2에서 기존 테이블 제거
  	}
}

// 해당 층에 맞는 데이터를 필터링하여 테이블 생성 함수
function filterAndDisplayTable(selectedDealType, floor) {
	//
	tableData1 = [];
	tableData2 = [];
	if (selectedDealType === '월세') {
		if (floor === "전체") {
			tableData1 = tableData1_copy;
			tableData2 = []; // 매매 데이터는 제외
		} else if (floor === "저층")	{
			tableData1 = tableData1_copy.filter(item => Number(item.해당층) <= 2);
			tableData2 = []; // 매매 데이터는 제외
		} else if (floor === "상층") {
			tableData1 = tableData1_copy.filter(item => Number(item.해당층) >= 3);
			tableData2 = []; // 매매 데이터는 제외
		} else {
			tableData1 = tableData1_copy.filter(item => item.해당층 === String(floor));
			tableData2 = []; // 매매 데이터는 제외
		}
	} else if (selectedDealType === '매매') {
		if (floor === "전체") {
			tableData1 = []; // 월세 데이터는 제외
			tableData2 = tableData2_copy;
		} else if (floor === "저층")	{
			tableData1 = []; // 월세 데이터는 제외
			tableData2 = tableData2_copy.filter(item => Number(item.해당층) <= 2);
		} else if (floor === "상층")	{
			tableData1 = []; // 월세 데이터는 제외
			tableData2 = tableData2_copy.filter(item => Number(item.해당층) >= 3);
		} else {
			tableData1 = []; // 월세 데이터는 제외
			tableData2 = tableData2_copy.filter(item => item.해당층 === String(floor));
		}
	} else { // 전체
		if (floor === "전체") {
			tableData1 = tableData1_copy;
			tableData2 = tableData2_copy;
		} else if (floor === "저층")	{
			tableData1 = tableData1_copy.filter(item => Number(item.해당층) <= 2);
			tableData2 = tableData2_copy.filter(item => Number(item.해당층) <= 2);
		} else if (floor === "상층")	{
			tableData1 = tableData1_copy.filter(item => Number(item.해당층) >= 3);
			tableData2 = tableData2_copy.filter(item => Number(item.해당층) >= 3);
		} else {
			tableData1 = tableData1_copy.filter(item => item.해당층 === String(floor));
			tableData2 = tableData2_copy.filter(item => item.해당층 === String(floor));
		}
	}
	// 요약정보
	summaryAndDisplayTable();
	// 리스트정보
	listAndDisplayTable();
}


// 요약정보
function summaryAndDisplayTable() {

		// tableData1:월세, tableData2:매매, tableData3:요약목록
		// 요약테이블 데이터 정리
		const tableData3 = [];

		// 값산출 1층
		const filteredData = tableData1.filter(item => item.해당층 === '1');
		const pValues = filteredData.map(item => item.평당가);
		console.log('필터된 데이터', filteredData);

		if (pValues.length != 0) {  // 1층 데이터가 0인 경우 열 안나타나도록
			let minPdanga = Math.min(...pValues);
			let maxPdanga = Math.max(...pValues);
			let avgPdanga = pValues.reduce((sum, value) => sum + value, 0) / pValues.length;

			// NaN 또는 Infinity인 경우 0으로 설정
			minPdanga = isFinite(minPdanga) ? minPdanga : 0;
			maxPdanga = isFinite(maxPdanga) ? maxPdanga : 0;
			avgPdanga = isFinite(avgPdanga) ? avgPdanga : 0;

			tableData3.push(['1층', minPdanga.toFixed(1), avgPdanga.toFixed(1), maxPdanga.toFixed(1), pValues.length]);
		}

		// 값산출 2층
		const filteredData2 = tableData1.filter(item => item.해당층 === '2');
		console.log('필터된 데이터 / 2층', filteredData2);
		const pValues2 = filteredData2.map(item => item.평당가);

		// 값산출 상
		const filteredData3 = tableData1.filter(item => item.해당층 >= 3);
		console.log('필터된 데이터 / 상층', filteredData3);
		const pValues3 = filteredData3.map(item => item.평당가);

		if (pValues2.length == 0) {
			if (pValues.length !=0 && pValues3.length != 0){
				tableData3.push(['2층', 0,0,0,0]);
			}
		} else {
			let minPdanga2 = Math.min(...pValues2);
			let maxPdanga2 = Math.max(...pValues2);
			let avgPdanga2 = pValues2.reduce((sum, value) => sum + value, 0) / pValues2.length;

			// NaN 또는 Infinity인 경우 0으로 설정
			minPdanga2 = isFinite(minPdanga2) ? minPdanga2 : 0;
			maxPdanga2 = isFinite(maxPdanga2) ? maxPdanga2 : 0;
			avgPdanga2 = isFinite(avgPdanga2) ? avgPdanga2 : 0;

			tableData3.push(['2층', minPdanga2.toFixed(1), avgPdanga2.toFixed(1), maxPdanga2.toFixed(1), pValues2.length]);
		}

		if (pValues3.length != 0) {
			let minPdanga3 = Math.min(...pValues3);
			let maxPdanga3 = Math.max(...pValues3);
			let avgPdanga3 = pValues3.reduce((sum, value) => sum + value, 0) / pValues3.length;

			// NaN 또는 Infinity인 경우 0으로 설정
			minPdanga3 = isFinite(minPdanga3) ? minPdanga3 : 0;
			maxPdanga3 = isFinite(maxPdanga3) ? maxPdanga3 : 0;
			avgPdanga3 = isFinite(avgPdanga3) ? avgPdanga3 : 0;

			tableData3.push(['상층', minPdanga3.toFixed(1), avgPdanga3.toFixed(1), maxPdanga3.toFixed(1), pValues3.length]);
		}

		const stable = document.createElement('table');
		const sthead = document.createElement('thead');
		const stbody = document.createElement('tbody');

		//테이블 스타일 정해주기
		stable.id = 'summaryTableId'; // Assign a unique ID to the table
		stable.style.fontSize = '10pt';
		stable.style.borderCollapse = 'collapse'; // 테이블 셀 간의 간격 제거
		stable.style.width = '70%'; // 테이블 폭 설정
		stable.style.marginTop = '10px';
		stable.style.marginBottom = '15px';
		stable.style.marginLeft = '75px'; // 왼쪽 여백 자동 설정
		stable.style.marginRight = 'auto'; // 오른쪽 여백 자동 설정

		// 테이블 헤더 생성
		const sheaderRow = document.createElement('tr');
		const sheaders = ['구분', '최소', '평균', '최대', '건수'];
		sheaders.forEach(headerText => {
			const th = document.createElement('th');
			th.textContent = headerText;
			sheaderRow.appendChild(th);

			th.style.backgroundColor = '#ddddff'; // 첫 번째 줄 배경색 설정
			th.style.border = '0.5px solid #333333'; // 테두리 설정
		});
		sthead.appendChild(sheaderRow);

		tableData3.forEach(item => {
			const row = document.createElement('tr');
			Object.values(item).forEach(value => {
				const td = document.createElement('td');
				td.textContent = value;
				td.style.border = '0.5px solid #333333'; // 테두리 설정
				td.style.textAlign = 'center'; // 텍스트 가운데 정렬
				row.appendChild(td);
			});
			stbody.appendChild(row);
		});

		// ==========================================================
		// 매매: 건수, 최소, 평균, 최대
		const tableDanga2 = tableData2.map(item => item.평당가);
		// add by kang 요약테이블에 매매정보 추가함.
		if (tableDanga2.length > 0) {
			const maxValue2 = Math.max(...tableDanga2);
			const minValue2 = Math.min(...tableDanga2);
			const avgValue2 = tableDanga2.reduce((sum, value) => sum + value, 0) / tableDanga2.length; //평균 구하기
			const summaryData = {
				titValue2: '매매',
				minValue2: Math.min(...tableDanga2),
				avgValue2: (tableDanga2.reduce((sum, value) => sum + value, 0) / tableDanga2.length).toFixed(0), // 소수점 2자리까지
				maxValue2: Math.max(...tableDanga2),
				cntValue2: tableDanga2.length
			};
			// 매매 요약 데이터 추가
			const summaryRow = document.createElement('tr');
			Object.values(summaryData).forEach((value,index) => {
				const td = document.createElement('td');
				if (index === 0) {
					// 첫 번째 열(첫 번째 td)의 텍스트를 파란색으로 설정
					td.style.color = 'blue';
				}
				td.textContent = value;
				td.style.border = '0.5px solid #333333';
				td.style.textAlign = 'center';
				summaryRow.appendChild(td);
			});
			stbody.appendChild(summaryRow);
		}

		// 요약테이블 생성
		stable.appendChild(sthead);
		stable.appendChild(stbody);
		newBox2.appendChild(stable); // 테이블을 newBox2에 추가
}

// 리스트 테이블
function listAndDisplayTable() {

		const table = document.createElement('table');
		const thead = document.createElement('thead');
		const tbody = document.createElement('tbody');

		//테이블 스타일 정해주기
		table.id = 'listTableId'; // Assign a unique ID to the table
		table.style.fontSize = '10pt';
		table.style.borderCollapse = 'collapse'; // 테이블 셀 간의 간격 제거
		table.style.width = '330px'; // 테이블 폭 설정
		table.style.marginleft = '0px'
		table.style.marginTop = '0px';

		if (floorsorting == true) {
			// 월세 자료를 층 오름차순으로 정리
			console.log('오름차순 정리전 data', tableData1)
			tableData1.sort((a, b) => {
				const secondKeyA = Object.values(a)[1];
				const secondKeyB = Object.values(b)[1];
				if (secondKeyA < secondKeyB) return -1;
				if (secondKeyA > secondKeyB) return 1;
				return 0;
			});
			console.log('오름차순 정리후 data', tableData1)

			// 매매자료를 단가 낮은것부터 오름차순으로 정리
			tableData2.sort((a, b) => {
				const secondKeyA = Object.values(a)[4];
				const secondKeyB = Object.values(b)[4];
				if (secondKeyA < secondKeyB) return -1;
				if (secondKeyA > secondKeyB) return 1;
				return 0;
			});

		} else {
			// 월세 자료를 층 오름차순으로 정리
			console.log('오름차순 정리전 data', tableData1)
			tableData1.sort((a, b) => {
				const secondKeyA = Object.values(a)[3];
				const secondKeyB = Object.values(b)[3];
				if (secondKeyA < secondKeyB) return -1;
				if (secondKeyA > secondKeyB) return 1;
				return 0;
			});
			console.log('오름차순 정리후 data', tableData1)


			// 매매자료를 단가 낮은것부터 오름차순으로 정리
			tableData2.sort((a, b) => {
				const secondKeyA = Object.values(a)[3];
				const secondKeyB = Object.values(b)[3];
				if (secondKeyA < secondKeyB) return -1;
				if (secondKeyA > secondKeyB) return 1;
				return 0;
			});
		}

		// 테이블 헤더 생성
		const headerRow = document.createElement('tr');
		const headers = ['구분', '층', '향', '평당가', '면적', '가격'];
		headers.forEach(headerText => {
			const th = document.createElement('th');
			th.textContent = headerText;
			headerRow.appendChild(th);
			th.style.backgroundColor = '#ddddff'; // 첫 번째 줄 배경색 설정
			th.style.border = '0.5px solid #333333'; // 테두리 설정
		});
		thead.appendChild(headerRow);

		tableData1.forEach(item => {
			const row = document.createElement('tr');
			Object.values(item).forEach((value, index) => {
				const td = document.createElement('td');
				if (index == 1) { // 2열 (index는 0부터 시작)
					td.textContent = value + ' / ' + Object.values(item)[2]; // 2열 값과 3열 값 결합
					td.style.border = '0.5px solid #333333'; // 테두리 설정
					td.style.textAlign = 'center'; // 텍스트 가운데 정렬
					row.appendChild(td);
				} else if (index !== 2) { // 3열은 이미 2열에 추가되었으므로 건너뜀
					td.textContent = value;
					td.style.border = '0.5px solid #333333'; // 테두리 설정
					td.style.textAlign = 'center'; // 텍스트 가운데 정렬
					row.appendChild(td);
				}
			});
			tbody.appendChild(row);
		});

		tableData2.forEach(item => {
			const row = document.createElement('tr');
			Object.values(item).forEach((value, index) => {
				const td = document.createElement('td');
				if (index === 0) {
					// 첫 번째 열(첫 번째 td)의 텍스트를 파란색으로 설정
					td.style.color = 'blue';
				}
				if (index == 1) { // 2열 (index는 0부터 시작)
					td.textContent = value + ' / ' + Object.values(item)[2]; // 2열 값과 3열 값 결합
					td.style.border = '0.5px solid #333333'; // 테두리 설정
					td.style.textAlign = 'center'; // 텍스트 가운데 정렬
					row.appendChild(td);
				} else if (index !== 2) { // 3열은 이미 2열에 추가되었으므로 건너뜀
					td.textContent = value;
					td.style.border = '0.5px solid #333333'; // 테두리 설정
					td.style.textAlign = 'center'; // 텍스트 가운데 정렬
					row.appendChild(td);
				}
			});
			tbody.appendChild(row);
		});

		table.appendChild(thead);
		table.appendChild(tbody);
		newBox2.appendChild(table); // 테이블을 newBox2에 추가
}

// 층선택 리스트 표시
function selectedAndDisplay() {

		// 1. tableData1와 tableData2 합치기
		const combinedData = [...tableData1_copy, ...tableData2_copy];

		// 2. 합쳐진 데이터에서 '해당층' 값만 추출하고 null, undefined 제외 후 중복 제거
		const uniqueFloors = [...new Set(combinedData.map(item => item.해당층).filter(floor => floor !== null && floor !== undefined))];

		// 3. 층 번호 오름차순 정렬
		uniqueFloors.sort((a, b) => a - b);

		// 4. 거래 형태 드롭다운 목록 생성
		const dealTypeSelect = document.createElement('select');
		// 드롭다운 스타일 (파란색 배경, 흰색 텍스트)
		dealTypeSelect.id = 'dealTypeSelect'; // id 추가
		dealTypeSelect.style.backgroundColor = '#dc3545'; // 부드러운 붉은색 (Bootstrap danger 색상)
		dealTypeSelect.style.border = '1px solid #b52b37'; // 테두리는 더 어두운 붉은색
		dealTypeSelect.style.color = 'white'; // 흰색 텍스트
		dealTypeSelect.style.padding = '3px 6px'; // 패딩 추가 (좌우 여백 추가)
		dealTypeSelect.style.borderRadius = '4px'; // 둥근 모서리
		dealTypeSelect.style.fontSize = '13px'; // 글자 크기 조정

		// 거래 형태 옵션 설정
		const dealOptions = ['전체'];
		if (tableData1_copy.length > 0) {
			dealOptions.push('월세');
		}
		if (tableData2_copy.length > 0) {
			dealOptions.push('매매');
		}
		// 옵션 추가
		dealOptions.forEach(type => {
			const option = document.createElement('option');
			option.value = type;
			option.textContent = type;
			dealTypeSelect.appendChild(option);
		});

		// 5. 층 선택 드롭다운 목록 생성
		const floorSelect = document.createElement('select');
		// 드롭다운 스타일 (파란색 배경, 흰색 텍스트)
		floorSelect.id = 'floorSelect'; // id 추가
		floorSelect.style.backgroundColor = '#66b3ff'; // 부드러운 푸른색 배경
		floorSelect.style.border = '1px solid #b52b37'; // 테두리는 더 어두운 붉은색
		floorSelect.style.color = 'white'; // 흰색 텍스트
		floorSelect.style.padding = '3px 1px'; // 패딩 추가 (좌우 여백 추가)
		floorSelect.style.borderRadius = '4px'; // 둥근 모서리
		floorSelect.style.fontSize = '13px'; // 글자 크기 조정

		// 5. "전체" 옵션 추가
		const options = ['전체'];
		options.forEach(optionText => {
			const option = document.createElement('option');
			option.value = optionText;
			option.textContent = optionText;
			floorSelect.appendChild(option);
		});

		// 저층 옵션 추가 (3층 이하가 있으면)
		if (uniqueFloors.some(floor => floor <= 2)) {
		  const lowOption = document.createElement('option');
		  lowOption.value = '저층';
		  lowOption.textContent = '저층';
		  floorSelect.appendChild(lowOption);
		}

		// 상층 옵션 추가 (2층 이상이 있으면)
		if (uniqueFloors.some(floor => floor >= 3)) {
		  const highOption = document.createElement('option');
		  highOption.value = '상층';
		  highOption.textContent = '상층';
		  floorSelect.appendChild(highOption);
		}

		// 6. 각 층을 드롭다운 목록에 추가
		uniqueFloors.forEach(floor => {
			const option = document.createElement('option');
			option.value = floor;
			option.textContent = `${floor}층`;
			floorSelect.appendChild(option);
		});

		// floorContainer 생성 및 위치 설정
		const floorContainer = document.createElement('div');
		floorContainer.style.position = 'absolute'; // floorContainer에 위치 설정
		floorContainer.style.top = '40px'; // 새로운 박스의 맨 위에 배치
		floorContainer.style.left = '7px'; // 새로운 박스의 왼쪽에 배치

		// 1. 층 선택 라벨 만들기
		const floorLabel = document.createElement('label');
		floorLabel.textContent = '구분/층선택';
		floorLabel.style.fontSize = '13px';
		floorLabel.style.fontWeight = 'bold';
		floorLabel.style.display = 'block'; // 라벨을 블록 요소로 설정하여 아래에 드롭다운이 오도록 설정
		floorLabel.style.marginBottom = '2px'; // 라벨과 드롭다운 간격 추가

		// 3. floorContainer에 라벨과 드롭다운 추가
		floorContainer.appendChild(floorLabel);
		floorContainer.appendChild(dealTypeSelect);  // 거래 형태 드롭다운 추가
		floorContainer.appendChild(floorSelect);

		// 4. newBox2에 floorContainer 추가
		newBox2.appendChild(floorContainer);
		/// 층선택 생성 마지막

		// 거래 형태 선택 드롭다운 이벤트 리스너
		dealTypeSelect.addEventListener('change', (event) => {
			const selectedDealType = event.target.value;
			//const selectedFloor = floorSelect.value; // 층 선택 값 가져오기
			const selectedFloor = "전체"; // 전체층 선택 값 가져오기

			removeTable(); // 기존 테이블 제거
			filterAndDisplayTable(selectedDealType, selectedFloor); // 선택된 거래 형태와 층에 맞게 필터링

			// floorSelect 초기화 => 구분 선택에 따라서 처리
			floorSelect.innerHTML = '';

			let floorsToAdd = [];

			// 선택된 거래 형태에 따른 층수 데이터 설정
			if (dealTypeSelect.value === '월세') {
				floorsToAdd = [...new Set(tableData1_copy.map(item => item.해당층).filter(floor => floor !== null && floor !== undefined))];
			} else if (dealTypeSelect.value === '매매') {
				floorsToAdd = [...new Set(tableData2_copy.map(item => item.해당층).filter(floor => floor !== null && floor !== undefined))];
			} else if (dealTypeSelect.value === '전체') {
				floorsToAdd = [...new Set(combinedData.map(item => item.해당층).filter(floor => floor !== null && floor !== undefined))];
			}
			// 중복 제거 후 오름차순 정렬
			floorsToAdd.sort((a, b) => a - b);

			// "전체" 옵션 추가
			const options = ['전체'];
			options.forEach(optionText => {
				const option = document.createElement('option');
				option.value = optionText;
				option.textContent = optionText;
				floorSelect.appendChild(option);
			});

			// 저층 옵션 추가 (3층 이하가 있으면)
			if (floorsToAdd.some(floor => floor <= 2)) {
			  const lowOption = document.createElement('option');
			  lowOption.value = '저층';
			  lowOption.textContent = '저층';
			  floorSelect.appendChild(lowOption);
			}

			// 상층 옵션 추가 (2층 이상이 있으면)
			if (floorsToAdd.some(floor => floor >= 3)) {
			  const highOption = document.createElement('option');
			  highOption.value = '상층';
			  highOption.textContent = '상층';
			  floorSelect.appendChild(highOption);
			}

			// 층수 옵션 추가
			floorsToAdd.forEach(floor => {
				const option = document.createElement('option');
				option.value = floor;
				option.textContent = `${floor}층`;
				floorSelect.appendChild(option);
			});

		});

		// 7. 층선택 드롭다운에 이벤트 리스너 추가
		floorSelect.addEventListener('change', (event) => {
			const selectedFloor = event.target.value;
			const selectedDealType = dealTypeSelect.value; // 거래 형태 선택 값 가져오기

			removeTable(); // 기존 테이블 제거
			filterAndDisplayTable(selectedDealType, selectedFloor); // 선택된 거래 형태와 층에 맞게 필터링
		});
}

// 평형분석팝업을 생성하는 함수
function openPyeongAnalysisPopup() {
  // 0. 안정적으로 select 값 가져오기 (id로 접근)
  const dealTypeSelect = document.getElementById('dealTypeSelect');
  const floorSelect = document.getElementById('floorSelect');
  const dealTypeValue = dealTypeSelect ? dealTypeSelect.value : "전체";
  const floorValue = floorSelect ? floorSelect.value : "전체";
  const headerText = `${dealTypeValue} > ${floorValue}`;

  // 1. tableData1과 tableData2 결합 후 중복 제거
  // (구분, 해당층, 향, 평당가, 전용면적, 가격이 동일하면 하나로 처리하며, 해당층이 falsy인 항목은 제외)
  const combinedData = [...tableData1, ...tableData2];
  const dedupedData = [];
  const seen = new Set();
  combinedData.forEach(item => {
    if (!item["해당층"]) return; // 해당층이 없으면 건너뜁니다.
    const key = `${item["구분"]}|${item["해당층"]}|${item["향"]}|${item["평당가"]}|${item["전용면적"]}|${item["가격"]}`;
    if (!seen.has(key)) {
      seen.add(key);
      dedupedData.push(item);
    }
  });

  // 2. 그룹화: 각 항목에서 floor(해당층의 "/" 앞 숫자)와 전용면적 그룹
  // (10미만: "9평", 10이상: floor(area/10)*10 + "평") 기준으로 그룹화
  const groups = {};
  dedupedData.forEach(item => {
    // 해당층이 없는 경우는 이미 제거됨
    const area = parseFloat(item["전용면적"]);
    if (isNaN(area)) return;
    // floor 추출 (예: "1/4" → "1")
    const floorExtract = item["해당층"].split('/')[0];
    let floorCategory;
    const floorNum = Number(floorExtract);
    if (floorNum === 1) floorCategory = "1층";
    else if (floorNum === 2) floorCategory = "2층";
    else if (floorNum >= 3) floorCategory = "상층";
    else floorCategory = item["해당층"];

    // 전용면적 그룹
    const areaGroup = area < 10 ? "9평" : `${Math.floor(area / 10) * 10}평`;
    if (!groups[floorCategory]) {
      groups[floorCategory] = {};
    }
    if (!groups[floorCategory][areaGroup]) {
      groups[floorCategory][areaGroup] = { count: 0, sum: 0 };
    }
    const unitPrice = parseFloat(item["평당가"]);
    if (!isNaN(unitPrice)) {
      groups[floorCategory][areaGroup].count += 1;
      groups[floorCategory][areaGroup].sum += unitPrice;
    }
  });

  // 3. 각 floor 그룹별 총계 계산
  const floorTotals = {};
  Object.keys(groups).forEach(floorCat => {
    let totalCount = 0, totalSum = 0;
    Object.values(groups[floorCat]).forEach(group => {
      totalCount += group.count;
      totalSum += group.sum;
    });
    floorTotals[floorCat] = { count: totalCount, avg: totalCount > 0 ? (totalSum / totalCount).toFixed(1) : 0 };
  });

  // 4. 팝업 컨테이너 생성
  const popupDiv = document.createElement("div");
  popupDiv.id = "pyeongAnalysisPopup";
  popupDiv.style.cssText =
    "position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);" +
    "width: 400px; background-color: #fff; border: 2px solid #007bff; border-radius: 8px;" +
    "box-shadow: 0 4px 8px rgba(0,0,0,0.2); padding: 10px; overflow-y: auto; z-index: 10000;";

  // 4.1 헤더 상단에 선택된 값 표시 (왼쪽 정렬)
  const headerDiv = document.createElement("div");
  headerDiv.style.textAlign = "left";
  headerDiv.style.marginBottom = "10px";
  headerDiv.style.fontSize = "14px";
  headerDiv.style.fontWeight = "bold";
  headerDiv.textContent = headerText;
  popupDiv.appendChild(headerDiv);

  //4.2 팝업 드래그 가능하게 처리 (headerDiv로 드래그)
  	headerDiv.style.cursor = 'move';
	headerDiv.onmousedown = function(event) {
	  let shiftX = event.clientX - popupDiv.getBoundingClientRect().left;
	  let shiftY = event.clientY - popupDiv.getBoundingClientRect().top;

	  function moveAt(pageX, pageY) {
		popupDiv.style.left = pageX - shiftX + 'px';
		popupDiv.style.top = pageY - shiftY + 'px';
	  }
	  moveAt(event.pageX, event.pageY);

	  function onMouseMove(event) {
		moveAt(event.pageX, event.pageY);
	  }
	  document.addEventListener('mousemove', onMouseMove);

	  // 마우스 업 이벤트를 document에 등록해서, 드래그 후 어디서든 업하면 드래그 종료
	  document.onmouseup = function() {
		document.removeEventListener('mousemove', onMouseMove);
		document.onmouseup = null;
	  };
	};

	headerDiv.ondragstart = function() {
	  return false;
	};

  // 5. 테이블 생성 (colgroup 설정)
  const table = document.createElement("table");
  table.style.width = "100%";
  table.style.borderCollapse = "collapse";
  const colgroup = document.createElement("colgroup");
  const col1 = document.createElement("col"); col1.style.width = "10%"; // 순번
  const col2 = document.createElement("col"); col2.style.width = "15%"; // 구분
  const col3 = document.createElement("col"); col3.style.width = "25%"; // 평형
  const col4 = document.createElement("col"); col4.style.width = "25%"; // 건수
  const col5 = document.createElement("col"); col5.style.width = "25%"; // 평균평당가
  colgroup.appendChild(col1);
  colgroup.appendChild(col2);
  colgroup.appendChild(col3);
  colgroup.appendChild(col4);
  colgroup.appendChild(col5);
  table.appendChild(colgroup);

  // 6. 테이블 헤더 생성
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  headerRow.style.textAlign = "center";
  headerRow.style.backgroundColor = "#f2f2f2";

  const th1 = document.createElement("th");
  th1.textContent = "순번";
  th1.style.border = "1px solid #ccc";
  const th2 = document.createElement("th");
  th2.textContent = "구분";
  th2.style.border = "1px solid #ccc";
  const th3 = document.createElement("th");
  th3.textContent = "평형";
  th3.style.border = "1px solid #ccc";
  const th4 = document.createElement("th");
  th4.textContent = "건수";
  th4.style.border = "1px solid #ccc";
  const th5 = document.createElement("th");
  th5.textContent = "평균평당가";
  th5.style.border = "1px solid #ccc";

  headerRow.appendChild(th1);
  headerRow.appendChild(th2);
  headerRow.appendChild(th3);
  headerRow.appendChild(th4);
  headerRow.appendChild(th5);
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // 7. 테이블 바디 생성
  const tbody = document.createElement("tbody");
  // 고정 순서: 1층, 2층, 상층
  const floorOrder = ["1층", "2층", "상층"];
  // 부드러운 색상 지정
  const floorColors = {
    "1층": "#ffe0e0",
    "2층": "#e0f7ff",
    "상층": "#e0ffe0"
  };

  floorOrder.forEach(floorCat => {
    if (groups[floorCat]) {
      // 순번을 그룹별로 새로 시작: 각 floorCat 내부에서 1부터 시작
      let groupRowIndex = 1;
      const sortedAreaKeys = Object.keys(groups[floorCat]).sort((a, b) => {
        const numA = parseInt(a.replace("평", ""), 10);
        const numB = parseInt(b.replace("평", ""), 10);
        return numA - numB;
      });
      sortedAreaKeys.forEach((areaGroup, index) => {
        const { count, sum } = groups[floorCat][areaGroup];
        const avg = (sum / count).toFixed(1);
        const tr = document.createElement("tr");
        tr.style.textAlign = "center";
        tr.style.borderBottom = "1px solid #eee";
        tr.style.backgroundColor = floorColors[floorCat] || "#fff";

        // 순번 셀 (그룹 내에서 재시작)
        const tdIndex = document.createElement("td");
        tdIndex.textContent = groupRowIndex;
        tdIndex.style.border = "1px solid #ccc";
        tr.appendChild(tdIndex);
        groupRowIndex++;

        // 구분 셀: 같은 floor 그룹 내 첫 행에만 표시 (rowspan = 전체 그룹 행 수 + 1)
        if (index === 0) {
          const tdFloor = document.createElement("td");
          tdFloor.textContent = floorCat;
          tdFloor.rowSpan = sortedAreaKeys.length + 1;
          tdFloor.style.border = "1px solid #ccc";
          tdFloor.style.backgroundColor = floorColors[floorCat] || "#fff";
          tdFloor.style.fontWeight = "bold";
          tr.appendChild(tdFloor);
        }
        // 평형 셀
        const tdArea = document.createElement("td");
        tdArea.textContent = areaGroup;
        tdArea.style.border = "1px solid #ccc";
        tr.appendChild(tdArea);

        // 건수 셀
        const tdCount = document.createElement("td");
        tdCount.textContent = count;
        tdCount.style.border = "1px solid #ccc";
        tr.appendChild(tdCount);

        // 평균평당가 셀
        const tdAvg = document.createElement("td");
        tdAvg.textContent = avg;
        tdAvg.style.border = "1px solid #ccc";
        tr.appendChild(tdAvg);

        tbody.appendChild(tr);
      });
      // 총합(합계) 행 for floor group
      const floorTotal = floorTotals[floorCat];
      const totalRow = document.createElement("tr");
      totalRow.style.textAlign = "center";
      totalRow.style.backgroundColor = "#f9f9f9";

      // 총합 행: 5개의 셀 - [빈셀, 빈셀, "합계", 건수, 평균평당가]
      const totalCellEmpty1 = document.createElement("td");
      totalCellEmpty1.textContent = "";
      totalCellEmpty1.style.border = "1px solid #ccc";
      totalRow.appendChild(totalCellEmpty1);

      const totalCellLabel = document.createElement("td");
      totalCellLabel.textContent = "합계";
      totalCellLabel.style.border = "1px solid #ccc";
      totalCellLabel.style.fontWeight = "bold";
      totalRow.appendChild(totalCellLabel);

      const totalCellCount = document.createElement("td");
      totalCellCount.textContent = floorTotal.count;
      totalCellCount.style.border = "1px solid #ccc";
      totalCellCount.style.fontWeight = "bold";
      totalRow.appendChild(totalCellCount);

      const totalCellAvg = document.createElement("td");
      totalCellAvg.textContent = floorTotal.avg;
      totalCellAvg.style.border = "1px solid #ccc";
      totalCellAvg.style.fontWeight = "bold";
      totalRow.appendChild(totalCellAvg);

      tbody.appendChild(totalRow);
    }
  });

  table.appendChild(tbody);
  popupDiv.appendChild(table);

  // 8. 팝업 하단 중앙에 닫기 버튼 생성
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

  // 9. 팝업을 body에 추가하여 표시
  document.body.appendChild(popupDiv);
}



function extractPropertyInfo() {
	// 기본 컨트롤 박스 넣기
	const onoffPanel = document.querySelector('.filter_area');
	onoffPanel.style.display = 'inline-block'; // 줄 바꿈 방지

	if (!onoffPanel.dataset.highlighted) {

		// 오토스크롤모드 on/off 버튼 생성
		const modeText4 = document.createElement('span');
		modeText4.textContent = '프로그램';
		modeText4.style.marginLeft = '10px'; // modeText와의 간격 조절

		const toggleSwitch4 = document.createElement('input');
		toggleSwitch4.type = 'checkbox';
		toggleSwitch4.id = 'toggleSwitch4';
		toggleSwitch4.style.width = '5px';
		toggleSwitch4.style.height = '15px';
		// toggleSwitch.style.position = 'relative';
		toggleSwitch4.checked = onoffstatus;

		// 토글 스위치 레이블 생성
		const label4 = document.createElement('label');
		label4.htmlFor = 'toggleSwitch4';
		label4.style.display = 'inline-block';
		label4.style.width = '30px';
		label4.style.height = '15px';
		label4.style.borderRadius = '7.5px';
		label4.style.position = 'relative';
		label4.style.cursor = 'pointer';
		label4.style.padding = '0'; // 추가된 부분
		label4.style.margin = '0'; // 추가된 부분
		label4.style.marginRight = '5px'; // modeText와의 간격 조절

		// 토글 스위치 핸들 생성
		const handle4 = document.createElement('span');
		handle4.style.display = 'block';
		handle4.style.width = '15px';
		handle4.style.height = '15px';
		handle4.style.background = 'white';
		handle4.style.borderRadius = '50%';
		handle4.style.position = 'relative';
		handle4.style.top = '0';
		handle4.style.transition = 'left 0.2s';

		if(onoffstatus){
			handle4.style.left = '15px';
			label4.style.background = 'green';

		} else {
			handle4.style.left = '0';
			label4.style.background = 'grey';
		}

		// 토글 스위치 상태 변경 시 핸들 위치 변경
		toggleSwitch4.addEventListener('change', function() {
			if (toggleSwitch4.checked) {
				handle4.style.left = '15px';
				label4.style.background = 'green';
				// modeText3.textContent = '수동';
				onoffstatus = true;

			} else {
				handle4.style.left = '0';
				label4.style.background = 'grey';
				// modeText3.textContent = '오토';

				let newBox = document.querySelector('.new-box'); // 기존 박스 요소 가져오기
				// newBox2 = document.querySelector('.new-box2'); // 기존 박스 요소 가져오기
				// console.log(newBox2);

				if (newBox){
					newBox.parentNode.removeChild(newBox);
					newBox = null;
				}

				if (newBox2){
					newBox2.parentNode.removeChild(newBox2);
					newBox2 = null;
				}
				onoffstatus = false;
			}

			// 설정을 불러와 변수 값을 변경하고 저장하는 함수
			getConfig(config => {
				console.log('Current config:', config);
				config.onoffstatus = onoffstatus;
				saveConfig(config, () => {
				  console.log('Feature toggled and config saved:', config);
				});
			});
		});

		// 요소들 DOM에 추가
		// let onoffPanel = document.createElement('span');

		onoffPanel.appendChild(modeText4);
		onoffPanel.appendChild(toggleSwitch4);
		label4.appendChild(handle4);
		onoffPanel.appendChild(label4);

		onoffPanel.dataset.highlighted = true;

		// 오토스크롤모드 버튼 추가
		const modeText5 = document.createElement('span');
		modeText5.textContent = '오토스크롤';
		modeText5.style.marginLeft = '10px'; // modeText와의 간격 조절

		const toggleSwitch5 = document.createElement('input');
		toggleSwitch5.type = 'checkbox';
		toggleSwitch5.id = 'toggleSwitch5';
		toggleSwitch5.style.width = '5px';
		toggleSwitch5.style.height = '15px';
		// toggleSwitch.style.position = 'relative';
		toggleSwitch5.checked = autoScroll;

		// 토글 스위치 레이블 생성
		const label5 = document.createElement('label');
		label5.htmlFor = 'toggleSwitch5';
		label5.style.display = 'inline-block';
		label5.style.width = '30px';
		label5.style.height = '15px';
		label5.style.borderRadius = '7.5px';
		label5.style.position = 'relative';
		label5.style.cursor = 'pointer';
		label5.style.padding = '0'; // 추가된 부분
		label5.style.margin = '0'; // 추가된 부분
		label5.style.marginRight = '5px'; // modeText와의 간격 조절

		// 토글 스위치 핸들 생성
		const handle5 = document.createElement('span');
		handle5.style.display = 'block';
		handle5.style.width = '15px';
		handle5.style.height = '15px';
		handle5.style.background = 'white';
		handle5.style.borderRadius = '50%';
		handle5.style.position = 'relative';
		handle5.style.top = '0';
		handle5.style.transition = 'left 0.2s';

		// 토글 스위치 위치 세팅
		if(autoScroll){
			handle5.style.left = '15px';
			label5.style.background = 'green';

		} else {
			handle5.style.left = '0';
			label5.style.background = 'grey';
		}

		// 토글 스위치 상태 변경 시 핸들 위치 변경
		toggleSwitch5.addEventListener('change', function() {
			if (toggleSwitch5.checked) {
				handle5.style.left = '15px';
				label5.style.background = 'green';
				autoScroll = true;;

			} else {
				handle5.style.left = '0px';
				label5.style.background = 'grey';
				autoScroll = false
			}

			getConfig(config => {
				console.log('Current config:', config);
				config.autoScroll = autoScroll;
				saveConfig(config, () => {
				  console.log('Feature toggled and config saved:', config);
				});
			});
		});

		// 요소들 DOM에 추가
		// let onoffPanel = document.createElement('span');

		onoffPanel.appendChild(modeText5);
		onoffPanel.appendChild(toggleSwitch5);
		label5.appendChild(handle5);
		onoffPanel.appendChild(label5);

		onoffPanel.dataset.highlighted = true;

		// 실거래검색 팝업
		//realSearchData();

		// 수익율 분석표
		//profitAnalData();
	}

	if (onoffstatus == true) {

		// 연속모드인지 확인하고 아니면 pass
			propertyData = [];
		if (contiStatus == false) {
			propertyData2 = [];
			tableData1 = []; // 월세 테이블 만들 데이터 { key: data, key2: data2} 형식으로 저장
			tableData2 = []; // 매매테이블 만들 데이터 - 필요하면 작성
			datalength1 = 0;
			datalength2 = 0;
			//
			// 테이블 복제처리
			tableData1_copy = [];
			tableData2_copy = [];
		}

		if (autoScroll == true) {
			const loadingStack = document.querySelector('.loader');
			const propertyItems = document.querySelectorAll('.item_inner:not(.is-loading)'); // 'is-loading' 클래스를 제외한 요소 선택

			console.log(loadingStack);
			if (loadingStack) {
				//해당 영역 스크롤
				loadingStack.scrollIntoView({ behavior: 'auto', block: 'center' }); // behavior auto / smooth
			}
		}

		const propertyItems = document.querySelectorAll('.item_inner:not(.is-loading)'); // 'is-loading' 클래스를 제외한 요소 선택
		console.log('propertyItems 불러옴',propertyItems);

		if (propertyItems != oldItems && propertyItems.length > 0) {

			propertyItems.forEach((item) => {
				// 매매, 월세 유형으로 추출하기
				item.style.padding = '5px'; // 간격 줄여주기
				const typeElement = item.querySelector('.type'); // 매매, 월세, 유형정보
				const type = typeElement.textContent.trim(); //텍스트로만 추출하기

				// 금액정보 찾아내기
				const priceElement = item.querySelector('.price'); // 금액정보
				const price = priceElement.textContent.trim().replace(/,/g, ''); // 매매는 '0억 000', 월세는 '2000/150'으로 표현됨
				const cleanedPrice2 = price.replace(/\(.*$/, ''); // ( 포함 이후 문자 삭제
				const cleanedPrice = cleanedPrice2.replace(/~.*$/, ''); // ~ 이후 문자 삭제
				const parts = cleanedPrice.split('/'); //문자열을 /로 분리

				//총 금액을 산출 - 억과 천단위를 찾아내기 위한 정규식
				const regex = /(\d+)억\s*(\d+)?/;
				let totalPrice = 0;
				parts.forEach(part => {
					const match = part.match(regex);
					if (match) {
						const billionPart = parseInt(match[1], 10) * 10000; // '억'을 10000으로 변환
						const thousandPart = match[2] ? parseInt(match[2].replace(/,/g, ''), 10) : 0; // '천' 단위를 숫자로 변환
						totalPrice = billionPart + thousandPart;
					} else {
						totalPrice = parseInt(part.replace(/[^0-9]/g, ''), 10);
					}
				});

				//전용면적 찾아내기
				const areaElement = item.querySelector('.spec'); // 상가,면적, 층수, 향, 기타설명
				const infodata = areaElement.textContent.trim();
				const info = infodata.split(',').map(part => part.trim());

				// 첫 번째 항목에서 /와 m² 사이의 숫자 추출
				const firstPart = info[0];
				const areaMatch = firstPart ? firstPart.match(/(\d+)m²/) : null;
				// const areaMatch = firstPart ? firstPart.match(/\/(\d+)m²/) : null;

				const areas2 = areaMatch ? parseInt(areaMatch[1], 10) : null; // 전용면적, 잘 찾아짐
				let areas = areas2 * 0.3025 ;
				const areas3 = areas.toFixed(2);
				// 전용면적 잘 찾아짐 but 토지는 안찾아짐 console.log(areas);

				// 층수 찾아내기
				const secondPart = info[1];
				const floorMatch = secondPart ? secondPart.match(/(\d+)\/(\d+)층/) : null;
				const cfloor = floorMatch ? floorMatch [1] : null; // 매물층
				const tfloor = floorMatch ? floorMatch [2] : null; // 전체층

				// 향 찾아내기
				const direction = info[2] !== undefined ? info[2] : '';

				if (areas > 0) {
					if (type == '월세') {
						const mprice = parts.length > 1 ? parseInt(parts[1].replace(/[^0-9]/g, ''), 10) : 0; // /뒤의 문자열 추출 mprice : 월세가격
						let pdanga = mprice / areas;
						pdanga = parseFloat(pdanga.toFixed(2)); // 소수점 2자리까지만 구하고 숫자로 변환

						let tprice = mprice * 12 * 100 / percentMargin / 10000;
						tprice = parseFloat(tprice.toFixed(1));

						areas = areas.toFixed(1);

						// 월세 정보를 붉은색으로 표시
						if (!priceElement.dataset.highlighted) {

							const priceSpan = document.createElement('span');
							priceSpan.textContent = `(${areas}평 @${pdanga}만`;
							priceSpan.style.opacity = 0.5; // 50% opacity
							priceSpan.style.color = 'red';
							priceSpan.style.fontSize = '11pt';

							const priceSpan2 = document.createElement('span');
							priceSpan2.textContent = `  >>${tprice}억)`;
							priceSpan2.style.opacity = 0.5; // 50% opacity
							priceSpan2.style.color = 'violet';
							priceSpan2.style.fontSize = '13pt';

							priceElement.appendChild(priceSpan);
							priceElement.appendChild(priceSpan2);


							// push함수를 사용하여 평단가를 목록으로 만들기
							propertyData.push(pdanga);
							let tabletext = `${info[1]}, ${direction}, ${pdanga}만/평, ${areas3}평, ${price}`;
							// console.log(tabletext);
							priceElement.dataset.highlighted = true; // 한 번만 실행되도록 표시
						}

						// 테이블에 넣기
						const tableitem = { 구분: type, 해당층: cfloor, 전체층: tfloor, 향: direction, 평당가: pdanga, 전용면적: areas3, 가격: cleanedPrice };

						//데이터를 배열화
						tableData1.push(tableitem);

						// 테이블 복제처리
						tableData1_copy = tableData1;
					}

					if (type == '매매') {
						let pdanga = parseInt(totalPrice / areas);
						areas = areas.toFixed(1);

						// 매매 정보를 붉은색으로 표시
						if (!priceElement.dataset.highlighted) {

							const priceSpan = document.createElement('span');
							priceSpan.textContent = `(${areas}평 @${pdanga}만)`;
							priceSpan.style.opacity = 0.5; // 50% opacity
							priceSpan.style.color = 'green';
							priceSpan.style.fontSize = '11pt';

							priceElement.appendChild(priceSpan);


							propertyData2.push(pdanga);
							priceElement.dataset.highlighted = true; // 한 번만 실행되도록 표시
						}

						// 테이블에 넣기
						const tableitem = { 구분: type, 해당층: cfloor, 전체층: tfloor, 향: direction, 평당가: pdanga, 전용면적: areas3, 가격: cleanedPrice };
						//데이터를 배열화
						tableData2.push(tableitem);

						// 테이블 복제처리
						tableData2_copy = tableData2;
					}
				}

				// 공인중개사 삭제
				const tagItem = item.querySelector('.tag_area');
				if (tagItem) {
					tagItem.remove();
				}

				// 공인중개사 삭제
				const cpItem = item.querySelector('.cp_area');
				if (cpItem) {
					cpItem.remove();
				}

				// 매물날짜 삭제
				const labelItem = item.querySelector('.label_area');
				if (labelItem) {
					labelItem.remove();
				}
			}); //propertyItems의 마지막
		}

		const mapWrap = document.querySelector('.map_wrap'); // .map_wrap 클래스를 가진 요소 선택

		//새창 띄울 부분(단가순,단일,층순,수익,요약표,초기화~ 그밑에 월세,매매 정보)
		if (mapWrap) {
			let newBox = mapWrap.querySelector('.new-box'); // 기존 박스 요소 가져오기
			// newBox2 = mapWrap.querySelectorAll('.new-box2'); // 기존 박스 요소 가져오기
			// console.log('새창띄우는 부분에서 newbox2확인', newBox2);

			if (!newBox) {
				const newBox = document.createElement('div'); // 새로운 박스 요소 생성
				newBox.classList.add('new-box'); // 필요한 클래스 추가 (예: .new-box)

				// 크기 설정 (200px x 200px)
				newBox.style.width = '400px';
				newBox.style.height = '80px';
				newBox.style.padding = '5px';


				// 배경색 설정 (#dddddd)
				newBox.style.backgroundColor = '#ffffff';

				// 내용 추가 (예: 텍스트, 이미지, 버튼 등)
				// newBox.textContent = '데이터 준비중'

				// 박스를 창 위로 올리기 (z-index 설정)
				newBox.style.zIndex = '9999';

				// 위치 설정 (오른쪽 위)
				newBox.style.position = 'absolute';
				newBox.style.top = '0px';
				newBox.style.left = '0px';


				// 정렬모드 on/off버튼 생성
				const modeText3 = document.createElement('span');
				modeText3.textContent = '단가순';

				const toggleSwitch3 = document.createElement('input');
				toggleSwitch3.type = 'checkbox';
				toggleSwitch3.id = 'toggleSwitch3';
				toggleSwitch3.style.width = '5px';
				toggleSwitch3.style.height = '10px';


				// 토글 스위치 레이블 생성
				const label3 = document.createElement('label');
				label3.htmlFor = 'toggleSwitch3';
				label3.style.display = 'inline-block';
				label3.style.width = '20px';
				label3.style.height = '10px';
				label3.style.borderRadius = '10px';
				label3.style.position = 'relative';
				label3.style.cursor = 'pointer';
				label3.style.padding = '0'; // 추가된 부분
				label3.style.margin = '0'; // 추가된 부분
				label3.style.marginRight = '5px'; // modeText와의 간격 조절


				// 토글 스위치 핸들 생성
				const handle3 = document.createElement('span');
				handle3.style.display = 'block';
				handle3.style.width = '10px';
				handle3.style.height = '10px';
				handle3.style.background = 'white';
				handle3.style.borderRadius = '50%';
				handle3.style.position = 'relative';
				handle3.style.top = '0';
				handle3.style.transition = 'left 0.2s';


				// 토글 스위치 위치 세팅
				if(dangaAsc){
					handle3.style.left = '10px';
					label3.style.background = 'blue';

				} else {
					handle3.style.left = '0';
					label3.style.background = 'grey';
				}

				// 토글 스위치 상태 변경 시 핸들 위치 변경
				toggleSwitch3.addEventListener('change', function() {
					toggleSwitch3.checked = dangaAsc;
					console.log('dangaAsc',dangaAsc);
					if (toggleSwitch3.checked) {
						console.log('checked', toggleSwitch3.checked)
						handle3.style.left = '0';
						label3.style.background = 'grey';
						dangaAsc = false;

					} else {
						console.log('checked', toggleSwitch3.checked)
						handle3.style.left = '10px';
						label3.style.background = 'blue';
						dangaAsc = true;
					}

					// config에 저장
					getConfig(config => {
						console.log('Current config:', config);
						config.dangaAsc = dangaAsc;
						saveConfig(config, () => {
						  console.log('dangaAsc config saved:', config);
						});
					});
				});

				// 요소들 DOM에 추가
				newBox.appendChild(modeText3);
				newBox.appendChild(toggleSwitch3);
				label3.appendChild(handle3);
				newBox.appendChild(label3);

				// 오토스크롤모드 on/off 버튼 생성 끝


				// 연속모드 on/off 버튼 생성
				// 연속모드 텍스트 생성
				const modeText = document.createElement('span');
				modeText.textContent = '|단일';
				// modeText.style.marginLeft = '10px'; // 텍스트앞 여백 조절

				const toggleSwitch = document.createElement('input');
				toggleSwitch.type = 'checkbox';
				toggleSwitch.id = 'toggleSwitch';
				toggleSwitch.style.width = '5px';
				toggleSwitch.style.height = '10px';
				// toggleSwitch.style.position = 'relative';
				toggleSwitch.checked = true;

				// 토글 스위치 레이블 생성
				const label = document.createElement('label');
				label.htmlFor = 'toggleSwitch';
				label.style.display = 'inline-block';
				label.style.width = '20px';
				label.style.height = '10px';
				label.style.background = 'grey';
				label.style.borderRadius = '10px';
				label.style.position = 'relative';
				label.style.cursor = 'pointer';
				label.style.padding = '0'; // 추가된 부분
				label.style.margin = '0'; // 추가된 부분
				label.style.marginRight = '5px'; // modeText와의 간격 조절


				// 토글 스위치 핸들 생성
				const handle = document.createElement('span');
				handle.style.display = 'block';
				handle.style.width = '10px';
				handle.style.height = '10px';
				handle.style.background = 'white';
				handle.style.borderRadius = '50%';
				handle.style.position = 'relative';
				handle.style.top = '0';
				handle.style.left = '10px';
				handle.style.transition = 'left 0.2s';


				// 토글 스위치 상태 변경 시 핸들 위치 변경
				toggleSwitch.addEventListener('change', function() {
					if (toggleSwitch.checked) {
						handle.style.left = '10px';
						label.style.background = 'grey';
						modeText.textContent = '|단일';
						contiStatus = false;

					} else {
						handle.style.left = '0';
						label.style.background = 'blue';
						modeText.textContent = '|누적';
						contiStatus = true;
					}
				});

				// 요소들 DOM에 추가
				newBox.appendChild(modeText);
				newBox.appendChild(toggleSwitch);
				label.appendChild(handle);
				newBox.appendChild(label);

				// 연속모드 on/off 버튼 생성 끝



				// 정렬 버튼 넣을 부분

				const modeText2 = document.createElement('span');
				modeText2.textContent = '|';

				const toggleSwitch2 = document.createElement('input');
				toggleSwitch2.type = 'checkbox';
				toggleSwitch2.id = 'toggleSwitch2';
				toggleSwitch2.style.width = '5px';
				toggleSwitch2.style.height = '10px';
				toggleSwitch2.checked = false;

				// 토글 스위치 레이블 생성
				const label2 = document.createElement('label');
				label2.htmlFor = 'toggleSwitch2';
				label2.style.display = 'inline-block';
				label2.style.width = '20px';
				label2.style.height = '10px';
				label2.style.background = 'blue';
				label2.style.borderRadius = '10px';
				label2.style.position = 'relative';
				label2.style.cursor = 'pointer';
				label2.style.padding = '0'; // 추가된 부분
				label2.style.margin = '0'; // 추가된 부분
				label2.style.marginRight = '5px'; // modeText와의 간격 조절


				// 토글 스위치 핸들 생성
				const handle2 = document.createElement('span');
				handle2.style.display = 'block';
				handle2.style.width = '10px';
				handle2.style.height = '10px';
				handle2.style.background = 'white';
				handle2.style.borderRadius = '50%';
				handle2.style.position = 'relative';
				handle2.style.top = '0';
				handle2.style.left = '10px';
				handle2.style.transition = 'left 0.2s';

				// 온오프를 글자로 표기
				const statusText2 = document.createElement('span');
				statusText2.textContent = '층순';


				// 토글 스위치 상태 변경 시 핸들 위치 변경
				toggleSwitch2.addEventListener('change', function() {
					if (toggleSwitch2.checked) {
						handle2.style.left = '10px';
						label2.style.background = 'grey';
						statusText2.textContent = '향순';
						floorsorting = false;

					} else {
						handle2.style.left = '0';
						label2.style.background = 'blue';
						statusText2.textContent = '층순';
						floorsorting = true;
					}
				});

				// 요소들 DOM에 추가
				newBox.appendChild(modeText2);
				newBox.appendChild(statusText2);
				newBox.appendChild(toggleSwitch2);
				label2.appendChild(handle2);
				newBox.appendChild(label2);

				// 정렬 버튼 넣기 마지막


				// 수익률 세팅부분
				const profitText = document.createElement('span');
				profitText.textContent = '|수익(%)';
				profitText.style.marginLeft = '0px'; // 텍스트앞 여백 조절

				const ptextBox = document.createElement('input'); // textarea 대신 input 요소 사용
				ptextBox.type = 'number';
				ptextBox.value = percentMargin.toFixed(1);
				ptextBox.style.width = '40px';
				ptextBox.style.height = '20px';
				ptextBox.style.resize = 'none'
				ptextBox.style.fontSize = '10pt'; // 글자 크기 설정
				ptextBox.style.border = '1px solid #333333'; // 테두리 설정
				ptextBox.step = '0.1'; // 소숫점 한자리까지 입력받기

				// input 값이 변경될 때 percentMargin 변수에 값을 다시 넣기
				ptextBox.addEventListener('input', function() {
					percentMargin = ptextBox.value;
					console.log('Updated percentMargin:', percentMargin); // 값이 업데이트된 것을 확인하기 위해 콘솔에 출력
				});

				newBox.appendChild(profitText);
				newBox.appendChild(ptextBox);
				// 수익률 세팅 끝


				// 표보이기/감추기 버튼 생성
				showButton = document.createElement('button');
				showButton.style.border = '1px solid #555555'; // 테두리 색 설정
				showButton.style.marginLeft = '10px';
				showButton.style.marginRight = '5px';

				if (tableshowstatus == false) {
					showButton.textContent = '요약표';
				} else {
					showButton.textContent = '표닫기';
				}

				showButton.addEventListener('click', () => { // showButton 동작부분
					if (tableshowstatus == true) {
						//
						newBox2.parentNode.removeChild(newBox2);
						tableshowstatus = false;
						console.log(tableshowstatus, '여닫기 버튼 작동 - removed');

					} else {
						// 테이블 복제처리
						tableData1 = tableData1_copy;
						tableData2 = tableData2_copy;

						console.log('여닫기 버튼 작동 - 표열기');
						console.log('tabledata1:', tableData1);
						console.log('tabledata2:', tableData2);
						console.log('tableData1_copy:', tableData1_copy);
						console.log('tableData2_copy:', tableData2_copy);

						newBox2 = document.createElement('div'); // 새로운 박스 요소 생성
						newBox2.classList.add('.new-box2'); // 필요한 클래스 추가 (예: .new-box)

						// 크기 설정 (200px x 200px)
						newBox2.style.width = '360px';
						newBox2.style.height = '550px';
						newBox2.style.padding = '10px';

						// 배경색 설정
						newBox2.style.backgroundColor = '#ffffff';

						// 박스를 창 위로 올리기 (z-index 설정)
						newBox2.style.zIndex = '9999';

						// 위치 설정 (오른쪽 위)
						newBox2.style.position = 'absolute';
						newBox2.style.top = '0px';
						newBox2.style.left = '410px';

						// 스크롤바사 생기도록 변경
						newBox2.style.overflowY = 'auto';

						// 층선택시작 =================
						console.log('=====층선택처리111 =====');
						selectedAndDisplay();

						// 평형보기 버튼 생성 시장
						pyeongButton = document.createElement('button');
						pyeongButton.style.border = '1px solid #555555'; // 테두리 색 설정
						pyeongButton.style.marginLeft = '10px';
						pyeongButton.style.marginRight = '5px';
						pyeongButton.style.right = '10px';
						// pyeongButton.style.backgroundColor = 'green'; // 배경색 설정
						pyeongButton.style.borderRadius = '5px'; // 라운드 처리
						pyeongButton.style.padding = '2px 5px'; // 패딩 설정
						pyeongButton.textContent = '평형분석';

						pyeongButton.addEventListener('click', () => {
							openPyeongAnalysisPopup();
							console.log("===== pyeongButton create.")
						});
						// 평형보기 버튼 생성 마지막

						// 표닫기 버튼 생성 시장
						closeButton = document.createElement('button');
						closeButton.style.border = '1px solid #555555'; // 테두리 색 설정
						closeButton.style.marginLeft = '5px';
						closeButton.style.marginRight = '0px';
						closeButton.style.position = 'absolute'
						closeButton.style.right = '10px';
						closeButton.textContent = '닫기';

						closeButton.addEventListener('click', () => {
							if (tableshowstatus == true) {
								newBox2.parentNode.removeChild(newBox2);
								tableshowstatus = false;
								console.log(tableshowstatus, 'removed');
							}
						});
						// 표닫기 버튼 생성 마지막

						// 버튼만들기
						copyButton = document.createElement('button');
						copyButton.textContent = '내용복사';
						copyButton.style.border = '1px solid #555555'; // 테두리 색 설정

						copyButton.addEventListener('click', () => {
							const textContent = newBox2.innerText;
							navigator.clipboard.writeText(textContent).then(() => {
								console.log('텍스트가 클립보드에 복사되었습니다.');
							}).catch(err => {
							console.error('클립보드에 복사하는 중 오류가 발생했습니다:', err);
							});
						});

						// 버튼 추가
						newBox2.appendChild(copyButton);
						newBox2.appendChild(pyeongButton);
						newBox2.appendChild(closeButton);

						// 테이블 생성
						// 요약테이블 생성
						// stable.appendChild(sthead);
						// stable.appendChild(stbody);
						// newBox2.appendChild(stable); // 테이블을 newBox2에 추가

						// 요약테이블 생성
						summaryAndDisplayTable();

						// 테이블 생성
						// table.appendChild(thead);
						// table.appendChild(tbody);
						// newBox2.appendChild(table); // 테이블을 newBox2에 추가

						/// 리스트 테이블 목록구조 정의 =========
						listAndDisplayTable();

						// 박스2 생성
						mapWrap.appendChild(newBox2);

						tableshowstatus = true;
					}

				});

				// 새로운 박스 안에 버튼 추가
				newBox.appendChild(showButton);
				// 표보이기/감추기 마지막


				// 초기화 버튼 생성
				resetButton = document.createElement('button');
				resetButton.textContent = '초기화';
				resetButton.style.border = '1px solid #555555'; // 테두리 색 설정
				resetButton.style.marginLeft = '5px';

				//reset button 기능
				resetButton.addEventListener('click', () => {
					// propertydata 배열 비우기
					propertyData = [];
					propertyData2 = [];
					tableData1 = [];
					tableData2 = [];
					tableData3 = [];
					datalength1 = 0;
					datalength2 = 0;
					textBox.placeholder = '초기화 완료, 데이터 대기중';
					//
					// 테이블 복제처리 초기화
					tableData1_copy = [];
					tableData2_copy = [];
					//
					if (tableshowstatus == true) {
						const tbodies = newBox2.querySelectorAll('table tbody');
						tbodies.forEach(tbody => {
							while (tbody.firstChild) {
								tbody.removeChild(tbody.firstChild);
							}
						});
						console.log('remove table');
					}
					//표가 있는 경우 없어지게 처리
					// if (tableshowstatus == true) {
					// showButton.click()
					// }
				});

				// newbox 요소에 추가하기
				newBox.appendChild(resetButton);

				// 초기화 버튼 생성 마지막

				// 텍스트 박스 생성
				const textBox = document.createElement('textarea');
				textBox.style.width = '380px';
				textBox.style.height = '40px';
				textBox.style.resize = 'none'
				textBox.placeholder = '데이터 준비중'
				textBox.style.fontSize = '10pt'; // 글자 크기 설정
				textBox.style.fontWeight = 'bold'; // 굵은 글씨체 설정
				textBox.style.marginLeft = '15px';
				textBox.style.marginTop = '5px';


				newBox.appendChild(textBox);
				// 텍스트 박스 생성 마지막

				// .map_wrap 내부에 새로운 박스 추가
				mapWrap.appendChild(newBox);
			}

			// 새창에 최소최대값 넣기 + 표 업데이트 하기
			if (propertyData.length > datalength1 || propertyData2.length > datalength2) {
				const tableDanga1 = tableData1.map(item => item.평당가);
				const maxValue = Math.max(...tableDanga1);
				const minValue = Math.min(...tableDanga1);
				const avgValue = tableDanga1.reduce((sum, value) => sum + value, 0) / tableDanga1.length; //평균 구하기

				// 매매: 건수, 최소, 평균, 최대
				const tableDanga2 = tableData2.map(item => item.평당가);
				const maxValue2 = Math.max(...tableDanga2);
				const minValue2 = Math.min(...tableDanga2);
				const avgValue2 = tableDanga2.reduce((sum, value) => sum + value, 0) / tableDanga2.length; //평균 구하기
				const textBox = document.querySelector('textarea'); // .map_wrap 클래스를 가진 요소 선택
				textBox.placeholder = `[월세 ${tableDanga1.length}건] 최소 : ${minValue}, 평균: ${avgValue.toFixed(2)}, 최대 : ${maxValue}\n[매매 ${tableDanga2.length}건] 최소 : ${minValue2}, 평균: ${avgValue2.toFixed(0)}, 최대 : ${maxValue2}\n`;

				datalength1 = propertyData.length;
				datalength2 = propertyData2.length;


				if (tableshowstatus == true) {
					// let newBox2 = mapWrap.querySelectorAll('.new-box2'); // 기존 박스 요소 가져오기
					// console.log('뉴박스2 확인', newBox2); // 현재는 nodelst []로 표기됨

					if (newBox2){
						newBox2.parentNode.removeChild(newBox2);
					}
					newBox2 = document.createElement('div'); // 새로운 박스 요소 생성
					newBox2.classList.add('.new-box2'); // 필요한 클래스 추가 (예: .new-box)

					// 크기 설정 (200px x 200px)
					newBox2.style.width = '360px';
					newBox2.style.height = '550px';
					newBox2.style.padding = '10px';


					// 배경색 설정
					newBox2.style.backgroundColor = '#ffffff';

					// 박스를 창 위로 올리기 (z-index 설정)
					newBox2.style.zIndex = '9999';

					// 위치 설정 (오른쪽 위)
					newBox2.style.position = 'absolute';
					newBox2.style.top = '5px';
					newBox2.style.left = '410px';

					// 스크롤바가 생기도록 변경
					newBox2.style.overflowY = 'auto';

					// 평형보기 버튼 생성 시장
					pyeongButton = document.createElement('button');
					pyeongButton.style.border = '1px solid #555555'; // 테두리 색 설정
					pyeongButton.style.marginLeft = '10px';
					pyeongButton.style.marginRight = '5px';
					pyeongButton.style.right = '10px';
					// pyeongButton.style.backgroundColor = 'green'; // 배경색 설정
					pyeongButton.style.borderRadius = '5px'; // 라운드 처리
					pyeongButton.style.padding = '2px 5px'; // 패딩 설정
					pyeongButton.textContent = '평형분석';

					pyeongButton.addEventListener('click', () => {
						openPyeongAnalysisPopup();
						console.log("===== pyeongButton create.")
					});

					// 표 여닫기 버튼 생성 시장
					closeButton = document.createElement('button');
					closeButton.style.border = '1px solid #555555'; // 테두리 색 설정
					closeButton.style.marginLeft = '5px';
					closeButton.style.marginRight = '0px';
					closeButton.style.position = 'absolute'
					closeButton.style.right = '10px';
					closeButton.textContent = '닫기';

					closeButton.addEventListener('click', () => {
						if (tableshowstatus == true) {
							newBox2.parentNode.removeChild(newBox2);
							tableshowstatus = false;
							console.log(tableshowstatus, 'removed');
						}
					});
					// 표닫기 버튼 생성 마지막

					console.log('=====층선택처리2222 =====');
					selectedAndDisplay();


					// 버튼만들기
					copyButton = document.createElement('button');
					copyButton.textContent = '내용복사';
					copyButton.style.border = '1px solid #555555'; // 테두리 색 설정

					copyButton.addEventListener('click', () => {
						const textContent = newBox2.innerText;
						navigator.clipboard.writeText(textContent).then(() => {
							console.log('텍스트가 클립보드에 복사되었습니다.');
						}).catch(err => {
						console.error('클립보드에 복사하는 중 오류가 발생했습니다:', err);
						});
					});

					// 버튼 추가
					newBox2.appendChild(copyButton);
					newBox2.appendChild(pyeongButton);
					newBox2.appendChild(closeButton);

					// // 요약테이블 생성
					// stable.appendChild(sthead);
					// stable.appendChild(stbody);
					// newBox2.appendChild(stable); // 테이블을 newBox2에 추가
					//
					// // 테이블 생성
					// table.appendChild(thead);
					// table.appendChild(tbody);
					// newBox2.appendChild(table); // 테이블을 newBox2에 추가

					// 요약테이블 생성
					summaryAndDisplayTable();

					// 리스트 테이블 목록구조 정의
					listAndDisplayTable();

					// 박스2 생성
					mapWrap.appendChild(newBox2);
					// 연속모드 확인해서 off 된 경우 기존 테이블 데이터를 초기화
					// if (contiStatus == false) {
						// propertyData = [];
						// propertyData2 = [];
						// tableData1 = []; // 월세 테이블 만들 데이터 { key: data, key2: data2} 형식으로 저장
						// tableData2 = []; // 매매테이블 만들 데이터 - 필요하면 작성
						// datalength1 = 0;
						// datalength2 = 0;
					// }
				}
			}

		} else {
			console.error('.map_wrap element not found.'); // .map_wrap 요소가 없는 경우 오류 메시지 출력
		}

		// div 요소들끼리 정리하는 부분
		if (dangaAsc == true){
			const propertyLists = document.querySelectorAll('div.item.false'); // 'is-loading' 클래스를 제외한 요소 선택
			const divs = Array.from(propertyLists); // 어레이에 맞게 정렬


			if(divs.length >0) { // 요소가 존재하는지 확인
				if (autoScroll) {
					//div 요소들을 내부 텍스트 기준으로 내림차순 정렬
					divs.sort((a, b) => {
						const textA = a.textContent.trim();
						const matchA = textA.match(/@([\d.]+)만/); // 소수점 포함 숫자 추출
						const textA2 = matchA ? matchA[1] : '';

						const textB = b.textContent.trim();
						const matchB = textB.match(/@([\d.]+)만/); // 소수점 포함 숫자 추출
						const textB2 = matchB ? matchB[1] : '';

						return textB2.localeCompare(textA2, undefined, { numeric: true });
					});

				} else{
					//div 요소들을 내부 텍스트 기준으로 오름차순 정렬
					divs.sort((a, b) => {
						const textA = a.textContent.trim();
						const matchA = textA.match(/@([\d.]+)만/); // 소수점 포함 숫자 추출
						const textA2 = matchA ? matchA[1] : '';

						const textB = b.textContent.trim();
						const matchB = textB.match(/@([\d.]+)만/); // 소수점 포함 숫자 추출
						const textB2 = matchB ? matchB[1] : '';

						return textA2.localeCompare(textB2, undefined, { numeric: true });
					});
				}

				const container = propertyLists[0].parentElement;
				container.innerHTML = ''; // 부모 요소 비우기

				divs.forEach(div => {
					container.appendChild(div);
				});
			} else {
				console.log('no elements sorted');
			}
		}

		// 세부조회항목에서 월세단가 표기하기 - 보류 / 귀찮음
		// const detailBox = document.querySelector('.detail_box--summary'); //  table.info_table_wrap
		// if (detailBox) {
			// const detailTable = detailBox.querySelector('.info_table_wrap');
			// console.log('detailTable', detailTable);
		// }

		// 세부조회항목에서 월세단가 표기하기 끝
	}
}

// 변경되면 감시하는 부분
function observeMutations() {
    const targetNode = document.querySelector('.item_list.item_list--article');
    const config = { childList: true, subtree: true }; // 감시할 변경 유형 설정

    const callback = function(mutationsList, observer) {
        if (!isScheduled) {
            isScheduled = true;
			observer.disconnect(); // 감시 중단
			extractPropertyInfo(); // 0.2초 후에 함수 실행
			observer.observe(targetNode, config); // 감시 재개
			isScheduled = false; // 플래그 초기화
        }
    };

    const observer = new MutationObserver(callback);
    observer.observe(targetNode, config);
}


function extractInfoM() {
	const propertyItems = document.querySelectorAll('.item_inner'); // 항목 선택
	const mapWrap = document.querySelector('#_root');

	if (propertyItems != oldItems && propertyItems.length > 0) {
		// 업데이트이므로 데이터 한번 초기화하기
		propertyData2 = [];
		tableData1 = []; // 월세 테이블 만들 데이터 { key: data, key2: data2} 형식으로 저장
		tableData2 = []; // 매매테이블 만들 데이터 - 필요하면 작성
		datalength1 = 0;
		datalength2 = 0;
		// 테이블 복제처리
		tableData1_copy = [];
		tableData2_copy = [];

		// 각 항목별 작업하기 + 데이터 추출
		propertyItems.forEach((item) => {
			// 매매, 월세 유형으로 추출하기
			// item.style.padding = '5px'; // 간격 줄여주기
			const typeElement = item.querySelector('.type'); // 매매, 월세, 유형정보
			const type = typeElement.textContent.trim(); //텍스트로만 추출하기
			console.log('type', type);

			// 금액정보 찾아내기
			const priceElement = item.querySelector('.price'); // 금액정보
			const price = priceElement.textContent.trim().replace(/,/g, ''); // 매매는 '0억 000', 월세는 '2000/150'으로 표현됨
			const cleanedPrice2 = price.replace(/\(.*$/, ''); // ( 포함 이후 문자 삭제
			const cleanedPrice = cleanedPrice2.replace(/~.*$/, ''); // ~ 이후 문자 삭제
			const parts = cleanedPrice.split('/'); //문자열을 /로 분리
			console.log(parts);

			//총 금액을 산출 - 억과 천단위를 찾아내기 위한 정규식
			const regex = /(\d+)억\s*(\d+)?/;
			let totalPrice = 0;
			parts.forEach(part => {
				const match = part.match(regex);
				if (match) {
					const billionPart = parseInt(match[1], 10) * 10000; // '억'을 10000으로 변환
					const thousandPart = match[2] ? parseInt(match[2].replace(/,/g, ''), 10) : 0; // '천' 단위를 숫자로 변환
					totalPrice = billionPart + thousandPart;
				} else {
					totalPrice = parseInt(part.replace(/[^0-9]/g, ''), 10);
				}
			});


			//전용면적 찾아내기
			const areaElement = item.querySelector('.spec'); // 상가,면적, 층수, 향, 기타설명
			const infodata = areaElement.textContent.trim();
			const info = infodata.split(',').map(part => part.trim());
			// 첫 번째 항목에서 /와 m² 사이의 숫자 추출
			const firstPart = info[0];
			const areaMatch = firstPart ? firstPart.match(/(\d+(\.\d+)?)㎡/) : null
			// const areaMatch = firstPart ? firstPart.match(/(\d+\.\d+)㎡/) : null;

			const areas2 = areaMatch ? parseInt(areaMatch[1], 10) : null; // 전용면적, 잘 찾아짐
			let areas = areas2 * 0.3025 ;
			const areas3 = areas.toFixed(2);
			// 전용면적 잘 찾아짐 but 토지는 안찾아짐 console.log(areas);

			// 층수 찾아내기
			const secondPart = info[1];
			const floorMatch = secondPart ? secondPart.match(/(\d+)\/(\d+)층/) : null;
			const cfloor = floorMatch ? floorMatch [1] : null; // 매물층
			const tfloor = floorMatch ? floorMatch [2] : null; // 전체층

			// 향 찾아내기
			const direction = info[2] !== undefined ? info[2] : '';

			if (areas > 0) {
				if (type == '월세') {
					const mprice = parts.length > 1 ? parseInt(parts[1].replace(/[^0-9]/g, ''), 10) : 0; // /뒤의 문자열 추출 mprice : 월세가격
					let pdanga = mprice / areas;
					pdanga = parseFloat(pdanga.toFixed(2)); // 소수점 2자리까지만 구하고 숫자로 변환

					let tprice = mprice * 12 * 100 / percentMargin / 10000;
					tprice = parseFloat(tprice.toFixed(1));

					areas = areas.toFixed(1);

					// 월세 정보를 붉은색으로 표시
					if (!priceElement.dataset.highlighted) {

						const priceSpan = document.createElement('span');
						priceSpan.textContent = `(${areas}평 @${pdanga}`;
						priceSpan.style.opacity = 0.5; // 50% opacity
						priceSpan.style.color = 'red';
						priceSpan.style.fontSize = '11pt';

						const priceSpan2 = document.createElement('span');
						priceSpan2.textContent = `  >>${tprice}억)`;
						priceSpan2.style.opacity = 0.5; // 50% opacity
						priceSpan2.style.color = 'violet';
						priceSpan2.style.fontSize = '13pt';

						priceElement.appendChild(priceSpan);
						priceElement.appendChild(priceSpan2);


						// push함수를 사용하여 평단가를 목록으로 만들기
						propertyData.push(pdanga);
						let tabletext = `${info[1]}, ${direction}, ${pdanga}만/평, ${areas3}평, ${price}`;
						// console.log(tabletext);
						priceElement.dataset.highlighted = true; // 한 번만 실행되도록 표시

					}

					// 테이블에 넣기
					const tableitem = { 구분: type, 해당층: cfloor, 전체층: tfloor, 향: direction, 평당가: pdanga, 전용면적: areas3, 가격: cleanedPrice };

					//데이터를 배열화
					tableData1.push(tableitem);

					// 테이블 복제처리
					//tableData1_copy = tableData1;
				}

				if (type == '매매') {
					let pdanga = parseInt(totalPrice / areas);
					areas = areas.toFixed(1);

					// 매매 정보를 붉은색으로 표시
					if (!priceElement.dataset.highlighted) {
						const priceSpan = document.createElement('span');
						priceSpan.textContent = `(${areas}평 @${pdanga})`;
						priceSpan.style.opacity = 0.5; // 50% opacity
						priceSpan.style.color = 'green';
						priceSpan.style.fontSize = '11pt';
						priceElement.appendChild(priceSpan);
						propertyData2.push(pdanga);
						priceElement.dataset.highlighted = true; // 한 번만 실행되도록 표시

					}

					const tableitem = { 구분: type, 해당층: cfloor, 전체층: tfloor, 향: direction, 평당가: pdanga, 전용면적: areas3, 가격: cleanedPrice};
					//데이터를 배열화
					tableData2.push(tableitem);

					// 테이블 복제처리
					//tableData2_copy = tableData2;
				}
			}

			// 공 삭제
			// const tagItem = item.querySelector('.tag_area');
			// if (tagItem) {
				// tagItem.remove();
			// }

			// 공인중개사 삭제
			const cpItem = item.querySelector('.cp_area');
			if (cpItem) {
				cpItem.remove();
			}

			// 매물날짜 삭제
			const labelItem = item.querySelector('.merit_area');
			if (labelItem) {
				labelItem.remove();
			}
		}); //propertyItems의 마지막

		// 업데이트된 내용을 반영
		oldItems = document.querySelectorAll('.item_inner');
		console.log(oldItems);

		// 기존 표 업데이트 부분 // 정상작동
		if (tableshowstatus == true) {
			newBox2.parentNode.removeChild(newBox2);

			console.log('tabledata:', tableData1);
			newBox2 = document.createElement('div'); // 새로운 박스 요소 생성
			newBox2.classList.add('new-box2'); // 필요한 클래스 추가 (예: .new-box)

			// 크기 설정
			newBox2.style.width = '360px';
			newBox2.style.height = '550px';
			newBox2.style.padding = '10px';
			newBox2.style.position = 'absolute';
			newBox2.style.left = '0px';
			newBox2.style.top = '150px';

			// 배경색 설정
			newBox2.style.backgroundColor = '#ffffff';

			// 박스를 창 위로 올리기 (z-index 설정)
			newBox2.style.zIndex = '9999';

			// 스크롤바사 생기도록 변경
			newBox2.style.overflowY = 'auto';

			// // 요약테이블 데이터 정리
			// const tableData3 = [];
			//
			// // 값산출 1층
			// const filteredData = tableData1.filter(item => item.해당층 === '1');
			// let pValues = filteredData.map(item => item.평당가);
			// console.log('필터된 데이터', filteredData);
			//
			// if (pValues.length != 0) {  // 1층 데이터가 0인 경우 열 안나타나도록
			// 	let minPdanga = Math.min(...pValues);
			// 	let maxPdanga = Math.max(...pValues);
			// 	let avgPdanga = pValues.reduce((sum, value) => sum + value, 0) / pValues.length;
			//
			// 	// NaN 또는 Infinity인 경우 0으로 설정
			// 	minPdanga = isFinite(minPdanga) ? minPdanga : 0;
			// 	maxPdanga = isFinite(maxPdanga) ? maxPdanga : 0;
			// 	avgPdanga = isFinite(avgPdanga) ? avgPdanga : 0;
			//
			// 	tableData3.push(['1층', minPdanga.toFixed(1), avgPdanga.toFixed(1), maxPdanga.toFixed(1), pValues.length]);
			// }
			//
			// // 값산출 2층
			// const filteredData2 = tableData1.filter(item => item.해당층 === '2');
			// let pValues2 = filteredData2.map(item => item.평당가);
			//
			// // 값산출 상
			// const filteredData3 = tableData1.filter(item => item.해당층 >= 3);
			// console.log('필터된 데이터 / 상층', filteredData3);
			// const pValues3 = filteredData3.map(item => item.평당가);
			//
			// if (pValues2.length == 0) {
			// 	if (pValues.length !=0 && pValues3.length != 0){
			// 		tableData3.push(['2층', 0,0,0,0]);
			// 	}
			// } else {
			// 	let minPdanga2 = Math.min(...pValues2);
			// 	let maxPdanga2 = Math.max(...pValues2);
			// 	let avgPdanga2 = pValues2.reduce((sum, value) => sum + value, 0) / pValues2.length;
			//
			// 	// NaN 또는 Infinity인 경우 0으로 설정
			// 	minPdanga2 = isFinite(minPdanga2) ? minPdanga2 : 0;
			// 	maxPdanga2 = isFinite(maxPdanga2) ? maxPdanga2 : 0;
			// 	avgPdanga2 = isFinite(avgPdanga2) ? avgPdanga2 : 0;
			//
			// 	tableData3.push(['2층', minPdanga2.toFixed(1), avgPdanga2.toFixed(1), maxPdanga2.toFixed(1), pValues2.length]);
			// }
			//
			//
			// if (pValues3.length != 0) {
			// 	let minPdanga3 = Math.min(...pValues3);
			// 	let maxPdanga3 = Math.max(...pValues3);
			// 	let avgPdanga3 = pValues3.reduce((sum, value) => sum + value, 0) / pValues3.length;
			//
			// 	// NaN 또는 Infinity인 경우 0으로 설정
			// 	minPdanga3 = isFinite(minPdanga3) ? minPdanga3 : 0;
			// 	maxPdanga3 = isFinite(maxPdanga3) ? maxPdanga3 : 0;
			// 	avgPdanga3 = isFinite(avgPdanga3) ? avgPdanga3 : 0;
			//
			// 	tableData3.push(['상층', minPdanga3.toFixed(1), avgPdanga3.toFixed(1), maxPdanga3.toFixed(1), pValues3.length]);
			// }
			//
			// // 요약테이블 생성
			// const stable = document.createElement('table');
			// const sthead = document.createElement('thead');
			// const stbody = document.createElement('tbody');
			//
			// //테이블 스타일 정해주기
			// stable.style.fontSize = '12pt';
			// stable.style.borderCollapse = 'collapse'; // 테이블 셀 간의 간격 제거
			// stable.style.width = '60%'; // 테이블 폭 설정
			// stable.style.marginTop = '10px';
			// stable.style.marginBottom = '15px';
			// stable.style.marginLeft = 'auto'; // 왼쪽 여백 자동 설정
			// stable.style.marginRight = 'auto'; // 오른쪽 여백 자동 설정
			//
			// // 테이블 헤더 생성
			// const sheaderRow = document.createElement('tr');
			// const sheaders = ['구분', '최소', '평균', '최대', '건수'];
			// sheaders.forEach(headerText => {
			// 	const th = document.createElement('th');
			// 	th.textContent = headerText;
			// 	sheaderRow.appendChild(th);
			//
			// 	th.style.backgroundColor = '#ddddff'; // 첫 번째 줄 배경색 설정
			// 	th.style.border = '0.5px solid #333333'; // 테두리 설정
			// });
			// sthead.appendChild(sheaderRow);
			//
			// tableData3.forEach(item => {
			// 	const row = document.createElement('tr');
			// 	Object.values(item).forEach(value => {
			// 		const td = document.createElement('td');
			// 		td.textContent = value;
			// 		td.style.border = '0.5px solid #333333'; // 테두리 설정
			// 		td.style.textAlign = 'center'; // 텍스트 가운데 정렬
			// 		row.appendChild(td);
			// 	});
			// 	stbody.appendChild(row);
			// });
			// 요약테이블 생성 마지막

			console.log('=====층선택처리3333 =====');
			selectedAndDisplay();

				// const table = document.createElement('table');
				// const thead = document.createElement('thead');
				// const tbody = document.createElement('tbody');
				//
				// //테이블 스타일 정해주기
				// table.style.fontSize = '11pt';
				// table.style.borderCollapse = 'collapse'; // 테이블 셀 간의 간격 제거
				// table.style.width = '360px'; // 테이블 폭 설정
				// table.style.marginleft = '0px'
				// table.style.marginTop = '0px';
				//
				//
				// if (floorsorting == true) {
				// 	// 월세 자료를 층 오름차순으로 정리
				// 	tableData1.sort((a, b) => Object.values(a)[1] - Object.values(b)[1]); // 간결하게 바꿈
				//
				// 	// 층이 같은 경우 단가 내림차순으로 정리
				// 	tableData1.sort((a, b) => {
				// 		const secondKeyA = Object.values(a)[1];
				// 		const secondKeyB = Object.values(b)[1];
				// 		const fourthKeyA = Object.values(a)[4];
				// 		const fourthKeyB = Object.values(b)[4];
				//
				// 		if (secondKeyA == secondKeyB) {
				// 			if (fourthKeyA > fourthKeyB) return -1;
				// 			if (fourthKeyA < fourthKeyB) return 1;
				// 			return 0;
				// 		}
				// 	});
				//
				// 	// 매매자료를 단가 낮은것부터 오름차순으로 정리
				// 	tableData2.sort((a, b) => {
				// 		const secondKeyA = Object.values(a)[4];
				// 		const secondKeyB = Object.values(b)[4];
				// 		if (secondKeyA < secondKeyB) return -1;
				// 		if (secondKeyA > secondKeyB) return 1;
				// 		return 0;
				// 	});
				//
				// } else {
				// 	// 월세 자료를 층 오름차순으로 정리
				// 	console.log('오름차순 정리전 data', tableData1)
				// 	tableData1.sort((a, b) => {
				// 		const secondKeyA = Object.values(a)[3];
				// 		const secondKeyB = Object.values(b)[3];
				// 		if (secondKeyA < secondKeyB) return -1;
				// 		if (secondKeyA > secondKeyB) return 1;
				// 		return 0;
				// 	});
				// 	console.log('오름차순 정리후 data', tableData1)
				//
				//
				// 	// 매매자료를 단가 낮은것부터 오름차순으로 정리
				// 	tableData2.sort((a, b) => {
				// 		const secondKeyA = Object.values(a)[3];
				// 		const secondKeyB = Object.values(b)[3];
				// 		if (secondKeyA < secondKeyB) return -1;
				// 		if (secondKeyA > secondKeyB) return 1;
				// 		return 0;
				// 	});
				// }
				//
				//
				// // 테이블 헤더 생성
				// const headerRow = document.createElement('tr');
				// const headers = ['구분', '층', '향', '평당가', '면적', '가격'];
				// headers.forEach(headerText => {
				// 	const th = document.createElement('th');
				// 	th.textContent = headerText;
				// 	headerRow.appendChild(th);
				// 	th.style.backgroundColor = '#ddddff'; // 첫 번째 줄 배경색 설정
				// 	th.style.border = '0.5px solid #333333'; // 테두리 설정
				// });
				// thead.appendChild(headerRow);
				//
				//
				// tableData1.forEach(item => {
				// 	const row = document.createElement('tr');
				// 	Object.values(item).forEach((value, index) => {
				// 		const td = document.createElement('td');
				// 		if (index == 1) { // 2열 (index는 0부터 시작)
				// 			td.textContent = value + ' / ' + Object.values(item)[2]; // 2열 값과 3열 값 결합
				// 			td.style.border = '0.5px solid #333333'; // 테두리 설정
				// 			td.style.textAlign = 'center'; // 텍스트 가운데 정렬
				// 			row.appendChild(td);
				// 		} else if (index !== 2) { // 3열은 이미 2열에 추가되었으므로 건너뜀
				// 			td.textContent = value;
				// 			td.style.border = '0.5px solid #333333'; // 테두리 설정
				// 			td.style.textAlign = 'center'; // 텍스트 가운데 정렬
				// 			row.appendChild(td);
				// 		}
				// 	});
				// 	tbody.appendChild(row);
				// });
				//
				// tableData2.forEach(item => {
				// 	const row = document.createElement('tr');
				// 	Object.values(item).forEach((value, index) => {
				// 		const td = document.createElement('td');
				// 		if (index == 1) { // 2열 (index는 0부터 시작)
				// 			td.textContent = value + ' / ' + Object.values(item)[2]; // 2열 값과 3열 값 결합
				// 			td.style.border = '0.5px solid #333333'; // 테두리 설정
				// 			td.style.textAlign = 'center'; // 텍스트 가운데 정렬
				// 			row.appendChild(td);
				// 		} else if (index !== 2) { // 3열은 이미 2열에 추가되었으므로 건너뜀
				// 			td.textContent = value;
				// 			td.style.border = '0.5px solid #333333'; // 테두리 설정
				// 			td.style.textAlign = 'center'; // 텍스트 가운데 정렬
				// 			row.appendChild(td);
				// 		}
				// 	});
				// 	tbody.appendChild(row);
				// });

				// 표닫기 버튼 생성 시장
				closeButton = document.createElement('button');
				closeButton.style.border = '1px solid #555555'; // 테두리 색 설정
				closeButton.style.marginLeft = '0px';
				closeButton.style.marginRight = '15px';
				closeButton.style.position = 'absolute'
				closeButton.style.right = '15px';
				closeButton.textContent = '닫기';

				closeButton.addEventListener('click', () => {
					if (tableshowstatus == true) {
						newBox2.parentNode.removeChild(newBox2);
						tableshowstatus = false;
						console.log(tableshowstatus, 'removed');
					}
				});
				// 표닫기 버튼 생성 마지막


				// 버튼만들기
				copyButton = document.createElement('button');
				copyButton.textContent = '내용복사';
				copyButton.style.border = '1px solid #555555'; // 테두리 색 설정

				copyButton.addEventListener('click', () => {
					const textContent = newBox2.innerText;
					navigator.clipboard.writeText(textContent).then(() => {
						console.log('텍스트가 클립보드에 복사되었습니다.');
					}).catch(err => {
					console.error('클립보드에 복사하는 중 오류가 발생했습니다:', err);
					});
				});

				// 버튼 추가
				newBox2.appendChild(closeButton);
									// 테이블 생성
				// // 요약테이블 생성
				// stable.appendChild(sthead);
				// stable.appendChild(stbody);
				// newBox2.appendChild(stable); // 테이블을 newBox2에 추가
				//
				// // 테이블 생성
				// table.appendChild(thead);
				// table.appendChild(tbody);
				// newBox2.appendChild(table); // 테이블을 newBox2에 추가

				// 요약테이블 생성
				summaryAndDisplayTable();

				// 리스트 테이블 목록구조 정의
				listAndDisplayTable();

				// 박스2 생성
				mapWrap.appendChild(newBox2);
				// 생성되었으므로 true로 표기
		}

	}


	// 요약표 버튼 생성
	const ngnbInner = document.querySelector('.Ngnb_inner'); // ngnbInner 클래스를 가진 요소 선택 // 요약표 버튼 넣을 곳

	// 표보이기/감추기 버튼 생성
	let showButton = ngnbInner.querySelector('button'); // 기존 버튼 요소 가져오기

	// 버튼 없으면 생성
	if (!showButton) {
		showButton = document.createElement('button');
		showButton.style.border = '1px solid #555555'; // 테두리 색 설정
		showButton.style.marginLeft = '10px';
		showButton.style.marginRight = '5px';
		if (tableshowstatus == false) {
			showButton.textContent = '요약표';
		} else {
			showButton.textContent = '표닫기';
		}
		ngnbInner.appendChild(showButton);


		showButton.addEventListener('click', () => { // showButton 동작부분
			if (tableshowstatus == true) {
				//
				newBox2.parentNode.removeChild(newBox2);
				tableshowstatus = false;
				console.log(tableshowstatus, '여닫기 버튼 작동 - 표닫기');

			} else {
				// 테이블 복제처리
				// tableData1_copy = [];
				// tableData2_copy = [];
				// tableData1_copy = tableData1;
				// tableData2_copy = tableData2;

				console.log('tabledata:', tableData1);
				newBox2 = document.createElement('div'); // 새로운 박스 요소 생성
				newBox2.classList.add('.new-box2'); // 필요한 클래스 추가 (예: .new-box)

				// 크기 설정
				newBox2.style.width = '390px';
				newBox2.style.height = '580px';
				newBox2.style.padding = '10px';
				newBox2.style.position = 'absolute';
				newBox2.style.left = '0px';
				newBox2.style.top = '150px';

				// 배경색 설정
				newBox2.style.backgroundColor = '#ffffff';

				// 박스를 창 위로 올리기 (z-index 설정)
				newBox2.style.zIndex = '9999';

				// 스크롤바사 생기도록 변경
				newBox2.style.overflowY = 'auto';

				// 요약테이블 데이터 정리
				const tableData3 = [];

				// 값산출 1층
				const filteredData = tableData1.filter(item => item.해당층 === '1');
				let pValues = filteredData.map(item => item.평당가);
				console.log('필터된 데이터', filteredData);

				if (pValues.length != 0) {  // 1층 데이터가 0인 경우 열 안나타나도록
					let minPdanga = Math.min(...pValues);
					let maxPdanga = Math.max(...pValues);
					let avgPdanga = pValues.reduce((sum, value) => sum + value, 0) / pValues.length;

					// NaN 또는 Infinity인 경우 0으로 설정
					minPdanga = isFinite(minPdanga) ? minPdanga : 0;
					maxPdanga = isFinite(maxPdanga) ? maxPdanga : 0;
					avgPdanga = isFinite(avgPdanga) ? avgPdanga : 0;

					tableData3.push(['1층', minPdanga.toFixed(1), avgPdanga.toFixed(1), maxPdanga.toFixed(1), pValues.length]);
				}

				// 값산출 2층
				const filteredData2 = tableData1.filter(item => item.해당층 === '2');
				let pValues2 = filteredData2.map(item => item.평당가);

				// 값산출 상
				const filteredData3 = tableData1.filter(item => item.해당층 >= 3);
				console.log('필터된 데이터 / 상층', filteredData3);
				const pValues3 = filteredData3.map(item => item.평당가);

				if (pValues2.length == 0) {
					if (pValues.length !=0 && pValues3.length != 0){
						tableData3.push(['2층', 0,0,0,0]);
					}
				} else {
					let minPdanga2 = Math.min(...pValues2);
					let maxPdanga2 = Math.max(...pValues2);
					let avgPdanga2 = pValues2.reduce((sum, value) => sum + value, 0) / pValues2.length;

					// NaN 또는 Infinity인 경우 0으로 설정
					minPdanga2 = isFinite(minPdanga2) ? minPdanga2 : 0;
					maxPdanga2 = isFinite(maxPdanga2) ? maxPdanga2 : 0;
					avgPdanga2 = isFinite(avgPdanga2) ? avgPdanga2 : 0;

					tableData3.push(['2층', minPdanga2.toFixed(1), avgPdanga2.toFixed(1), maxPdanga2.toFixed(1), pValues2.length]);
				}

				if (pValues3.length != 0) {
					let minPdanga3 = Math.min(...pValues3);
					let maxPdanga3 = Math.max(...pValues3);
					let avgPdanga3 = pValues3.reduce((sum, value) => sum + value, 0) / pValues3.length;

					// NaN 또는 Infinity인 경우 0으로 설정
					minPdanga3 = isFinite(minPdanga3) ? minPdanga3 : 0;
					maxPdanga3 = isFinite(maxPdanga3) ? maxPdanga3 : 0;
					avgPdanga3 = isFinite(avgPdanga3) ? avgPdanga3 : 0;

					tableData3.push(['상층', minPdanga3.toFixed(1), avgPdanga3.toFixed(1), maxPdanga3.toFixed(1), pValues3.length]);
				}

				// 요약테이블 생성
				const stable = document.createElement('table');
				const sthead = document.createElement('thead');
				const stbody = document.createElement('tbody');

				//테이블 스타일 정해주기
				stable.style.fontSize = '12pt';
				stable.style.borderCollapse = 'collapse'; // 테이블 셀 간의 간격 제거
				stable.style.width = '60%'; // 테이블 폭 설정
				stable.style.marginTop = '10px';
				stable.style.marginBottom = '15px';
				stable.style.marginLeft = 'auto'; // 왼쪽 여백 자동 설정
				stable.style.marginRight = 'auto'; // 오른쪽 여백 자동 설정

				// 테이블 헤더 생성
				const sheaderRow = document.createElement('tr');
				const sheaders = ['구분', '최소', '평균', '최대', '건수'];
				sheaders.forEach(headerText => {
					const th = document.createElement('th');
					th.textContent = headerText;
					sheaderRow.appendChild(th);

					th.style.backgroundColor = '#ddddff'; // 첫 번째 줄 배경색 설정
					th.style.border = '0.5px solid #333333'; // 테두리 설정
				});

				sthead.appendChild(sheaderRow);

				tableData3.forEach(item => {
					const row = document.createElement('tr');
					Object.values(item).forEach(value => {
						const td = document.createElement('td');
						td.textContent = value;
						td.style.border = '0.5px solid #333333'; // 테두리 설정
						td.style.textAlign = 'center'; // 텍스트 가운데 정렬
						row.appendChild(td);
					});
					stbody.appendChild(row);
				});

				// 요약테이블 생성 마지막

				const table = document.createElement('table');
				const thead = document.createElement('thead');
				const tbody = document.createElement('tbody');

				//테이블 스타일 정해주기
				table.style.fontSize = '11pt';
				table.style.borderCollapse = 'collapse'; // 테이블 셀 간의 간격 제거
				table.style.width = '360px'; // 테이블 폭 설정
				table.style.marginleft = '0px'
				table.style.marginTop = '0px';


				if (floorsorting == true) {
					// 월세 자료를 층 오름차순으로 정리
					tableData1.sort((a, b) => Object.values(a)[1] - Object.values(b)[1]); // 간결하게 바꿈

					// 층이 같은 경우 단가 내림차순으로 정리
					tableData1.sort((a, b) => {
						const secondKeyA = Object.values(a)[1];
						const secondKeyB = Object.values(b)[1];
						const fourthKeyA = Object.values(a)[4];
						const fourthKeyB = Object.values(b)[4];

						if (secondKeyA == secondKeyB) {
							if (fourthKeyA > fourthKeyB) return -1;
							if (fourthKeyA < fourthKeyB) return 1;
							return 0;
						}
					});

					// 매매자료를 단가 낮은것부터 오름차순으로 정리
					tableData2.sort((a, b) => {
						const secondKeyA = Object.values(a)[4];
						const secondKeyB = Object.values(b)[4];
						if (secondKeyA < secondKeyB) return -1;
						if (secondKeyA > secondKeyB) return 1;
						return 0;
					});

				} else {
					// 월세 자료를 층 오름차순으로 정리
					console.log('오름차순 정리전 data', tableData1)
					tableData1.sort((a, b) => {
						const secondKeyA = Object.values(a)[3];
						const secondKeyB = Object.values(b)[3];
						if (secondKeyA < secondKeyB) return -1;
						if (secondKeyA > secondKeyB) return 1;
						return 0;
					});
					console.log('오름차순 정리후 data', tableData1)


					// 매매자료를 단가 낮은것부터 오름차순으로 정리
					tableData2.sort((a, b) => {
						const secondKeyA = Object.values(a)[3];
						const secondKeyB = Object.values(b)[3];
						if (secondKeyA < secondKeyB) return -1;
						if (secondKeyA > secondKeyB) return 1;
						return 0;
					});
				}


				// 테이블 헤더 생성
				const headerRow = document.createElement('tr');
				const headers = ['구분', '층', '향', '평당가', '면적', '가격'];
				headers.forEach(headerText => {
					const th = document.createElement('th');
					th.textContent = headerText;
					headerRow.appendChild(th);
					th.style.backgroundColor = '#ddddff'; // 첫 번째 줄 배경색 설정
					th.style.border = '0.5px solid #333333'; // 테두리 설정
				});
				thead.appendChild(headerRow);


				tableData1.forEach(item => {
					const row = document.createElement('tr');
					Object.values(item).forEach((value, index) => {
						const td = document.createElement('td');
						if (index == 1) { // 2열 (index는 0부터 시작)
							td.textContent = value + ' / ' + Object.values(item)[2]; // 2열 값과 3열 값 결합
							td.style.border = '0.5px solid #333333'; // 테두리 설정
							td.style.textAlign = 'center'; // 텍스트 가운데 정렬
							row.appendChild(td);
						} else if (index !== 2) { // 3열은 이미 2열에 추가되었으므로 건너뜀
							td.textContent = value;
							td.style.border = '0.5px solid #333333'; // 테두리 설정
							td.style.textAlign = 'center'; // 텍스트 가운데 정렬
							row.appendChild(td);
						}
					});
					tbody.appendChild(row);
				});

				tableData2.forEach(item => {
					const row = document.createElement('tr');
					Object.values(item).forEach((value, index) => {
						const td = document.createElement('td');
						if (index == 1) { // 2열 (index는 0부터 시작)
							td.textContent = value + ' / ' + Object.values(item)[2]; // 2열 값과 3열 값 결합
							td.style.border = '0.5px solid #333333'; // 테두리 설정
							td.style.textAlign = 'center'; // 텍스트 가운데 정렬
							row.appendChild(td);
						} else if (index !== 2) { // 3열은 이미 2열에 추가되었으므로 건너뜀
							td.textContent = value;
							td.style.border = '0.5px solid #333333'; // 테두리 설정
							td.style.textAlign = 'center'; // 텍스트 가운데 정렬
							row.appendChild(td);
						}
					});
					tbody.appendChild(row);
				});


				// 표닫기 버튼 생성 시장
				closeButton = document.createElement('button');
				closeButton.style.border = '1px solid #555555'; // 테두리 색 설정
				closeButton.style.marginLeft = '0px';
				closeButton.style.marginRight = '15px';
				closeButton.style.position = 'absolute'
				closeButton.style.right = '15px';
				closeButton.textContent = '닫기';

				closeButton.addEventListener('click', () => {
					if (tableshowstatus == true) {
						newBox2.parentNode.removeChild(newBox2);
						tableshowstatus = false;
						console.log(tableshowstatus, 'removed');
					}
				});
				// 표닫기 버튼 생성 마지막


				// 버튼만들기
				copyButton = document.createElement('button');
				copyButton.textContent = '내용복사';
				copyButton.style.border = '1px solid #555555'; // 테두리 색 설정

				copyButton.addEventListener('click', () => {
					const textContent = newBox2.innerText;
					navigator.clipboard.writeText(textContent).then(() => {
						console.log('텍스트가 클립보드에 복사되었습니다.');
					}).catch(err => {
					console.error('클립보드에 복사하는 중 오류가 발생했습니다:', err);
					});
				});

				// 버튼 추가
				newBox2.appendChild(closeButton);
									// 테이블 생성
				// 요약테이블 생성
				stable.appendChild(sthead);
				stable.appendChild(stbody);
				newBox2.appendChild(stable); // 테이블을 newBox2에 추가

				// 테이블 생성
				table.appendChild(thead);
				table.appendChild(tbody);
				newBox2.appendChild(table); // 테이블을 newBox2에 추가

				// 박스2 생성
				mapWrap.appendChild(newBox2);
				// 생성되었으므로 true로 표기
				tableshowstatus = true;
				console.log('표 표시', tableshowstatus);
			}
		});

	}
	// 요약표 버튼 생성 종료

}


function observeMutationM() {
    const targetNode = document.querySelector('.map_fixed_area_inner._inner'); // 감시할 노드 선택
    const config = { childList: true, subtree: false }; // 감시할 변경 유형 설정

    const callback = function(mutationsList, observer) {
        mutationsList.forEach(mutation => {
            mutation.addedNodes.forEach(node => {
                if (node.classList && node.classList.contains('article_box--sale')) {
                    console.log('New article_box--sale detected');
                    extractInfoM(); // 새로운 요소가 추가될 때 extractInfoM 실행

                    // 두 번째 MutationObserver 설정
                    const saleBoxObserver = new MutationObserver(saleBoxCallback);
                    const saleBoxConfig = { childList: true, subtree: false };
                    saleBoxObserver.observe(node, saleBoxConfig);
                }
            });
        });
    };

    const saleBoxCallback = function(mutationsList, observer) {
        if (!isScheduled) {
            isScheduled = true;
            clearTimeout(timeout); // 기존 타이머 초기화
            timeout = setTimeout(() => {
                extractInfoM(); // 0.1초 후에 함수 실행
                isScheduled = false; // 플래그 초기화
            }, 100); // 0.1초 대기
        }
    };

    const observer = new MutationObserver(callback);
    observer.observe(targetNode, config);
}

// 옥션원 세부조회 적용
function extractPropertyInfo2() {
	//물건번호 복사 버튼만들기
	const auctElement = document.querySelector('table.head_title.clear.no_print tr td.head_num.bold.no.left');
	console.log(auctElement);
	const numText = auctElement.innerText.trim().replace(/\s+/g, '');
	console.log(numText);

	const numcopyButton = document.createElement('button');

	numcopyButton.addEventListener('click', () => {
		navigator.clipboard.writeText(numText); // 아파트이름을 문자로 붙여넣기
	});

	numcopyButton.textContent = '복사';
	auctElement.appendChild(numcopyButton);

	//물건번호 복사 버튼만들기끝


	//전용면적
	let areaPy;

	const tbody = document.querySelector('div.view_gibon.clear');
	console.log(tbody);

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
					// console.log(areaPy);
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
					// console.log(areaPy);
				} else {
					console.log('면적 추출 실패');
				}
			});
		}
	}


	for (const headerCell of headerCells) {
		if (headerCell.textContent.includes('감 정 가')) {
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
		if (headerCell.textContent.includes('최 저 가')) {
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

	//낙찰 물건인 경우 낙찰단가에 표기하기
	const tbody2 = tbody.querySelector('.tbl_grid.clear');
	const sellCell = tbody2.querySelectorAll('td[colspan="4"]');
	console.log('낙찰가',sellCell);

	if (sellCell) {
		sellCell.forEach((cell) => {
			const cellText = cell.textContent.trim();
			const match = cellText.match(/\s([0-9,]+)원/);
			const price3Text = match ? match[1].replace(/,/g,''): null;

			console.log('price3Text', price3Text);
			if (price3Text) {
				const price3num = parseInt(price3Text);
				const pydanga3 = parseInt(price3num / (areaPy * 10000));

				const pydanga3Span = document.createElement('span');
				pydanga3Span.textContent = `@${pydanga3}만원`;
				pydanga3Span.style.opacity = 0.5; // 50% opacity
				pydanga3Span.style.color = 'green';

				// Append the line break and the calculated value to the content
				cell.appendChild(pydanga3Span);
			}
		});
	}
	//낙찰 물건인 경우 낙찰 단가에 표기하기 끝.

	// 아실 연동 테스트
	for (const headerCell of headerCells) {
		if (headerCell.textContent.includes('소 재 지')) {
			const asilCell = headerCell.nextElementSibling;
			const searchText = asilCell.textContent.split(',')[1].trim().split(' ')[0];
			console.log(searchText);
			const asilButton = document.createElement('button');
			asilButton.style.margin = '0'; // 버튼 여백 제거
			asilButton.style.padding = '0'; // 버튼 패딩 제거
			asilButton.style.display = 'inline-flex'; // 버튼 크기를 이미지에 맞춤
			asilButton.style.alignItems = 'center';
			const icon = document.createElement('img');
			icon.src = chrome.runtime.getURL('asil.png'); // 크롬 확장프로그램 내 경로
			icon.alt = '아실'; // 접근성을 위한 대체 텍스트
			icon.style.width = '16px'; // 아이콘 크기 조정
			icon.style.height = '16px';
			icon.style.margin = '0'; // 아이콘 여백 제거
			icon.style.padding = '0px';

			asilButton.appendChild(icon);

			asilButton.addEventListener('click', () => {

				navigator.clipboard.writeText(searchText); // 아파트이름을 문자로 붙여넣기

				// 새창열기
				const width = screen.width / 2;
				const height = screen.height;
				const left = screen.width / 2;
				const top = 0;

				window.open('https://asil.kr/asil/index.jsp', '_blank', `width=${width},height=${height},top=${top},left=${left}`);


				// searchWindow.onload = function() {
					// searchWindow.postMessage(searchText, '*'); // 데이터 전송
					// console.log('메시지 전송됨:', searchText);
				// };
			});

			asilCell.appendChild(asilButton);

			let naddress = ""
			// 네이버 부동산 붙여넣기
			const liElement = Array.from(document.querySelectorAll('li')).find(li => li.textContent.trim() === "네이버부동산+");
			console.log('liElement',liElement);
			if (liElement) {
				const onclickAttr = liElement.getAttribute('onclick');
				const urlMatch = onclickAttr.match(/window\.open\(['"]([^'"]+)['"]/); // 작은따옴표와 큰따옴표 모두 처리
				console.log('match', urlMatch);
				naddress = urlMatch ? urlMatch[1] : null;
				console.log('address', naddress);
			}

			const nlandButton = document.createElement('button');
			nlandButton.style.margin = '0'; // 버튼 여백 제거
			nlandButton.style.padding = '0'; // 버튼 패딩 제거
			nlandButton.style.display = 'inline-flex'; // 버튼 크기를 이미지에 맞춤
			nlandButton.style.alignItems = 'center';

			const icon2 = document.createElement('img');
			icon2.src = chrome.runtime.getURL('nland.png'); // 크롬 확장프로그램 내 경로
			icon2.alt = 'N부동산'; // 접근성을 위한 대체 텍스트
			icon2.style.width = '16px'; // 아이콘 크기 조정
			icon2.style.height = '16px';
			icon2.style.margin = '0'; // 아이콘 여백 제거
			icon2.style.padding = '0';

			nlandButton.appendChild(icon2);


			nlandButton.addEventListener('click', () => {
				console.log('naddress',naddress);

				if (naddress){
					// 새창열기
					const width = screen.width / 2;
					const height = screen.height;
					const left = screen.width / 2;
					const top = 0;

					window.open(naddress, '_blank', `width=${width},height=${height},top=${top},left=${left}`);
				}
			});

			asilCell.appendChild(nlandButton);

			// G지도 삭제하기
			const gmapElement = asilCell.querySelector('img[alt="구글지도"]');
			if (gmapElement) {
				gmapElement.remove();
			}
		}
	}

	// 아실 연동 테스트 끝.


	// 광고 없애는 부분
	const adItem = document.querySelector('#piper_loan_bn');
	if (adItem) {
		adItem.remove();
	}

	// 배너 없애는 부분
	const bannerItem = document.querySelector('.logo clear no_print');
	if (bannerItem) {
		bannerItem.remove();
	}

	// 광고 없애는 부분
	const adItem2 = document.querySelector('#ly_banner');
	if (adItem2) {
		adItem2.remove();
	}
}

function auction1Print() {
	console('프린트 단축화 실행');
	// 국토교통부 실거래가
	const adItem = document.querySelector('#molit_block');
	if (adItem) {
		adItem.remove();
	}

	// 매각사례 분석
	const adItem2 = document.querySelector('#nk_total');
	if (adItem2) {
		adItem2.remove();
	}

}


//아실 후작업 부분 - 작동 안함
function asilCon() {
    window.addEventListener('message', (event) => {
		if (event.origin === 'https://auction1.co.kr/') { // 보안 검사를 위해 부모 도메인 확인
			console.log('메세지 수신됨', event.data);
			const searchInput = document.getElementById('keyword');
			if (searchInput && event.data) {
				searchInput.value = event.data;
				searchInput.form.submit(); // 폼 자동 제출
			}
		}
    });
}

function extractPropertyInfo3() {

	let tbody = document.querySelector('#list_body');

	// 로드되지 않는 경우를 고려해서 넣기
	if (!tbody) {
		const frame = parent.frames['land_info_kils'];
		const frameDocument = frame.document || frame.contentDocument
		console.log('frameDocument', frameDocument);
		tbody = frameDocument.querySelector('#list_body');
		console.log('tbody', tbody);
	}


	const propertyItems = tbody.querySelectorAll('tr');

	propertyItems.forEach((item) => {
		let areaPy;
		let areastatus = true;
		//건물 전용면적 산출하기
		const areaElement = item.querySelector('.view_gray');
		const areaText = areaElement.textContent.trim();
		// console.log(areaText);
		const textParts = areaText.split(',');

		//문자열 찾기
		const regex = /\((\d+\.\d+)\평\)/;

		textParts.forEach (part => {
			const match = part.match(regex);
			// console.log(match)
			if (match) {
				areaPy = parseFloat(match[1]);
				// console.log(`추출된 숫자: ${areaPy}`);
				// 건물은 전용면적 토지는 토지면적을로 숫자가 할당됨
			}
		});

		if (areaPy) {
			// 금액1 추출 (auct_iprice_숫자 아이디 내부 텍스트) //auct_jprice_2406369
			const price1Element = item.querySelector('[id^="auct_jprice_"]');
			const price1Text = price1Element.textContent.trim().replace(/,/g, '');
			const price1num = parseInt(price1Text);
			console.log(price1num);

			// 금액2 추출 (auct_iprice_숫자 아이디 내부 텍스트) //auct_jprice_2406369
			const price2Element = item.querySelector('[id^="auct_bprice_"]');
			const price2Text = price2Element.textContent.trim().replace(/,/g, '');
			const price2num = parseInt(price2Text);
			// console.log(price2num);

			const pydanga1 = parseInt(price1num / (areaPy * 10000));
			const pydanga2 = parseInt(price2num / (areaPy * 10000));
			// console.log(pydanga1);

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


			const price3Element = item.querySelector('[id^="auct_sprice_"]');

			if (price3Element) {
				// 금액3 추출 (auct_iprice_숫자 아이디 내부 텍스트) //auct_sprice_2406369
				const price3Text = price3Element.textContent.trim().replace(/,/g, '');
				const price3num = parseInt(price3Text);
				const pydanga3 = parseInt(price3num / (areaPy * 10000));

				const lineBreakSpan3 = document.createElement('span');
				lineBreakSpan3.innerHTML = '<br>'; // This will render as an actual line break

				const pydanga3Span = document.createElement('span');
				pydanga3Span.textContent = `@${pydanga3}만원`;
				pydanga3Span.style.opacity = 0.5; // 50% opacity
				pydanga3Span.style.color = 'blue';

				price3Element.appendChild(lineBreakSpan3);
				price3Element.appendChild(pydanga3Span);
			}
		} else {
			console.log('면적 없어서 pass');
		}
	});

}


function auction1myItem() {
	const propertyItems = document.querySelectorAll("#list_body div[id^='tr'");
	console.log ('propertyItems', propertyItems);

	propertyItems.forEach((item) => {

		let areaPy

		console.log(item);
		const tbody = item.querySelector('.tbl_grid tbody');
		console.log('table body', tbody);

		const headerCells = tbody.querySelectorAll('th');


		for (const headerCell of headerCells) {
			if (headerCell.textContent.includes('면적')) {
				const areaLand = headerCell.nextElementSibling;
				// const content = areaLand.textContent.trim(); //내용에서 공백 제가
				const content = areaLand.textContent.trim(); //내용에서 공백 제가
				// 정규 표현식을 사용하여 '평' 앞의 숫자 추출

				const matches = content.match(/(\d+\.?\d*)평/g);
				// const regex = /\((\d+\.\d+)\평\)/;

				if (matches) {
					// 결과 배열의 숫자 추출
					const values = matches.map(match => match.match(/(\d+\.?\d*)/)[1]);
					console.log(values);

					areaPy = values[0]; // 면적 추출
					console.log(areaPy);
				}
			}
		}

		if (areaPy) {
			for (const headerCell of headerCells) {
				if (headerCell.textContent.includes('감정가')) {
					const price1Element = headerCell.nextElementSibling;
					const price1Text = price1Element.textContent.trim().replace(/,/g, '');
					const price1num = parseInt(price1Text);
					const pydanga1 = parseInt(price1num / (areaPy * 10000));

					// Create a new <span> element for the line break
					// const lineBreakSpan = document.createElement('span');
					// lineBreakSpan.innerHTML = '<br>'; // This will render as an actual line break

					const pydanga1Span = document.createElement('span');
					pydanga1Span.textContent = `@${pydanga1}만원`;
					pydanga1Span.style.opacity = 0.5; // 50% opacity
					pydanga1Span.style.color = 'red';

					// Append the line break and the calculated value to the content
					// price1Element.appendChild(lineBreakSpan);
					price1Element.insertBefore(pydanga1Span, price1Element.firstChild);
				}
			}

			for (const headerCell of headerCells) {
				if (headerCell.textContent.includes('최저가') || headerCell.textContent.includes('매각가')) {
					const price2Element = headerCell.nextElementSibling;
					const price2Text1 = price2Element.textContent.trim().replace(/\(\d+%\)\s*/g, '');
					const price2Text = price2Text1.replace(/[,원]/g,'');
					const price2num = parseInt(price2Text);
					console.log(price2num);
					const pydanga2 = parseInt(price2num / (areaPy * 10000));

					// // Create a new <span> element for the line break
					// const lineBreakSpan2 = document.createElement('span');
					// lineBreakSpan2.innerHTML = '<br>'; // This will render as an actual line break

					const pydanga2Span = document.createElement('span');
					pydanga2Span.textContent = `@${pydanga2}만원`;
					pydanga2Span.style.opacity = 0.5; // 50% opacity
					pydanga2Span.style.color = 'green';

					// Append the line break and the calculated value to the content
					// price2Element.appendChild(lineBreakSpan2);
					price2Element.insertBefore(pydanga2Span, price2Element.firstChild);

				}
			}
		}
	});
}


function observeMutation3() {
    const targetNode = document.querySelector('#list_body'); // 감시할 노드 선택
    const config = { childList: true, subtree: false }; // 감시할 변경 유형 설정

    const callback = function(mutationsList, observer) {
        if (!isScheduled) {
            isScheduled = true;
			observer.disconnect(); // 감시 중단
			auction1myItem(); // 0.2초 후에 함수 실행
			observer.observe(targetNode, config); // 감시 재개
			isScheduled = false; // 플래그 초기화
        }
    };

    const observer = new MutationObserver(callback);
    observer.observe(targetNode, config);
}


function extractPropertyInfo4() {
	const tbody = document.querySelector('#lsTbody');
	const propertyItems = tbody.querySelectorAll('tr');

	propertyItems.forEach((item) => {
		let areaPy;
		let areastatus = true;
		//건물 전용면적 산출하기
		const areaElement = item.querySelector('.blue.f12');
		const areaText = areaElement.textContent.trim();
		const textParts = areaText.split(',');

		//문자열 찾기
		const regex = /\((\d+\.\d+)\평\)/;

		const match = textParts[0].match(regex);
		console.log(match);
		if (match) {
			areaPy = parseFloat(match[1]);
			console.log(`추출된 숫자: ${areaPy}`);
			// 건물은 전용면적 토지는 토지면적으로 숫자가 할당됨
		}

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


function observeMutationsTank() {
    const targetNode = document.querySelector('body'); // 감시할 노드 선택
    const config = { childList: true, subtree: true }; // 감시할 변경 유형 설정

    const callback = function(mutationsList, observer) {
		// 제거된 부분이 있는지 확인 - 제거가 안되서 문제... 파악다시
        for (let mutation of mutationsList) {
            if (mutation.type === 'childList') {
                setTimeout(extractPropertyInfo4, 300); // 1초 후에 extractPropertyInfo 함수 실행
            }
        }
    };

    const observer = new MutationObserver(callback);
    observer.observe(targetNode, config);
}


// auction 세부조회 적용
function extractPropertyInfo5() {
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



// 아파트 매물축약기
function summaryInfo() {
	// 광고부분 확인 및 삭제
	const adItem = document.getElementById('land_panel_da');
	if (adItem) {
		adItem.remove();
	}

	// 각 항목 선택
	const propertyItems = document.querySelectorAll('.item_inner:not(.is-loading)'); // 'is-loading' 클래스를 제외한 요소 선택
	// 각 항목별로 필요 없는 부분 삭제
    propertyItems.forEach((item) => {

		// 공인중개사 삭제
		const cpItem = item.querySelector('.cp_area');
		if (cpItem) {
			cpItem.remove();
		}

		// 매물날짜 삭제
		const labelItem = item.querySelector('.label_area');
		if (labelItem) {
			labelItem.remove();
		}
	});
}


// 변경되면 감시하는 부분
function observeMutations2() {
    const targetNode = document.querySelector('body'); // 감시할 노드 선택
    const config = { childList: true, subtree: true }; // 감시할 변경 유형 설정

    const callback = function(mutationsList, observer) {
		// 제거된 부분이 있는지 확인 - 제거가 안되서 문제... 파악다시
        for (let mutation of mutationsList) {
            if (mutation.type === 'childList') {
                setTimeout(summaryInfo, 50); // 1초 후에 extractPropertyInfo 함수 실행
            }
        }
    };

    const observer = new MutationObserver(callback);
    observer.observe(targetNode, config);
}


function expandMyfr() {
	const styleElement = document.querySelector('style[data-emotion="css 1n85g5d"]');
	if (styleElement) {
		styleElement.innerHTML = styleElement.innerHTML.replace(/\.css-1n85g5d{[^}]*}/, '.css-1n85g5d{position:relative;width:1000px;min-height:100vh;background-color:#ffffff;box-shadow:0px 0px 20px 0px #191E2333;}');
		console.log('Width updated to 1000px');
	} else {
		console.log('Element not found');
	}
}

window.addEventListener('DOMContentLoaded', function() {
	// 옥션원 인쇄 적용
	if (window.location.href.startsWith('https://www.auction1.co.kr/common/print_1.html')) {
		console.log('프린트축약');
		auction1Print();
	}
});


// 설정 파일을 로드하는 함수
function loadConfig(callback) {
  fetch(chrome.runtime.getURL('config.json'))
    .then(response => response.json())
    .then(data => {
      callback(data);
    })
    .catch(error => {
      console.error('Error loading config:', error);
    });
}


// 설정 저장 함수
function saveConfig(newConfig, callback) {
  chrome.storage.local.set({ config: newConfig }, () => {
    console.log('Config saved');
    if (callback) callback();
  });
}

// 설정 불러오기 함수
function getConfig(callback) {
	chrome.storage.local.get(['config'], result => {
		if (result.config) {
		  callback(result.config);
		} else {
		  // 설정이 저장되어 있지 않은 경우, 기본 설정 로드
		  loadConfig(callback);
		}
	});
}

// 설정을 로드하고 콘솔에 출력
getConfig(config => {
	console.log('Loaded config:', config);
	onoffstatus = config.onoffstatus; // onoffstaus변수에 설정 값 할당
	autoScroll = config.autoScroll;
	contiStatus = config.contiStatus;
	floorsorting = config.floorsorting;
	dangaAsc = config.dangaAsc;
	percentMargin = config.percentMargin;
});



// 페이지가 로드되면 실행
window.addEventListener('load', function() {

	// 네이버 세부조회조회 적용
	if (window.location.href.startsWith('https://new.land.naver.com/offices') ||
		window.location.href.startsWith('https://new.land.naver.com/houses') ||
		window.location.href.startsWith('https://new.land.naver.com/complexes')){
		setTimeout(extractPropertyInfo,50);
		observeMutations(); //DOM 변경 감시 시작
	}


	// 네이버 모바일 적용
	if (window.location.href.startsWith('https://m.land.naver.com/map')) {
		extractInfoM();
		setTimeout(observeMutationM, 500); //DOM 변경 감시 시작
	}

	// 옥션원 세부조회조회 적용
	if (window.location.href.startsWith('https://www.auction1.co.kr/auction/ca_view.php')) {
		extractPropertyInfo2();
	}

		// 아실연동 -- 실패
	if (window.location.href.startsWith('https://asil.kr/asil/index.jsp')) {
		console.log('asilcon 실행');
		asilCon();
	}

	// 옥션원 목록조회아이템 적용
	if (window.location.href.startsWith('https://www.auction1.co.kr/auction/ca_list.php') ||
		window.location.href.startsWith('https://www.auction1.co.kr/auction/ca_land_info_kils.php')) {
		extractPropertyInfo3();
	}

	// 옥션원 관심물건 적용
	if (window.location.href.startsWith('https://www.auction1.co.kr/member/inter_list.php')) {
		auction1myItem();
		observeMutation3();
	}

	// auction 목록조회아이템 적용
	if (window.location.href.startsWith('https://www.tankauction.com/ca/caList.php')) {
		setTimeout(extractPropertyInfo4,50);
		observeMutationsTank();
	}

	// auction 세부조회아이템 적용
	if (window.location.href.startsWith('https://www.tankauction.com/ca/caView.php')) {
		extractPropertyInfo5();
	}

	// 네이버 아파트매물정보 축소기
	if (window.location.href.startsWith('https://new.land.naver.com/complexes')) {
		setTimeout(summaryInfo,50);
		observeMutations2(); //DOM 변경 감시 시작
	}

	// 마이프차 지도키우기
	if (window.location.href.startsWith('https://myfranchise.kr/map')) {
		expandMyfr();
	}


});
