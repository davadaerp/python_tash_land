// 전역 선택 인덱스/값 (기존 유지)
// let selectedIndex = -1;
// let selectedLawdCd = null;
// let selectedUmdNm = null;

//==============================================================
// 법정동명을 이용한 자동완성코드 정의 ===================
$(document).ready(function() {
  $('#locatadd_nm').on('input', function() {
    const locatadd_nm = $('#locatadd_nm').val().trim();
    if (locatadd_nm) {
      selectedIndex = -1;
      searchRegionData(locatadd_nm, 1);  // pageNo는 형식상 유지
    } else {
      $('#suggestions').empty().hide();
    }
  });

  $('#locatadd_nm').on('keydown', function(e) {
    const items = $('#suggestions li');
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

  $(document).on('click', function(event) {
    if (!$(event.target).closest('.input-wrapper').length) {
      $('#suggestions').empty().hide();
    }
  });
});

// 서버(JSON)로 자동완성 데이터 받기
function searchRegionData(locatadd_nm, pageNo) {
  $.ajax({
    url: BASE_URL + '/api/lawdcd/autocomplete',
    type: 'GET',
    dataType: 'json',
    data: {
      locatadd_nm: locatadd_nm,
      limit: 10,      // 서버에서도 기본 30, 여기선 10개만
      page: pageNo    // 형식상 유지 (서버는 optional로 무시 가능)
    },
    success: function(resp) {
      $('#suggestions').empty();
      const items = (resp && resp.items) ? resp.items : [];

      if (items.length > 0) {
        items.forEach((it, index) => {
          const region_cd   = it.region_cd || '';
          const locat_name  = it.locatadd_nm || '';

          const $li = $('<li></li>').text(locat_name);
          $li.data('region_cd', region_cd);
          $li.on('click', function() {
            selectItem(index);
          });
          $('#suggestions').append($li);
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

    const formattedName = `법정코드: ${name}(${region_cd})`;
    const formattedDistrict = `동명: ${district}`;

    $('#locatadd_nm').val(name + ' ' + district);
    selectedLawdCd = region_cd;
    selectedUmdNm  = district;

    console.log(`${formattedName}\n${formattedDistrict}`);

    $('#suggestions').hide();
    selectedIndex = -1;
  }
}
