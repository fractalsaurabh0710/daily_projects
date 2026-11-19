const fs = require("fs");
const html = fs.readFileSync(process.argv[2], "utf8");
const src = html.match(/<script>([\s\S]*?)<\/script>/)[1];

// 1. whole-script syntax check (no DOM needed to parse)
new Function(src);
console.log("syntax ok");

// 2. run the pure game-theory half
const pure = src.slice(0, src.indexOf("/* ---------- play"));
const api = new Function(pure + "\nreturn {eat,moves,win,bestMove,verify,memo,ROWS,COLS};")();
const { eat, moves, win, bestMove, verify, memo, ROWS, COLS } = api;

function eq(a, b, m) { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(m + ": " + JSON.stringify(a)); }
eq(eat([3,3,3], 1, 1), [3,1,1], "eat clips columns at and right of c");
eq(eat([3,3,3], 0, 0), [0,0,0], "eating the poison clears the board");
eq(moves([1,0,0]).length, 0, "poison-only has no legal move");
eq(moves([2,1]).length, 2, "L-shape of 3 cookies has 2 moves");

eq(win([1]), false, "1x1 is a loss for the mover");
eq(win([1,1,1,1]), true, "1xN wins by taking everything but the poison");
eq(win([2,2]), true, "2x2 is a first-player win");
eq(win([2,1]), false, "the L of 3 is the losing shape");
// square boards are won by taking (1,1) and mirroring
for (let n = 2; n <= 7; n++) eq(bestMove(new Array(n).fill(n)), [1,1], n+"x"+n+" best move is the diagonal");

const report = verify(6, 6);
if (!report.includes("all agree")) throw new Error("verify() disagreed:\n" + report);
if (win(new Array(COLS).fill(ROWS)) !== true) throw new Error("the shipped board is not a P1 win");

console.log(report);
console.log("\nall assertions passed (" + memo.size + " positions memoized)");
