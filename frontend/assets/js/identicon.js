// frontend/assets/js/identicon.js
// Generates GitHub-style geometric identicons from a string hash.

function generateIdenticon(value, size) {
  size = size || 64;
  const hash = hashCode(value || "default");
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");

  // Background
  ctx.fillStyle = "#e1e4e8";
  ctx.fillRect(0, 0, size, size);

  // Derive color from hash
  const hue = Math.abs(hash) % 360;
  const color = `hsl(${hue}, 65%, 50%)`;
  ctx.fillStyle = color;

  // 5x5 grid, mirrored horizontally (only compute left 3 columns)
  const cellSize = size / 5;
  for (let row = 0; row < 5; row++) {
    for (let col = 0; col < 3; col++) {
      const bit = (hash >> (row * 3 + col)) & 1;
      if (bit) {
        ctx.fillRect(col * cellSize, row * cellSize, cellSize, cellSize);
        if (col < 2) {
          ctx.fillRect((4 - col) * cellSize, row * cellSize, cellSize, cellSize);
        }
      }
    }
  }

  return canvas.toDataURL("image/png");
}

function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return hash;
}
