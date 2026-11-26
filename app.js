/* Simulasi Monte Carlo edukatif: satu slab kulit, satu panjang gelombang. */

const DEFAULTS = {
  photons: 5000,
  thickness: 1.0,
  muA: 0.03316,
  muSPrime: 1.88212,
  g: 0.91,
  seed: 42,
  bins: 40,
  maxSteps: 8000,
};

const numberFormat = new Intl.NumberFormat("id-ID", {
  maximumFractionDigits: 2,
});
const preciseFormat = new Intl.NumberFormat("id-ID", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const controls = {
  photons: document.querySelector("#photons"),
  thickness: document.querySelector("#thickness"),
  muA: document.querySelector("#mu-a"),
  muSPrime: document.querySelector("#mu-s-prime"),
  g: document.querySelector("#g"),
  seed: document.querySelector("#seed"),
};

let latestMain = null;
let latestValidation = null;

function makeRandom(seed) {
  // PRNG deterministik agar hasil dapat diulang dengan seed yang sama.
  let state = seed >>> 0;
  return function random() {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function sampleCosTheta(random, g) {
  const u = random();
  if (Math.abs(g) < 1e-10) return 2 * u - 1;

  const ratio = (1 - g * g) / (1 - g + 2 * g * u);
  return Math.max(-1, Math.min(1, (1 + g * g - ratio * ratio) / (2 * g)));
}

function simulate({ photons, muA, muSPrime, g, thickness, seed, bins, maxSteps }) {
  const random = makeRandom(seed);
  const muS = muSPrime / (1 - g);
  const muT = muA + muS;
  const absorbedByDepth = new Array(bins).fill(0);
  let absorbedCount = 0;
  let reflectedCount = 0;
  let transmittedCount = 0;
  let unfinishedCount = 0;
  let stepsUsed = 0;

  if (muT === 0) {
    return {
      absorbed: 0,
      reflected: 0,
      transmitted: 1,
      unfinished: 0,
      absorbedByDepth,
      muS,
      stepsUsed,
    };
  }

  for (let packet = 0; packet < photons; packet += 1) {
    let z = 0;
    let uz = 1; // Berkas datang tegak lurus ke arah +z.
    let finished = false;

    for (let step = 1; step <= maxSteps; step += 1) {
      stepsUsed = Math.max(stepsUsed, step);
      const u = Math.max(random(), Number.MIN_VALUE);
      const stepLength = -Math.log(u) / muT;

      let distanceToBoundary = Number.POSITIVE_INFINITY;
      if (uz > 1e-14) {
        distanceToBoundary = (thickness - z) / uz;
      } else if (uz < -1e-14) {
        distanceToBoundary = (0 - z) / uz;
      }

      if (stepLength >= distanceToBoundary) {
        if (uz > 0) transmittedCount += 1;
        else reflectedCount += 1;
        finished = true;
        break;
      }

      z += uz * stepLength;

      if (random() < muA / muT) {
        absorbedCount += 1;
        const bin = Math.min(bins - 1, Math.max(0, Math.floor((z / thickness) * bins)));
        absorbedByDepth[bin] += 1;
        finished = true;
        break;
      }

      // Hamburan Henyey–Greenstein; cukup simpan komponen arah terhadap sumbu z.
      const cosTheta = sampleCosTheta(random, g);
      const sinTheta = Math.sqrt(Math.max(0, 1 - cosTheta * cosTheta));
      const radialComponent = Math.sqrt(Math.max(0, 1 - uz * uz));
      const phi = 2 * Math.PI * random();
      uz = Math.max(
        -1,
        Math.min(1, uz * cosTheta + radialComponent * sinTheta * Math.cos(phi)),
      );
    }

    if (!finished) unfinishedCount += 1;
  }

  const inverseN = 1 / photons;
  const transmitted = transmittedCount * inverseN;
  return {
    absorbed: absorbedCount * inverseN,
    reflected: reflectedCount * inverseN,
    transmitted,
    unfinished: unfinishedCount * inverseN,
    absorbedByDepth: absorbedByDepth.map((count) => count * inverseN),
    muS,
    stepsUsed,
    transmissionSE: Math.sqrt((transmitted * (1 - transmitted)) / photons),
  };
}

function getParameters() {
  const photons = Number(controls.photons.value);
  const thickness = Number(controls.thickness.value);
  const muA = Number(controls.muA.value);
  const muSPrime = Number(controls.muSPrime.value);
  const g = Number(controls.g.value);
  const seed = Number(controls.seed.value);

  if (![photons, thickness, muA, muSPrime, g, seed].every(Number.isFinite)) {
    throw new Error("Isi semua parameter dengan angka yang valid.");
  }
  if (muA < 0 || muA > 0.2 || muSPrime < 0 || muSPrime > 4) {
    throw new Error("Nilai koefisien optik berada di luar batas kontrol.");
  }
  if (thickness <= 0 || g < 0 || g >= 1 || seed < 0) {
    throw new Error("Periksa lagi ketebalan, g, dan seed.");
  }

  return { photons, thickness, muA, muSPrime, g, seed };
}

function percent(value) {
  return `${preciseFormat.format(value * 100)}%`;
}

function setText(selector, value) {
  document.querySelector(selector).textContent = value;
}

function updateReadouts() {
  document.querySelector("#photons-value").textContent = numberFormat.format(Number(controls.photons.value));
  document.querySelector("#thickness-value").textContent = `${Number(controls.thickness.value).toFixed(1).replace(".", ",")} mm`;
  document.querySelector("#g-value").textContent = Number(controls.g.value).toFixed(2).replace(".", ",");
}

function prepareCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * ratio));
  canvas.height = Math.max(1, Math.floor(rect.height * ratio));
  const context = canvas.getContext("2d");
  context.scale(ratio, ratio);
  return { context, width: rect.width, height: rect.height };
}

function drawOutcomeChart(result) {
  const canvas = document.querySelector("#outcome-chart");
  const { context: ctx, width, height } = prepareCanvas(canvas);
  const left = 45;
  const right = 12;
  const top = 16;
  const bottom = 38;
  const chartHeight = height - top - bottom;
  const chartWidth = width - left - right;
  ctx.clearRect(0, 0, width, height);
  ctx.font = "12px system-ui, sans-serif";
  ctx.textBaseline = "middle";

  for (let tick = 0; tick <= 100; tick += 25) {
    const y = top + chartHeight * (1 - tick / 100);
    ctx.strokeStyle = "#e4e9e6";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(left, y);
    ctx.lineTo(width - right, y);
    ctx.stroke();
    ctx.fillStyle = "#64716d";
    ctx.textAlign = "right";
    ctx.fillText(`${tick}%`, left - 8, y);
  }

  const items = [
    { label: "Diserap A", value: result.absorbed, color: "#374542" },
    { label: "Keluar atas R", value: result.reflected, color: "#74817d" },
    { label: "Diteruskan T", value: result.transmitted, color: "#bac3c0" },
  ];
  const gap = chartWidth * 0.07;
  const barWidth = (chartWidth - gap * 2) / 3;

  items.forEach((item, index) => {
    const x = left + index * (barWidth + gap) + gap / 2;
    const barHeight = Math.max(0, chartHeight * item.value);
    ctx.fillStyle = item.color;
    ctx.fillRect(x, top + chartHeight - barHeight, barWidth, barHeight);
    ctx.fillStyle = "#263532";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillText(item.label, x + barWidth / 2, top + chartHeight + 12);
  });
}

function drawDepthChart(result, thickness) {
  const canvas = document.querySelector("#depth-chart");
  const { context: ctx, width, height } = prepareCanvas(canvas);
  const left = 46;
  const right = 12;
  const top = 16;
  const bottom = 39;
  const chartHeight = height - top - bottom;
  const chartWidth = width - left - right;
  const maxValue = Math.max(0.01, ...result.absorbedByDepth) * 1.15;
  ctx.clearRect(0, 0, width, height);
  ctx.font = "12px system-ui, sans-serif";

  for (let tick = 0; tick <= 4; tick += 1) {
    const fraction = tick / 4;
    const y = top + chartHeight * (1 - fraction);
    ctx.strokeStyle = "#e4e9e6";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(left, y);
    ctx.lineTo(width - right, y);
    ctx.stroke();
    ctx.fillStyle = "#64716d";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.fillText(`${preciseFormat.format(maxValue * fraction * 100)}%`, left - 7, y);
  }

  const slot = chartWidth / result.absorbedByDepth.length;
  const barWidth = Math.max(1, slot - 1);
  result.absorbedByDepth.forEach((value, index) => {
    const barHeight = chartHeight * (value / maxValue);
    ctx.fillStyle = "#52635e";
    ctx.fillRect(left + index * slot, top + chartHeight - barHeight, barWidth, barHeight);
  });

  ctx.fillStyle = "#64716d";
  ctx.textBaseline = "top";
  ctx.textAlign = "left";
  ctx.fillText("0 mm", left, top + chartHeight + 12);
  ctx.textAlign = "right";
  ctx.fillText(`${thickness.toFixed(1)} mm`, width - right, top + chartHeight + 12);
}

function updateResults(result, validation, parameters) {
  setText("#absorbed-value", percent(result.absorbed));
  setText("#reflected-value", percent(result.reflected));
  setText("#transmitted-value", percent(result.transmitted));
  setText(
    "#transmitted-error",
    `T · galat baku MC ± ${preciseFormat.format(result.transmissionSE * 100)} poin persentase`,
  );
  const total = result.absorbed + result.reflected + result.transmitted + result.unfinished;
  setText("#total-value", percent(total));
  setText(
    "#result-summary",
    `${numberFormat.format(parameters.photons)} paket · d = ${parameters.thickness.toFixed(1).replace(".", ",")} mm · seed ${parameters.seed}`,
  );

  setText("#validation-mc", percent(validation.transmitted));
  setText("#validation-bl", percent(Math.exp(-parameters.muA * parameters.thickness)));
  setText(
    "#validation-diff",
    `${preciseFormat.format(Math.abs(validation.transmitted - Math.exp(-parameters.muA * parameters.thickness)) * 100)} poin persentase`,
  );
  const muS = parameters.muSPrime / (1 - parameters.g);
  setText("#mu-s-used", `Untuk parameter ini, μₛ yang dipakai dalam langkah foton = ${preciseFormat.format(muS)} mm⁻¹.`);

  const warning = result.unfinished > 0
    ? `Ada ${preciseFormat.format(result.unfinished * 100)}% paket yang belum selesai dalam batas langkah. Paket ini ditampilkan terpisah.`
    : "Semua paket sudah terserap atau keluar dari lapisan.";
  setText("#run-status", warning);
  drawOutcomeChart(result);
  drawDepthChart(result, parameters.thickness);
}

function runSimulation(event) {
  if (event) event.preventDefault();
  const button = document.querySelector("#run-button");
  const status = document.querySelector("#run-status");
  button.disabled = true;
  status.textContent = "Simulasi sedang dihitung…";

  // Beri kesempatan peramban menampilkan status sebelum menghitung.
  window.setTimeout(() => {
    try {
      const parameters = getParameters();
      latestMain = simulate({ ...parameters, bins: DEFAULTS.bins, maxSteps: DEFAULTS.maxSteps });
      latestValidation = simulate({
        ...parameters,
        muSPrime: 0,
        g: 0,
        seed: (parameters.seed + 1) >>> 0,
        bins: DEFAULTS.bins,
        maxSteps: DEFAULTS.maxSteps,
      });
      updateResults(latestMain, latestValidation, parameters);
    } catch (error) {
      status.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  }, 20);
}

controls.photons.addEventListener("input", updateReadouts);
controls.thickness.addEventListener("input", updateReadouts);
controls.g.addEventListener("input", updateReadouts);
document.querySelector("#controls").addEventListener("submit", runSimulation);
window.addEventListener("resize", () => {
  if (latestMain && latestValidation) {
    drawOutcomeChart(latestMain);
    drawDepthChart(latestMain, Number(controls.thickness.value));
  }
});

updateReadouts();
runSimulation();
