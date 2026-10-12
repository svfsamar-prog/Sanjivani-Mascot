function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function createAssetCard(item, isBanner = false) {
  const card = document.createElement('article');
  card.className = 'asset-card';

  const previewContainer = document.createElement('div');
  previewContainer.className = 'asset-preview-container';
  if (item.transparency) {
    previewContainer.classList.add('checkerboard');
  }

  const img = document.createElement('img');
  img.src = item.preview_path;
  img.alt = item.label;
  img.loading = 'lazy';
  img.width = item.width;
  img.height = item.height;
  img.className = 'asset-preview-img';
  previewContainer.appendChild(img);
  card.appendChild(previewContainer);

  const cardBody = document.createElement('div');
  cardBody.className = 'asset-card-body';

  const title = document.createElement('h3');
  title.className = 'asset-card-title';
  title.textContent = item.label;
  cardBody.appendChild(title);

  const badgeRow = document.createElement('div');
  badgeRow.className = 'asset-badge-row';

  const formatBadge = document.createElement('span');
  formatBadge.className = 'badge badge-format';
  formatBadge.textContent = item.format;
  badgeRow.appendChild(formatBadge);

  const transBadge = document.createElement('span');
  transBadge.className = 'badge ' + (item.transparency ? 'badge-transparency' : 'badge-opaque');
  transBadge.textContent = item.transparency ? 'Transparent' : 'Opaque';
  badgeRow.appendChild(transBadge);

  cardBody.appendChild(badgeRow);

  const metaList = document.createElement('ul');
  metaList.className = 'asset-meta-list';

  const dimItem = document.createElement('li');
  dimItem.className = 'asset-meta-item';
  const unit = item.format === 'SVG' && item.filename.includes('outline') ? 'pt' : 'px';
  dimItem.innerHTML = '<strong>Dimensions:</strong> ' + item.width + ' × ' + item.height + ' ' + unit;
  metaList.appendChild(dimItem);

  const sizeItem = document.createElement('li');
  sizeItem.className = 'asset-meta-item';
  sizeItem.innerHTML = '<strong>File Size:</strong> ' + formatBytes(item.bytes);
  metaList.appendChild(sizeItem);

  cardBody.appendChild(metaList);

  if (item.flag) {
    const flagBox = document.createElement('div');
    flagBox.className = 'asset-flag-note';
    flagBox.textContent = item.flag;
    cardBody.appendChild(flagBox);
  }

  const downloadLink = document.createElement('a');
  downloadLink.href = item.path;
  downloadLink.download = item.filename;
  downloadLink.className = 'btn-download';
  downloadLink.setAttribute('aria-label', 'Download ' + item.label + ' (' + item.format + ')');
  downloadLink.textContent = 'Download ' + item.format;
  cardBody.appendChild(downloadLink);

  card.appendChild(cardBody);
  return card;
}

function renderColorCards(colours, container) {
  colours.forEach(function (color) {
    const card = document.createElement('div');
    card.className = 'color-card';

    const preview = document.createElement('div');
    preview.className = 'color-preview-box';
    preview.style.backgroundColor = color.hex;
    if (color.name === 'Support Cream') {
      preview.style.borderBottom = '1px solid #E5D5C0';
    }
    card.appendChild(preview);

    const body = document.createElement('div');
    body.className = 'color-card-body';

    const title = document.createElement('h3');
    title.className = 'color-card-title';
    title.textContent = color.name;
    body.appendChild(title);

    const hexRow = document.createElement('div');
    hexRow.className = 'color-card-hex-row';

    const hexCode = document.createElement('span');
    hexCode.className = 'color-card-hex';
    hexCode.textContent = color.hex;
    hexRow.appendChild(hexCode);

    const copyBtn = document.createElement('button');
    copyBtn.className = 'btn-copy-hex';
    copyBtn.type = 'button';
    copyBtn.textContent = 'Copy hex';
    copyBtn.setAttribute('aria-label', 'Copy ' + color.name + ' hex code ' + color.hex);
    copyBtn.addEventListener('click', function () {
      navigator.clipboard.writeText(color.hex).then(function () {
        copyBtn.textContent = 'Copied!';
        setTimeout(function () {
          copyBtn.textContent = 'Copy hex';
        }, 2000);
      });
    });
    hexRow.appendChild(copyBtn);
    body.appendChild(hexRow);

    const use = document.createElement('p');
    use.className = 'color-card-use';
    use.textContent = color.use;
    body.appendChild(use);

    card.appendChild(body);
    container.appendChild(card);
  });
}

function loadManifestData() {
  if (typeof window.MANIFEST_DATA !== 'undefined' && window.MANIFEST_DATA) {
    return Promise.resolve(window.MANIFEST_DATA);
  }
  return fetch('data/manifest.json').then(function (res) {
    if (!res.ok) throw new Error('Failed to load manifest: ' + res.status);
    return res.json();
  });
}

document.addEventListener('DOMContentLoaded', function () {
  loadManifestData()
    .then(function (data) {
      const filesByCategory = {};
      data.files.forEach(function (file) {
        if (!filesByCategory[file.category]) {
          filesByCategory[file.category] = [];
        }
        filesByCategory[file.category].push(file);
      });

      // 1. Brand Identity Section
      const colorContainer = document.getElementById('brand-colors-container');
      if (colorContainer && data.brand && data.brand.colours) {
        renderColorCards(data.brand.colours, colorContainer);
      }

      const brandFilesContainer = document.getElementById('brand-assets-grid');
      if (brandFilesContainer && filesByCategory['01-brand']) {
        filesByCategory['01-brand'].forEach(function (item) {
          brandFilesContainer.appendChild(createAssetCard(item));
        });
      }

      // 2. Mascot Views Section
      const mascotContainer = document.getElementById('mascot-assets-grid');
      if (mascotContainer && filesByCategory['02-mascot']) {
        filesByCategory['02-mascot'].forEach(function (item) {
          mascotContainer.appendChild(createAssetCard(item));
        });
      }

      // 3. Icons Section
      const iconsContainer = document.getElementById('icons-assets-grid');
      if (iconsContainer && filesByCategory['03-icons']) {
        filesByCategory['03-icons'].forEach(function (item) {
          iconsContainer.appendChild(createAssetCard(item));
        });
      }

      // 4. Stickers Section
      const stickersContainer = document.getElementById('stickers-assets-grid');
      if (stickersContainer && filesByCategory['04-stickers']) {
        filesByCategory['04-stickers'].forEach(function (item) {
          stickersContainer.appendChild(createAssetCard(item));
        });
      }

      // 5. Social Banners Section
      const bannersContainer = document.getElementById('banners-assets-grid');
      if (bannersContainer && filesByCategory['05-banners']) {
        filesByCategory['05-banners'].forEach(function (item) {
          bannersContainer.appendChild(createAssetCard(item, true));
        });
      }

      // 6. Web & UI Section
      const uiContainer = document.getElementById('web-ui-assets-grid');
      if (uiContainer && filesByCategory['06-web-ui']) {
        filesByCategory['06-web-ui'].forEach(function (item) {
          uiContainer.appendChild(createAssetCard(item));
        });
      }

      // 7. Vector Section
      const vectorContainer = document.getElementById('vector-assets-grid');
      if (vectorContainer && filesByCategory['07-vector']) {
        filesByCategory['07-vector'].forEach(function (item) {
          vectorContainer.appendChild(createAssetCard(item));
        });
      }

      // Web & UI Background Toggle
      const uiToggleBtn = document.getElementById('btn-toggle-ui-bg');
      if (uiToggleBtn && uiContainer) {
        let isCheckerboard = true;
        uiToggleBtn.addEventListener('click', function () {
          isCheckerboard = !isCheckerboard;
          const previewBoxes = uiContainer.querySelectorAll('.asset-preview-container');
          previewBoxes.forEach(function (box) {
            if (isCheckerboard) {
              box.classList.add('checkerboard');
            } else {
              box.classList.remove('checkerboard');
            }
          });
          uiToggleBtn.textContent = isCheckerboard ? 'Background: Checkerboard' : 'Background: Cream';
          uiToggleBtn.classList.toggle('active', isCheckerboard);
        });
      }
    })
    .catch(function (err) {
      console.error(err);
    });
});
