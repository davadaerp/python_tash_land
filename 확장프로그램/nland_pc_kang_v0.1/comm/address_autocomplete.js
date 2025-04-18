 //==============================================================
    // 법정동명을 이용한 자동완성코드 정의 ===================
      //
      //hideDetailPopup();
      document.addEventListener("DOMContentLoaded", function() {
            // input 이벤트 핸들러 등록
            document.getElementById('locatadd_nm').addEventListener('input', function() {
              const locatadd_nm = this.value.trim();
              if (locatadd_nm) {
                selectedIndex = -1;
                searchRegionData(locatadd_nm, 1);
              } else {
                const suggestions = document.getElementById('suggestions');
                suggestions.innerHTML = '';
                suggestions.style.display = 'none';
              }
            });

            // keydown 이벤트 핸들러 등록
            document.getElementById('locatadd_nm').addEventListener('keydown', function(e) {
              const items = document.querySelectorAll('#suggestions li');
              if (e.key === 'ArrowDown') {
                if (selectedIndex < items.length - 1) {
                  selectedIndex++;
                  updateSelectedItem(items);
                }
                e.preventDefault();
              } else if (e.key === 'ArrowUp') {
                if (selectedIndex > 0) {
                  selectedIndex--;
                  updateSelectedItem(items);
                }
                e.preventDefault();
              } else if (e.key === 'Enter') {
                e.preventDefault();
                selectItem(selectedIndex);
              }
            });

            document.addEventListener('click', function(event) {
              if (!event.target.closest('.input-wrapper')) {
                const suggestions = document.getElementById('suggestions');
                suggestions.innerHTML = '';
                suggestions.style.display = 'none';
              }
            });
      });

      function searchRegionData(locatadd_nm, pageNo) {
          $.ajax({
            url: 'https://apis.data.go.kr/1741000/StanReginCd/getStanReginCdList',
            type: 'GET',
            dataType: 'xml',
            data: {
              ServiceKey: 'B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA==',
              type: 'xml',
              pageNo: pageNo,
              numOfRows: 10,
              flag: 'Y',
              locatadd_nm: locatadd_nm
            },
            success: function(response) {
              $('#suggestions').empty();
              const rows = $(response).find('row');
              if (rows.length > 0) {
                rows.each(function(index, item) {
                  const region_cd = $(item).find('region_cd').text() || '';
                  const locatadd_nm = $(item).find('locatadd_nm').text() || '';
                  const listItem = $('<li></li>').text(locatadd_nm);
                  listItem.data('region_cd', region_cd);
                  listItem.on('click', function() {
                    selectItem(index);
                  });
                  $('#suggestions').append(listItem);
                });
                $('#suggestions').show();
              } else {
                $('#suggestions').append('<li>검색 결과가 없습니다.</li>').show();
              }
            },
            error: function(xhr, status, error) {
              alert('오류 발생: ' + error);
            }
          });
      }

      function updateSelectedItem(items) {
          items.removeClass('selected');
          if (selectedIndex >= 0 && selectedIndex < items.length) {
            items.eq(selectedIndex).addClass('selected');
          }
      }

      function selectItem(index) {
          const items = $('#suggestions li');
          if (index >= 0 && index < items.length) {
            const selectedItem = items.eq(index);
            const fullName = selectedItem.text();
            const region_cd = selectedItem.data('region_cd');
            const spaceIndex = fullName.lastIndexOf(' ');
            if (spaceIndex === -1) {
              alert('올바른 형식의 법정동명이 아닙니다.');
              return;
            }
            const name = fullName.substring(0, spaceIndex);
            const district = fullName.substring(spaceIndex + 1);
            const formattedName = `법정코드: ${name}(${region_cd.slice(0, 5)})`;
            const formattedDistrict = `동명: ${district}`;
            $('#locatadd_nm').val(name + ' ' + district);
            selectedLawdCd = region_cd.slice(0, 5);
            selectedUmdNm = district;
            //alert(`${formattedName}\n${formattedDistrict}`);
            $('#suggestions').hide();
            selectedIndex = -1;
            //
            fetchData();
          }
      }
