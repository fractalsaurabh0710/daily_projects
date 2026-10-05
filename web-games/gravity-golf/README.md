# Gravity Golf

Three holes of golf in space. Drag from the white ball to aim, release to launch, and
the planets bend the shot the rest of the way — there is no second touch, so every
stroke is a guess about an orbit. A shot counts only if the ball arrives inside the
hole *and* slower than 300 px/s; screaming past the flag is not a putt.

## Run it

Open `index.html` in a browser. No build, no dependencies.

    node solvable.js   # proves every hole can actually be sunk

## The two things worth knowing

**Softened gravity.** A true 1/r² force goes infinite at a planet's centre, and a
ball that clips the surface gets flung off the screen at a speed no integrator can
follow. Adding the planet's own radius to the squared distance (`d2 = dx² + dy² + r²`)
caps the force at the surface while leaving the far field untouched, so grazing a
planet is a slingshot rather than a numerical explosion.

**Velocity Verlet, not Euler.** Plain Euler integration loses energy every step, so a
ball placed in a circular orbit spirals inward and the game feels broken. Velocity
Verlet is symmetric in time and conserves energy to second order: `solvable.js` puts a
ball in a circular orbit for 40 simulated seconds and the radius drifts by 0.000%.

`solvable.js` lifts `LEVELS`, `accel` and `step` straight out of `index.html` by
brace-matching the function text, so the test can never drift from the game it tests.
It brute-forces 720 launch angles × 109 speeds per hole and reports the first winning
shot it finds — currently 60, 202 and 204 winning shots for holes 1 to 3.
