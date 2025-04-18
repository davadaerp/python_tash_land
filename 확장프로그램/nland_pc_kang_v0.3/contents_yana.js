// content.js

// config초기화를 위한 부분(개발용)
// chrome.storage.local.remove(['config'], function() {
	// console.log('Config removed from local storage.');
// });

let propertyData = [];
let propertyData2 = [];
let propertyData3 = [];
let tableData1 = []; // 월세 테이블 만들 데이터 { key: data, key2: data2} 형식으로 저장
let tableData2 = []; // 매매테이블 만들 데이터
let tableData3 = []; // 전세테이블 만들 데이터
let newBox2;
let datalength1 = 0;
let datalength2 = 0;
let datalength3 = 0;

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
let tableData3_copy = []; // 전세테이블 만들 데이터
// 탭구분(apt,villa,sanga)
let tabGugun = 'sanga';

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
	//console.log('selectedDealType: ' + selectedDealType + ', floor:' + floor );
	tableData1 = [];
	tableData2 = [];
	tableData3 = [];
	if (selectedDealType === '월세') {
		if (floor === "전체") {
			tableData1 = tableData1_copy;
			tableData2 = []; // 매매 데이터는 제외
			tableData3 = [];
		} else if (floor === "저층")	{
			tableData1 = tableData1_copy.filter(item => Number(item.해당층) <= 2);
			tableData2 = []; // 매매 데이터는 제외
		} else if (floor === "상층") {
			tableData1 = tableData1_copy.filter(item => Number(item.해당층) >= 3);
			tableData2 = []; // 매매 데이터는 제외
		} else {
			tableData1 = tableData1_copy.filter(item => Number(item.해당층) === Number(floor));
			tableData2 = []; // 매매 데이터는 제외
			tableData3 = [];
		}
	} else if (selectedDealType === '매매') {
		if (floor === "전체") {
			tableData1 = []; // 월세 데이터는 제외
			tableData2 = tableData2_copy;
			tableData3 = [];
		} else if (floor === "저층")	{
			tableData1 = []; // 월세 데이터는 제외
			tableData2 = tableData2_copy.filter(item => Number(item.해당층) <= 2);
		} else if (floor === "상층")	{
			tableData1 = []; // 월세 데이터는 제외
			tableData2 = tableData2_copy.filter(item => Number(item.해당층) >= 3);
		} else {
			tableData1 = []; // 월세 데이터는 제외
			tableData2 = tableData2_copy.filter(item => Number(item.해당층) === Number(floor));
			tableData3 = [];
		}
	} else if (selectedDealType === '전세') {
		if (floor === "전체") {
			tableData1 = []; // 월세 데이터는 제외
			tableData2 = [];
			tableData3 = tableData3_copy;
		} else {
			tableData1 = []; // 월세 데이터는 제외
			tableData2 = []
			tableData3 = tableData3_copy.filter(item => item.해당층 === String(floor));
		}
	} else { // 전체
		if (floor === "전체") {
			tableData1 = tableData1_copy;
			tableData2 = tableData2_copy;
			tableData3 = tableData3_copy;
		} else if (floor === "저층")	{
			tableData1 = tableData1_copy.filter(item => Number(item.해당층) <= 2);
			tableData2 = tableData2_copy.filter(item => Number(item.해당층) <= 2);
		} else if (floor === "상층")	{
			tableData1 = tableData1_copy.filter(item => Number(item.해당층) >= 3);
			tableData2 = tableData2_copy.filter(item => Number(item.해당층) >= 3);
		} else {
			tableData1 = tableData1_copy.filter(item => Number(item.해당층) === Number(floor));
			tableData2 = tableData2_copy.filter(item => Number(item.해당층) === Number(floor));
			tableData3 = tableData3_copy.filter(item => Number(item.해당층) === Number(floor));
		}
	}
	// 요약정보
	if (tabGugun === 'sanga') {
		summarySangaAndDisplayTable();
	} else if (tabGugun === 'apt' || tabGugun === 'villa') {
		summaryAptVillaAndDisplayTable();
	} else {
		//
	}
	// 리스트정보
	listAndDisplayTable();
}


// 요약정보
function summarySangaAndDisplayTable() {

		// tableData1:월세, tableData2:매매, tableData3:전세, tableDataSum: 요약테이블
		// 요약테이블 데이터 정리
		const tableDataSum = [];

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

			tableDataSum.push(['1층', minPdanga.toFixed(1), avgPdanga.toFixed(1), maxPdanga.toFixed(1), pValues.length]);
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
				tableDataSum.push(['2층', 0,0,0,0]);
			}
		} else {
			let minPdanga2 = Math.min(...pValues2);
			let maxPdanga2 = Math.max(...pValues2);
			let avgPdanga2 = pValues2.reduce((sum, value) => sum + value, 0) / pValues2.length;

			// NaN 또는 Infinity인 경우 0으로 설정
			minPdanga2 = isFinite(minPdanga2) ? minPdanga2 : 0;
			maxPdanga2 = isFinite(maxPdanga2) ? maxPdanga2 : 0;
			avgPdanga2 = isFinite(avgPdanga2) ? avgPdanga2 : 0;

			tableDataSum.push(['2층', minPdanga2.toFixed(1), avgPdanga2.toFixed(1), maxPdanga2.toFixed(1), pValues2.length]);
		}

		if (pValues3.length != 0) {
			let minPdanga3 = Math.min(...pValues3);
			let maxPdanga3 = Math.max(...pValues3);
			let avgPdanga3 = pValues3.reduce((sum, value) => sum + value, 0) / pValues3.length;

			// NaN 또는 Infinity인 경우 0으로 설정
			minPdanga3 = isFinite(minPdanga3) ? minPdanga3 : 0;
			maxPdanga3 = isFinite(maxPdanga3) ? maxPdanga3 : 0;
			avgPdanga3 = isFinite(avgPdanga3) ? avgPdanga3 : 0;

			tableDataSum.push(['상층', minPdanga3.toFixed(1), avgPdanga3.toFixed(1), maxPdanga3.toFixed(1), pValues3.length]);
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

		// 1층,2층,상층
		tableDataSum.forEach(item => {
			const row = document.createElement('tr');
			Object.values(item).forEach(value => {
				const td = document.createElement('td');
				// 첫 번째 열(첫 번째 td)의 텍스트를 파란색으로 설정
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


// 아파트,빌라 요약정보
function summaryAptVillaAndDisplayTable() {

		console.log('=== summaryAptVillaAndDisplayTable Start. =====')

		// tableData1:월세, tableData2:매매, tableData3:전세, tableDataSum: 요약테이블
		// 요약테이블 데이터 정리
		const tableDataSum = [];

		// 월세 보증금 최소/평균/최대 구하기
		if (tableData1.length > 0) {
			// 월세 보증금 최소/평균/최대 구하기
			const result = calculateStats(tableData1);
			// console.log(`최소 보증금: ${result.minDeposit}만, 평균 보증금: ${result.avgDeposit}만, 최대 보증금: ${result.maxDeposit}만`);
			// console.log(`최소 월세: ${result.minRent}천, 평균 월세: ${result.avgRent}천, 최대 월세: ${result.maxRent}천`);

			// 보증금
			const minDeposit = result.minDeposit * 10000;
			const maxDeposit = result.maxDeposit * 10000;
			const avgDeposit = result.avgDeposit * 10000;
			// 월세
			const minRent = result.minRent / 10;
			const maxRent = result.maxRent / 10;
			const avgRent = result.avgRent / 10;

			let minDepositRent = formatToEok(minDeposit.toFixed(0)) + '억/' + minRent.toFixed(0);
			let maxDepositRent = formatToEok(maxDeposit.toFixed(0)) + '억/' + maxRent.toFixed(0);
			let avgDepositRent = formatToEok(avgDeposit.toFixed(0)) + '억/' + avgRent.toFixed(0);

			tableDataSum.push(['월세', minDepositRent, avgDepositRent, maxDepositRent, tableData1.length]);
		}

		const stable = document.createElement('table');
		const sthead = document.createElement('thead');
		const stbody = document.createElement('tbody');

		//테이블 스타일 정해주기
		stable.id = 'summaryTableId'; // Assign a unique ID to the table
		stable.style.fontSize = '10pt';
		stable.style.borderCollapse = 'collapse'; // 테이블 셀 간의 간격 제거
		stable.style.width = '80%'; // 테이블 폭 설정
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

		// 월세는 그냥 보여주기
		tableDataSum.forEach(item => {
			const row = document.createElement('tr');
			Object.values(item).forEach((value, index) => {
				const td = document.createElement('td');
				if (index === 0) {
					// 첫 번째 열(첫 번째 td)의 텍스트를 파란색으로 설정
					td.style.color = 'black';
				}
				td.textContent = value;
				td.style.border = '0.5px solid #333333'; // 테두리 설정
				td.style.textAlign = 'center'; // 텍스트 가운데 정렬
				row.appendChild(td);
			});
			stbody.appendChild(row);
		});

		// ==========================================================
		// 전세: 건수, 최소, 평균, 최대
		const tableDanga3 = tableData3.map(item => item.가격);
		if (tableDanga3.length > 0) {
			//
			const summaryData = {
				titValue3: '전세',
				minValue3: Math.min(...tableDanga3),
				avgValue3: (tableDanga3.reduce((sum, value) => sum + value, 0) / tableDanga3.length).toFixed(0), // 소수점 2자리까지
				maxValue3: Math.max(...tableDanga3),
				cntValue3: tableDanga3.length
			};
			// 전세 요약 데이터 추가
			const summaryRow = document.createElement('tr');
			Object.values(summaryData).forEach((value,index) => {
				const td = document.createElement('td');
				if (index === 0) {
					// 첫 번째 열(첫 번째 td)의 텍스트를 파란색으로 설정
					td.style.color = 'green';
				}
				if (index === 0 || index === 4) {
					td.textContent = value;
				} else {
					td.textContent = formatToEok(value) + '억';
				}
				td.style.border = '0.5px solid #333333';
				td.style.textAlign = 'center';
				summaryRow.appendChild(td);
			});
			stbody.appendChild(summaryRow);
		}

		// ==========================================================
		// 매매: 건수, 최소, 평균, 최대
		const tableDanga2 = tableData2.map(item => item.가격);
		// add by kang 요약테이블에 매매정보 추가함.
		if (tableDanga2.length > 0) {
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
				if (index === 0 || index === 4) {
					td.textContent = value;
				} else {
					td.textContent = formatToEok(value) + '억';
				}
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

		console.log('=== listAndDisplayTable Start. =====')

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

		// const tableitem = { 구분: type, 해당층: cfloor, 전체층: tfloor, 향: direction, 평당가: pdanga, 전용면적: areas, 가격: totalPrice };
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

			// 매매자료를 가격 낮은것부터 오름차순으로 정리
			tableData2.sort((a, b) => {
				const secondKeyA = Object.values(a)[6];
				const secondKeyB = Object.values(b)[6];
				if (secondKeyA < secondKeyB) return -1;
				if (secondKeyA > secondKeyB) return 1;
				return 0;
			});
			console.log('오름차순 정리후 data', tableData2)

			// 전세자료를 가격 낮은것부터 오름차순으로 정리
			tableData3.sort((a, b) => {
				const secondKeyA = Object.values(a)[6];
				const secondKeyB = Object.values(b)[6];
				if (secondKeyA < secondKeyB) return -1;
				if (secondKeyA > secondKeyB) return 1;
				return 0;
			});
			console.log('오름차순 정리후 data', tableData3)

		} else {
			// 월세 자료를 층 내림차순 정리
			console.log('내림차순 정리전 data', tableData1)
			tableData1.sort((a, b) => {
				const secondKeyA = Object.values(a)[3];
				const secondKeyB = Object.values(b)[3];
				if (secondKeyA < secondKeyB) return -1;
				if (secondKeyA > secondKeyB) return 1;
				return 0;
			});
			console.log('내림차순 정리후 data', tableData1)

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
				// 층/전체층
				if (index === 1) { // 2열 (index는 0부터 시작)
					td.textContent = value + ' / ' + Object.values(item)[2]; // 2열 값과 3열 값 결합
					td.style.border = '0.5px solid #333333'; // 테두리 설정
					td.style.textAlign = 'center'; // 텍스트 가운데 정렬
					row.appendChild(td);
				} else if (index !== 2) { // 전체층은 패스함
					td.textContent = value;
					td.style.border = '0.5px solid #333333'; // 테두리 설정
					td.style.textAlign = 'center'; // 텍스트 가운데 정렬
					row.appendChild(td);
				}
			});
			tbody.appendChild(row);
		});

		//const tableitem = { 구분: type, 해당층: cfloor, 전체층: tfloor, 향: direction, 평당가: pdanga, 전용면적: areas3, 가격: totalPrice };
		// 전세처리
		tableData3.forEach(item => {
			const row = document.createElement('tr');
			Object.values(item).forEach((value, index) => {
				const td = document.createElement('td');
				if (index === 0) {
					// 첫 번째 열(첫 번째 td)의 텍스트를 파란색으로 설정
					td.style.color = 'green';
				}
				// 층/전체층
				if (index === 1) { // 2열 (index는 0부터 시작)
					td.textContent = value + ' / ' + Object.values(item)[2]; // 2열 값과 3열 값 결합
					td.style.border = '0.5px solid #333333'; // 테두리 설정
					td.style.textAlign = 'center'; // 텍스트 가운데 정렬
					row.appendChild(td);
				} else if (index !== 2) { // 전체층은 패스함
					if (index === 6) {
						td.textContent = (tabGugun === 'sanga') ? value : formatToEok(value) + '억';
					} else {
						td.textContent = value;
					}
					td.style.border = '0.5px solid #333333'; // 테두리 설정
					td.style.textAlign = 'center'; // 텍스트 가운데 정렬
					row.appendChild(td);
				}
			});
			tbody.appendChild(row);
		});

		// 매매현황
		tableData2.forEach(item => {
			const row = document.createElement('tr');
			Object.values(item).forEach((value, index) => {
				const td = document.createElement('td');
				if (index === 0) {
					// 첫 번째 열(첫 번째 td)의 텍스트를 파란색으로 설정
					td.style.color = 'blue';
				}
				// 층/전체층
				if (index === 1) { // 2열 (index는 0부터 시작)
					td.textContent = value + ' / ' + Object.values(item)[2]; // 2열 값과 3열 값 결합
					td.style.border = '0.5px solid #333333'; // 테두리 설정
					td.style.textAlign = 'center'; // 텍스트 가운데 정렬
					row.appendChild(td);
				} else if (index !== 2) { // 전체층은 패스함
					if (index === 6) {
						td.textContent = (tabGugun === 'sanga') ? value : formatToEok(value) + '억';
					} else {
						td.textContent = value;
					}
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

		console.log('=== selectedAndDisplay Start. =====')

		// 1. tableData1와 tableData2 합치기
		const combinedData = [...tableData1_copy, ...tableData2_copy, ...tableData3_copy];

		// 2. 합쳐진 데이터에서 '해당층' 값만 추출하고 null, undefined 제외 후 중복 제거
		const uniqueFloors = [...new Set(combinedData.map(item => item.해당층).filter(floor => floor !== null && floor !== undefined))];

		// 3. 층 번호 오름차순 정렬
		uniqueFloors.sort((a, b) => a - b);

		// 4. 거래 형태 드롭다운 목록 생성
		const dealTypeSelect = document.createElement('select');
		// 드롭다운 스타일 (파란색 배경, 흰색 텍스트)
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
		if (tableData3_copy.length > 0) {
			dealOptions.push('전세');
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

		// 상가,창고,사무실은 저층,상층비교(아파트와 빌라는 층만처리)
		if (tableData3_copy.length <= 0) {
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
			} else if (dealTypeSelect.value === '전세') {
				floorsToAdd = [...new Set(tableData3_copy.map(item => item.해당층).filter(floor => floor !== null && floor !== undefined))];
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

			// 상가,창고,사무실은 저층,상층비교(아파트와 빌라는 층만처리)
			if (tableData3_copy.length <= 0) {
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

// 국토부실거래검색 처리
function realSearchData() {
  // 기본 컨트롤 박스 가져오기
  const onoffPanel = document.querySelector('.filter_area');
  onoffPanel.style.display = 'inline-block'; // 줄 바꿈 방지

  // 실거래검색 버튼 생성
  const realDataSearch = document.createElement('span');
  realDataSearch.id = 'realDataSearch'; // id 지정
  realDataSearch.textContent = '실거래검색';
  realDataSearch.style.marginLeft = '10px'; // 다른 요소와의 간격 조절
  realDataSearch.style.backgroundColor = '#007bff'; // 파란색 배경
  realDataSearch.style.color = '#fff'; // 흰색 텍스트
  realDataSearch.style.padding = '4px 8px'; // 내부 여백
  realDataSearch.style.fontSize = '12px'; // 작은 글씨 크기
  realDataSearch.style.borderRadius = '8px'; // 둥근 모서리
  realDataSearch.style.cursor = 'pointer'; // 클릭 가능한 커서
  realDataSearch.style.transition = 'all 0.3s ease'; // 부드러운 애니메이션 효과

  // 클릭 시 지정 URL을 새 팝업창으로 엽니다.
  realDataSearch.addEventListener('click', function() {
    const popupWidth = 1490;   // 원하는 팝업 너비
    const popupHeight = 1300;  // 원하는 팝업 높이
    const left = (screen.width - popupWidth) / 2;
    const top = (screen.height - popupHeight) / 2;
    window.open("https://erp-dev.bacchuserp.com/ts/", "realDataPopup",
      `width=${popupWidth},height=${popupHeight},left=${left},top=${top},resizable=yes,scrollbars=yes`);
  });

  // onoffPanel에 실거래검색 버튼 추가
  onoffPanel.appendChild(realDataSearch);
}

// 수익율분석
function profitAnalData() {
	// 기본 컨트롤 박스 가져오기
	const onoffPanel = document.querySelector('.filter_area');
	onoffPanel.style.display = 'inline-block'; // 줄 바꿈 방지

	// 수익율분석 버튼 생성
	const profitDataSearch = document.createElement('span');
	profitDataSearch.textContent = '수익율분석표';
	profitDataSearch.style.marginLeft = '10px'; // modeText와의 간격 조절
	profitDataSearch.style.backgroundColor = '#ffff00'; // 노란색 배경
	profitDataSearch.style.color = '#000'; // 검정색 텍스트
	profitDataSearch.style.fontWeight = 'bold'; // 볼드체
	profitDataSearch.style.padding = '4px 8px'; // 내부 여백 줄이기
	profitDataSearch.style.fontSize = '12px'; // 작은 글씨 크기
	profitDataSearch.style.borderRadius = '8px'; // 둥근 모서리
	profitDataSearch.style.cursor = 'pointer'; // 클릭 가능 커서
	profitDataSearch.style.transition = 'all 0.3s ease'; // 부드러운 애니메이션 효과

	// 반짝반짝 효과를 위한 애니메이션 적용
	profitDataSearch.style.animation = 'sparkle 1.5s infinite alternate';

	// sparkle 애니메이션을 위한 keyframes 추가
	const style = document.createElement('style');
	style.textContent = `
	  @keyframes sparkle {
		0% {
		  box-shadow: 0 0 5px rgba(255, 255, 255, 0.5);
		}
		50% {
		  box-shadow: 0 0 20px rgba(255, 255, 255, 1);
		}
		100% {
		  box-shadow: 0 0 5px rgba(255, 255, 255, 0.5);
		}
	  }
	`;
	document.head.appendChild(style);

	// 클릭 시 새 팝업 창 열기
	profitDataSearch.addEventListener('click', function () {
		alert('1기분들 준비중입니다. 쫌만 기둘려주세요.')
		/*
		// 확장 프로그램의 HTML 파일 경로 가져오기
		const externalHtmlPath = chrome.runtime.getURL('realdata_sanga.html');

		// 현재 화면 크기 가져오기
		const screenWidth = window.screen.width;
		const screenHeight = window.screen.height;

		// 팝업 창 크기 설정
		const popupWidth = 900;
		const popupHeight = 1280;

		// 중앙 정렬 계산
		const popupLeft = (screenWidth - popupWidth) / 2;
		const popupTop = (screenHeight - popupHeight) / 2;

		// 새 창을 띄우는 코드 (중앙 위치 적용)
		const popupWindow = window.open(
			externalHtmlPath,
			'RealDataSearchPopup',
			`width=${popupWidth},height=${popupHeight},top=${popupTop},left=${popupLeft},scrollbars=yes,resizable=yes`
		);

		// 팝업이 차단되었는지 확인
		if (!popupWindow) {
			alert('팝업이 차단되었습니다. 팝업 차단을 해제해주세요.');
		}
		 */
	});
	// onoffPanel에 실거래검색 버튼 추가
	onoffPanel.appendChild(profitDataSearch);
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
			// tab1에 대한 추가 처리
	  		tabGugun = 'apt';
			break;
		  case 'tab2':
			console.log('빌라/주택 탭이 선택되었습니다.');
			// 빌라적용 프로퍼티
		  	tabGugun = 'villa';
			villaPropertyInfo();
			break;
		  case 'tab3':
			console.log('원룸/투룸 탭이 선택되었습니다.');
			// tab3에 대한 추가 처리
			break;
		  case 'tab4':
			console.log('상가/업무/공장/토지 탭이 선택되었습니다.');
			// 상가적용 프로퍼티
			tabGugun = 'sanga';
			sanggaPropertyInfo();
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
	});
}

// 상가적용 프로퍼티
function sanggaPropertyInfo() {

	// 기본 컨트롤 박스 넣기
	const onoffPanel = document.querySelector('.filter_area');
	onoffPanel.style.display = 'inline-block'; // 줄 바꿈 방지

	if (!onoffPanel.dataset.highlighted) {

		// 프로그램모드 on/off 버튼 생성
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
		realSearchData();

		// 수익율 분석표
		//profitAnalData();
	}
	// 프로그램 On/Off
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
						newBox2.appendChild(closeButton);
											// 테이블 생성

						// 요약테이블 생성
						summarySangaAndDisplayTable();

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
					newBox2.appendChild(closeButton);

					// 요약테이블 생성
					summarySangaAndDisplayTable();

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
		/*
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
		*/

		// 세부조회항목에서 월세단가 표기하기 - 보류 / 귀찮음
		// const detailBox = document.querySelector('.detail_box--summary'); //  table.info_table_wrap
		// if (detailBox) {
			// const detailTable = detailBox.querySelector('.info_table_wrap');
			// console.log('detailTable', detailTable);
		// }

		// 세부조회항목에서 월세단가 표기하기 끝
	}
}

// 억단위 변환
function convertToEokNumber(value) {
    let match = value.match(/(\d+)억(?:\s*(\d{1,3},?\d{0,3})?)?/);
    if (match) {
        let eok = parseInt(match[1], 10) * 100000000; // 억 단위 변환
        let man = match[2] ? parseInt(match[2].replace(/,/g, ""), 10) * 10000 : 0; // 만 단위 변환
        return eok + man;
    }
    return parseInt(value.replace(/[^0-9]/g, ""), 10) * 10000;
}

// 금액,보증금,월세 구하는거
function extractDepositAndRent(text) {
    const match = text.match(/([\d억,\s]+)\/([\d,]+)/);
    if (match) {
        let deposit = convertToEokNumber(match[1].trim()); // 억/만 변환
        let rent = parseInt(match[2].replace(/,/g, ""), 10) * 10000;
        return { deposit: deposit, rent: rent };
    }
    return { deposit: "N/A", rent: "N/A" };
}

// 금액을 억단위로 변환시 적용
function formatToEok(value) {
    return (value / 100000000).toFixed(1);
}

// 월세 보증금 최소/평균/최대 구할때 보증금,렌트 가져오기.
function calculateDepositAndRent(value) {
    const match = value.match(/([\d,]+)\/([\d,]+)/);
    if (match) {
        let deposit = parseInt(match[1].replace(/,/g, ""), 10) * 10000; // 보증금 변환 (만원 → 원)
        let rent = parseInt(match[2].replace(/,/g, ""), 10) * 10000; // 월세 변환 (만원 → 원)
        return { deposit, rent };
    }
    return { deposit: 0, rent: 0 };
}

// 월세 보증금 최소/평균/최대 구하기
function calculateStats(data) {
    const deposits = data.map(item => calculateDepositAndRent(item.가격).deposit);
    const rents = data.map(item => calculateDepositAndRent(item.가격).rent);

    return {
        minDeposit: Math.min(...deposits) / 10000, // 만 단위 변환
        avgDeposit: Math.round(deposits.reduce((a, b) => a + b, 0) / deposits.length) / 10000,
        maxDeposit: Math.max(...deposits) / 10000,

        minRent: Math.min(...rents) / 1000, // 천 단위 변환
        avgRent: Math.round(rents.reduce((a, b) => a + b, 0) / rents.length) / 1000, // 천 단위 변환
        maxRent: Math.max(...rents) / 1000,
    };
}

// 95/72m², 2/5층, 남서향 분석처리
function parsePropertyData(entry) {
	console.log("== parsePropertyData: "  + entry);
    const parts = entry.split(", ");

    // 면적 추출 및 변환
    const [saleArea, exclusiveArea] = parts[0].split("/").map(num => parseInt(num));
    const exclusiveAreaPyeong = (exclusiveArea * 0.3025).toFixed(1);

	 // 층 정보 추출 및 변환
    // 층 정보 추출 및 변환
    const floorMatch = parts.length > 1 ? parts[1].match(/([가-힣]*)\/?(\d+)?\/(\d+)/) : null;
    if (!floorMatch) {
        console.error(`Invalid floor format: ${parts[1] || "N/A"}`);
        return { error: "Invalid floor format" };
    }
	console.log("== floorMatch: "  + floorMatch);
    let floorCategory = floorMatch[1] || ""; // null 방지
    let tfloor = parseInt(floorMatch[3] || "1", 10);
    let cfloor;
	console.log("== floorCategory: "  + floorMatch);

    function getRandomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }
	//
    // B1, B2 같은 경우 음수 층으로 변환
    if (/B\d+/.test(floorCategory)) {
        cfloor = -parseInt(floorCategory.replace("B", ""), 10);
    } else if (floorCategory === "저") {
        cfloor = getRandomInt(1, 2);
    } else if (floorCategory === "중") {
        cfloor = getRandomInt(Math.floor(tfloor / 3), Math.ceil(tfloor / 2));
    } else if (floorCategory === "상" || floorCategory === "고") {
        cfloor = getRandomInt(Math.ceil(tfloor / 2) + 1, tfloor);
    } else {
        cfloor = parseInt(floorMatch[2], 10);
    }

    // 방향 추출
    const direction = parts[2];

    return {
        saleArea,
        exclusiveArea,
        exclusiveAreaPyeong,
        cfloor,
        tfloor,
        direction
    };
}

// 빌라적용 프로퍼티
function villaPropertyInfo() {

	// 기본 컨트롤 박스 넣기
	const onoffPanel = document.querySelector('.filter_area');
	onoffPanel.style.display = 'inline-block'; // 줄 바꿈 방지

	//==== 아래부문은 공통으로 사용가능할듯..
	if (!onoffPanel.dataset.highlighted) {

		// 프로그램모드 on/off 버튼 생성
		const modeText4 = document.createElement('span');
		modeText4.textContent = '빌라프로그램';
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
		realSearchData();

		// 수익율 분석표
		//profitAnalData();
	}

	//========= 리스트 스크롤 데이타 설정 ===================
	if (onoffstatus == true) {

		// 연속모드인지 확인하고 아니면 pass
			propertyData = [];
		if (contiStatus == false) {
			propertyData2 = [];
			tableData1 = []; // 월세 테이블 만들 데이터 { key: data, key2: data2} 형식으로 저장
			tableData2 = []; // 매매테이블 만들 데이터 - 필요하면 작성
			tableData3 = []; // 전세테이블 만들 데이터 - 필요하면 작성
			datalength1 = 0;
			datalength2 = 0;
			datalength3 = 0;
			//
			// 테이블 복제처리
			tableData1_copy = [];
			tableData2_copy = [];
			tableData3_copy = [];
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
		// console.log('propertyItems 불러옴',propertyItems);

		if (propertyItems != oldItems && propertyItems.length > 0) {

			propertyItems.forEach((item) => {
				// 매매, 월세 유형으로 추출하기
				item.style.padding = '5px'; // 간격 줄여주기
				const typeElement = item.querySelector('.type'); // 매매, 월세, 유형정보
				const type = typeElement.textContent.trim(); //텍스트로만 추출하기

				// 금액정보 찾아내기
				const priceElement = item.querySelector('.price'); // 금액정보
				const priceValueString = priceElement.textContent.trim();
				//console.log('== priceVlaueString: ' + priceValueString);
				//
				let totalPrice = 0;
				let deposit = 0;
				let rent = 0;
				if (priceValueString.includes("/")) {
					const result = extractDepositAndRent(priceValueString);
					console.log(`보증금: ${result.deposit}, 월세: ${result.rent}`);
					deposit = result.deposit;
					rent = result.rent;
				} else {
					totalPrice = convertToEokNumber(priceValueString);
					//console.log(`금액: ${totalPrice}`);
				}

				//전용면적 찾아내기
				const areaElement = item.querySelector('.spec'); // 상가,면적, 층수, 향, 기타설명
				const infodata = areaElement.textContent.trim();
				console.log("=== area infodata: " + infodata);
				//
				const parsedData = parsePropertyData(infodata);
				const cfloor = parsedData.cfloor; // 매물층
				const tfloor = parsedData.tfloor; // 전체층
				const direction = parsedData.direction;
				const areas = parsedData.exclusiveAreaPyeong;

				console.log('cfloor:', cfloor, ', tfloor:', tfloor);
				/*
				const info = infodata.split(',').map(part => part.trim());

				// 첫 번째 항목에서 /와 m² 사이의 숫자 추출
				const firstPart = info[0];
				const areaMatch = firstPart ? firstPart.match(/(\d+)m²/) : null;
				// const areaMatch = firstPart ? firstPart.match(/\/(\d+)m²/) : null;

				const areas2 = areaMatch ? parseInt(areaMatch[1], 10) : null; // 전용면적, 잘 찾아짐
				let areas = areas2 * 0.3025 ; // 전용면적(평변환)
				const areas3 = areas.toFixed(2);
				// 전용면적 잘 찾아짐 but 토지는 안찾아짐 console.log(areas);

				// 층수 찾아내기
				const secondPart = info[1];
				//console.log('villa secondPart = ' + secondPart);

				const floorMatch = secondPart ? secondPart.match(/(\d+)\/(\d+)층/) : null;
				const cfloor = floorMatch ? floorMatch [1] : null; // 매물층
				const tfloor = floorMatch ? floorMatch [2] : null; // 전체층

				console.log('cfloor:', cfloor, ', tfloor:', tfloor);

				// 향 찾아내기
				const direction = info[2] !== undefined ? info[2] : '';
				*/

				if (areas > 0) {
					if (type == '월세') {
						//
						// 월세 매매가 환산 => 보증금 * (월세 * 200)
						let salePrice = deposit + (rent * 200);
						// 평단가 계산
						let pdanga = (rent / areas) / 10000;
						// 보증금 및 월셰저장
						let depositRent = (deposit/10000).toFixed(0) + '/' + (rent/10000).toFixed(0);

						pdanga = parseFloat(pdanga.toFixed(2)); // 소수점 2자리까지만 구하고 숫자로 변환
						// 억단이 변환처리
						let salePriceEok = formatToEok(salePrice);

						// 월세 정보를 붉은색으로 표시
						if (!priceElement.dataset.highlighted) {

							const priceSpan = document.createElement('span');
							priceSpan.textContent = `(${areas}평 @${pdanga}만`;
							priceSpan.style.opacity = 0.5; // 50% opacity
							priceSpan.style.color = 'red';
							priceSpan.style.fontSize = '11pt';

							const priceSpan2 = document.createElement('span');
							priceSpan2.textContent = `  >>${salePriceEok}억)`;
							priceSpan2.style.opacity = 0.5; // 50% opacity
							priceSpan2.style.color = 'violet';
							priceSpan2.style.fontSize = '13pt';

							priceElement.appendChild(priceSpan);
							priceElement.appendChild(priceSpan2);


							// push함수를 사용하여 평단가를 목록으로 만들기
							propertyData.push(pdanga);
							//let tabletext = `${info[1]}, ${direction}, ${pdanga}만/평, ${areas3}평, ${salePrice}`;
							// console.log(tabletext);
							priceElement.dataset.highlighted = true; // 한 번만 실행되도록 표시
						}
						// 테이블에 넣기
						const tableitem = { 구분: type, 해당층: cfloor, 전체층: tfloor, 향: direction, 평당가: pdanga, 전용면적: areas, 가격: depositRent };

						//데이터를 배열화
						tableData1.push(tableitem);

						// 테이블 복제처리
						tableData1_copy = tableData1;
					}

					if (type == '매매') {
						let pdanga = parseInt((totalPrice / areas) / 10000);

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

						// 매매경우 5천이상만 거래표시되게
						if (parseInt(totalPrice) > 50000000) {
							// 테이블에 넣기
							const tableitem = { 구분: type, 해당층: cfloor, 전체층: tfloor, 향: direction, 평당가: pdanga, 전용면적: areas, 가격: totalPrice };

							//데이터를 배열화
							tableData2.push(tableitem);

							// 테이블 복제처리
							tableData2_copy = tableData2;
						}
					}
					//===========================================================
					if (type == '전세') {
						let pdanga = parseInt((totalPrice / areas) / 10000);

						// 전세경우 3천이상만 거래표시되게
						if (parseInt(totalPrice) > 30000000) {
							// 테이블에 넣기
							const tableitem = { 구분: type, 해당층: cfloor, 전체층: tfloor, 향: direction, 평당가: pdanga, 전용면적: areas, 가격: totalPrice };
							//데이터를 배열화
							tableData3.push(tableitem);

							// 테이블 복제처리
							tableData3_copy = tableData3;
						}
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
				newBox.style.height = '90px';
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
				newBox.style.marginBottom = '5px'; // 밑으로 마진 5px 추가

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
				profitText.textContent = '|수익(' + percentMargin.toFixed(1) + '%)';
				profitText.style.marginLeft = '0px'; // 텍스트앞 여백 조절
				profitText.style.marginRight = '20px'

				// const ptextBox = document.createElement('input'); // textarea 대신 input 요소 사용
				// ptextBox.type = 'number';
				// ptextBox.value = percentMargin.toFixed(1);
				// ptextBox.style.width = '40px';
				// ptextBox.style.height = '20px';
				// ptextBox.style.resize = 'none'
				// ptextBox.style.fontSize = '10pt'; // 글자 크기 설정
				// ptextBox.style.border = '1px solid #333333'; // 테두리 설정
				// ptextBox.step = '0.1'; // 소숫점 한자리까지 입력받기
				//
				// // input 값이 변경될 때 percentMargin 변수에 값을 다시 넣기
				// ptextBox.addEventListener('input', function() {
				// 	percentMargin = ptextBox.value;
				// 	console.log('Updated percentMargin:', percentMargin); // 값이 업데이트된 것을 확인하기 위해 콘솔에 출력
				// });

				newBox.appendChild(profitText);
				//newBox.appendChild(ptextBox);
				//===========
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
						tableData3 = tableData3_copy;

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
						newBox2.appendChild(closeButton);
											// 테이블 생성

						// 요약테이블 생성
						summaryAptVillaAndDisplayTable();

						/// 리스트 테이블 목록구조 정의 =========
						listAndDisplayTable();


						// 박스2 생성
						mapWrap.appendChild(newBox2);

						tableshowstatus = true;
					}

				}); // end if

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
					datalength3 = 0;
					textBox.placeholder = '초기화 완료, 데이터 대기중';
					//
					// 테이블 복제처리 초기화
					tableData1_copy = [];
					tableData2_copy = [];
					tableData3_copy = [];
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
				textBox.style.height = '70px';
				textBox.style.resize = 'none'
				textBox.placeholder = '데이터 준비중'
				textBox.style.fontSize = '10pt'; // 글자 크기 설정
				textBox.style.fontWeight = 'bold'; // 굵은 글씨체 설정
				textBox.style.marginLeft = '15px';
				textBox.style.marginTop = '5px';
				textBox.readOnly = true;			// readonly 설정

				newBox.appendChild(textBox);
				// 텍스트 박스 생성 마지막

				// .map_wrap 내부에 새로운 박스 추가
				mapWrap.appendChild(newBox);
			}

			// 새창에 최소최대값 넣기 + 표 업데이트 하기
			if (propertyData.length > datalength1 || propertyData2.length > datalength2 || propertyData3.length > datalength3) {

				// 월세 보증금 최소/평균/최대 구하기
				const result = calculateStats(tableData1);
				// console.log(`최소 보증금: ${result.minDeposit}만, 평균 보증금: ${result.avgDeposit}만, 최대 보증금: ${result.maxDeposit}만`);
				// console.log(`최소 월세: ${result.minRent}천, 평균 월세: ${result.avgRent}천, 최대 월세: ${result.maxRent}천`);
				// 보증금

				// 결과 값이 Infinity이면 0으로 처리
				const safeValue = (value) => (isFinite(value) ? value : 0);

				// 보증금
				const minDeposit = safeValue(result.minDeposit) * 10000;
				const maxDeposit = safeValue(result.maxDeposit) * 10000;
				const avgDeposit = safeValue(result.avgDeposit) * 10000;

				// 월세
				const minRent = safeValue(result.minRent);
				const maxRent = safeValue(result.maxRent);
				const avgRent = safeValue(result.avgRent);

				const minValue = formatToEok(minDeposit.toFixed(0)) + '억/' + minRent.toFixed(0) ;
				const maxValue = formatToEok(maxDeposit.toFixed(0)) + '억/' + maxRent.toFixed(0);
				const avgValue = formatToEok(avgDeposit.toFixed(0)) + '억/' + avgRent.toFixed();

				// 매매: 건수, 최소, 평균, 최대
				const tableDanga2 = tableData2.map(item => item.가격);
				const maxValue2 = Math.max(...tableDanga2);
				const minValue2 = Math.min(...tableDanga2);
				const avgValue2 = tableDanga2.reduce((sum, value) => sum + value, 0) / tableDanga2.length; //평균 구하기

				// 전세: 건수, 최소, 평균, 최대
				const tableDanga3 = tableData3.map(item => item.가격);
				const maxValue3 = Math.max(...tableDanga3);
				const minValue3 = Math.min(...tableDanga3);
				const avgValue3 = tableDanga3.reduce((sum, value) => sum + value, 0) / tableDanga3.length; //평균 구하기

				// 월세 억단위변환
				const maxValue_Eok = maxValue;
				const minValue_Eok = minValue;
				const avgValue_Eok = avgValue;

				// 매매 억단위변환
				const maxValue2_Eok = (!maxValue2 || !isFinite(maxValue2)) ? "0억" : formatToEok(maxValue2) + "억";
				const minValue2_Eok = (!minValue2 || !isFinite(minValue2)) ? "0억" : formatToEok(minValue2) + "억";
				const avgValue2_Eok = (!avgValue2 || !isFinite(avgValue2)) ? "0억" : formatToEok(avgValue2) + "억";

				// 전세 억단위변환
				const maxValue3_Eok = (!maxValue3 || !isFinite(maxValue3)) ? "0억" : formatToEok(maxValue3) + "억";
				const minValue3_Eok = (!minValue3 || !isFinite(minValue3)) ? "0억" : formatToEok(minValue3) + "억";
				const avgValue3_Eok = (!avgValue3 || !isFinite(avgValue3)) ? "0억" : formatToEok(avgValue3) + "억";

				const textBox = document.querySelector('textarea'); // .map_wrap 클래스를 가진 요소 선택
				//textBox.placeholder = `[월세 ${tableData1.length}건] 최소 : ${minValue_Eok}, 평균: ${avgValue_Eok}, 최대 : ${maxValue_Eok}\n[전세 ${tableDanga3.length}건] 최소 : ${minValue3_Eok}, 평균: ${avgValue3_Eok}, 최대 : ${maxValue3_Eok}\n[매매 ${tableDanga2.length}건] 최소 : ${minValue2_Eok}, 평균: ${avgValue2_Eok}, 최대 : ${maxValue2_Eok}\n`;
				textBox.placeholder = `[월세 ${tableData1.length}건]최소:${minValue_Eok},평균:${avgValue_Eok},최대:${maxValue_Eok}\n[전세 ${tableDanga3.length}건] 최소 : ${minValue3_Eok}, 평균: ${avgValue3_Eok}, 최대 : ${maxValue3_Eok}\n[매매 ${tableDanga2.length}건] 최소 : ${minValue2_Eok}, 평균: ${avgValue2_Eok}, 최대 : ${maxValue2_Eok}\n`;

				datalength1 = propertyData.length;
				datalength2 = propertyData2.length;
				datalength3 = propertyData3.length;

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

					console.log('=====빌라층선택처리2222 =====');
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
					newBox2.appendChild(closeButton);

					// 요약테이블 생성
					summaryAptVillaAndDisplayTable();

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

// 키위-모바일
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

			console.log('=====층선택처리3333 =====');
			selectedAndDisplay();

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

// 옥션원 목록조회아이템 적용
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
	const propertyItems = document.querySelectorAll("#list_body div[id^='tr']");
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

// 탱크옥션처리시 사용할거
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
			labelItem.removsummaryInfoe();
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
	// 아파트 tab1, 빌라,주택 tab2, 원룸 tab3, 상가,창고 tab4
	/*
	<a href="javascript:void(0);" class="lnb_item" role="tab" aria-selected="true" aria-controls="tab4" data-nclk="LNB.shop"><span class="lnb_item_line"><em class="text">상가</em><em class="text">업무</em><em class="text">공장</em><em class="text">토지</em></span></a>
	 */
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

	// 아실연동 -- 실패
	if (window.location.href.startsWith('https://asil.kr/asil/index.jsp')) {
		console.log('asilcon 실행');
		asilCon();
	}

});
