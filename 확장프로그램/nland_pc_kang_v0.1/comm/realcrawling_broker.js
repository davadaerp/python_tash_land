
    window.allFetchedItems = [];
    let selectedLawdCd = "";
    let selectedUmdNm = "";
    let selectedIndex = -1;
    // 슬라이더 관련 변수
    let currentSlide = 0;
    let totalThumbnails = 0;
    const visibleCount = 4; // 기본 4개 보임

    function fetchData() {
      let searchTerm = $('#locatadd_nm').val();
      let dangiName = $('#aptNm').val();
      $('#loading').show();
      $('#noData').hide();
      $('table').hide();
      $.ajax({
        //url: 'http://192.168.45.167:8001/api/data',
        url: 'https://erp-dev.bacchuserp.com/api/data',
        method: 'GET',
        data: { lawdCd: selectedLawdCd, umdNm: selectedUmdNm, searchTerm: searchTerm, dangiName: dangiName },
        dataType: 'json',
        timeout: 5000,
        beforeSend: function () {
          $('#loading').show();
          $('#noData').hide();
          $('#errorMessage').hide();
          $('table').hide();
        },
        success: function (data) {
          $('#loading').hide();
          if (data.length === 0) {
            $('#noData').show();
            $('#errorMessage').hide();
          } else {
            $('#noData').hide();
            $('#errorMessage').hide();
            $('table').show();
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
        tableBody.append(`
          <tr>
            <td class="center-align"><input type="checkbox" class="row-checkbox"></td>
            <td class="center-align">${index}</td>
            <td class="center-align">${item.제목}</td>
            <td class="center-align">${item.대표자.replace(/\s/g, "")}</td>
            <td class="left-align">${item.주소명1.length > 30 ? item.주소명1.substring(0, 30) + '...' : item.주소명1}</td>
            <td class="center-align">${item.일반전화}</td>
            <td class="center-align">${item.휴대전화}</td>
            <td><button class="map-btn" data-map="${item.주소명1}">위치</button></td>
          </tr>
        `);
      });
      document.querySelectorAll('.map-btn').forEach(button => {
        button.addEventListener('click', function () {
          let address = this.getAttribute('data-map');
          openMap(address);
        });
      });
    }

    function updateThumbnailSlider() {
      const slider = document.querySelector('.thumbnail-list');
      if(slider) {
        slider.style.transform = `translateX(-${currentSlide * 85}px)`;
      }
    }

    document.addEventListener("DOMContentLoaded", function() {
      // #search-btn 클릭 이벤트
      document.getElementById('search-btn').addEventListener('click', function() {
        let searchTerm = document.getElementById('locatadd_nm').value.trim();
        if (!searchTerm) {
          alert("법정동명을 입력하세요.");
          document.getElementById('locatadd_nm').focus();
          return;
        }
        fetchData();
      });

      // #select-all 변경 이벤트
      document.getElementById('select-all').addEventListener('change', function() {
        let checked = this.checked;
        document.querySelectorAll('input.row-checkbox').forEach(function(checkbox) {
          checkbox.checked = checked;
        });
      });

      // #message-btn 클릭 이벤트
      document.getElementById('message-btn').addEventListener('click', function() {
            let selectedItems = [];
            document.querySelectorAll('input.row-checkbox:checked').forEach(function(checkbox) {
              let row = checkbox.closest('tr');
              let tds = row.querySelectorAll('td');
              let seq = tds[1].textContent;
              let rep = tds[3].textContent;
              let mobile = tds[6].textContent.trim();
              if (mobile.startsWith("010")) {
                selectedItems.push({ seq: seq, rep: rep, mobile: mobile });
              }
            });
            if (selectedItems.length === 0) {
              alert("선택된 항목 중 휴대전화가 '010'인 목록이 없습니다.");
              return;
            }
            // 팝업 헤더에 건수 표시
            let popupCountElem = document.querySelector('.popup-count');
            if (popupCountElem) {
              popupCountElem.textContent = `(${selectedItems.length}건)`;
            }
            // 선택 목록 구성: 순번, 대표자, 휴대전화
            let listHtml = `
              <div id="selected-list-container">
                <div class="selected-list-header">
                  <span>순번</span>
                  <span>대표자</span>
                  <span>휴대전화</span>
                </div>
                <div id="selected-list">
            `;
            selectedItems.forEach(function(item, index) {
              listHtml += `<div class="selected-list-item">
                             <span>${index + 1}</span>
                             <span>${item.rep}</span>
                             <span>${item.mobile}</span>
                           </div>`;
            });
            listHtml += `</div></div>`;
            document.getElementById('selected-list-container').innerHTML = listHtml;
            // 첨부파일 영역 초기화
            let thumbnailList = document.querySelector('.thumbnail-list');
            if (thumbnailList) {
              thumbnailList.innerHTML = '';
            }
            currentSlide = 0;
            updateThumbnailSlider();
            document.getElementById('message-content').value = "";
            document.getElementById('message-popup').style.display = 'block';
          });

          // #send-message-btn 클릭 이벤트
          document.getElementById('send-message-btn').addEventListener('click', function() {
            let messageContent = document.getElementById('message-content').value.trim();
            if (messageContent === '') {
              alert("메시지를 작성해주세요.");
              return;
            }
            let filesCount = document.getElementById('file-input').files.length;
            if (filesCount === 0) {
              alert("파일을 첨부하세요.");
              return;
            }
            if (confirm("전송하시겠습니까?")) {
              alert("메시지가 전송되었습니다.");
              document.getElementById('message-popup').style.display = 'none';
            }
          });

          // 팝업 닫기 (메시지 팝업 내 .close-btn 클릭)
          document.querySelectorAll('#message-popup .close-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
              document.getElementById('message-popup').style.display = 'none';
            });
          });

          // 파일 첨부 (이미지 썸네일 미리보기) - 최대 7개 첨부
          document.getElementById('file-input').addEventListener('change', function(event) {
            const files = event.target.files;
            if (files.length > 7) {
              alert("파일첨부는 최대 7개까지 가능합니다.");
              event.target.value = "";
              let thumbnailList = document.querySelector('.thumbnail-list');
              if (thumbnailList) {
                thumbnailList.innerHTML = '';
              }
              totalThumbnails = 0;
              return;
            }
            let thumbnailList = document.querySelector('.thumbnail-list');
            if (thumbnailList) {
              thumbnailList.innerHTML = '';
            }
            totalThumbnails = files.length;
            for (let i = 0; i < totalThumbnails; i++) {
              let file = files[i];
              let reader = new FileReader();
              reader.onload = function(e) {
                if (thumbnailList) {
                  thumbnailList.innerHTML += `<div class="thumbnail-item"><img src="${e.target.result}" alt="첨부이미지"></div>`;
                }
              }
              reader.readAsDataURL(file);
            }
          });

          // 썸네일 슬라이더 좌측 네비 버튼 클릭
          let thumbNavLeft = document.querySelector('.thumb-nav.left');
          if (thumbNavLeft) {
            thumbNavLeft.addEventListener('click', function() {
              if (currentSlide > 0) {
                currentSlide--;
                updateThumbnailSlider();
              }
            });
          }

          // 썸네일 슬라이더 우측 네비 버튼 클릭
          let thumbNavRight = document.querySelector('.thumb-nav.right');
          if (thumbNavRight) {
            thumbNavRight.addEventListener('click', function() {
              if (currentSlide < totalThumbnails - visibleCount) {
                currentSlide++;
                updateThumbnailSlider();
              }
            });
          }

          // 썸네일 클릭 시 해당 이미지를 팝업으로 표시 (이벤트 위임)
          let thumbnailList = document.querySelector('.thumbnail-list');
          if (thumbnailList) {
            thumbnailList.addEventListener('click', function(e) {
              if (e.target && e.target.matches('.thumbnail-item img')) {
                const src = e.target.getAttribute('src');
                let imagePopup = document.getElementById('image-popup');
                if (imagePopup) {
                  imagePopup.querySelector('img').setAttribute('src', src);
                  imagePopup.style.display = 'block';
                }
              }
            });
          }

          // 이미지 팝업 클릭 시 닫기
          let imagePopup = document.getElementById('image-popup');
          if (imagePopup) {
            imagePopup.addEventListener('click', function() {
              this.style.display = 'none';
            });
          }

          // #excel-btn 클릭 시 CSV 생성 및 다운로드
          document.getElementById('excel-btn').addEventListener('click', function() {
            let csvContent = "\ufeff"; // UTF-8 BOM 추가
            // 헤더
            csvContent += "순번,제목,대표자,주소지,일반전화,휴대전화\n";
            document.querySelectorAll('input.row-checkbox:checked').forEach(function(checkbox) {
              let row = checkbox.closest('tr');
              let tds = row.querySelectorAll('td');
              let seq = tds[1].textContent;
              let title = tds[2].textContent;
              let rep = tds[3].textContent;
              let addr = tds[4].textContent;
              let phone = tds[5].textContent;
              let mobile = tds[6].textContent;
              let rowData = [seq, title, rep, addr, phone, mobile].join(",");
              csvContent += rowData + "\n";
            });
            if (csvContent === "\ufeff순번,제목,대표자,주소지,일반전화,휴대전화\n") {
              alert("체크된 데이터가 없습니다.");
              return;
            }
            let encodedUri = encodeURI(csvContent);
            let link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "checked_data.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          });
    });
