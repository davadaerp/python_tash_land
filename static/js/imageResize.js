// 예: 1MB 제한이 있다면
const MAX_SIZE = 1 * 1024 * 1024; // 필요 없으면 null 전달 가능

/**
 * 1) 해상도 상자(1500x1440)에 먼저 맞춤 (종횡비 유지)
 * 2) 그 결과가 여전히 용량 초과면 품질/해상도를 추가로 줄여 maxBytes 맞춤
 */
async function resizeToBoxAndBytes(file, {
  maxWidth  = 1500,
  maxHeight = 1440,
  maxBytes  = MAX_SIZE
} = {}) {
  if (!file.type.startsWith('image/')) return file;

  // 원본 이미지 로드
  const img = await loadImageFromFile(file);

  // ── 1) 해상도 제한(1500x1440) 적용 ─────────────────────────────
  const fit = calcFitSize(img.width, img.height, maxWidth, maxHeight);
  let mime = file.type || 'image/jpeg';
  if (!/^image\/(jpeg|png|webp)$/.test(mime)) mime = 'image/jpeg';

  // 먼저 "상자 맞춤"으로 1차 변환
  let blob = await canvasToBlob(img, fit.w, fit.h, mime, 0.92);
  let out  = new File([blob], file.name, { type: mime, lastModified: Date.now() });

  // 상자 맞춘 뒤에도 플랫폼이 종종 예민하니, 안전하게 한 번 더 검증
  if (fit.w > maxWidth || fit.h > maxHeight) {
    // (논리상 나오면 안 되지만 가드)
    const saferFit = calcFitSize(fit.w, fit.h, maxWidth, maxHeight);
    blob = await canvasToBlob(img, saferFit.w, saferFit.h, mime, 0.9);
    out  = new File([blob], file.name, { type: mime, lastModified: Date.now() });
  }

  // ── 2) 용량 제한(maxBytes)이 있으면 추가 축소 ─────────────────
  if (typeof maxBytes === 'number' && maxBytes > 0 && out.size > maxBytes) {
    const reduced = await reduceBytes(out, maxBytes);
    if (reduced) out = reduced;
  }

  return out;
}

// 해상도 상자 맞춤 계산(종횡비 유지)
function calcFitSize(w, h, maxW, maxH) {
  const scale = Math.min(1, maxW / w, maxH / h); // 1 이하면 축소, 1 이상이면 그대로
  return { w: Math.max(1, Math.round(w * scale)), h: Math.max(1, Math.round(h * scale)) };
}

function loadImageFromFile(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
    img.onerror = (e) => { URL.revokeObjectURL(url); reject(e); };
    img.src = url;
  });
}

function canvasToBlob(img, width, height, mime, quality = 0.92) {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas');
    canvas.width = width; canvas.height = height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0, width, height);
    canvas.toBlob((blob) => resolve(blob), mime, quality);
  });
}

// 용량 줄이기(우선 품질, 그다음 해상도)
async function reduceBytes(file, maxBytes) {
  const img = await loadImageFromFile(file);
  let mime = file.type || 'image/jpeg';
  if (!/^image\/(jpeg|png|webp)$/.test(mime)) mime = 'image/jpeg';

  // 초기값
  let quality = 0.9;
  let width = img.width;
  let height = img.height;

  for (let i = 0; i < 10; i++) {
    const blob = await canvasToBlob(img, width, height, mime, quality);
    if (blob && blob.size <= maxBytes) {
      return new File([blob], file.name, { type: mime, lastModified: Date.now() });
    }
    // 줄이는 전략: jpeg/webp는 품질 먼저 낮추고, 그래도 크면 해상도 축소
    if (/image\/(jpeg|webp)/.test(mime) && quality > 0.5) {
      quality = Math.max(0.5, quality * 0.85);
    } else {
      width  = Math.max(1, Math.round(width  * 0.9));
      height = Math.max(1, Math.round(height * 0.9));
    }
  }
  // 실패 시 마지막 결과라도 반환
  const last = await canvasToBlob(img, width, height, mime, quality);
  return new File([last], file.name, { type: mime, lastModified: Date.now() });
}

// [공용] 바이트 → 보기좋게
function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const dm = 2;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}