// content.js
let propertyData = [];
let propertyData2 = [];
let tableData1 = []; // 월세 테이블 만들 데이터 { key: data, key2: data2} 형식으로 저장
let tableData2 = []; // 매매테이블 만들 데이터
let newBox2;
let datalength1 = 0;
let datalength2 = 0;
let tableshowstatus = false;
let contiStatus = false;
let floorsorting = true;
let percentMargin = 6.5;
let oldItems;


let timeout; // 타이머를 저장할 변수
let isScheduled = false; // 함수 호출이 예약되었는지 여부를 나타내는 플래그


function extractInfoM() {
	console.log('작업시작');
	const propertyItems = document.querySelectorAll('.item_inner'); // 항목 선택
	console.log(propertyItems);

	const mapWrap = document.querySelector('#_root');
	
	if (propertyItems != oldItems &&propertyItems.length > 0) {
		// 업데이트이므로 데이터 한번 초기화하기
		propertyData2 = [];
		tableData1 = []; // 월세 테이블 만들 데이터 { key: data, key2: data2} 형식으로 저장
		tableData2 = []; // 매매테이블 만들 데이터 - 필요하면 작성
		datalength1 = 0;
		datalength2 = 0;
		
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
			const cleanedPrice = price.replace(/~.*$/, ''); // ~ 이후 문자 삭제
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


						// 테이블에 넣기 
						const tableitem = { 구분: type, 해당층: cfloor, 전체층: tfloor, 향: direction, 평당가: pdanga, 전용면적: areas3, 가격: cleanedPrice };
						
						//데이터를 배열화
						tableData1.push(tableitem);
					}
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
						
						// 테이블에 넣기 
						const cleanedPrice = price.replace(/~.*$/, ''); // ~ 이후 문자 삭제
						const tableitem = { 구분: type, 해당층: cfloor, 전체층: tfloor, 향: direction, 평당가: pdanga, 전용면적: areas3, 가격: cleanedPrice};
						//데이터를 배열화
						tableData2.push(tableitem);	
					}
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
			console.log('작동여부 확인');
			newBox2.parentNode.removeChild(newBox2);
			
			console.log('tabledata:', tableData1);
			newBox2 = document.createElement('div'); // 새로운 박스 요소 생성
			newBox2.classList.add('new-box2'); // 필요한 클래스 추가 (예: .new-box)

			// 크기 설정
			newBox2.style.width = '390px';
			//newBox2.style.height = '580px';
			newBox2.style.height = '180px';
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

				// tbody가 스크롤 가능하도록 CSS 추가
				tbody.style.overflowY = 'auto';


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
					// 자동 스크롤 처리
					tbody.scrollTop = tbody.scrollHeight;
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
					// 자동 스크롤 처리
					tbody.scrollTop = tbody.scrollHeight;
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
				newBox2.parentNode.removeChild(newBox2);
				tableshowstatus = false;
				console.log(tableshowstatus, '여닫기 버튼 작동 - 표닫기');

			} else {
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

	// item_area _Listitem

	// div 요소들끼리 정리하는 부분
	const propertyLists = document.querySelectorAll('.item_area._Listitem'); // 'is-loading' 클래스를 제외한 요소 선택
	const divs = Array.from(propertyLists); // 어레이에 맞게 정렬


	if(divs.length >0) { // 요소가 존재하는지 확인
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

		const container = propertyLists[0].parentElement;
		container.innerHTML = ''; // 부모 요소 비우기

		divs.forEach(div => {
			container.appendChild(div);
		});
	} else {
		console.log('no elements sorted');
	}

}

// 시작부터 너무 많이 반복됨
function observeMutationM() {
    const targetNode = document.querySelector('.map_fixed_area_inner._inner'); // 감시할 노드 선택
    const config = { childList: true, subtree: true }; // 감시할 변경 유형 설정

    const callback = function(mutationsList, observer) {
        if (!isScheduled) {
            isScheduled = true;
			observer.disconnect(); // 함수실행중 감시 중단
			extractInfoM(); // 함수 실행
			observer.observe(targetNode, config); // 감시 재개				
			isScheduled = false; // 플래그 초기화
        }
    };

    const observer = new MutationObserver(callback);
    observer.observe(targetNode, config);
}

function observeAuctM() {
    const targetNode = document.querySelector('#list_body'); // 감시할 노드 선택
    const config = { childList: true, subtree: true }; // 감시할 변경 유형 설정

    const callback = function(mutationsList, observer) {
        if (!isScheduled) {
            isScheduled = true;
			observer.disconnect(); // 함수실행중 감시 중단
			auctiononeM(); // 함수 실행
			observer.observe(targetNode, config); // 감시 재개				
			isScheduled = false; // 플래그 초기화
        }
    };

    const observer = new MutationObserver(callback);
    observer.observe(targetNode, config);
}

// 옥션원 모바일 즐겨찾기 적용 시작
function auctiononeM()  {
	const propertyItems = document.querySelectorAll('#list_body table.tbl_noline_s');
	console.log('propertyItems', propertyItems);
	
	// 각 항목별로 실행하기
	if (propertyItems) {
		propertyItems.forEach(item => {
			console.log('item', item);
			const areaElement = item.querySelector('tr:nth-of-type(4)'); // 네번째 TR 선택하기
			const areaElement2 = areaElement.textContent.trim().split('/');
			
			// 면적뽑아내기
			let areaPy
			if (areaElement2.length > 0) {
				console.log(areaElement2);
				matches = areaElement2.map(item => {
					const match = item.match(/(\d+\.?\d*)평/); // 소수점 포함 숫자 추출
					return match ? match[1] : null; // ['37.4', '19']로 반환됨
				}).filter(value => value !== null);
				areaPy = matches [0]; // 전용 면적을 입력하기
			}
			
			// 면적이 있는 경우
			if (areaPy) {
				console.log('면적(평)', areaPy);
				// 감정가 구하기
				const price1Element = item.querySelector('table td[id^="auct_jprice_"]');
				const price1Text = price1Element.textContent.trim().replace(/[^\d]/g, '');
				const price1num = parseInt(price1Text);
				console.log(price1num);
				const pydanga1 = parseInt(price1num / (areaPy * 10000)); // 평단가 계산

				// 평당가 추가하기
				const pydanga1Span = document.createElement('span');
				pydanga1Span.textContent = `@${pydanga1}만원`;
				pydanga1Span.style.opacity = 0.5; // 50% opacity
				pydanga1Span.style.color = 'grey';				
				
				price1Element.appendChild(pydanga1Span);

				
				// 두번째 가격 구하기 
				const price2Element = item.querySelector('table table tr:nth-of-type(2) td');
				console.log(price2Element);
				const price2Text = price2Element.textContent.trim().replace(/[^\d]/g, '');
				const price2Num = parseInt(price2Text);
				console.log(price2Num);
				const pydanga2 = parseInt(price2Num / (areaPy * 10000)); // 평단가 계산

				// 평당가 추가하기
				const pydanga2Span = document.createElement('span');
				pydanga2Span.textContent = `@${pydanga2}만원`;
				pydanga2Span.style.opacity = 0.5; // 50% opacity
				pydanga2Span.style.color = 'blue';				
				
				price2Element.appendChild(pydanga2Span);

			
			}
		});
	}
	// 각 항목별로 실행하기 끝
}
// 옥션원 모바일 적용 끝.


// 옥션원 모바일 검색 적용 시작
		
function auctionMsearch() {
	const propertyItems = document.querySelectorAll('#list_body tr[id^="list_tr"]');
	console.log('propertyItems', propertyItems);
	
	// 각 항목별로 실행하기
	if (propertyItems) {
		propertyItems.forEach(item => {
			console.log('item', item);
			const areaElement = item.querySelector('div:nth-of-type(5) div'); // 네번째 TR 선택하기
			console.log('areaElement', areaElement)
			const areaElement2 = areaElement.textContent.trim().split(',');
			
			// 면적뽑아내기
			let areaPy
			if (areaElement2.length > 0) {
				console.log(areaElement2);
				matches = areaElement2.map(item => {
					const match = item.match(/(\d+\.?\d*)평/); // 소수점 포함 숫자 추출
					return match ? match[1] : null; // ['37.4', '19']로 반환됨
				}).filter(value => value !== null);
				console.log(matches);
				
				if (matches.length >= 2){
					areaPy = matches [1]; // 전용 면적을 입력하기
				} else{
					areaPy = matches [0]; // 전용 면적을 입력하기
				}
			}
			
			// 면적이 있는 경우
			if (areaPy) {
				console.log('면적(평)', areaPy);
				// 감정가 구하기
				const price1Element = item.querySelector('span[id^="auct_jprice_"]');
				const price1Text = price1Element.textContent.trim().replace(/[^\d]/g, '');
				const price1num = parseInt(price1Text);
				console.log(price1num);
				const pydanga1 = parseInt(price1num / (areaPy * 10000)); // 평단가 계산

				// 평당가 추가하기
				const pydanga1Span = document.createElement('span');
				pydanga1Span.textContent = `@${pydanga1}만원`;
				pydanga1Span.style.opacity = 0.5; // 50% opacity
				pydanga1Span.style.color = 'grey';				
				
				price1Element.appendChild(pydanga1Span);

				
				// 두번째 가격 구하기 
				const price2Element = item.querySelector('span[id^="auct_bprice_"]');
				console.log(price2Element);
				const price2Text = price2Element.textContent.trim().replace(/[^\d]/g, '');
				const price2Num = parseInt(price2Text);
				console.log(price2Num);
				const pydanga2 = parseInt(price2Num / (areaPy * 10000)); // 평단가 계산


				// 평당가 추가하기
				const pydanga2Span = document.createElement('span');
				pydanga2Span.textContent = `@${pydanga2}만원`;
				pydanga2Span.style.opacity = 0.5; // 50% opacity
				pydanga2Span.style.color = 'blue';				
				
				price2Element.appendChild(pydanga2Span);
			}
		});
	}
	// 각 항목별로 실행하기 끝
}
// 옥션원 모바일 검색 적용 끝



function auctionMdetail() {
	console.log('모바일 세부항목 평단가 적용');
	let areaPy
	moneyItems = document.querySelector('.auct_money.clear');
	console.log(moneyItems);

	// 면적 산출하기
	if (moneyItems) {
		const areaElement = moneyItems.nextElementSibling;
		console.log ('area Element', areaElement);
		
		const headerCells = areaElement.querySelectorAll('th');
		for (const headerCell of headerCells) {
			if (headerCell.textContent.includes('토지')) {
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
			if (headerCell.textContent.includes('건물')) {
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
	}
	// 면적 산출 끝

	// 면적이 있는 경우
	if (areaPy !=0) {
		console.log('면적(평)', areaPy);
		const moneyItems2 = moneyItems.querySelectorAll('dt, dd');
		
		for (const item of moneyItems2) {
			//감정가 구하기
			if (item.textContent.includes('감정가')) {
				const price1Element = item.nextElementSibling;
				const price1Text = price1Element.textContent.trim().replace(/[^\d]/g, '');
				const price1num = parseInt(price1Text);
				console.log(price1num);
				const pydanga1 = parseInt(price1num / (areaPy * 10000)); // 평단가 계산

				// 평당가 추가하기
				const pydanga1Span = document.createElement('span');
				pydanga1Span.textContent = `@${pydanga1}만원`;
				pydanga1Span.style.opacity = 0.5; // 50% opacity
				pydanga1Span.style.color = 'grey';				
				
				price1Element.appendChild(pydanga1Span);
			}

			// 최저가 구하기
			if (item.textContent.includes('최저가')) {
				const price2Element = item.nextElementSibling;
				let price2Text = price2Element.textContent.trim()
				price2Text = price2Text.replace(/\([^\)]*\)/g, ''); // 괄호 및 그 안의 내용 제거
				price2Text = price2Text.replace(/[^\d]/g, ''); // 쉼표와 공백 제거
				const price2Num = parseInt(price2Text);
				console.log(price2Num);
				const pydanga2 = parseInt(price2Num / (areaPy * 10000)); // 평단가 계산

				// 평당가 추가하기
				const pydanga2Span = document.createElement('span');
				pydanga2Span.textContent = `@${pydanga2}만원`;
				pydanga2Span.style.opacity = 0.5; // 50% opacity
				pydanga2Span.style.color = 'blue';				
				
				price2Element.appendChild(pydanga2Span);
			}
		}
	}	
}



// 페이지가 로드되면 실행
window.addEventListener('load', function() {
	// 네이버 모바일 적용
	if (window.location.href.startsWith('https://m.land.naver.com/map')) {
		extractInfoM();
		setTimeout(observeMutationM, 100); //DOM 변경 감시 시작
	}

	// 옥션원 모바일 즐겨찾기 적용
	if (window.location.href.startsWith('https://m.auction1.co.kr/member/inter_list.php')) {
		console.log('즐겨찾기 평단가 계산기 작동');
		auctiononeM();
		setTimeout(observeAuctM(), 100);
	}	

	// 옥션원 모바일 검색 적용
	if (window.location.href.startsWith('https://m.auction1.co.kr/auction/ca_list.php')) {
		console.log('검색 평단가 계산기 작동');
		auctionMsearch();
	}	

	// 옥션원 모바일 검색 적용
	if (window.location.href.startsWith('https://m.auction1.co.kr/auction/ca_view_mb.php')) {
		console.log('세부항목 평단가 계산기 작동');
		auctionMdetail();
	}	
});