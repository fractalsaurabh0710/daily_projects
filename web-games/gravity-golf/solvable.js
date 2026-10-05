// Proves every hole in index.html can actually be sunk, by lifting the game's own
// physics out of the HTML (so there is one source of truth) and brute-forcing the
// launch. Run: node solvable.js
const fs = require("fs");
const js = /<script>([\s\S]*)<\/script>/.exec(fs.readFileSync(__dirname + "/index.html", "utf8"))[1];

const grab = name => {               // the function text, matched by brace depth
  const i = js.indexOf("function " + name);
  let depth = 0;
  for (let j = i; ; j++) {
    if (js[j] === "{") depth++;
    else if (js[j] === "}" && --depth === 0) return js.slice(i, j + 1);
  }
};
const head = /const W = [\s\S]*?^\];/m.exec(js)[0];   // W, H, G and LEVELS
const { LEVELS, HOLE_R, SINK, G, accel, step, state } = new Function(`
  ${head}
  let ball, vel, planets;
  ${grab("accel")}
  ${grab("step")}
  return { LEVELS, HOLE_R, SINK, G, accel, step,
           state: (b, v, p) => { ball = b; vel = v; planets = p; return () => ball; } };
`)();

// First, the integrator itself: a ball placed in a circular orbit should stay in one.
// Plain Euler loses energy and spirals in; velocity Verlet holds the radius.
{
  const R = 150, d2 = R * R + 34 * 34;
  const planets = [{ x: 0, y: 0, r: 34, m: 1 }];
  const ball = { x: R, y: 0 };
  const vel = { x: 0, y: Math.sqrt((G * R * R) / (d2 * Math.sqrt(d2))) };
  state(ball, vel, planets);
  let lo = Infinity, hi = 0;
  for (let i = 0; i < 240 * 40; i++) {
    step(1 / 240);
    const d = Math.hypot(ball.x, ball.y);
    lo = Math.min(lo, d); hi = Math.max(hi, d);
  }
  const drift = (hi - lo) / R;
  console.log(`orbit held 40s: radius ${lo.toFixed(2)}-${hi.toFixed(2)}, drift ${(drift * 100).toFixed(3)}%`);
  if (drift > 0.01) throw new Error("integrator is leaking energy");
  const [ax, ay] = accel(0, 0);               // softening: finite force at the centre
  if (!Number.isFinite(ax) || !Number.isFinite(ay)) throw new Error("singularity at planet centre");
}

// One shot: integrate at the game's substep rate until it sinks, crashes or leaves.
function shoot(level, angle, speed) {
  const planets = level.planets.map(([x, y, r, m]) => ({ x, y, r, m }));
  const ball = { x: level.ball[0], y: level.ball[1] };
  const vel = { x: Math.cos(angle) * speed, y: Math.sin(angle) * speed };
  state(ball, vel, planets);
  const [hx, hy] = level.hole;
  for (let i = 0; i < 240 * 14; i++) {
    step(1 / 240);
    for (const p of planets) if (Math.hypot(p.x - ball.x, p.y - ball.y) < p.r + 4) return "crash";
    if (Math.hypot(hx - ball.x, hy - ball.y) < HOLE_R && Math.hypot(vel.x, vel.y) < SINK) return "sunk";
    if (ball.x < -40 || ball.x > 680 || ball.y < -40 || ball.y > 480) return "lost";
  }
  return "stalled";
}

let bad = 0;
LEVELS.forEach((level, n) => {
  const found = [];
  for (let a = -180; a < 180; a += 0.5) {
    for (let s = 60; s <= 600; s += 5) {
      if (shoot(level, (a * Math.PI) / 180, s) === "sunk") found.push([a, s]);
    }
  }
  if (found.length) {
    const [a, s] = found[0];
    console.log(`hole ${n + 1}: sinkable — ${found.length} winning shots, e.g. ${a}deg at ${s}px/s`);
  } else {
    console.log(`hole ${n + 1}: NO WINNING SHOT FOUND`);
    bad++;
  }
});
if (bad) { console.error(`${bad} hole(s) unsinkable`); process.exit(1); }
console.log("all holes sinkable");
