# Project Guide - Understanding the math behind the filter magic!

---

## PART 1: THE VERY BASICS - What is this app actually doing?

### Simple way to think about it:

Imagine you have a **photograph**. 

Your photo is made of millions of tiny dots called **pixels**.

Each pixel has three colors mixed together:
- **Red** (how much red)
- **Green** (how much green)
- **Blue** (how much blue)

This app takes these three colors in each pixel and **changes them** using math.

**That's it.**

The math part is like a recipe:
- Old Red + Old Green + Old Blue → New Red
- Old Red + Old Green + Old Blue → New Green
- Old Red + Old Green + Old Blue → New Blue

The app shows you what changed, and also shows you the "recipe" (the math).

---

## PART 2: Understanding X in R^{N x 3} (The Image as a Big Table)

### What does R^{N x 3} mean in super simple words?

Let me break this down letter by letter:

**R** = Real numbers (just regular numbers, like 1, 2, 3.5, etc.)

**N** = How many pixels you have

**x** = "by" or "times" (like 3 x 4 means 3 times 4)

**3** = Always 3 (Red, Green, Blue)

So R^{N x 3} means: "A table of real numbers with N rows and 3 columns."

### Visual way to understand:

If your photo is 10 pixels wide and 10 pixels tall, you have 100 pixels total.

So N = 100.

Now make a table:

```
Row 1 (Pixel 1):     [ R=255,  G=100,  B=50  ]
Row 2 (Pixel 2):     [ R=200,  G=150,  B=75  ]
Row 3 (Pixel 3):     [ R=180,  G=180,  B=100 ]
...
Row 100 (Pixel 100): [ R=50,   G=50,   B=50  ]
```

This table is X in R^{100 x 3}.

Each row = one pixel.
Each column = one color (Red, Green, or Blue).

### Why do we do this?

Because with a table, we can use **multiplication** to change all pixels at once.

Instead of changing pixel 1, then pixel 2, then pixel 3... we can use one "recipe" and apply it to all 100 rows at once.

---

## PART 3: Understanding v' = T v (The Magic Recipe)

### Simple analogy:

Imagine a recipe for lemonade:

**Recipe (T):**
- Take 2 cups of lemon juice
- Add 1 cup of sugar
- Add 3 cups of water

**Input (v):**
- 1 cup of lemon juice = [1, 0, 0]
- 1 cup of sugar = [0, 1, 0]
- 1 cup of water = [0, 0, 1]

**Output (v'):**
- Using the recipe on [1, 0, 0] gives [2, 1, 3]

This is exactly what v' = T v means.

### In color terms:

**Input pixel v:**
```
v = [100 Red, 50 Green, 30 Blue]
```

**Recipe matrix T (a 3x3 table of numbers):**
```
T = [
  [0.5,  0.2,  0.1],
  [0.3,  0.6,  0.2],
  [0.2,  0.2,  0.7]
]
```

**New pixel v':**
To get new Red:
- Take old Red (100) and multiply by first number (0.5) → 50
- Take old Green (50) and multiply by second number (0.2) → 10
- Take old Blue (30) and multiply by third number (0.1) → 3
- Add them: 50 + 10 + 3 = 63 → **New Red = 63**

Repeat for Green and Blue.

**Result: v' = [63, 60, 44]**

The pixel changed!

### Why have a matrix (recipe)?

Because this one T can be used on all 100 pixels (or 1 million pixels) at once.

That's the power of linear algebra.

---

## PART 4: Optional Operations After Transform (Stages After the Recipe)

### Timeline of what happens to your pixel:

**Stage 1: Apply T transform**
- Input: [100R, 50G, 30B]
- Output: [63R, 60G, 44B]

**Stage 2: Optional Grayscale Projection**
- If you checked the "Grayscale Projection" checkbox
- Input: [63R, 60G, 44B]
- Output: [50R, 50G, 50B] (all equal, so it looks gray)

**Stage 3: Tone Controls (Exposure, Contrast, etc.)**
- Input: [50R, 50G, 50B]
- Apply exposure, contrast, saturation formulas
- Output: [52R, 48G, 49B]

**Stage 4: Vibrance**
- Makes dull colors more colorful
- Input: [52R, 48G, 49B]
- Output: [55R, 45G, 47B]

**Stage 5: Sharpen**
- Makes edges more clear
- Compares pixel to neighbors
- Increases difference

**Stage 6: Vignette**
- Darkens edges of photo
- Only applies to pixels near edges

**Stage 7: Optional Least Squares Correction**
- If you checked "Least Squares Correction"
- Applies an extra correction

**Stage 8: Optional PCA Reduction**
- If PCA Components is not 3
- Simplifies the colors

### Key point:

Each stage is like a different filter applied on top of the previous one.

Like applying Instagram filters one after another.

---

## PART 5: Full Backend Pipeline Order (Step by Step)

When you upload a photo, this happens in this order:

### Step 1: Load and Resize
- Read the image file from your computer
- If it's too big, make it smaller (for preview speed)
- Example: 4000 x 3000 → downscale to 1280 x 960

### Step 2: Convert to Table (X)
- Take the image and flatten it into table format
- Each pixel becomes one row
- If image is 1280 x 960, you have 1,228,800 rows
- Each row has 3 columns (R, G, B)

### Step 3: Build the Transform Recipe (T)
This is the most important step.

**Step 3a: Get Preset Matrix T_p**
- You chose a preset like "Cinematic" or "Sepia"
- This preset is a pre-made 3x3 matrix

Example Sepia preset:
```
T_p = [
  [0.393, 0.769, 0.189],
  [0.349, 0.686, 0.168],
  [0.272, 0.534, 0.131]
]
```

**Step 3b: Build Hue Rotation R_theta**
- You moved the Hue slider to 30 degrees
- This creates a rotation in color space
- Think of rotating colors on a color wheel
- Creates new matrix R_theta

**Step 3c: Blend with Identity**
- You moved Filter Strength to 0.5
- Formula: T = (1 - 0.5) × I + 0.5 × (R_theta × T_p)
- Meaning: T = 0.5 × I + 0.5 × (rotated preset)
- Half identity, half rotated preset
- Result: T (final recipe matrix)

### Step 4: Apply Transform to Every Pixel
- Take recipe T
- For each of 1.2 million pixels:
  - Multiply pixel by T
  - Store result

### Step 5: Check Grayscale
- If you checked Grayscale Projection:
  - For each pixel, project it to grayscale line
  - All pixels become [G, G, G] where G is luminance

### Step 6: Apply Tone Controls
- If you moved Exposure slider to 0.5:
  - Brighten by multiplying each value by 2^0.5
- If you moved Contrast slider:
  - Expand values away from 0.5
- If you moved Saturation slider:
  - Move toward or away from gray
- Repeat for Temperature, Tint, Gamma
- Each one modifies the pixel values

### Step 7: Apply Vibrance
- Look at each pixel
- Calculate how saturated it is
- If not very saturated, boost it more
- If already saturated, boost it less

### Step 8: Apply Sharpen
- Look at each pixel and its neighbors
- If it's very different from neighbors, make it MORE different
- Creates edge enhancement

### Step 9: Apply Vignette
- Calculate distance from pixel to center of image
- If pixel is near edge, darken it
- If pixel is near center, don't change it

### Step 10: Check Least Squares
- If Least Squares Correction is checked:
  - Apply extra correction matrix X_hat
  - This tries to make the image colors more balanced

### Step 11: Check PCA
- If PCA Components is less than 3:
  - Reduce to lower-dimensional color space
  - If k=2: forget one weak color direction
  - If k=1: force everything onto dominant direction

### Step 12: Convert Back to Image
- Take the table (now modified)
- Convert back to pixel format
- Create actual image file

### Step 13: Compute Dashboard Metrics
- Calculate Rank, Nullity, Determinant, etc.
- These describe the T matrix
- Show metrics to user

### Step 14: Return Results
- Send edited image to browser
- Send all metrics
- Browser displays everything

---

## PART 6: Controls Explained in Depth

### Control 6.1: PRESET FILTER

**What it is:**
A pre-made color recipe.

**What it does:**
Defines the base matrix T_p.

**Available presets:**

**1. Identity:**
```
[ [1, 0, 0],
  [0, 1, 0],
  [0, 0, 1] ]
```
This means: Don't change anything. Red stays red, green stays green, blue stays blue.

**2. Sepia:**
```
[ [0.393, 0.769, 0.189],
  [0.349, 0.686, 0.168],
  [0.272, 0.534, 0.131] ]
```

Let's trace one pixel with Sepia:
- Input: [100R, 50G, 30B]
- New Red = 0.393×100 + 0.769×50 + 0.189×30 = 39.3 + 38.45 + 5.67 = 83.42
- New Green = 0.349×100 + 0.686×50 + 0.168×30 = 34.9 + 34.3 + 5.04 = 74.24
- New Blue = 0.272×100 + 0.534×50 + 0.131×30 = 27.2 + 26.7 + 3.93 = 57.83
- Output: [83R, 74G, 58B]

Notice: Red went up, Green went down, Blue went way down.
Result: Brownish tone = Sepia look!

**3. Cinematic:**
Makes colors pop. Increases blues and yellows.

**4. Vintage:**
Reduces blues. Makes image look old and faded.

**5. Teal and Gold:**
Increases teal (blue-green) and gold (yellow-red). Trendy look.

**6. Noir:**
Pushes all colors toward gray. Makes blacks darker.

**7. Cool:**
Increases blue. Makes everything cooler/bluer.

**8. Warm:**
Increases red. Makes everything warmer/redder.

**9. No Red:**
Removes all red. Image has only green and blue.

**Effect on image:** HUGE. This is the main color transformation.

---

### Control 6.2: FILTER STRENGTH (0 to 1)

**What it is:**
How much of the preset to use.

**What it does:**
Blends between "no change" and "full preset".

**Formula:**
T = (1 - s) × I + s × (Rotated Preset)

Where s = strength value.

**Examples:**

**s = 0 (strength slider all the way left):**
T = (1 - 0) × I + 0 × (Rotated Preset)
T = 1 × I + 0 × (anything)
T = I (identity)
Result: No color change at all. Image stays original.

**s = 0.5 (strength slider middle):**
T = (1 - 0.5) × I + 0.5 × (Rotated Preset)
T = 0.5 × I + 0.5 × (Rotated Preset)
Result: Half of identity, half of preset. Mild effect.

**s = 1 (strength slider all the way right):**
T = (1 - 1) × I + 1 × (Rotated Preset)
T = 0 × I + 1 × (Rotated Preset)
T = Rotated Preset (full effect)
Result: Full preset applied. Maximum effect.

**Effect on image:** Strong. Controls how visible the preset is.

---

### Control 6.3: HUE ROTATION (-180 to 180 degrees)

**What it is:**
Rotates colors on a color wheel.

**Why it's special:**
It rotates ONLY the color information, NOT the brightness.

**Real world analogy:**
Imagine a color wheel with all colors around a circle.

You can rotate that circle.

Rotate by 30°: Red becomes orange, blue becomes purple, green becomes cyan, etc.

**What happens technically:**
1. Image is converted from RGB to YIQ space
   - Y = brightness
   - IQ = color information
2. In IQ space, only the color part is rotated
3. Converted back to RGB

**Formula:**
T_hue = YIQ^{-1} × R_theta × YIQ

Don't worry about this formula. Just remember: **only colors rotate, brightness stays same**.

**Examples:**

**+90 degrees:**
- Red → Blue
- Blue → Cyan
- Green → Purple

**-90 degrees:**
- Red → Yellow
- Green → Magenta

**180 degrees:**
- Red → Cyan
- Green → Magenta
- Blue → Yellow

**Effect on image:** Strong. All colors shift on the wheel.

---

### Control 6.4: EXPOSURE (-1.5 to 1.5)

**What it is:**
Make image brighter or darker.

**Formula:**
new_pixel = old_pixel × 2^e

Where e = exposure value.

**Real world analogy:**
Like opening or closing camera aperture.

**Math explanation:**

**e = 0:**
new = old × 2^0 = old × 1 = old
Result: No change.

**e = 0.5:**
new = old × 2^0.5 = old × 1.414
Result: Everything gets 1.414x brighter.
Pixel [100, 100, 100] → [141, 141, 141]

**e = 1:**
new = old × 2^1 = old × 2
Result: Everything doubles.
Pixel [100, 50, 75] → [200, 100, 150]

**e = -0.5:**
new = old × 2^{-0.5} = old × 0.707
Result: Everything gets dimmer.
Pixel [100, 100, 100] → [71, 71, 71]

**e = -1:**
new = old × 2^{-1} = old × 0.5
Result: Everything gets half as bright.
Pixel [100, 50, 75] → [50, 25, 37]

**Effect on image:** Strong. Makes entire image brighter or darker uniformly.

---

### Control 6.5: CONTRAST (-1 to 1)

**What it is:**
Make differences between light and dark areas bigger or smaller.

**Formula:**
new = clip((old - 0.5) × (1 + c) + 0.5)

Where c = contrast value.

**Real world analogy:**
Like turning up or down the contrast knob on a TV.

**Math explanation:**

The magic number here is **0.5** (mid-gray in normalized 0-1 scale).

**c = 0:**
new = (old - 0.5) × 1 + 0.5 = old
Result: No change.

**c = 0.5 (positive contrast):**
new = (old - 0.5) × 1.5 + 0.5

Let's trace:
- Old = 0.8 (light): new = (0.8 - 0.5) × 1.5 + 0.5 = 0.3 × 1.5 + 0.5 = 0.95 (even lighter!)
- Old = 0.5 (gray): new = (0.5 - 0.5) × 1.5 + 0.5 = 0 + 0.5 = 0.5 (stays same)
- Old = 0.2 (dark): new = (0.2 - 0.5) × 1.5 + 0.5 = -0.3 × 1.5 + 0.5 = 0.05 (even darker!)

Result: Lights get lighter, darks get darker. More "pop".

**c = -0.5 (negative contrast):**
new = (old - 0.5) × 0.5 + 0.5

Let's trace:
- Old = 0.8 (light): new = (0.8 - 0.5) × 0.5 + 0.5 = 0.3 × 0.5 + 0.5 = 0.65 (less light)
- Old = 0.5 (gray): new = (0.5 - 0.5) × 0.5 + 0.5 = 0.5 (stays same)
- Old = 0.2 (dark): new = (0.2 - 0.5) × 0.5 + 0.5 = -0.3 × 0.5 + 0.5 = 0.35 (less dark)

Result: Lights get darker, darks get lighter. Everything flattens. Washed out look.

**Effect on image:** Strong. Changes punch/drama of image.

---

### Control 6.6: SATURATION (-1 to 1)

**What it is:**
How vibrant the colors are.

**Real world analogy:**
Imagine color paint mixed with gray.

More color paint = more saturated = more vibrant.
More gray = less saturated = more dull.

**Formula:**
1. Find luminance (brightness): g = 0.299×R + 0.587×G + 0.114×B
2. This g is the "gray" version of the pixel
3. new = clip(g + (old - g) × (1 + s))

Where s = saturation value.

**Math explanation:**

**s = 0:**
new = g + (old - g) × 1 = g + old - g = old
Result: No change.

**s = 0.5 (increase saturation):**
new = g + (old - g) × 1.5

Let's say:
- old = [100R, 50G, 50B]
- luminance g = [70, 70, 70] (the gray version)
- new_R = 70 + (100 - 70) × 1.5 = 70 + 45 = 115
- new_G = 70 + (50 - 70) × 1.5 = 70 - 30 = 40
- new_B = 70 + (50 - 70) × 1.5 = 70 - 30 = 40
- Result: [115R, 40G, 40B]

Notice: Red got more red-ish, Green and Blue got more blue-ish.
Colors are now MORE different from gray = MORE saturated!

**s = -0.5 (decrease saturation):**
new = g + (old - g) × 0.5

- new_R = 70 + (100 - 70) × 0.5 = 70 + 15 = 85
- new_G = 70 + (50 - 70) × 0.5 = 70 - 10 = 60
- new_B = 70 + (50 - 70) × 0.5 = 70 - 10 = 60
- Result: [85R, 60G, 60B]

Colors are now LESS different from gray = LESS saturated! More grayish, muted.

**Effect on image:** Strong. Makes colors vivid or muted.

---

### Control 6.7: VIBRANCE (-1 to 1)

**What it is:**
Like saturation, but SMART. Boosts dull colors more than already-vibrant colors.

**Real world analogy:**
Imagine you're painting with watercolors.

Your brush automatically uses more paint on dull areas and less paint on already-vibrant areas.

**Formula:**
1. For each pixel, calculate current saturation: sat = max_channel - min_channel
2. If sat is low (dull color): boost more
3. If sat is high (already vibrant): boost less
4. boost = a × (1 - sat)  [where a is vibrance amount]
5. new = old + (old - gray) × boost

**Real example:**

Pixel 1 (dull): [70R, 65G, 68B]
- sat = 70 - 65 = 5 (very low saturation)
- boost = 0.5 × (1 - 5) = huge boost!
- Gets boosted a LOT

Pixel 2 (vivid): [255R, 10G, 10B]
- sat = 255 - 10 = 245 (very high saturation)
- boost = 0.5 × (1 - 245) = very small boost
- Stays mostly the same

Result: Dull parts get more vibrant. Already-vibrant parts stay vibrant. Natural looking.

**Effect on image:** Moderate to strong. Smarter than saturation.

---

### Control 6.8: TEMPERATURE (-1 to 1)

**What it is:**
Make image warmer (more red/orange) or cooler (more blue).

**Formula:**
- R_new = clip(R + 0.08 × tau)
- B_new = clip(B - 0.08 × tau)
- G stays the same

Where tau = temperature value.

**Examples:**

**tau = 1 (warm, slider all right):**
- R increases by 0.08
- B decreases by 0.08
- Result: More red, less blue = warmer = sunset feeling

**tau = -1 (cool, slider all left):**
- R decreases by 0.08
- B increases by 0.08
- Result: Less red, more blue = cooler = ice feeling

**Real pixel example:**

Original: [200R, 150G, 100B] (neutral)

With tau = 1 (warm):
- New_R = 200 + 0.08 = 200.08
- New_G = 150 (no change)
- New_B = 100 - 0.08 = 99.92
- Result: [200R, 150G, 100B] → [200R, 150G, 100B]
(Slight shift toward red, slight shift away from blue)

**Effect on image:** Moderate. Changes color temperature feeling.

---

### Control 6.9: TINT (-1 to 1)

**What it is:**
Shift between green and magenta (purple-red).

**Formula:**
- G_new = clip(G + 0.06 × eta)

Where eta = tint value.

**Examples:**

**eta = 1 (positive, slider right):**
- G increases
- Result: More green = greenish tint

**eta = -1 (negative, slider left):**
- G decreases
- Result: Less green = more magenta (because magenta = R + B, no G)

**Effect on image:** Weak to moderate. Subtle color shift.

---

### Control 6.10: GAMMA (0.3 to 2.2)

**What it is:**
Power-law remapping. Changes how dark/light values are distributed.

**Formula:**
new = old ^ (1/gamma)

**Real world analogy:**
Like adjusting monitor brightness, but non-uniformly.

---

**Examples:**

**gamma = 1:**
new = old ^ 1 = old
Result: No change.

**gamma = 2 (lift shadows):**
new = old ^ 0.5

Let's trace:
- old = 0.25 (dark): new = 0.25 ^ 0.5 = 0.5 (much lighter!)
- old = 0.5 (mid): new = 0.5 ^ 0.5 = 0.707 (lighter)
- old = 1 (bright): new = 1 ^ 0.5 = 1 (stays same)

Result: Dark areas get brighter, mid-tones get brighter, bright areas stay same.
Overall brightening, but especially darks.

**gamma = 0.5 (darken shadows):**
new = old ^ 2

Let's trace:
- old = 0.25 (dark): new = 0.25 ^ 2 = 0.0625 (much darker!)
- old = 0.5 (mid): new = 0.5 ^ 2 = 0.25 (darker)
- old = 1 (bright): new = 1 ^ 2 = 1 (stays same)

Result: Dark areas get darker, bright areas stay bright. Increases contrast in non-uniform way.

**Effect on image:** Strong. Changes tonal distribution dramatically.

---

### Control 6.11: SHARPEN (0 to 2)

**What it is:**
Unsharp mask. Makes edges more crisp by enhancing differences.

**Formula:**
1. Create blurry version of image: blur
2. new = clip(old + alpha × (old - blur))

Where alpha = sharpen amount.

**Real world analogy:**
Subtract a blurry version from the original.

Blurry version has no detail. Original - Blurry = detail.

Add detail back = sharper image.

**Examples:**

**alpha = 0:**
new = old + 0 × (old - blur) = old
Result: No change.

**alpha = 0.5:**
new = old + 0.5 × (old - blur)

At an edge (big jump from light to dark):
- old = 200 (bright side)
- blur = 150 (blurry version averaged)
- detail = 200 - 150 = 50
- new = 200 + 0.5 × 50 = 225 (even brighter!)

And on dark side:
- old = 100 (dark side)
- blur = 150 (blurry version averaged)
- detail = 100 - 150 = -50
- new = 100 + 0.5 × (-50) = 75 (even darker!)

Result: Edge becomes sharper and more defined.

**Effect on image:** Moderate. Makes edges crisper, details pop.

---

### Control 6.12: VIGNETTE (0 to 1)

**What it is:**
Darken edges of photo. Like old camera or spotlight effect.

**Formula:**
1. For each pixel, calculate distance from center: r
2. Calculate mask: m = clip(1 - s × (1.9r)^1.4, 0.25, 1)
3. new = old × m

Where s = vignette strength.

**Real world analogy:**
Imagine a spotlight shining from center of image.

Edges are dark, center is bright.

**Math explanation:**

At center (r = 0):
- m = clip(1 - s × 0, 0.25, 1) = clip(1, 0.25, 1) = 1 (no darkening)

At edges (r = large):
- m = clip(1 - s × (large)^1.4, 0.25, 1) = clip(small value, 0.25, 1) = 0.25 to 0.5 (darkening!)

**Effect on image:** Moderate. Adds dramatic edges.

---

### Control 6.13: PCA COMPONENTS (1 to 3)

**What it is:**
The only control that uses actual PCA (Principal Component Analysis).

**Important: This is real math that university students learn!**

### First: What is PCA in simple words?

Imagine you have a flock of sheep.

Each sheep has:
- Height
- Weight
- Wool thickness

Most sheep follow a pattern:
- Tall sheep tend to be heavy
- Short sheep tend to be light

So you don't really need all three measurements.

You can describe each sheep with just two numbers:
- "Size" (height + weight combined)
- "Wool"

You've compressed 3 measurements to 2.

**That's PCA in a nutshell: Find the main patterns in your data and ignore the rest.**

### In color terms:

Each pixel has 3 colors: R, G, B.

But colors are not independent!

If a pixel is very red, it's probably not very blue (most of the time).

Red pixels tend to have certain ratios of G and B.

**PCA finds these patterns and removes the weak/unnecessary color information.**

### Algorithm step by step:

**Step 1: Normalize**
- Take all pixels: X
- Scale to 0-1 range: x = X / 255

**Step 2: Calculate mean**
- For all pixels, average them: μ = mean(x)
- Example: μ = [0.5, 0.4, 0.6] (average red, green, blue)

**Step 3: Center**
- Subtract mean from each pixel: x_c = x - μ
- This removes the "average" to focus on variation

**Step 4: Calculate covariance**
- Covariance = how much channels vary together
- C = (x_c^T × x_c) / (N-1)
- This creates a 3×3 matrix
- Shows which colors go together

**Step 5: Find eigenvectors**
- Special vectors of the covariance matrix
- First eigenvector = direction of most variation
- Second eigenvector = direction of next most variation
- Third eigenvector = least variation

**Real example:**

If image is mostly red with some green, but very little blue:
- First eigenvector might be [1, 0.5, 0.1] (red-ish direction)
- Second eigenvector might be [0, 1, 0] (green direction)
- Third eigenvector might be [0, 0, 1] (blue direction)

**Step 6: Choose k components**

**If k = 3 (PCA slider at "3"):**
- Keep all 3 eigenvectors
- No compression
- Image looks exactly the same
- Full 3D color space

**If k = 2:**
- Keep first 2 eigenvectors
- Ignore third
- Compression!
- Blue variation is removed (or heavily reduced)
- Image loses one color dimension
- Image looks flatter, less colorful

**If k = 1:**
- Keep only first eigenvector
- Heavy compression
- Image forced onto single color direction
- Extreme color reduction
- Image looks like grayscale-ish but along one weird direction

**Step 7: Reconstruct**
- Project each centered pixel onto chosen k vectors
- Multiply back
- Add mean back
- x_recon = (x_c @ basis) @ basis^T + μ

### Visual example:

**3D color space** (all 3 colors used):
```
        B (Blue)
       /|
      / |
     /  |
    /   |--- G (Green)
   /   /
  |___/
  R (Red)
```

Each pixel is a point in this 3D space.

**PCA with k=2** (remove blue):
```
        
        
        
        
        
  /---\
  R---G
```

2D space. Remove blue. Pixels are projected down to RG plane.

**PCA with k=1** (keep only first direction):
```
    \
     \
    --*--
     /
    /
```

1D space. Pixels are projected onto single line.

### Effect on image:

**k=3:** No change. Full color.

**k=2:** Moderate color loss. Image looks less colorful, slightly muted.

**k=1:** Extreme color loss. Image looks almost grayscale, very compressed, artistic.

**Effect on image:** Variable, depends on k.

---

### Control 6.14: PREVIEW SIZE (600 to image max)

**What it is:**
How big a preview to compute.

**Why this exists:**
Processing a 4000×3000 image is slow.
Processing a 1280×960 image is fast.

**How it works:**
1. If you choose Preview Size = 800
2. Backend downscales image so max dimension = 800
3. Processes smaller version
4. Shows in preview area

**Does NOT affect:**
- Downloaded file (download is always full resolution)
- Math calculations (done on preview size only)

**Effect on app:** Controls speed/quality tradeoff. Larger = slower, better looking.

---

### Control 6.15: GRAYSCALE PROJECTION

**What it is:**
A geometric projection in 3D space.

**Important: This is a LINEAR ALGEBRA CONCEPT!**

### First: What is projection in simple words?

Imagine:
- You're standing in 3D room (X, Y, Z axes)
- You shine a light from above (along Z axis)
- Your shadow on the floor is your "projection" to 2D

**Projection = dropping a dimension while keeping important info.**

### In color terms:

RGB space is 3D.

There's a special direction called **luminance** (brightness).

Luminance vector: **u = [0.299, 0.587, 0.114]**

This means: Luminance is roughly 30% red + 59% green + 11% blue.

(Why? Because human eyes are most sensitive to green!)

**When you enable Grayscale Projection:**
- Every pixel is projected onto the luminance line
- Imagine shining light along luminance direction
- Shadow on luminance line = pixel's grayscale version

### Formula:

For pixel v and luminance direction u:

proj_u(v) = ((v · u) / (u · u)) × u

Let's break this down:

**v · u** = dot product = how much pixel aligns with luminance direction

**u · u** = how "long" the luminance vector is (a normalization)

**((v · u) / (u · u)) × u** = project to that direction

### Real example:

Pixel v = [100R, 50G, 30B]
Luminance u = [0.299, 0.587, 0.114]

**Step 1: Calculate v · u**
= 100 × 0.299 + 50 × 0.587 + 30 × 0.114
= 29.9 + 29.35 + 3.42
= 62.67

**Step 2: Calculate u · u**
= 0.299 × 0.299 + 0.587 × 0.587 + 0.114 × 0.114
= 0.0894 + 0.3446 + 0.0130
= 0.447

**Step 3: Calculate projection**
projection_strength = 62.67 / 0.447 = 140.2

**Step 4: Calculate new pixel**
new_v = 140.2 × u
= 140.2 × [0.299, 0.587, 0.114]
= [41.9, 82.4, 16.0]

Wait, this doesn't look right. Let me recalculate...

Actually, let's use a simpler approach:

Luminance value L = 0.299×R + 0.587×G + 0.114×B
= 0.299×100 + 0.587×50 + 0.114×30
= 62.67

After projection: pixel becomes [62.67, 62.67, 62.67]

All three channels equal = gray!

### Why this is useful:

**Before projection:**
- Pixel is [100R, 50G, 30B]
- Mix of all three colors
- Somewhat reddish

**After projection:**
- Pixel is [63R, 63G, 63B]
- All channels equal
- Pure gray, no hue

But the gray level (63) is based on the luminance formula, not just averaging (100+50+30)/3 = 60.

So it preserves brightness perception better than naive averaging.

**Effect on image:** Makes image grayscale, but brightness is perceived correctly.

---

### Control 6.16: LEAST SQUARES CORRECTION

**What it is:**
A mathematical optimization to balance image colors.

**Important: This is an OPTIMIZATION PROBLEM!**

### First: What is least squares?

Imagine you want to fit a line through scattered dots.

You can't make the line pass through every dot.

But you can find the best line that minimizes total distance to all dots.

**That's least squares: finding best fit when perfect fit is impossible.**

### In color correction:

The app wants to:
1. Keep red channel roughly red
2. Keep green channel roughly green
3. Keep blue channel roughly blue
4. Make global color balance neutral (gray)

But there's no single correction that satisfies all of this perfectly for every pixel.

So it finds the **best compromise**: the least squares approximation.

### Algorithm:

**Step 1: Define anchor constraints**

Create two matrices A and B:

**A (what we have):**
```
A = [
  [1, 0, 0],      <- Red basis
  [0, 1, 0],      <- Green basis
  [0, 0, 1],      <- Blue basis
  [mean_R, mean_G, mean_B]  <- Average color of image
]
```

**B (what we want):**
```
B = [
  [1, 0, 0],      <- Keep red as red
  [0, 1, 0],      <- Keep green as green
  [0, 0, 1],      <- Keep blue as blue
  [mean_gray, mean_gray, mean_gray]  <- Make average color neutral gray
]
```

Where mean_gray = (mean_R + mean_G + mean_B) / 3

**Step 2: Solve for best correction matrix X_hat**

Find X_hat that minimizes:

||A × X_hat - B||_F^2

This reads as: "minimize the Frobenius norm squared of (A × X_hat - B)"

Frobenius norm is like distance in high-dimensional space.

We want A × X_hat to be as close to B as possible.

The solution (using linear algebra):

X_hat = (A^T × A)^{-1} × A^T × B

Or simpler, use numpy's lstsq function.

**Step 3: Apply correction (if enabled)**

For each pixel x:

x_corrected = x × X_hat

### Real example:

Let's say:
- mean_R = 150 (image is too red)
- mean_G = 100 (greenish)
- mean_B = 80 (blueish)
- mean_gray = (150 + 100 + 80) / 3 = 110

Solver creates X_hat something like:
```
X_hat = [
  [0.85, 0.05, 0.05],
  [0.05, 1.10, 0.05],
  [0.05, 0.05, 1.30]
]
```

When applied:
- Red gets multiplied by 0.85 (reduced, because image is too red)
- Green gets multiplied by 1.10 (increased, to balance)
- Blue gets multiplied by 1.30 (increased, to balance)

Result: Colors become more balanced!

### Why "Approximation" matrix?

Because this matrix is the least-squares **approximation**.

It doesn't fix every pixel perfectly.

But it finds the best single matrix that improves the whole image overall.

**Effect on image:** Subtle to moderate. Balances colors globally.

---

## PART 7: Understanding Least Squares Deep Dive

(This is in the markdown already, keeping for reference)

---

## PART 8: Understanding Grayscale Projection Deep Dive

(This is in the markdown already, keeping for reference)

---

## PART 9: Understanding PCA Deep Dive

(This is in the markdown already, keeping for reference)

---

## PART 10: Main Top-Strip Formulas

These are the live formulas shown at top of dashboard.

### Transformation tile shows:

T = (1-s)I + s R_θ T_p

This is the current blend formula.
- s = strength slider value
- R_θ = hue rotation matrix (θ in degrees)
- T_p = preset matrix
- I = identity matrix

Below this formula, shows:
- rank(T) = how many independent color dimensions
- det(T) = volume scaling factor

### Projection tile shows:

**If grayscale ON:**
proj_u(v) = ((v·u)/(u·u))u

**If grayscale OFF:**
v_out = v' (just the transformed pixel, no projection)

### Least Squares tile shows:

X_hat = arg min_X ||AX - B||_F^2

This is the optimization problem.

Below:
- If LS correction is OFF: "X_hat computed only" (calculated but not used)
- If LS correction is ON: "X_out = X × X_hat" (applied to pixels)

### Covariance tile shows:

C = (1/(N-1)) X_c^T X_c

Where X_c = centered pixels (X - mean)

Below:
- λ₁ = largest eigenvalue (most variation)
- ρ₁ = PC1 variance % (percent explained by first component)

---

## PART 11: The Term-by-Term Table (Simple Version)

| Term | Meaning | How Computed | Impact |
|---|---|---|---|
| **Transformation** | Full color recipe (3x3 matrix) | T = (1-s)I + s(R_θ T_p) | Directly changes all pixel colors |
| **Projection** | Maps 3D RGB to 1D luminance line | proj_u(v) = ((v·u)/(u·u))u | Removes color, keeps brightness |
| **Least Squares** | Best-fit color balance matrix | Solves min ||AX - B||_F^2 | Balances global color tone |
| **Covariance** | Measure of color variation together | C = (1/(N-1))(X-μ)^T(X-μ) | Diagnostic only |
| **Rank** | Number of independent dimensions | Linear algebra rank computation | Shows if colors are compressed |
| **Nullity** | Missing dimensions (3 - rank) | 3 - rank | Shows color information loss |
| **cond(T)** | How sensitive is the transform | Ratio of largest to smallest singular value | Shows numerical stability |
| **Invertible** | Can T be reversed? | Check if |det(T)| > 10^-8 | Shows if transform is reversible |
| **trace(T)** | Sum of diagonal entries | T[0,0] + T[1,1] + T[2,2] | Diagnostic |
| **||T||_F** | Total magnitude of T | √(sum of all T_ij squared) | Shows transform strength |
| **PC1 Variance** | % of variation in first PC | λ₁ / (λ₁ + λ₂ + λ₃) × 100% | Shows if one color dominates |
| **Dynamic Range** | Brightness spread of output | max(pixel) - min(pixel) | Shows output contrast |
| **Transformation Matrix** | Numeric 3x3 T | From preset + hue + strength | Used to transform every pixel |
| **RREF** | Row-reduced form of T | Gaussian elimination | Diagnostic (shows structure) |
| **Covariance Matrix** | 3x3 color variation | From centered pixels | Diagnostic |
| **LS Approximation Matrix** | Best-fit correction | Least squares solve | Applied if LS enabled |
| **Eigen Spectrum** | Principal color directions | Eigenvectors of covariance | Diagnostic (shows color modes) |
| **Explained Variance** | % variance per component | λ_i / sum(λ) | Shows which colors matter most |
| **Dominant Eigenvector** | Direction of most variation | First eigenvector | Diagnostic (main color direction) |
| **Color Statistics** | Summary of colors | Mean/std on normalized pixels | Diagnostic |
| **Mean RGB** | Average color | Mean per channel | Diagnostic |
| **Std RGB** | Spread of color | Std dev per channel | Diagnostic |

---

## PART 12: What changes the image vs. what's just diagnostic

### CHANGES THE IMAGE:
1. ✅ Preset Filter (base colors)
2. ✅ Filter Strength (blend amount)
3. ✅ Hue Rotation (color wheel rotation)
4. ✅ Exposure (brightness)
5. ✅ Contrast (light/dark spread)
6. ✅ Saturation (color vividness)
7. ✅ Vibrance (smart saturation)
8. ✅ Temperature (warm/cool)
9. ✅ Tint (green/magenta)
10. ✅ Gamma (dark/light distribution)
11. ✅ Sharpen (edge enhancement)
12. ✅ Vignette (edge darkening)
13. ✅ PCA Components (color reduction)
14. ✅ Grayscale Projection (if enabled)
15. ✅ Least Squares Correction (if enabled)

### DIAGNOSTIC ONLY (don't change image):
1. ❌ Rank, Nullity, det, cond, Invertible
2. ❌ trace, ||T||_F
3. ❌ Dynamic Range
4. ❌ Transformation Matrix (shown for reference)
5. ❌ RREF
6. ❌ Covariance Matrix
7. ❌ Eigen Spectrum
8. ❌ Explained Variance
9. ❌ Dominant Eigenvector
10. ❌ Mean RGB, Std RGB
11. ❌ PC1 Variance (just reports result)

---

## PART 13: Summary: The Full Story in Simple Terms

**"This app is a visual linear algebra demonstration.**

**Step 1: Image representation**
We treat an image as a matrix X with N pixels and 3 color columns.
Each row is [Red, Green, Blue] for one pixel.

**Step 2: Linear transform**
We apply a 3x3 transformation matrix T.
For each pixel: new_pixel = T × old_pixel.

**Step 3: Optional projection**
If Grayscale Projection is on, we project each pixel onto the luminance line.
This removes color but keeps brightness.

**Step 4: Tone controls**
We apply exposure, contrast, saturation, etc.
Each changes pixel values according to formulas.

**Step 5: Quality improvement**
Vibrance smartly boosts dull colors.
Sharpen enhances edges.
Vignette darkens edges.

**Step 6: Color balance**
Least Squares Correction finds the best global color balance matrix.

**Step 7: Dimensionality reduction**
PCA reduces to k color dimensions.
This compresses color information.

**Step 8: Analysis**
Dashboard shows rank, eigenvalues, covariance.
These describe the mathematical properties of the transformation."

---

## PART 14: FAQ and Quick Clarifications

### Q: What does "matrix" mean in simple terms?
A: A table of numbers arranged in rows and columns.

### Q: What does "eigenvalue" mean?
A: A special number that describes how much variation happens in a particular direction.

### Q: What does "covariance" mean?
A: How much two things vary together. If one goes up, does the other also go up? That's covariance.

### Q: What does "normalize" mean?
A: Scale values to a standard range, usually 0-1 or 0-255.

### Q: What does "clip" mean?
A: Clamp values to a range. If value > 255, make it 255. If value < 0, make it 0.

### Q: Why 0.299, 0.587, 0.114 for luminance?
A: Human eyes are more sensitive to green than red, and least sensitive to blue.
These are the biological weights.

### Q: Why use matrix multiplication instead of just changing RGB separately?
A: Because matrix multiplication lets us apply one formula to all pixels at once,and it captures color mixing (e.g., R affects output G).

### Q: What's the difference between Saturation and Vibrance?
A: Saturation changes all colors equally. Vibrance adapts: it boosts dull colors more.

### Q: What does "Frobenius norm" mean?
A: Square root of sum of squares of all matrix elements. It's the "magnitude" of a matrix.

### Q: Why is Least Squares useful?
A: Because we can't always satisfy all color constraints perfectly. Least Squares finds the best compromise.

### Q: What happens if I set PCA to 1?
A: Colors are collapsed to 1 dimension. Image looks extremely compressed, almost one-color.

---

## Done!

You now understand every single concept from first principles! 

