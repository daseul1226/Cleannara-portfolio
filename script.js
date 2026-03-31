const toggleButton = document.querySelector(".nav-toggle");
const nav = document.querySelector(".site-nav");
const navLinks = [...document.querySelectorAll(".site-nav a")];
const revealItems = [...document.querySelectorAll(".reveal")];
const countItems = [...document.querySelectorAll("[data-count]")];
const imageTriggers = [...document.querySelectorAll(".project-image-trigger")];
const imageModal = document.querySelector(".image-modal");
const imageModalContent = document.querySelector(".image-modal-content");
const imageModalClose = document.querySelector(".image-modal-close");
const caseShortcutLinks = [...document.querySelectorAll(".case-shortcuts a")];
const caseCards = [...document.querySelectorAll(".case-card[id]")];
const datalabStatus = document.getElementById("datalab-status");
const datalabBrandPills = document.getElementById("datalab-brand-pills");
const datalabCategoryPills = document.getElementById("datalab-category-pills");
const datalabScoreboard = document.getElementById("datalab-scoreboard");
const datalabResults = document.getElementById("datalab-results");
const datalabCategoryGrid = document.getElementById("datalab-category-grid");

if (toggleButton && nav) {
  toggleButton.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    toggleButton.classList.toggle("is-open", isOpen);
    toggleButton.setAttribute("aria-expanded", String(isOpen));
  });

  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      nav.classList.remove("is-open");
      toggleButton.classList.remove("is-open");
      toggleButton.setAttribute("aria-expanded", "false");
    });
  });
}

const revealObserver = new IntersectionObserver(
  (entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) {
        return;
      }

      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  },
  {
    threshold: 0.18,
  }
);

revealItems.forEach((item) => revealObserver.observe(item));

const countObserver = new IntersectionObserver(
  (entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) {
        return;
      }

      const el = entry.target;
      const goal = Number(el.dataset.count);
      const duration = 1200;
      const startedAt = performance.now();

      const animate = (now) => {
        const progress = Math.min((now - startedAt) / duration, 1);
        el.textContent = Math.floor(goal * progress).toLocaleString("ko-KR");

        if (progress < 1) {
          requestAnimationFrame(animate);
          return;
        }

        if (goal === 20) {
          el.textContent = "20+";
        }
      };

      requestAnimationFrame(animate);
      observer.unobserve(el);
    });
  },
  {
    threshold: 0.5,
  }
);

countItems.forEach((item) => countObserver.observe(item));

const sectionIds = ["intro", "fit", "cases", "proposal", "roadmap"];
const sections = sectionIds
  .map((id) => document.getElementById(id))
  .filter(Boolean);

const updateActiveLink = () => {
  const scrollPoint = window.scrollY + window.innerHeight * 0.3;

  sections.forEach((section) => {
    const top = section.offsetTop;
    const bottom = top + section.offsetHeight;
    const link = document.querySelector(`.site-nav a[href="#${section.id}"]`);

    if (!link) {
      return;
    }

    link.classList.toggle("is-active", scrollPoint >= top && scrollPoint < bottom);
  });
};

updateActiveLink();
window.addEventListener("scroll", updateActiveLink, { passive: true });

if (caseShortcutLinks.length > 0 && caseCards.length > 0) {
  const updateCurrentShortcut = (id) => {
    caseShortcutLinks.forEach((link) => {
      link.classList.toggle("is-current", link.getAttribute("href") === `#${id}`);
    });
  };

  const shortcutObserver = new IntersectionObserver(
    (entries) => {
      const visibleEntries = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio);

      if (visibleEntries.length === 0) {
        return;
      }

      updateCurrentShortcut(visibleEntries[0].target.id);
    },
    {
      threshold: [0.3, 0.55, 0.8],
      rootMargin: "-10% 0px -35% 0px",
    }
  );

  caseCards.forEach((card) => shortcutObserver.observe(card));
  updateCurrentShortcut(caseCards[0].id);
}

const closeImageModal = () => {
  if (!imageModal || !imageModalContent) {
    return;
  }

  imageModal.classList.remove("is-open");
  imageModal.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
  imageModalContent.src = "";
  imageModalContent.alt = "";
};

if (imageModal && imageModalContent && imageTriggers.length > 0) {
  imageTriggers.forEach((trigger) => {
    trigger.addEventListener("click", () => {
      imageModalContent.src = trigger.dataset.image || "";
      imageModalContent.alt = trigger.dataset.alt || "프로젝트 이미지 확대 보기";
      imageModal.classList.add("is-open");
      imageModal.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
    });
  });

  imageModal.addEventListener("click", (event) => {
    if (event.target === imageModal) {
      closeImageModal();
    }
  });
}

if (imageModalClose) {
  imageModalClose.addEventListener("click", closeImageModal);
}

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeImageModal();
  }
});

const renderDatalab = (payload) => {
  if (
    !datalabStatus ||
    !datalabBrandPills ||
    !datalabCategoryPills ||
    !datalabScoreboard ||
    !datalabResults ||
    !datalabCategoryGrid
  ) {
    return;
  }

  const categories = Array.isArray(payload.categories) ? payload.categories : [];
  const brands = Array.isArray(payload.brands) ? payload.brands : [];
  const recommendation = payload.recommendation || {};
  const priorityCategory = categories.find(
    (category) => category.name === recommendation.priorityCategory
  );
  const focusProducts = priorityCategory?.products || [];

  if (payload.generatedAt) {
    const formatted = new Date(payload.generatedAt).toLocaleString("ko-KR", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
    datalabStatus.textContent = `최근 업데이트: ${formatted}`;
  } else {
    datalabStatus.textContent = "네이버 데이터랩 연동 대기 중";
  }

  datalabBrandPills.innerHTML = brands
    .map((item) => `<span>${item}</span>`)
    .join("");

  datalabCategoryPills.innerHTML = categories
    .map((item) => `<span>${item.name}</span>`)
    .join("");

  const maxScore = Math.max(...focusProducts.map((item) => Number(item.score) || 0), 1);
  datalabScoreboard.innerHTML = focusProducts
    .map((item) => {
      const score = Number(item.score) || 0;
      const momentum = Number(item.momentum) || 0;
      const width = Math.max((score / maxScore) * 100, 12);

      return `
        <div class="score-row">
          <div class="score-head">
            <strong>${item.name}</strong>
            <span>추천 점수 ${score.toFixed(1)}</span>
          </div>
          <div class="score-bar">
            <span style="width:${width}%"></span>
          </div>
          <small>최근 3개월 평균 ${Number(item.last3Avg || 0).toFixed(1)} · 모멘텀 ${momentum.toFixed(1)}%</small>
        </div>
      `;
    })
    .join("");

  datalabResults.innerHTML = `
    <div class="result-item">
      <span class="result-label">상품 제안</span>
      <strong>${recommendation.priorityMessage || "추천 데이터를 준비 중입니다."}</strong>
    </div>
    <div class="result-item">
      <span class="result-label">지역 제안</span>
      <strong>${recommendation.regionalMessage || "지역 추천은 내부 데이터와 결합 시 확장됩니다."}</strong>
    </div>
    <div class="result-item">
      <span class="result-label">판촉 제안</span>
      <strong>${recommendation.promoMessage || "프로모션 추천 데이터를 준비 중입니다."}</strong>
    </div>
  `;

  datalabCategoryGrid.innerHTML = categories
    .map((category) => {
      const leader = category.products?.[0];
      return `
        <article class="category-card">
          <p class="mini-label">${category.name}</p>
          <h3>${leader ? `${leader.brand} 우세` : "데이터 준비 중"}</h3>
          <p>${category.seasonNote || ""}</p>
          <div class="category-meta">
            <span>리더 브랜드: ${category.leader || "데이터 없음"}</span>
            <span>추천 점수: ${leader ? Number(leader.score || 0).toFixed(1) : "0.0"}</span>
          </div>
        </article>
      `;
    })
    .join("");
};

fetch("./assets/data/datalab.json")
  .then((response) => {
    if (!response.ok) {
      throw new Error("failed to load datalab.json");
    }

    return response.json();
  })
  .then(renderDatalab)
  .catch(() => {
    renderDatalab({
      generatedAt: null,
      brands: ["깨끗한나라", "크리넥스", "커클랜드", "잘풀리는집"],
      categories: [
        {
          name: "화장지",
          seasonNote: "환절기·연말 수요가 큰 카테고리",
          leader: "연동 필요",
          products: [],
        },
        {
          name: "물티슈",
          seasonNote: "여름철·야외활동 시즌 수요가 큰 카테고리",
          leader: "연동 필요",
          products: [],
        },
      ],
      recommendation: {
        priorityCategory: "화장지",
        priorityMessage:
          "데이터 파일을 불러오지 못했습니다. GitHub Actions 연동 후 브랜드+카테고리 비교가 자동 갱신됩니다.",
        regionalMessage: "지역 추천은 내부 판매 데이터와 결합 시 확장됩니다.",
        promoMessage:
          "브랜드별 검색 모멘텀과 시즌성을 기준으로 프로모션 타이밍을 제안하도록 설계했습니다.",
      },
    });
  });
