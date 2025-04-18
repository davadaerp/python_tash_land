// VxHttp.js
// jQuery.ajax()를 사용하여 HTTP 요청을 처리하는 모듈

const VxHttp = (function () {
  // null이나 undefined인 파라미터를 제거하는 함수
  function removeNullParams(params) {
    if (params == null) return null;
    const data = {};
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        data[key] = value;
      }
    });
    return data;
  }

  // 간단한 오류 처리 함수 (필요에 따라 alert() 대신 다른 UI 처리 가능)
  function doErrorHandler(err) {
    const response = err.response || { status: 900 };
    switch (response.status) {
      case 400:
        alert('요청이 유효하지 않습니다.');
        break;
      case 401:
        alert('인증정보가 유효하지 않습니다. 로그인 페이지로 이동합니다.');
        window.location.href = '/login';
        break;
      case 403:
        alert('권한이 올바르지 않습니다.');
        break;
      case 404:
        alert('요청이 올바르지 않습니다.');
        break;
      case 500:
        alert('처리 중 오류가 발생하였습니다.');
        break;
      case 900:
        alert('스크립트 오류가 발생하였습니다.');
        break;
      default:
        alert('서버에 알 수 없는 오류가 발생하였습니다.');
        break;
    }
  }

  // 내부: HTTP 요청을 수행하는 함수
  function execute(method, url, data, options = {}) {
    data = removeNullParams(data);
    return new Promise(function (resolve, reject) {
      // GET/DELETE 요청은 data를 query string으로, 나머지는 JSON payload로 처리
      let ajaxData = (method.toLowerCase() === 'get' || method.toLowerCase() === 'delete')
        ? data
        : JSON.stringify(data);

      // 기본 헤더 설정 (토큰은 localStorage에서 가져옴)
      let headers = {
        'Access-Control-Allow-Origin': '*',
        'userType': 'ADM',
        'Auth-Key': localStorage.getItem('logToken') || ''
      };

      // 옵션에 추가 헤더가 있으면 병합
      if (options.headers) {
        headers = Object.assign(headers, options.headers);
      }

      $.ajax({
        url: url,
        type: method.toUpperCase(),
        data: ajaxData,
        headers: headers,
        dataType: 'json',
        timeout: options.timeout || 0,
        contentType: (method.toLowerCase() === 'get' || method.toLowerCase() === 'delete')
          ? 'application/x-www-form-urlencoded; charset=UTF-8'
          : 'application/json; charset=UTF-8'
      })
        .done(function (response, textStatus, jqXHR) {
          // 만약 응답 데이터에 새 토큰(authKey)이 있으면 localStorage에 저장
          if (response && response.authKey) {
            localStorage.setItem('logToken', response.authKey);
          }
          // 여기서는 HTTP status가 200인 경우 정상으로 처리
          if (jqXHR.status === 200) {
            resolve(response);
          } else {
            reject(response);
          }
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
          doErrorHandler({ response: jqXHR });
          reject(jqXHR);
        });
    });
  }

  // 파일 업로드를 처리하는 함수 (FormData 사용)
  function upload(method, url, data) {
    const formData = new FormData();
    for (const [key, value] of Object.entries(data)) {
      if (value !== null) {
        formData.append(key, value);
      }
    }
    return new Promise(function (resolve, reject) {
      $.ajax({
        url: url,
        type: method.toUpperCase(),
        data: formData,
        processData: false,
        contentType: false,
        headers: {
          'Auth-Key': localStorage.getItem('logToken') || '',
          'Access-Control-Allow-Origin': '*',
          'userType': 'ADM'
        },
        dataType: 'json'
      })
        .done(function (response) {
          if (response && response.authKey) {
            localStorage.setItem('logToken', response.authKey);
          }
          resolve(response);
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
          doErrorHandler({ response: jqXHR });
          reject(jqXHR);
        });
    });
  }

  // 파일 다운로드 (또는 blob 데이터) 처리 함수
  function download(method, url, data, options) {
    return new Promise(function (resolve) {
      $.ajax({
        url: url,
        type: method.toUpperCase(),
        data: (method.toLowerCase() === 'get' || method.toLowerCase() === 'delete')
          ? data
          : JSON.stringify(data),
        headers: {
          'Auth-Key': localStorage.getItem('logToken') || '',
          'Access-Control-Allow-Origin': '*',
          'userType': 'ADM'
        },
        dataType: 'blob'
      })
        .done(function (response) {
          resolve(response);
        })
        .fail(function (jqXHR) {
          resolve(jqXHR);
        });
    });
  }

  // Public API: jQuery.ajax()를 이용한 HTTP 메서드들
  return {
    get: (url, params = null, options) => execute('get', url, params, options),
    post: (url, data, options) => execute('post', url, data, options),
    put: (url, data, options) => execute('put', url, data, options),
    delete: (url, data, options) => execute('delete', url, data, options),
    postFile: (url, data) => upload('post', url, data),
    putFile: (url, data) => upload('put', url, data),
    postDownFile: (url, data, options) => download('post', url, data, options)
  };
})();

// 전역 객체에 할당하여 어디서든 사용 가능하게 함.
window.VxHttp = VxHttp;

// 예시 사용법:
// VxHttp.get('/endpoint', { key: 'value' })
//   .then(data => console.log('Data:', data))
//   .catch(error => console.error('Error:', error));
