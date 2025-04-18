// 전역 변수: 데이터베이스 이름과 버전
const dbName = "tashDatabase";
const dbVersion = 1; // 버전 번호

/**
 * IndexedDB 데이터베이스 열기 및 (필요한 경우) 오브젝트 스토어 생성
 * @param {string | string[]} storeNames - 단일 스토어 이름 또는 여러 개의 스토어 이름 배열
 * @returns {Promise<IDBDatabase>}
 */
function openDb(storeNames) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(dbName, dbVersion);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            const storeList = Array.isArray(storeNames) ? storeNames : [storeNames]; // 단일 값도 배열로 변환

            storeList.forEach((storeName) => {
                if (!db.objectStoreNames.contains(storeName)) {
                    console.log(`오브젝트 스토어 생성: ${storeName}`);
                    const objectStore = db.createObjectStore(storeName, { keyPath: 'id', autoIncrement: true });

                    // ✅ storeName에 맞는 인덱스 추가
                    if (storeName === 'kland_sanga') {
                        objectStore.createIndex('lawdCD_umdNm_kland_sanga', ['lawdCD', 'umdNm'], { unique: false });
                    } else if (storeName === 'kland_villa') {
                        objectStore.createIndex('lawdCD_umdNm_kland_villa', ['lawdCD', 'umdNm'], { unique: false });
                    } else if (storeName === 'auction_sanga') {
                        objectStore.createIndex('lawdCD_umdNm_auction_sanga', ['lawdCD', 'umdNm'], { unique: false });
                    } else if (storeName === 'crawl_sanga') {
                        objectStore.createIndex('lawdCD_umdNm_crawl_sanga', ['lawdCD', 'umdNm'], { unique: false });
                    }
                }
            });
        };

        request.onsuccess = (event) => {
            const db = event.target.result;
            const storeList = Array.isArray(storeNames) ? storeNames : [storeNames];

            // ✅ 모든 스토어가 존재하는지 확인
            const missingStores = storeList.filter(storeName => !db.objectStoreNames.contains(storeName));
            if (missingStores.length > 0) {
                console.error(`오브젝트 스토어 생성 실패: `);
                //reject(new Error(`오브젝트 스토어 생성 실패: ${missingStores.join(', ')}`));
                return;
            }

            console.log(`IndexedDB 오픈 성공: ${storeList.join(', ')}`);
            resolve(db);
        };

        request.onerror = (event) => {
            console.error("IndexedDB 열기 실패:", event.target.error);
            reject(event.target.error);
        };
    });
}

// function fetchData()에서 동기식에 순차적 처리시이용
async function checkDataExists(lawdCD, umdNm, currDate, storeName) {
    return new Promise(async (resolve, reject) => {
        try {
            const db = await openDb(storeName);
            const transaction = db.transaction([storeName], 'readwrite');
            const objectStore = transaction.objectStore(storeName);
            const index_name = 'lawdCD_umdNm_' + storeName;
            const index = objectStore.index(index_name);

            const keyRange = IDBKeyRange.bound([lawdCD, umdNm], [lawdCD, umdNm, '\uffff']);
            const request = index.openCursor(keyRange);

            request.onsuccess = function(event) {
                const cursor = event.target.result;
                if (cursor) {
                    const dataDate = new Date(cursor.value.ymd);
                    const currentDate = new Date(currDate);
                    const diffTime = currentDate - dataDate;
                    const diffDays = diffTime / (1000 * 60 * 60 * 24);

                    if (diffDays > 7) {
                        console.log(`데이터가 1주일 이상됨. 삭제 진행: ${cursor.value.ymd}`);
                        deleteOldData(lawdCD, umdNm, storeName).then(() => resolve(false)).catch(() => resolve(false));
                    } else {
                        console.log("데이터 있음. 1주일 안됨:", cursor.value);
                        resolve(true);
                    }
                } else {
                    console.log("데이터 없음");
                    resolve(false);
                }
            };

            request.onerror = function() {
                console.error("IndexedDB 데이터 조회 중 오류 발생");
                resolve(false);
            };
        } catch (error) {
            console.error("IndexedDB 접근 중 오류 발생", error);
            resolve(false);
        }
    });
}

// 특정 lawdCD, umdNm 조건의 데이터 전부 삭제하는 함수
async function deleteOldData(lawdCD, umdNm, storeName, callback) {
    const db = await openDb(storeName);
    const transaction = db.transaction([storeName], 'readwrite');
    const objectStore = transaction.objectStore(storeName);
    const index_name = 'lawdCD_umdNm_' + storeName;
    const index = objectStore.index(index_name);

    const keyRange = IDBKeyRange.bound([lawdCD, umdNm], [lawdCD, umdNm, '\uffff']);
    const request = index.openCursor(keyRange);

    request.onsuccess = function(event) {
        const cursor = event.target.result;
        if (cursor) {
            console.log("삭제 중:", cursor.value);
            objectStore.delete(cursor.primaryKey); // 데이터 삭제
            cursor.continue(); // 다음 데이터 삭제 진행
        } else {
            console.log("모든 오래된 데이터 삭제 완료");
            callback(false); // 데이터 삭제 후 false 반환
        }
    };

    request.onerror = function() {
        console.error("IndexedDB 데이터 삭제 중 오류 발생");
        callback(false);
    };
}

/**
 * 여러 항목 추가 (배열로 전달)
 * @param {Array<Object>} items - 저장할 객체 배열
 * @param {string} storeName - 저장할 오브젝트 스토어 이름
 */
async function addItems(items, storeName) {
  try {
    const db = await openDb(storeName);
    const transaction = db.transaction(storeName, "readwrite");
    const store = transaction.objectStore(storeName);

    items.forEach(item => {
      // item 객체에 id 속성이 없으면 autoIncrement가 자동 처리됨
      store.put(item);
    });

    return new Promise((resolve, reject) => {
      transaction.oncomplete = function() {
        resolve("Items added successfully");
      };
      transaction.onerror = function(event) {
        reject(event.target.error);
      };
    });
  } catch (error) {
    console.error("Error adding items:", error);
  }
}

/**
 * 모든 데이터 조회 (특정 스토어)
 * @param {string} storeName - 조회할 오브젝트 스토어 이름
 */
/**
 * IndexedDB에서 특정 lawdCd, umdNm, ymd 값으로 데이터를 검색하여 반환
 * @param {string} lawdCd - 법정동 코드
 * @param {string} umdNm - 읍면동 명
 * @param {string} storeName - 검색할 IndexedDB의 Object Store 이름
 * @returns {Promise<Array>} - 검색된 데이터 배열
 */
async function getAllItems(lawdCd, umdNm, storeName) {
    try {
        const db = await openDb(storeName);
        const transaction = db.transaction(storeName, "readonly");
        const objectStore = transaction.objectStore(storeName);

        // ✅ 인덱스 설정
        const index_name = 'lawdCD_umdNm_' + storeName;
        // if (!objectStore.indexNames.contains(index_name)) {
        //     throw new Error(`인덱스 ${index_name}가 존재하지 않습니다.`);
        // }
        const index = objectStore.index(index_name);
        const keyRange = IDBKeyRange.bound([lawdCd, umdNm], [lawdCd, umdNm, '\uffff']); // 검색 범위 설정

        // ✅ 인덱스를 이용하여 데이터를 검색
        const results = [];
        const items = await new Promise((resolve, reject) => {
            const request = index.openCursor(keyRange);
            request.onsuccess = function (event) {
                const cursor = event.target.result;
                if (cursor) {
                    results.push(cursor.value);
                    cursor.continue(); // 다음 데이터 검색
                } else {
                    resolve(results); // 검색 완료 후 결과 반환
                }
            };
            request.onerror = function (event) {
                reject(event.target.error);
            };
        });

        return results; // 검색된 데이터 배열 반환
    } catch (error) {
        console.error("Error getting items:", error);
        return []; // 오류 발생 시 빈 배열 반환
    }
}


/**
 * 특정 조건을 만족하는 모든 데이터를 삭제하는 함수
 * @param {Function} conditionFn - 조건을 검사하는 함수 (item을 인자로 받아 true/false 반환)
 * @param {string} storeName - 삭제할 오브젝트 스토어 이름
 */
async function deleteAllItems(conditionFn, storeName) {
  try {
    const db = await openDb(storeName);
    const transaction = db.transaction(storeName, "readwrite");
    const store = transaction.objectStore(storeName);

    // 커서를 열어 모든 레코드를 순회하면서 조건 검사 후 삭제
    const request = store.openCursor();
    request.onsuccess = function(event) {
      const cursor = event.target.result;
      if (cursor) {
        if (conditionFn(cursor.value)) {
          cursor.delete();
        }
        cursor.continue();
      }
    };

    transaction.oncomplete = function() {
      console.log("조건에 맞는 모든 데이터 삭제 완료.");
    };

    transaction.onerror = function(event) {
      console.error("삭제 트랜잭션 오류:", event.target.error);
    };
  } catch (error) {
    console.error("데이터베이스 열기 실패:", error);
  }
}


/**
 * 레코드 추가 (입력)
 * @param {Object} record - 저장할 객체 (예: { article_no: "1234", trade_type: "매매", ... })
 * @param {string} storeName - 저장할 오브젝트 스토어 이름
 */
function addRecord(record, storeName) {
  return openDb(storeName).then(db => {
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, "readwrite");
      const store = transaction.objectStore(storeName);
      const request = store.add(record);

      request.onsuccess = () => {
        resolve(request.result); // 생성된 key(id) 반환
      };
      request.onerror = () => {
        reject(request.error);
      };
    });
  });
}

/**
 * 레코드 조회 (전체 조회)
 * @param {string} storeName - 조회할 오브젝트 스토어 이름
 */
function getRecords(storeName) {
  return openDb(storeName).then(db => {
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, "readonly");
      const store = transaction.objectStore(storeName);
      const request = store.getAll();

      request.onsuccess = () => {
        resolve(request.result);
      };
      request.onerror = () => {
        reject(request.error);
      };
    });
  });
}

/**
 * 레코드 수정 (업데이트)
 * @param {Object} record - 수정할 객체, 반드시 id 필드를 포함해야 함.
 * @param {string} storeName - 수정할 오브젝트 스토어 이름
 */
function updateRecord(record, storeName) {
  return openDb(storeName).then(db => {
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, "readwrite");
      const store = transaction.objectStore(storeName);
      const request = store.put(record); // put은 기존 id가 있으면 수정, 없으면 추가

      request.onsuccess = () => {
        resolve(request.result);
      };
      request.onerror = () => {
        reject(request.error);
      };
    });
  });
}

/**
 * 레코드 삭제
 * @param {number|string} id - 삭제할 레코드의 키 (id)
 * @param {string} storeName - 삭제할 오브젝트 스토어 이름
 */
function deleteRecord(id, storeName) {
  return openDb(storeName).then(db => {
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, "readwrite");
      const store = transaction.objectStore(storeName);
      const request = store.delete(id);

      request.onsuccess = () => {
        resolve();
      };
      request.onerror = () => {
        reject(request.error);
      };
    });
  });
}
//
//
// /* 사용 예시 */
// // 1. 레코드 추가
// addRecord({
//   article_no: "A001",
//   trade_type: "매매",
//   sggNm: "서울 강남구",
//   dealDate: "2025-03-15",
//   buildYear: "2010",
//   floor: "3",
//   buildingAr: "100",
//   buildingArPyeong: "30.3",
//   dealAmount: "1000000",
//   convertedDealAmount: "백만원",
//   jibun: "123-45",
//   landUse: "주거",
//   umdNm: "역삼동"
// }, "kland_sanga")
//   .then(id => {
//     console.log("레코드 추가 성공, id:", id);
//     return getRecords("kland_sanga");
//   })
//   .then(records => {
//     console.log("전체 레코드:", records);
//     // 2. 수정 예시: 첫번째 레코드의 건축년도 변경
//     if (records.length > 0) {
//       const firstRecord = records[0];
//       firstRecord.buildYear = "2012";
//       return updateRecord(firstRecord, "kland_sanga");
//     }
//   })
//   .then(() => {
//     return getRecords("kland_sanga");
//   })
//   .then(records => {
//     console.log("수정 후 전체 레코드:", records);
//     // 3. 삭제 예시: id가 1인 레코드 삭제
//     return deleteRecord(1, "kland_sanga");
//   })
//   .then(() => {
//     return getRecords("kland_sanga");
//   })
//   .then(records => {
//     console.log("삭제 후 전체 레코드:", records);
//   })
//   .catch(err => {
//     console.error("IndexedDB 에러:", err);
//   });
