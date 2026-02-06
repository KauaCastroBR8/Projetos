const dowNames = [
  "Sunday","Monday","Tuesday",
  "Wednesday","Thursday","Friday","Saturday"
];

function pad(n){
  return n.toString().padStart(2,"0");
}

function update() {
  const now = new Date();

  const year  = now.getFullYear();
  const month = now.getMonth()+1;
  const day   = now.getDate();

  const hour = now.getHours();
  const min  = now.getMinutes();
  const sec  = now.getSeconds();

  const dow = dowNames[now.getDay()];

  // progresso do dia
  const secondsToday =
      hour*3600 + min*60 + sec;

  const progress =
      (secondsToday / 86400 * 100)
      .toFixed(2);

  // ---- TEXTO ----
  document.getElementById("year").textContent = year;
  document.getElementById("month").textContent = pad(month);
  document.getElementById("day").textContent = pad(day);
  document.getElementById("dow").textContent = dow;

  document.getElementById("t-hour").textContent = pad(hour);
  document.getElementById("t-minute").textContent = pad(min);
  document.getElementById("t-second").textContent = pad(sec);

  document.getElementById("progress").textContent = progress;
  document.getElementById("bar").textContent = makeBar(progress);

  // ---- RELÓGIO ANALÓGICO ----
  const secDeg  = sec * 6;
  const minDeg  = min * 6 + sec * 0.1;
  const hourDeg = (hour % 12) * 30 + min * 0.5;

  document.getElementById("second")
    .setAttribute("transform", `rotate(${secDeg} 100 100)`);

  document.getElementById("minute")
    .setAttribute("transform", `rotate(${minDeg} 100 100)`);

  document.getElementById("hour")
    .setAttribute("transform", `rotate(${hourDeg} 100 100)`);
}

function makeBar(percent){
  const total = 30;
  const filled = Math.round(percent/100 * total);
  const empty = total - filled;

  return "[ " +
    "/".repeat(filled) +
    ".".repeat(empty) +
    " ]";
}

setInterval(update, 1000);
update();
