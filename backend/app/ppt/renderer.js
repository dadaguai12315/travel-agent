/**
 * PptxGenJS Travel Plan Renderer
 *
 * Reads slide JSON + images from a temp directory, writes .pptx.
 *
 * Usage: node renderer.js <input.json> <output.pptx>
 *
 * JSON schema:
 * {
 *   "theme": {"bg": "FFF8F0", "accent": "E8734A", "text": "2C3E50", "sub": "8E6E53"},
 *   "title": "Trip Title",
 *   "destination": "Phuket",
 *   "duration": "5 days",
 *   "slides": [
 *     {"type": "cover", "title": "...", "subtitle": "...", "image": "/tmp/ppt/slide_0.jpg"},
 *     {"type": "timeline", "title": "...", "subtitle": "...", "days": [...]},
 *     {"type": "cards", "title": "...", "items": [{"name": "...", "desc": "..."}]},
 *     {"type": "budget", "title": "...", "items": [{"category": "...", "detail": "...", "amount": "..."}], "total": "..."},
 *     {"type": "map", "title": "...", "image": "/tmp/ppt/slide_N.jpg"},
 *     {"type": "ending", "title": "...", "subtitle": "..."}
 *   ]
 * }
 */

const pptxgen = require("pptxgenjs");
const fs = require("fs");

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath) {
  console.error("Usage: node renderer.js <input.json> <output.pptx>");
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(inputPath, "utf-8"));
const theme = data.theme || {};
const slides = data.slides || [];

const BG = theme.bg || "FFFFFF";
const ACCENT = theme.accent || "111111";
const TEXT = theme.text || "1A1A1A";
const SUB = theme.sub || "757575";
const LIGHT = "F5F5F5";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3" x 7.5"
pres.author = "Travel Advisor";
pres.title = data.title || "Travel Plan";

// ---- Helpers ----

function addImageSafe(slide, path, opts) {
  if (path && fs.existsSync(path)) {
    try {
      slide.addImage({ path, ...opts });
      return true;
    } catch (e) {
      console.error(`Failed to add image ${path}: ${e.message}`);
    }
  }
  return false;
}

// ---- Slide Renderers ----

function renderCover(slide, s) {
  slide.background = { color: BG };

  if (s.image) {
    // Full right-half image
    addImageSafe(slide, s.image, { x: 6.65, y: 0, w: 6.65, h: 7.5, sizing: { type: "cover", w: 6.65, h: 7.5 } });
    // Left panel overlay for text
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 7.1, h: 7.5, fill: { color: BG },
    });
  }

  slide.addText(s.title || "Travel Plan", {
    x: 0.8, y: 2.0, w: 5.5, h: 1.5,
    fontSize: 44, fontFace: "Arial Black", bold: true,
    color: ACCENT, align: "left", margin: 0,
  });

  if (s.subtitle) {
    slide.addText(s.subtitle, {
      x: 0.8, y: 3.6, w: 5.0, h: 0.8,
      fontSize: 20, fontFace: "Arial", color: SUB, margin: 0,
    });
  }

  // Accent line
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: 4.6, w: 2.5, h: 0.04, fill: { color: ACCENT },
  });
}

function renderTimeline(slide, s) {
  slide.background = { color: BG };

  slide.addText(s.title || "Itinerary", {
    x: 0.8, y: 0.4, w: 11.5, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", bold: true, color: TEXT, margin: 0,
  });
  if (s.subtitle) {
    slide.addText(s.subtitle, {
      x: 0.8, y: 1.05, w: 11.5, h: 0.5,
      fontSize: 16, fontFace: "Arial", color: SUB, margin: 0,
    });
  }

  const days = s.days || [];
  if (days.length === 0) return;

  const colW = 11.5 / days.length;
  days.forEach((day, i) => {
    const x = 0.8 + i * colW;

    // Day number circle
    slide.addShape(pres.shapes.OVAL, {
      x: x, y: 1.8, w: 0.45, h: 0.45, fill: { color: ACCENT },
    });
    slide.addText(String(day.day || i + 1), {
      x: x, y: 1.8, w: 0.45, h: 0.45,
      fontSize: 14, fontFace: "Arial", bold: true, color: "FFFFFF",
      align: "center", valign: "middle", margin: 0,
    });

    slide.addText(day.theme || "", {
      x: x, y: 2.4, w: colW - 0.3, h: 0.8,
      fontSize: 14, fontFace: "Arial", bold: true, color: ACCENT, margin: 0,
    });

    const activities = day.activities || [];
    let y = 3.3;
    activities.slice(0, 5).forEach((act) => {
      slide.addText(String(act).substring(0, 70), {
        x: x, y: y, w: colW - 0.3, h: 0.55,
        fontSize: 11, fontFace: "Arial", color: TEXT,
        bullet: true, margin: 0,
      });
      y += 0.6;
    });
  });
}

function renderCards(slide, s) {
  slide.background = { color: BG };

  slide.addText(s.title || "", {
    x: 0.8, y: 0.4, w: 11.5, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", bold: true, color: TEXT, margin: 0,
  });

  const items = (s.items || []).map((item) => {
    if (typeof item === "string") return { name: item.substring(0, 60), desc: "" };
    return {
      name: String(item.name || item.title || "").substring(0, 50),
      desc: String(item.desc || item.subtitle || "").substring(0, 120),
    };
  });

  if (items.length === 0) return;

  const cols = items.length <= 4 ? 2 : 3;
  const colW = 11.5 / cols;
  const rows = Math.ceil(items.length / cols);

  items.forEach((item, i) => {
    const row = Math.floor(i / cols);
    const col = i % cols;
    const x = 0.8 + col * colW;
    const y = 1.5 + row * 2.5;
    const cardW = colW - 0.4;

    // Card background
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: cardW, h: 2.1,
      fill: { color: "FFFFFF" },
      shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.08 },
    });

    slide.addText(item.name, {
      x: x + 0.2, y: y + 0.15, w: cardW - 0.4, h: 0.45,
      fontSize: 16, fontFace: "Arial", bold: true, color: ACCENT, margin: 0,
    });
    if (item.desc) {
      slide.addText(item.desc, {
        x: x + 0.2, y: y + 0.7, w: cardW - 0.4, h: 1.2,
        fontSize: 11, fontFace: "Arial", color: TEXT, margin: 0,
      });
    }
  });
}

function renderBudget(slide, s) {
  slide.background = { color: BG };

  slide.addText(s.title || "Budget", {
    x: 0.8, y: 0.4, w: 11.5, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", bold: true, color: TEXT, margin: 0,
  });

  const headers = ["Category", "Details", "Amount"];
  const colWidths = [2.5, 6.0, 3.0];
  const xPositions = [0.8];
  colWidths.slice(0, -1).forEach((w) => xPositions.push(xPositions[xPositions.length - 1] + w));

  const headerRow = headers.map((h, j) => ({
    text: h,
    options: { fontSize: 13, fontFace: "Arial", bold: true, color: ACCENT },
  }));

  const tableData = [headerRow];

  (s.items || []).slice(0, 10).forEach((item) => {
    if (typeof item === "string") {
      tableData.push([{ text: item.substring(0, 80), options: { colspan: 3, fontSize: 12, fontFace: "Arial", color: TEXT } }]);
    } else {
      tableData.push([
        { text: String(item.category || "").substring(0, 30), options: { fontSize: 12, fontFace: "Arial", color: TEXT } },
        { text: String(item.detail || "").substring(0, 50), options: { fontSize: 12, fontFace: "Arial", color: TEXT } },
        { text: String(item.amount || "").substring(0, 30), options: { fontSize: 12, fontFace: "Arial", color: TEXT } },
      ]);
    }
  });

  slide.addTable(tableData, {
    x: 0.8, y: 1.5, w: 11.5,
    colW: colWidths,
    border: { pt: 0.5, color: "E0E0E0" },
    rowH: [0.4],
    autoPage: false,
  });

  // Total row highlight
  if (s.total) {
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.8, y: 1.5 + 0.4 * (tableData.length + 0.5), w: 11.5, h: 0.45,
      fill: { color: LIGHT },
    });
    slide.addText(s.total, {
      x: 0.8, y: 1.5 + 0.4 * (tableData.length + 0.5), w: 11.5, h: 0.45,
      fontSize: 16, fontFace: "Arial", bold: true, color: ACCENT,
      align: "center", valign: "middle", margin: 0,
    });
  }
}

function renderMap(slide, s) {
  slide.background = { color: BG };

  slide.addText(s.title || "Route Map", {
    x: 0.8, y: 0.4, w: 11.5, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", bold: true, color: TEXT, margin: 0,
  });

  if (s.image) {
    const added = addImageSafe(slide, s.image, {
      x: 1.5, y: 1.5, w: 10.3, h: 5.2,
      sizing: { type: "contain", w: 10.3, h: 5.2 },
    });
    if (!added) {
      slide.addText(s.description || "Route map image", {
        x: 1.5, y: 3.0, w: 10.3, h: 2.0,
        fontSize: 14, fontFace: "Arial", color: SUB, align: "center", margin: 0,
      });
    }
  }
}

function renderEnding(slide, s) {
  slide.background = { color: ACCENT };

  slide.addText(s.title || "Bon Voyage! ✈️", {
    x: 1.5, y: 2.5, w: 10.3, h: 1.2,
    fontSize: 42, fontFace: "Arial Black", bold: true, color: "FFFFFF",
    align: "center", valign: "middle", margin: 0,
  });
  slide.addText(s.subtitle || "Have a wonderful trip", {
    x: 1.5, y: 3.8, w: 10.3, h: 0.7,
    fontSize: 20, fontFace: "Arial", color: "FFFFFF",
    align: "center", valign: "middle", margin: 0,
  });
}

function renderContent(slide, s) {
  slide.background = { color: BG };

  slide.addText(s.title || "", {
    x: 0.8, y: 0.4, w: 11.5, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", bold: true, color: TEXT, margin: 0,
  });

  const bullets = s.bullets || [];
  const textItems = bullets.slice(0, 10).map((b, i) => ({
    text: String(b).substring(0, 120),
    options: { bullet: true, breakLine: i < bullets.length - 1, fontSize: 14, fontFace: "Arial", color: TEXT },
  }));

  slide.addText(textItems, {
    x: 1.2, y: 1.5, w: 10.5, h: 5.5,
    valign: "top", margin: 0,
  });
}

// ---- Render Dispatch ----

const RENDERERS = {
  cover: renderCover,
  timeline: renderTimeline,
  overview: renderTimeline,
  itinerary: renderTimeline,
  food: renderCards,
  hotel: renderCards,
  tips: renderCards,
  budget: renderBudget,
  map: renderMap,
  ending: renderEnding,
  content: renderContent,
};

// ---- Build Presentation ----

slides.forEach((s) => {
  const slide = pres.addSlide();
  const render = RENDERERS[s.type] || renderContent;
  render(slide, s);
});

// ---- Write Output ----

pres.writeFile({ fileName: outputPath }).then(() => {
  console.log(`PPTX written: ${outputPath}`);
}).catch((err) => {
  console.error("PPTX generation failed:", err);
  process.exit(1);
});
