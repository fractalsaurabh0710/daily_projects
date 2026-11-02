// Checks the generator the game ships with, by running the page's own script in
// Node: index.html guards its DOM setup behind `typeof document`, so the module
// below is exactly the code the browser runs.
const fs = require('fs');
const html = fs.readFileSync(__dirname + '/index.html', 'utf8');
const src = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const api = new Function(src + '\nreturn { N, makePuzzle, neighbours };')();
const { N, makePuzzle, neighbours } = api;

let checked = 0;
const firstCells = new Set(), markCounts = new Set();

for (let seed = 1; seed <= 300; seed++) {
  const { sol, marks } = makePuzzle(seed);
  const where = c => `seed ${seed}`;

  // 1. the solution visits every cell exactly once...
  console.assert(sol.length === N * N, `${where()}: wrong length`);
  console.assert(new Set(sol).size === N * N, `${where()}: repeated cell`);
  // 2. ...and every step is a single grid move.
  for (let i = 1; i < sol.length; i++)
    console.assert(neighbours(sol[i - 1]).includes(sol[i]),
      `${where()}: cells ${sol[i - 1]} and ${sol[i]} are not adjacent`);

  // 3. the numbers are 1..k, and walking the solution meets them in order —
  //    which is the rule the game enforces while you drag, so the generated
  //    path is legal play and no puzzle can be unsolvable.
  const seen = [];
  for (const cell of sol) if (marks.has(cell)) seen.push(marks.get(cell));
  console.assert(seen.length === marks.size, `${where()}: numbered cell off the path`);
  console.assert(seen.every((v, i) => v === i + 1), `${where()}: numbers out of order`);
  console.assert(marks.get(sol[0]) === 1, `${where()}: path does not start at 1`);
  console.assert(marks.get(sol[N * N - 1]) === marks.size, `${where()}: path does not end on the last number`);
  console.assert(marks.size >= 3, `${where()}: too few numbers`);

  firstCells.add(sol[0]);
  markCounts.add(marks.size);
  checked++;
}

// 4. backbite should actually wander: the snake seed always starts at cell 0.
console.assert(firstCells.size > 10, `starts barely vary: ${firstCells.size}`);
console.log(`${checked} puzzles valid — ${firstCells.size} distinct start cells, ` +
            `${[...markCounts].sort((a, b) => a - b).join('/')} numbers per puzzle`);
