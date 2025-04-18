class NewLand {
  constructor() {
    this.observer = null;
    this.e = null;
    this.renderCollapseSummaryButton();
    this.startObserveForDetail();
    this.startObserveForDetail2();
  }

  startObserveForDetail2() {
    const existingPanels = document.querySelectorAll(".detail_panel");
    existingPanels.forEach((panel) => {
      this.collapseSummary();
    });

    // MutationObserver 콜백 함수
    const callback = function (mutationsList, observer) {
      for (let mutation of mutationsList) {
        if (mutation.type === "childList") {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === 1) {
              if (node.classList.contains("detail_panel")) {
                const box_summary = document.querySelector("#skykeySummary");
                const detail_panel = document.querySelector(".detail_panel");

                if (box_summary.style.display === "block") {
                  if (detail_panel) {
                    detail_panel.style.left = "85rem";
                  }
                } else {
                  if (detail_panel) {
                    detail_panel.style.left = "401px";
                  }
                }
              }
              // 추가된 노드의 하위 요소도 검사
              node.querySelectorAll(".detail_panel").forEach((panel) => {
                const box_summary = document.querySelector("#skykeySummary");
                const detail_panel = document.querySelector(".detail_panel");

                if (box_summary.style.display === "block") {
                  if (detail_panel) {
                    detail_panel.style.left = "85rem";
                  }
                } else {
                  if (detail_panel) {
                    detail_panel.style.left = "401px";
                  }
                }
              });
            }
          });

          mutation.removedNodes.forEach((node) => {
            if (
              node.nodeType === 1 &&
              node.classList.contains("detail_panel")
            ) {
              const box_summary = document.querySelector("#skykeySummary");
              const detail_panel = document.querySelector(".detail_panel");

              if (box_summary.style.display === "block") {
                if (detail_panel) {
                  detail_panel.style.left = "85rem";
                }
              } else {
                if (detail_panel) {
                  detail_panel.style.left = "401px";
                }
              }
            }
          });
        }
      }
    };

    // 관찰 대상이 될 부모 엘리먼트를 선택합니다.
    const targetNode = document.body;

    // 관찰자의 옵션을 설정합니다
    const config = { childList: true, subtree: true };

    // 관찰자 인스턴스를 생성하고 콜백 함수를 전달합니다
    const observer = new MutationObserver(callback);

    // 설정한 옵션으로 타겟의 관찰을 시작합니다
    observer.observe(targetNode, config);
  }

  renderCollapseSummaryButton() {
    var list_panel = document.querySelector(".list_panel");
    var detail_panel = document.querySelector(".detail_panel");
    if (list_panel && detail_panel) {
      this.startObserveForDetail();
    }

    var panel_group__upper = document.querySelector(".panel_group--upper");
    if (panel_group__upper) {
      this.generateFloorSummary();
    }

    var filter_wrap = document.querySelector("div.filter_wrap div.filter_area");
    var box_option = document.querySelector("#skykey-main-wrap");
    if (filter_wrap && !box_option) {
      let t =
        '<div id="skykey-main-wrap" class="skykey-main-button-wrap"><button class="skykey-main-button"><label>요약</label><div class="unionKeyIcon"></div></button></div>';

      filter_wrap.insertAdjacentHTML("afterbegin", t);

      var summary_badge_button = document.querySelector(".skykey-main-button");
      if (summary_badge_button) {
        summary_badge_button.addEventListener("click", () =>
          this.collapseSummary()
        );
      }
    }
  }

  collapseSummary() {
    const box_summary = document.querySelector("#skykeySummary");
    const detail_panel = document.querySelector(".detail_panel");

    if (!box_summary) {
      this.renderCollapseSummaryButton();
      return;
    }

    if (box_summary.style.display === "block") {
      box_summary.style.display = "none";
      if (detail_panel) {
        detail_panel.style.left = "401px";
      }
    } else {
      box_summary.style.display = "block";
      if (detail_panel) {
        detail_panel.style.left = "85rem";
      }
      console.log("collapseSummary", "showSummary")
      this.showSummary();
    }
  }

  applyNewProfitRate() {
    const profitRateInput = document.getElementById("skykeyProfitRate");
    const newRate = profitRateInput ? profitRateInput.value : 3;
    console.log("applyNewProfitRate - 새로운 수익률:", newRate);

    localStorage.setItem("skykeyProfitRate", newRate);
    this.updatePriceItems("applyNewProfitRate");
  }

  showSummary() {
    console.log("showSummary")
    const skykeySummary = document.getElementById("skykeySummary");
    if (skykeySummary.style.display === "none") {
      return;
    }

    const items = this.getItemList();
    items.sort(this.getSortFunction());

    const commercialRentSummary = this.getSummaryByFloor(
      items,
      ["상가", "사무실"],
      "월세"
    );
    const commercialSaleSummary = this.getSummaryByFloor(
      items,
      ["상가", "사무실"],
      "매매"
    );
    const apartmentRentSummary = this.getSummaryByLandSpace(
      items,
      ["아파트", "재건축", "아파트분양권"],
      "전세"
    );
    const apartmentSaleSummary = this.getSummaryByLandSpace(
      items,
      ["아파트", "재건축", "아파트분양권"],
      "매매"
    );
    const residentialRentSummary = this.getSummaryByType(
      items,
      ["아파트", "오피스텔", "빌라", "공장/창고", "원룸", "지식산업센터"],
      "월세"
    );
    const otherSaleSummary = this.getSummaryByType(
      items,
      ["토지", "건물", "공장/창고", "단독/다가구", "지식산업센터"],
      "매매"
    );

    const summaryTableHeader = `<table class="table"><thead><tr><th>종류</th><th>구분</th><th>최저</th><th>평균</th><th>최고</th></tr></thead>`;
    const summaryTableFooter = `</table><br>`;
    const skykeyProfitRate = localStorage.getItem("skykeyProfitRate") || 3;

    const filterHeader = `
      <div class="skykey-filter-header">
        <div class="radio-button-wrap">
          <div class="radio-button">
            <input type="radio" id="default" name="skykeySummarySort" value="default" checked />
            <label for="default">기본</label>
          </div>
          <div class="radio-button">
            <input type="radio" id="floor" name="skykeySummarySort" value="floor" />
            <label for="floor">층수</label>
          </div>
          <div class="radio-button">
            <input id="unitPrice" type="radio" name="skykeySummarySort" value="unitPrice"/>
            <label for="unitPrice">평단</label>
          </div>
        </div>
        <div class="skykeyProfitRateWrap">
          <input type="number" placeholder="수익률" id="skykeyProfitRate" class="profit_rate" value="${skykeyProfitRate}"/>
          <div class="percentIcon"></div>
          <button id="applyProfitRate" class="apply-button">적용</button>
        </div>
      </div>
      <table class="table"><thead><tr class="summary_header"><th>층</th><th>평단가</th><th>평수</th><th>종류</th><th>가격</th></tr></thead>`;

    let summaryContent =
      summaryTableHeader +
      apartmentRentSummary +
      apartmentSaleSummary +
      commercialRentSummary +
      commercialSaleSummary +
      residentialRentSummary +
      otherSaleSummary +
      summaryTableFooter +
      filterHeader;

    summaryContent +=
      items
        .map(
          (item) =>
            `<tr><td>${
              item.floorText
            }${item.directionHtml()}</td><td style="color:#${
              item.unitPriceColor
            }">${item.unitPrice.toFixed(1)}</td><td>${item.py.toFixed(
              1
            )}</td><td>${item.type}</td><td>${item.priceText}</td></tr>`
        )
        .join("") + "</table>";

    const summaryTop = document.documentElement.scrollHeight / 4;
    skykeySummary.style.display = "flex";
    skykeySummary.style.top = `${summaryTop}px`;
    document.getElementById("skykeySummaryContent").innerHTML = summaryContent;
    skykeySummary.style.display = "block";

    // 적용 버튼에 이벤트 리스너 추가
    const applyButton = document.getElementById("applyProfitRate");
    if (applyButton) {
      applyButton.addEventListener("click", () => this.applyNewProfitRate());
    }

    document
      .querySelectorAll("input[name=skykeySummarySort]")
      .forEach((radio) => {
        radio.addEventListener("click", () => {
          // 화살표 함수로 변경
          skykeySummary.style.display = "block";
          console.log("collapseSummary", "showSummary")
          this.showSummary(); // 이제 'this'는 올바른 컨텍스트를 가리킵니다
        });
      });

    const savedSortValue =
      localStorage.getItem("skykeySummarySort") || "default";
    document.querySelector(
      `input[name=skykeySummarySort][value=${savedSortValue}]`
    ).checked = true;
  }

  _(t, e = 0) {
    if (e == 0) {
      return (t.toFixed(e) * 1).toLocaleString();
    } else {
      return t.toFixed(e);
    }
  }

  getSummaryByFloor(t, e, i) {
    let r = t.filter((t) => e.includes(t.type) && t.saleType === i);
    if (!r.length) {
      return "";
    }
    let l = (t) => t.unitPrice;
    let n = r.filter((t) => t.floor == 1).map(l);
    let o = r.filter((t) => t.floor == 2).map(l);
    let a = r.filter((t) => t.floor > 2).map(l);
    let s = r.filter((t) => t.floor.includes("B")).map(l);
    let c = i == "월세" ? 1 : 0;
    let d = "";
    d += this.formatSummaryRow("상층", a, c, i);
    d += this.formatSummaryRow("2층", o, c, i);
    d += this.formatSummaryRow("1층", n, c, i);
    d += this.formatSummaryRow("지하", s, c, i);
    return d;
  }

  m = function (t, e) {
    return t.replace(/\D/, "") - e.replace(/\D/, "") || t.localeCompare(e) || 0;
  };

  getSummaryByLandSpace(t, e, i) {
    let c = i == "월세" ? 1 : 0;
    let r = t.filter((t) => e.includes(t.type) && t.saleType === i);
    if (!r.length) {
      return "";
    }
    let l = (t) => t.price;
    let n = [...new Set(r.map((t) => t.landSpace))].sort(this.m);
    let o = "";

    n.forEach((e) => {
      let t = r.filter((t) => t.landSpace == e).map(l);

      o += this.formatSummaryRow(e, t, c, i);
    });
    return o;
  }

  getSummaryByType(t, e, i) {
    let r = t.filter((t) => e.includes(t.type) && t.saleType === i);
    if (!r.length) {
      return "";
    }
    let l = (t) => t.unitPrice;
    let n = [...new Set(r.map((t) => t.type))].sort();
    let o = i == "월세" ? 1 : 0;
    let a = "";
    n.forEach((e) => {
      let t = r.filter((t) => t.type == e).map(l);
      a += this.formatSummaryRow(e, t, o, i);
    });

    return a;
  }

  startObserveForDetail() {
    const currentClickProduct =
      localStorage.getItem("currentClickProduct") || null;

    const items = [];
    const itemListSelector = "div#listContents1>div.item_list";
    const alternativeSelector = "div#complexOverviewList div.item_list";

    const itemList =
      document.querySelector(itemListSelector) ||
      document.querySelector(alternativeSelector);

    if (itemList) {
      const selectedItems = itemList.querySelectorAll(
        "div.item.is-selected>div.item_inner"
      );
      selectedItems.forEach((element) => {
        const itemData = this.parseItemData(element);
        items.push(itemData);
      });
    }

    if (items.length === 0) return;

    const priceItemHtml = this.createPriceItemHtml(items[0]);
    const priceArea = document.querySelector(
      "div.detail_panel div.info_article_price"
    );
    items[0].priceArea = priceArea;

    if (currentClickProduct === `${items[0].unitPrice}/${items[0].py}`) {
      if (document.querySelector("div.detail_panel .box-price-item")) {
        return;
      } else {
        priceArea.insertAdjacentHTML("beforeend", priceItemHtml);
        return;
      }
    } else {
      const existingPriceItem = document.querySelector(
        "div.detail_panel .box-price-item"
      );
      if (existingPriceItem) {
        existingPriceItem.remove();
      }
      priceArea.insertAdjacentHTML("beforeend", priceItemHtml);
      localStorage.setItem(
        "currentClickProduct",
        `${items[0].unitPrice}/${items[0].py}`
      );
      return;
    }
  }

  createPriceItemHtml(item) {
    let priceItemHtml = `<span class="box-price-item">(<font size="4" color="${item.unitPriceColor}">@${item.unitPrice}</font> <font size="4" color="858D9D">${item.py}py</font>`;

    if (item.skykeyProfitRatePrice > 0) {
      priceItemHtml += ` <font size="4" color="4c94e8">${item.skykeyProfitRatePriceText}</font>`;
    }

    priceItemHtml += `)</span>`;

    return priceItemHtml;
  }

  generateFloorSummary() {
    var box_summary = document.querySelector("#skykeySummary");
    if (!box_summary) {
      var panel_group__upper = document.querySelector(".panel_group--upper");
      panel_group__upper.style.display = "flex";
      panel_group__upper.style.width = "fit-content";

      var list_panel = document.querySelector(".list_panel");
      list_panel.insertAdjacentHTML(
        "beforebegin",
        `<div id="skykeySummary">
        <div class="row-box space-between align-center">
          <div class="box-summary-heaer">
            <div class="logo"></div>
          </div>
          <button class="copy-button">
            <div class="copy"></div>
            <label>복사</label>
          </button>
        </div>
        <div id="skykeySummaryContent" class="table-wrap"></div>
      </div>`
      );

      var copy_button = document.querySelector(".copy-button");
      if (copy_button) {
        copy_button.addEventListener("click", () => this.copyTxt());
      }

      this.startObserve();
    } else {
      if (box_summary.style.display === "block") {
        var detail_panel = document.querySelector(".detail_panel");
        detail_panel.style.left = "85rem";
      }
    }
  }

  startObserve() {
    var map_wrap = document.querySelector("div.map_wrap");

    this.e = new MutationObserver(() => {
      setTimeout(() => {
        this.updatePriceItems("observeItemList");
        this.showSummary();
      }, 100);
    });

    if (map_wrap) {
      this.addOptionBox();
      this.updatePriceItems("startObserve");
      this.showSummary();
    }
  }

  updatePriceItems(value) {
    console.log("updatePriceItems 호출됨:", value);

    if (this.e) {
      this.e.disconnect();
    }

    document
      .querySelectorAll(".box-price-item")
      .forEach((item) => item.remove());

    const items = this.getItemList();
    console.log("updatePriceItems - 아이템 개수:", items.length);

    items.forEach((item, index) => {
      const priceItemHtml = this.createPriceItemHtml(item);
      console.log(`updatePriceItems - 아이템[${index}] HTML 생성:`, {
        priceArea: item.priceArea instanceof Element,
        html: priceItemHtml
      });

      if (item.priceArea instanceof Element) {
        item.priceArea.insertAdjacentHTML("beforeend", priceItemHtml);
      }
    });

    this.observeItemList();
  }

  addOptionBox() {
    const existingBoxOption = document.getElementById("skykey-main-wrap");

    if (!existingBoxOption) {
      const t = `
      <div id="skykey-main-wrap" class="skykey-main-button-wrap">
          <button class="skykey-main-button">
              <label>요약</label>
              <div class="unionKeyIcon"></div>
          </button>
      </div>
  `;

      const filterArea = document.querySelector(
        "div.filter_wrap div.filter_area"
      );

      if (filterArea) {
        filterArea.insertAdjacentHTML("afterbegin", t); // 목록 고정 영역 아래에 옵션 박스 추가

        var summaryBadgeButton = document.querySelector(".skykey-main-button");
        if (summaryBadgeButton) {
          summaryBadgeButton.addEventListener("click", () =>
            this.collapseSummary()
          );
        }
      }
    }

    const skykeySummary = document.getElementById("skykeySummary");
    if (skykeySummary) {
      skykeySummary.style.display = "none";
    }

    const detailPanel = document.querySelector(".detail_panel");
    if (detailPanel) {
      detailPanel.style.left = "401px";
    }
  }

  formatSummaryRow(t, e, c, i) {
    if (!e.length) {
      return "";
    }
    let r = this._(Math.min(...e), c);
    let l = this._(Math.max(...e), c);
    let n = this._(e.reduce((t, e) => t + e, 0) / e.length, c);
    return `<tr><td>${i}</td><td>${t}(${e.length})</td><td>${r}</td><td>${n}</td><td>${l}</td></tr>`;
  }

  copyTxt() {
    let t = this.getItemList();
    t.sort(this.getSortFunction());
    let e = t.map(
      (t) =>
        `${t.floorText}${t.directionText}\t@${t.unitPrice.toFixed(
          1
        )}\t${t.py.toFixed(1)}py\t${t.type}\t${t.priceText}`
    );
    let i = [...new Set(e)];
    this.copyClipboard(i.join("\r\n"));
  }

  copyClipboard(text) {
    const textarea = document.createElement("textarea");
    document.body.appendChild(textarea);
    textarea.value = text;
    textarea.select();
    navigator.clipboard.writeText(text);
    // document.execCommand("copy");
    document.body.removeChild(textarea);
  }

  getItemList() {
    const items = [];
    const itemListSelector = "div#listContents1>div.item_list";
    const alternativeSelector = "div#complexOverviewList div.item_list";

    const itemList =
      document.querySelector(itemListSelector) ||
      document.querySelector(alternativeSelector);

    if (itemList) {
      const itemElements = itemList.querySelectorAll(
        "div.item:not(.item--child)>div.item_inner"
      );
      itemElements.forEach((element) => {
        const itemData = this.parseItemData(element);
        items.push(itemData);
      });
    }

    return items;
  }

  observeItemList() {
    const listContainers = [
      "div#listContents1>div.item_list",
      "div#complexOverviewList div.item_list",
      "div#listContents1>div.item_list>div>div",
      "div#complexOverviewList div.item_list>div",
    ];

    listContainers.forEach((selector) => {
      const element = document.querySelector(selector);
      if (element) {
        // this.e = new MutationObserver(() =>
        //   setTimeout(() => {
        //     this.updatePriceItems("observeItemList");
        //     this.showSummary();
        //   }, 100)
        // );
        this.e.observe(element, { childList: true });
      }
    });
  }

  getSortFunction() {
    const sortTypeElement = document.querySelector(
      "input[name=skykeySummarySort]:checked"
    );
    const sortType = sortTypeElement ? sortTypeElement.value : null;

    if (sortType) {
      localStorage.setItem("skykeySummarySort", sortType);
    }

    switch (sortType) {
      case "floor":
        return this.sortByFloor;
      case "unitPrice":
        return this.sortByUnitPrice;
      default:
        return this.sortByDefault;
    }
  }

  sortByFloor(a, b) {
    return (
      a.floor.replace("B", "100") - b.floor.replace("B", "100") ||
      a.totalFloor - b.totalFloor ||
      a.floor.localeCompare(b.floor) ||
      0
    );
  }

  sortByUnitPrice(a, b) {
    return a.unitPrice - b.unitPrice || a.price - b.price || 0;
  }

  sortByDefault(a, b) {
    return 1;
  }

  parseItemData(itemElement) {
    const itemData = {};

    const priceArea = itemElement.querySelector(".price_line");
    const priceInfo = this.parsePriceInfo(priceArea);
    const spaceInfo = this.parseSpaceInfo(
      itemElement.querySelector(".info_area span.spec").textContent
    );

    itemData.priceArea = priceArea;
    itemData.type = itemElement.querySelector(
      ".info_area strong.type"
    ).textContent;
    itemData.shortType = itemData.type.substr(0, 1);
    itemData.saleType = priceInfo.saleType;
    itemData.deposit = priceInfo.deposit;
    itemData.price = priceInfo.price;
    itemData.priceText = priceInfo.priceText;
    itemData.priceSimpleText = priceInfo.priceSimpleText;
    itemData.landSpace = spaceInfo.landSpace;
    itemData.buildingSpace = spaceInfo.buildingSpace;
    itemData.floorText = spaceInfo.floorText;
    itemData.floor = spaceInfo.floor;
    itemData.totalFloor = spaceInfo.totalFloor;
    itemData.direction = spaceInfo.direction;
    itemData.directionText = spaceInfo.direction
      ? `,${spaceInfo.direction}`
      : "";
    itemData.agentName = itemElement.querySelector(
      ".agent_info:last-child"
    )?.textContent;

    itemData.isRental = function () {
      return this.saleType === "월세";
    };

    itemData.directionHtml = function () {
      if (this.direction) {
        return `,<span style="display:inline-block;width:40px">${this.direction}</span>`;
      }
      return "";
    };

    this.calculateAdditionalData(itemData);

    return itemData;
  }

  calculateAdditionalData(itemData) {
    const skykeyProfitRate = localStorage.getItem("skykeyProfitRate") || 3;
    console.log("calculateAdditionalData - 현재 수익률:", skykeyProfitRate);

    if (itemData.isRental()) {
      console.log("calculateAdditionalData - 임대물건 계산:", {
        deposit: itemData.deposit,
        monthlyPrice: itemData.price,
        isRental: itemData.isRental()
      });

      if (skykeyProfitRate > 0) {
        const annualRent = itemData.price * 12;
        const capitalizedValue = (annualRent / skykeyProfitRate) * 100;
        itemData.skykeyProfitRatePrice = itemData.deposit + capitalizedValue;

        console.log("calculateAdditionalData - 수익률 계산결과:", {
          annualRent,
          capitalizedValue,
          totalValue: itemData.skykeyProfitRatePrice
        });

        itemData.skykeyProfitRatePriceText = this.formatAsBillions(
          itemData.skykeyProfitRatePrice
        );
      } else {
        console.log("calculateAdditionalData - 수익률이 0이하임");
        itemData.skykeyProfitRatePrice = 0;
        itemData.skykeyProfitRatePriceText = '';
      }
    }

    const buildingTypes = [
      "아파트",
      "오피스텔",
      "빌라",
      "원룸",
      "사무실",
      "상가",
      "지식산업센터",
      "재건축",
      "재개발",
    ];

    if (buildingTypes.includes(itemData.type) || itemData.isRental()) {
      itemData.representSpace =
        Number(itemData.buildingSpace) || Number(itemData.landSpace);
    } else {
      itemData.representSpace =
        Number(itemData.landSpace) || Number(itemData.buildingSpace);
    }

    const unitPrice = (itemData.price / itemData.representSpace) * 3.3058;
    itemData.py = Number((itemData.representSpace * 0.3025).toFixed(1));
    itemData.unitPrice =
      unitPrice < 10 ? Number(unitPrice.toFixed(1)) : Math.floor(unitPrice);

    if (itemData.isRental()) {
      itemData.unitPriceColor = this.getColorOfRentalPrice(itemData.unitPrice);
    } else {
      itemData.unitPriceColor = this.getColorOfPrice(itemData.unitPrice);
    }

    return itemData;
  }

  parsePriceInfo(itemElement) {
    const typeElement = itemElement.querySelector("span.type");
    const priceElement = itemElement.querySelector("span.price");

    const saleType = typeElement ? typeElement.textContent : "";
    const priceText = priceElement ? priceElement.textContent : "";
    const priceWithoutCommas = priceText.replaceAll(",", "");

    let deposit = 0;
    let price = 0;

    if (saleType === "월세") {
      const [depositStr, priceStr] = priceWithoutCommas
        .split("/")
        .map((s) => s.trim());
      deposit = this.convertToNumber(depositStr);
      price = this.convertToNumber(priceStr);
    } else {
      price = this.convertToNumber(priceWithoutCommas);
    }

    const priceSimpleText = this.formatAsBillions(price);

    return {
      saleType,
      deposit,
      price,
      priceText,
      priceSimpleText,
    };
  }

  convertToNumber(t) {
    let e = t.split("억");
    if (e.length > 1) {
      return e[0] * 1e4 + e[1] * 1;
    } else {
      return e[0] * 1;
    }
  }

  parseSpaceInfo(t) {
    let [e, i = "-", r] = t.split(", ");
    let [l, n] = e.replace("m²", "").split("/");
    let [o, a] = i?.replace("층", "").split("/") || ["-", "-"];
    return {
      landSpace: l,
      buildingSpace: n,
      floorText: i,
      floor: o,
      totalFloor: a,
      direction: r,
    };
  }

  formatAsBillions(t) {
    var e = Math.floor(t / 100) / 100;

    if (e === Infinity) {
      return ``;
    }

    return `${e}억`;
  }

  getColorOfRentalPrice(price) {
    switch (price) {
      case price >= 30:
        return "858D9D";
      case price >= 20:
        return "3DA172";
      case price >= 10:
        return "FFC400";
      case price >= 5:
        return "F04438";
      default:
        return "F04438";
    }
  }

  getColorOfPrice(price) {
    switch (price) {
      case price <= 50:
        return "F04438";
      case price <= 100:
        return "FFC400";
      case price <= 200:
        return "3DA172";
      case price <= 300:
        return "858D9D";
      default:
        return "9E9E9E";
    }
  }
}

const newLand = new NewLand();
// setTimeout(() => newLand.initializeUI(), 100);
