        //
        document.addEventListener("DOMContentLoaded", function() {
            const tabs = document.querySelectorAll(".tab");
            const contents = document.querySelectorAll(".tab-content");

            tabs.forEach(tab => {
                tab.addEventListener("click", function() {
                    tabs.forEach(t => t.classList.remove("active"));
                    contents.forEach(c => c.classList.remove("active"));

                    this.classList.add("active");
                    document.getElementById(this.getAttribute("data-target")).classList.add("active");
                });
            });

            // 1번째 탭 (경매) 활성화
            document.querySelector(".tab[data-target='realdata_apt']").click();
        });