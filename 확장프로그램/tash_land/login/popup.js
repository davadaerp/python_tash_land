
  //BASE_URL = 'http://192.168.45.167:8081';
  BASE_URL = 'https://erp-dev.bacchuserp.com';
  // 로그인 인증 요청 함수
  function login_auth() {
    $('#error-message').text('');
    const userid = document.getElementById("userid").value.trim();
    const password = document.getElementById("password").value.trim();
    if (!userid || !password) {
      $('#error-message').text("아이디와 비밀번호를 입력하세요.");
      return;
    }
    // base64 인코딩: "userid:password"
    const credential = btoa(userid + ":" + password);
    const cs = '7987f7cb05cb1992';
    const data = {
      credential: credential,
      grant_type: 'access_token',
      client_id: 'dp',
      client_secret: cs
    };
    $.ajax({
      url: BASE_URL + '/api/token',
      method: 'POST',
      headers: { "Content-Type": "application/json" },
      data: JSON.stringify(data),
      dataType: 'json',
      success: function(response) {
        const access_token = response.access_token;
        const apt_key = response.apt_key;
        const villa_key = response.villa_key;
        const sanga_key = response.sanga_key;
        localStorage.setItem("access_token", access_token.trim());
        // localStorage.setItem("apt_key", response.apt_key);
        // localStorage.setItem("villa_key", response.villa_key);
        // localStorage.setItem("sanga_key", response.sanga_key);
        //
        chrome.storage.local.set({
          access_token: access_token,
          apt_key: apt_key,
          villa_key: villa_key,
          sanga_key: sanga_key
        }, function() {
          console.log("✅ 여러 값이 저장되었습니다.");
        });
        //
        login(access_token);
      },
      error: function(xhr, status, error) {
        let errorMsg = '오류가 발생했습니다.';
        try {
          const responseJson = JSON.parse(xhr.responseText);
          if (responseJson.error) {
            errorMsg = responseJson.error;
          }
        } catch (e) {
          errorMsg += ' (서버 응답을 파싱할 수 없습니다)';
        }
        $('#error-message').text(errorMsg);
      }
    });
  }

  // 실제 로그인 처리 함수
  function login(access_token) {
    $.ajax({
      url: BASE_URL + '/api/login_token',
      method: 'GET',
      headers: { "Authorization": "Bearer " + access_token },
      success: function(response) {
        if (response.result == "Success") {
          // 로그인 성공 시, 로그인 섹션은 숨기고 로그인 상태 메시지 및 로그아웃 버튼은 보이게 처리
          $("#login-section").hide();
          $("#login-status").show();
          $("#logout-section").show();
        } else {
          $('#error-message').text(response.errmsg);
          //login_auth();
        }
      },
      error: function(xhr, status, error) {
        $('#error-message').text('오류가 발생했습니다: ' + error);
      }
    });
  }

  // 로그아웃 처리 함수
  function logout() {
    // localStorage에서 토큰 제거 등 로그아웃 처리
    localStorage.removeItem("access_token");
    chrome.storage.local.set({ access_token: "" }, function() {
      alert("로그아웃되었습니다.")
    });
    // 로그인 입력 영역 및 로그인 버튼 복원, 상태 메시지와 로그아웃 버튼 숨김
    $("#login-section").show();
    $("#login-status").hide();
    $("#logout-section").hide();
  }

  // window.onload에서 전역 함수를 호출합니다.
  window.onload = function() {
      const accessToken = localStorage.getItem("access_token");
      console.log('=== access_token: ', accessToken);
      if (accessToken === null || accessToken === '') {
        login_auth();
      } else {
        login(accessToken);
      }
  };

  // 로그아웃처리
  document.getElementById("logoutBtn").addEventListener("click", function () {
      logout();
  });

  // 폼 제출 시 로그인 요청 실행
  $(document).ready(function(){
    $('#login-form').submit(function(e) {
      e.preventDefault();
      login_auth();
    });
  });