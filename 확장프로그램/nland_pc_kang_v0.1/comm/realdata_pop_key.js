    //
    document.addEventListener("DOMContentLoaded", function () {
      const keyInputs = {
        sanga: document.getElementById("sanga-key"),
        apt: document.getElementById("apt-key"),
        villa: document.getElementById("villa-key")
      };
      const saveKeyBtn = document.getElementById("save-key");
      const deleteKeyBtn = document.getElementById("delete-key");
      const closePopupBtn = document.getElementById("close-popup");
      const popupTitle = document.getElementById("popup-title");

      const urlParams = new URLSearchParams(window.location.search);
      const keyType = urlParams.get("type");
      const typeLabels = { sanga: "상가", apt: "아파트", villa: "빌라" };

      if (keyType && typeLabels[keyType]) {
        popupTitle.innerText = `${typeLabels[keyType]} 키 입력`;

        Object.keys(keyInputs).forEach(type => {
          const keyField = keyInputs[type];
          keyField.value = localStorage.getItem(`${type}_key`) || "";
          keyField.disabled = type !== keyType;
        });
      }

      function saveKey() {
        let key = keyInputs[keyType].value.trim();
        if (!key) {
          alert("키를 입력해주세요.");
          return;
        }
        if (confirm(`${typeLabels[keyType]} 키를 입력하시겠습니까?`)) {
          localStorage.setItem(`${keyType}_key`, key);
          closePopup();
        }
      }

      function deleteKey() {
        if (confirm(`${typeLabels[keyType]} 키를 삭제하시겠습니까?`)) {
          localStorage.removeItem(`${keyType}_key`);
          keyInputs[keyType].value = "";
          closePopup();
        }
      }

      function closePopup() {
        window.close();
      }

      saveKeyBtn.addEventListener("click", saveKey);
      deleteKeyBtn.addEventListener("click", deleteKey);
      closePopupBtn.addEventListener("click", closePopup);
    });