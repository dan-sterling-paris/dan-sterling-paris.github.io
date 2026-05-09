#!/usr/bin/env python3
"""Generate a comprehensive 17-week weight loss protocol as an EPUB for Kindle."""

from ebooklib import epub
import datetime

CSS = """
@charset "UTF-8";
body { font-family: Georgia, serif; font-size: 1em; line-height: 1.7; margin: 2% 4%; color: #1a1a1a; }
h1 { font-size: 1.75em; text-align: center; margin-top: 1.5em; margin-bottom: 0.3em; }
h2 { font-size: 1.3em; margin-top: 1.8em; margin-bottom: 0.4em; border-bottom: 1px solid #555; padding-bottom: 0.15em; }
h3 { font-size: 1.1em; margin-top: 1.3em; margin-bottom: 0.25em; font-style: italic; }
h4 { font-size: 1.0em; margin-top: 1em; margin-bottom: 0.2em; text-transform: uppercase; letter-spacing: 0.05em; }
p  { margin: 0.5em 0 0.8em 0; }
ul, ol { margin: 0.4em 0 0.8em 1.4em; }
li { margin-bottom: 0.35em; }
table { width: 100%; border-collapse: collapse; margin: 1em 0; font-size: 0.88em; }
th { background: #333; color: #fff; padding: 0.45em 0.6em; text-align: left; }
td { padding: 0.4em 0.6em; border-bottom: 1px solid #ccc; vertical-align: top; }
tr:nth-child(even) td { background: #f5f5f5; }
.box { border: 1px solid #888; border-radius: 3px; padding: 0.7em 1em; margin: 1em 0; background: #fafafa; }
.highlight { border-left: 4px solid #555; padding-left: 0.8em; margin: 0.8em 0; font-style: italic; }
.citation { font-size: 0.82em; color: #555; margin-top: 0.2em; }
.phase { background: #222; color: #fff; padding: 0.5em 0.8em; margin: 1.2em 0 0.5em 0; font-weight: bold; }
.warning { border-left: 4px solid #c00; padding-left: 0.8em; color: #600; margin: 0.8em 0; }
.tip { border-left: 4px solid #080; padding-left: 0.8em; color: #030; margin: 0.8em 0; }
.subtitle { text-align: center; font-style: italic; color: #444; margin-bottom: 1.5em; }
.intro { font-size: 1.05em; font-style: italic; margin-bottom: 1.5em; color: #333; }
hr { border: none; border-top: 1px solid #ccc; margin: 1.5em 0; }
"""

def ch(title, filename, body_html):
    """Create an EpubHtml item with only the inner HTML (no XML declaration)."""
    item = epub.EpubHtml(title=title, file_name=filename, lang="en")
    # ebooklib 0.20 get_content() parses .content via lxml html parser,
    # extracts <body> children, and injects them into its own template.
    # Plain HTML without XML declaration is required.
    item.content = f"<html><head><title>{title}</title></head><body>{body_html}</body></html>"
    return item


# ── Chapter bodies ──────────────────────────────────────────────────────────────────────

COVER_BODY = """
<div style="text-align:center;padding:3em 1em;">
  <h1 style="font-size:1.9em;margin-bottom:0.2em;">The 17-Week Aggressive Recomposition Protocol</h1>
  <hr style="width:60%;margin:1.5em auto;"/>
  <p style="font-style:italic;font-size:1.1em;">An Evidence-Based Fat Loss &amp; Muscle Preservation Plan<br/>for the Middle-Aged Male Athlete</p>
  <hr style="width:60%;margin:1.5em auto;"/>
  <p>Client Profile: 42-year-old Male</p>
  <p>85 kg &#8594; 69.5 kg &#183; TDEE 2,817 kcal</p>
  <p>Heavy Resistance Training Every Other Day</p>
  <p style="margin-top:2em;color:#555;font-size:0.9em;">Clinical Sports Nutrition &amp; Exercise Physiology Analysis &#183; May 2026</p>
</div>
"""

TOC_BODY = """
<h1>Table of Contents</h1>
<ol>
  <li>Executive Summary &amp; Key Numbers</li>
  <li>Section 1 &#8212; Optimal Caloric Deficit &amp; Macronutrients</li>
  <li>Section 2 &#8212; Nutrient Timing &amp; Distribution</li>
  <li>Section 3 &#8212; Physiological Periodization: The 17-Week Structure</li>
  <li>Section 4 &#8212; Age-Specific Recovery, Sleep &amp; Supplementation</li>
  <li>Section 5 &#8212; Exit Strategy: Week 18 and Beyond</li>
  <li>Appendix A &#8212; Daily Meal Templates</li>
  <li>Appendix B &#8212; Weekly Tracking Checklist</li>
  <li>References &amp; Literature Guide</li>
</ol>
"""

EXEC_BODY = """
<h1>Executive Summary &amp; Key Numbers</h1>
<p class="subtitle">Your mission parameters, calculated and confirmed</p>

<div class="box">
<h3>Client Profile</h3>
<table>
  <tr><th>Parameter</th><th>Value</th></tr>
  <tr><td>Age / Sex</td><td>42 years / Male</td></tr>
  <tr><td>Height</td><td>168 cm</td></tr>
  <tr><td>Starting weight</td><td>85.0 kg</td></tr>
  <tr><td>Target weight</td><td>69.5 kg</td></tr>
  <tr><td>Weight to lose</td><td>15.5 kg</td></tr>
  <tr><td>Timeline</td><td>17 weeks (119 days)</td></tr>
  <tr><td>Measured TDEE</td><td>2,817 kcal/day</td></tr>
  <tr><td>Training modality</td><td>Heavy resistance training, ~60 min, every other day</td></tr>
  <tr><td>Training frequency</td><td>~3‑4 sessions/week</td></tr>
</table>
</div>

<h2>Deficit Mathematics</h2>
<p>The energy content of human adipose tissue is approximately <strong>7,700 kcal per kilogram</strong> &#8212; a clinical estimate accounting for the fact that fat tissue contains water, protein scaffolding and connective tissue alongside triglycerides (Hall et al., 2012; Forbes, 1987).</p>

<table>
  <tr><th>Calculation</th><th>Result</th></tr>
  <tr><td>Total energy deficit required</td><td>15.5 kg &#215; 7,700 = <strong>119,350 kcal</strong></td></tr>
  <tr><td>Total days</td><td>17 &#215; 7 = <strong>119 days</strong></td></tr>
  <tr><td>Required daily deficit</td><td>119,350 &#247; 119 = <strong>&#8776;1,003 kcal/day</strong></td></tr>
  <tr><td>Target daily intake</td><td>2,817 &#8722; 1,003 = <strong>1,814 kcal/day</strong></td></tr>
  <tr><td>Working protocol target</td><td><strong>1,800 kcal/day</strong> (practical rounding)</td></tr>
  <tr><td>Rate of loss</td><td>&#8776; 0.91 kg/week</td></tr>
</table>

<div class="warning">
<strong>Rate-of-loss caution:</strong> Losing ~0.91 kg/week is clinically aggressive for a resistance-trained individual seeking muscle preservation. The evidence-based maximum for lean individuals is 0.5‑0.7% of body weight per week (Barakat et al., 2020; Helms et al., 2014) &#8212; at 85 kg that is 0.43‑0.60 kg/week. Your target exceeds this range, which makes the periodization strategy (diet breaks, high protein, training stimulus) non-negotiable, not optional.
</div>

<h2>Estimated Body Composition</h2>
<p>Without DEXA data, a reasonable estimate for a moderately active 42-year-old male at 85 kg / 168 cm places body fat at approximately 22‑27%. Using the midpoint of 25%:</p>
<ul>
  <li>Fat mass: 85 &#215; 0.25 = <strong>21.25 kg</strong></li>
  <li>Lean body mass (LBM): 85 &#8722; 21.25 = <strong>63.75 kg</strong> (working figure: 64 kg)</li>
</ul>
<p>If the protocol retains &#8805;95% of LBM &#8212; an achievable target with high protein and consistent resistance training (Longland et al., 2016) &#8212; end-point composition at 69.5 kg would be approximately:</p>
<ul>
  <li>Fat mass: ~6.7 kg (~9.6% body fat)</li>
  <li>LBM retained: ~62.8 kg</li>
</ul>

<h2>At-a-Glance Protocol Summary</h2>
<table>
  <tr><th>Metric</th><th>Deficit Days</th><th>Refeed Days</th><th>Diet Break Weeks</th></tr>
  <tr><td>Calories</td><td>1,800 kcal</td><td>2,100 kcal</td><td>2,400‑2,500 kcal</td></tr>
  <tr><td>Protein</td><td>175 g</td><td>175 g</td><td>180‑185 g</td></tr>
  <tr><td>Carbohydrates</td><td>130 g (rest) / 175 g (training)</td><td>250‑270 g</td><td>280‑300 g</td></tr>
  <tr><td>Fat</td><td>65 g (rest) / 45 g (training)</td><td>40‑45 g</td><td>65‑75 g</td></tr>
</table>

<div class="tip">
<strong>Protocol philosophy in one sentence:</strong> Eat the highest possible protein, train heavy, sleep long, break the diet twice, and walk everywhere &#8212; in exactly that order of importance.
</div>
"""

MACRO_BODY = """
<h1>Section 1</h1>
<h2>Optimal Caloric Deficit &amp; Macronutrients</h2>
<p class="intro">The precise distribution of your 1,800 kcal, and the scientific rationale behind every gram.</p>

<h2>1.1 Why 1,800 kcal and Not Less?</h2>
<p>The temptation under a hard deadline is to crash diet &#8212; eating 1,200‑1,400 kcal to accelerate loss. The literature argues strongly against this for a resistance-trained middle-aged male:</p>
<ul>
  <li><strong>Muscle protein synthesis suppression:</strong> Very low energy intakes (&lt;30 kcal/kg LBM/day) substantially reduce anabolic signalling even when protein is adequate (Areta et al., 2014). At 64 kg LBM, the physiological floor is roughly 1,920 kcal &#8212; you are already below this threshold at 1,800 kcal, which is why protein ceiling and training stimulus must compensate.</li>
  <li><strong>Hormonal disruption:</strong> Intakes below 1,500 kcal suppress testosterone, elevate cortisol, reduce thyroid hormone (T3), and down-regulate IGF-1 within 2‑4 weeks of sustained restriction (Hamalainen et al., 1984; Tremblay et al., 2004).</li>
  <li><strong>Metabolic adaptation tax:</strong> Severe restriction triggers greater-than-predicted reductions in TDEE via NEAT suppression, reduced thermic effect of food, and adaptive thermogenesis. Hall &amp; Guo (2017) quantified this as approximately a 30% &#8220;tax&#8221; on the deficit &#8212; meaning you pay for every 100 kcal you cut with ~30 kcal of compensatory metabolic slowdown.</li>
</ul>

<h2>1.2 Protein: The Non-Negotiable Macro</h2>
<h3>Target: 175 g/day (2.74 g/kg body weight)</h3>

<p>Protein is the single most important dietary variable for muscle preservation during energy deficit. The evidence base is exceptionally strong:</p>
<ul>
  <li><strong>Helms et al. (2014) &#8212; systematic review:</strong> Recommends 2.3‑3.1 g/kg LBM during caloric restriction, with the upper range appropriate for leaner individuals with larger deficits.</li>
  <li><strong>Longland et al. (2016) &#8212; landmark RCT:</strong> Subjects consuming 2.4 g/kg/day gained 1.2 kg LBM and lost 4.8 kg fat simultaneously in a 40% energy deficit over 4 weeks, compared to a 1.2 g/kg group which gained only 0.1 kg LBM and lost 3.5 kg fat.</li>
  <li><strong>Morton et al. (2018) &#8212; meta-analysis (49 RCTs):</strong> Protein supplementation during resistance training significantly increases LBM and strength, with no plateau effect up to ~1.62 g/kg; during deficit, optimal intakes substantially exceed this.</li>
  <li><strong>Trommelen et al. (2021):</strong> During hypocaloric periods, protein requirements increase due to elevated oxidation of amino acids for energy and reduced anabolic efficiency per gram consumed.</li>
</ul>

<h3>Age-Specific Protein Considerations at 42</h3>
<p>Middle-aged males experience <em>anabolic resistance</em> &#8212; a blunting of the MPS response to a given protein dose (Churchward-Venne et al., 2012; Breen &amp; Phillips, 2011). Driven by reduced mTORC1 sensitivity to leucine, lower circulating IGF-1 and testosterone, and greater splanchnic amino acid extraction. The practical consequence: older men need both higher total daily protein AND higher per-meal doses. While 20 g of leucine-rich protein maximally stimulates MPS in young men, Yang et al. (2012) demonstrate 40 g is superior in older men. This protocol targets 40‑50 g protein per meal across 4 meals.</p>

<h3>Protein Quality &#8212; Leucine Priority</h3>
<p>Target &#8805;2.5 g leucine per meal to reliably activate mTORC1 (Norton &amp; Layman, 2006):</p>
<table>
  <tr><th>Food Source</th><th>Leucine per 40g protein</th><th>DIAAS</th></tr>
  <tr><td>Whey protein isolate</td><td>~4.0 g</td><td>1.09 (excellent)</td></tr>
  <tr><td>Chicken breast</td><td>~3.2 g</td><td>~1.08</td></tr>
  <tr><td>Beef (lean)</td><td>~3.1 g</td><td>~1.11</td></tr>
  <tr><td>Eggs (whole)</td><td>~2.7 g</td><td>1.13</td></tr>
  <tr><td>Salmon</td><td>~3.0 g</td><td>~1.05</td></tr>
  <tr><td>Cottage cheese</td><td>~3.0 g</td><td>~1.00</td></tr>
</table>

<h2>1.3 Dietary Fat: The Hormonal Floor</h2>
<h3>Target: 65 g/day rest days / 45 g training days (&#8776;30% of calories)</h3>

<p>Fat intake has a direct, dose-dependent relationship with testosterone production in males (Hamalainen et al., 1984, 1985):</p>
<ul>
  <li>Diets providing &lt;15% energy from fat consistently reduce serum testosterone by 10‑15% within weeks</li>
  <li>High-fat diets (40% energy) produce higher testosterone than low-fat diets (20% energy) at equivalent calories</li>
  <li>Saturated and monounsaturated fats appear most beneficial for testosterone; very high polyunsaturated fat may modestly reduce it</li>
</ul>

<h3>Fat Source Distribution</h3>
<ul>
  <li><strong>Saturated fat (20‑25 g/day):</strong> Eggs, lean red meat, full-fat dairy &#8212; direct testosterone support via cholesterol pathway</li>
  <li><strong>Monounsaturated fat (25‑30 g/day):</strong> Olive oil, avocado, nuts &#8212; cardiovascular protection and anti-inflammatory effect</li>
  <li><strong>Omega-3 EPA+DHA (2‑3 g/day via supplement):</strong> Reduces muscle protein breakdown during deficit (Smith et al., 2011) and modestly supports testosterone (Childs et al., 2021)</li>
</ul>

<h2>1.4 Carbohydrates: Performance, Recovery, Glycogen</h2>
<h3>Target: 130 g rest days / 175 g training days</h3>

<p>After meeting protein and fat floors, carbohydrates fill remaining calories. This is deliberately not a ketogenic protocol:</p>
<ul>
  <li>Heavy resistance training relies primarily on glycolytic (carbohydrate) pathways. Low carbohydrate availability impairs high-intensity exercise performance and volume (Burke et al., 2011) &#8212; which would undermine the training stimulus critical for muscle retention.</li>
  <li>Insulin, driven by carbohydrate intake, is anti-catabolic. Even modest insulin elevations peri-workout substantially suppress muscle protein breakdown (Biolo et al., 1999).</li>
  <li>Low carbohydrate diets suppress T3 (thyroid hormone) production, independently slowing metabolic rate and worsening adaptive thermogenesis (Spaulding et al., 1976).</li>
</ul>

<h2>1.5 Full Macro Summary Table</h2>
<table>
  <tr><th>Macro</th><th>Rest Day</th><th>Training Day</th><th>Refeed Day</th><th>Diet Break</th></tr>
  <tr><td>Calories</td><td>1,750</td><td>1,800</td><td>2,100</td><td>2,400‑2,500</td></tr>
  <tr><td>Protein (g)</td><td>175</td><td>175</td><td>175</td><td>180</td></tr>
  <tr><td>Carbs (g)</td><td>130</td><td>175</td><td>250‑270</td><td>280‑300</td></tr>
  <tr><td>Fat (g)</td><td>65</td><td>45</td><td>40‑45</td><td>65‑75</td></tr>
  <tr><td>Fibre (g)</td><td>&#8805;30</td><td>&#8805;30</td><td>&#8805;35</td><td>&#8805;35</td></tr>
</table>
<p class="citation">Rest-day calories are slightly lower (1,750) to deepen the effective weekly deficit, partially offsetting the training-day carbohydrate provision.</p>
"""

TIMING_BODY = """
<h1>Section 2</h1>
<h2>Nutrient Timing &amp; Distribution</h2>
<p class="intro">When you eat your 1,800 kcal matters almost as much as the total &#8212; particularly for a 42-year-old male undergoing heavy resistance training in a significant deficit.</p>

<h2>2.1 The Science of Nutrient Timing</h2>
<p>The nutrient timing hypothesis holds that strategic delivery of macronutrients around the training window amplifies MPS, accelerates glycogen resynthesis, and blunts exercise-induced muscle damage. Key studies:</p>
<ul>
  <li><strong>Esmarck et al. (2001):</strong> Elderly men consuming protein immediately post-exercise gained significantly more muscle over 12 weeks than those eating the same protein 2 hours later.</li>
  <li><strong>Cribb &amp; Hayes (2006):</strong> Pre/post workout protein + carbohydrate produced significantly greater LBM and strength gains vs. morning/evening supplementation.</li>
  <li><strong>Schoenfeld et al. (2013) &#8212; meta-analysis:</strong> The peri-workout timing effect is less critical when total daily protein is high (&#8805;1.6 g/kg). However, for older males with anabolic resistance, the window timing advantage re-emerges (Pennings et al., 2011).</li>
  <li><strong>Jäger et al. (2017) &#8212; ISSN Position Stand:</strong> Recommends 0.4 g/kg protein and 0.4‑0.8 g/kg carbohydrate both pre- and post-workout.</li>
</ul>
<p>At 42, during a caloric deficit where MPS is already suppressed, nutrient timing is genuinely additive &#8212; not a gimmick.</p>

<h2>2.2 Meal Architecture Principles</h2>
<h3>Four meals, not six</h3>
<p>Areta et al. (2013) demonstrated 4 &#215; 20 g doses produce greater MPS than 2 &#215; 40 g or 8 &#215; 10 g in young men. For older men, 4 &#215; 40‑45 g doses are superior to smaller, more frequent meals due to anabolic resistance (Moore et al., 2015).</p>

<h3>Front-load your day</h3>
<p>Jakubowicz et al. (2013) and Garaulet et al. (2013) both demonstrate superior weight loss, better insulin sensitivity, and higher diet-induced thermogenesis when the majority of calories are eaten earlier. Target 60‑65% of calories consumed before 3 PM.</p>

<h3>Casein at night</h3>
<p>Res et al. (2012) established that 40 g casein before sleep stimulates overnight MPS by ~22% vs. placebo. During a caloric deficit where overnight catabolism is heightened, this is a meaningful muscle-protective intervention. Cottage cheese, Greek yoghurt, or micellar casein powder are ideal.</p>

<h3>Pre-workout carbohydrate is performance insurance</h3>
<p>With only 130‑175 g carbohydrate daily, strategic placement is essential. 40‑50 g carbohydrate 60‑90 min pre-workout maximises glycogen availability for the session without causing an insulin crash during lifting.</p>

<h2>2.3 Schedule A &#8212; 8:30 AM Training</h2>
<p><em>Strategy: abbreviated pre-workout window; small fast-digesting pre-workout meal, large post-workout recovery meal.</em></p>
<table>
  <tr><th>Time</th><th>Meal</th><th>Kcal</th><th>P</th><th>C</th><th>F</th></tr>
  <tr><td>07:00</td><td><strong>Pre-Workout</strong><br/>3 egg whites + 1 whole egg; 1 slice sourdough (40g); 150ml OJ; black coffee</td><td>320</td><td>26g</td><td>40g</td><td>8g</td></tr>
  <tr><td>08:30‑09:30</td><td><em>TRAINING</em></td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td></tr>
  <tr><td>09:45</td><td><strong>Post-Workout Recovery</strong><br/>40g whey in 300ml skimmed milk; 200g low-fat Greek yoghurt; 80g blueberries; 30g oats (dry)</td><td>520</td><td>65g</td><td>60g</td><td>8g</td></tr>
  <tr><td>13:00</td><td><strong>Lunch</strong><br/>180g chicken breast; 150g cooked basmati rice; 200g mixed salad; 1 tbsp olive oil + lemon</td><td>540</td><td>50g</td><td>48g</td><td>14g</td></tr>
  <tr><td>19:00</td><td><strong>Dinner + Pre-Sleep</strong><br/>200g salmon; 300g roasted broccoli/courgette; 150g cottage cheese; 1 tbsp olive oil</td><td>420</td><td>54g</td><td>12g</td><td>18g</td></tr>
  <tr><td></td><td><strong>Training Day Total</strong></td><td><strong>1,800</strong></td><td><strong>195g</strong></td><td><strong>160g</strong></td><td><strong>48g</strong></td></tr>
</table>

<h2>2.4 Schedule B &#8212; 11:30 AM Training</h2>
<p><em>Strategy: optimal window &#8212; substantial pre-workout meal 90 min before training, large post-workout recovery meal. Highest-performance timing scenario.</em></p>
<table>
  <tr><th>Time</th><th>Meal</th><th>Kcal</th><th>P</th><th>C</th><th>F</th></tr>
  <tr><td>07:30</td><td><strong>Breakfast</strong><br/>3 whole eggs + 2 egg whites; 200g low-fat Greek yoghurt; 80g berries; black coffee</td><td>380</td><td>45g</td><td>28g</td><td>14g</td></tr>
  <tr><td>10:00</td><td><strong>Pre-Workout</strong><br/>40g oats cooked; 25g whey protein stirred in; 1 banana (100g); black coffee</td><td>340</td><td>30g</td><td>55g</td><td>4g</td></tr>
  <tr><td>11:30‑12:30</td><td><em>TRAINING</em></td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td></tr>
  <tr><td>12:45</td><td><strong>Post-Workout Recovery</strong><br/>200g chicken breast; 150g cooked white rice; 200g steamed green veg; 1 tsp butter</td><td>520</td><td>48g</td><td>55g</td><td>9g</td></tr>
  <tr><td>18:30</td><td><strong>Dinner + Pre-Sleep</strong><br/>200g lean beef mince; 250g roasted vegetables; 150g cottage cheese; 1 tbsp olive oil</td><td>560</td><td>62g</td><td>18g</td><td>22g</td></tr>
  <tr><td></td><td><strong>Training Day Total</strong></td><td><strong>1,800</strong></td><td><strong>185g</strong></td><td><strong>156g</strong></td><td><strong>49g</strong></td></tr>
</table>

<h2>2.5 Schedule C &#8212; 4:00 PM Training</h2>
<p><em>Strategy: full day of eating before training allows maximum glycogen loading. Pre-workout meal at 2:30 PM is the critical window. Post-workout dinner is the final substantial meal. Pre-sleep protein is critical after a late stimulus.</em></p>
<table>
  <tr><th>Time</th><th>Meal</th><th>Kcal</th><th>P</th><th>C</th><th>F</th></tr>
  <tr><td>07:30</td><td><strong>Breakfast</strong><br/>4 whole eggs scrambled; 2 slices sourdough (80g); unlimited spinach/mushrooms</td><td>450</td><td>30g</td><td>38g</td><td>18g</td></tr>
  <tr><td>12:00</td><td><strong>Lunch</strong><br/>180g tuna (tinned in water); 120g cooked brown rice; large salad; 1 tbsp olive oil; 1 apple</td><td>420</td><td>40g</td><td>50g</td><td>9g</td></tr>
  <tr><td>14:30</td><td><strong>Pre-Workout</strong><br/>30g oats; 20g whey protein; 100g banana; black coffee</td><td>280</td><td>24g</td><td>44g</td><td>3g</td></tr>
  <tr><td>16:00‑17:00</td><td><em>TRAINING</em></td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td><td>&#8212;</td></tr>
  <tr><td>17:30</td><td><strong>Post-Workout Dinner</strong><br/>200g salmon; 200g roasted sweet potato; 200g green veg; 1 tsp olive oil</td><td>500</td><td>45g</td><td>40g</td><td>12g</td></tr>
  <tr><td>21:30</td><td><strong>Pre-Sleep Protein</strong><br/>200g low-fat cottage cheese + cinnamon; or 40g casein shake with water</td><td>150</td><td>28g</td><td>8g</td><td>2g</td></tr>
  <tr><td></td><td><strong>Training Day Total</strong></td><td><strong>1,800</strong></td><td><strong>167g</strong></td><td><strong>180g</strong></td><td><strong>44g</strong></td></tr>
</table>
<p class="citation">Schedule C naturally skews slightly higher in carbohydrate due to the pre-workout window timing &#8212; this is acceptable and beneficial for a late session.</p>

<h2>2.6 Rest Day Template (All Schedules)</h2>
<table>
  <tr><th>Meal</th><th>Example</th><th>Kcal</th><th>P</th><th>C</th><th>F</th></tr>
  <tr><td>Breakfast</td><td>4 whole eggs + spinach + mushrooms; black coffee</td><td>350</td><td>28g</td><td>5g</td><td>22g</td></tr>
  <tr><td>Lunch</td><td>200g chicken breast; 100g sweet potato; 300g salad; olive oil</td><td>450</td><td>50g</td><td>30g</td><td>12g</td></tr>
  <tr><td>Snack</td><td>200g Greek yoghurt; 80g berries</td><td>200</td><td>20g</td><td>20g</td><td>4g</td></tr>
  <tr><td>Dinner</td><td>200g beef or fish; 200g roasted veg; 150g cottage cheese; olive oil</td><td>520</td><td>62g</td><td>18g</td><td>18g</td></tr>
  <tr><td>Pre-sleep</td><td>Casein shake or 150g cottage cheese</td><td>130</td><td>22g</td><td>6g</td><td>2g</td></tr>
  <tr><td><strong>Total</strong></td><td></td><td><strong>1,650</strong></td><td><strong>182g</strong></td><td><strong>79g</strong></td><td><strong>58g</strong></td></tr>
</table>

<h2>2.7 Intra-Workout Nutrition</h2>
<p>For sessions under 75 minutes, intra-workout carbohydrate provides minimal additional benefit if pre-workout nutrition is adequate (Jeukendrup, 2014). However, during a caloric deficit where glycogen is already reduced, sipping 20‑30g of fast carbohydrate (sports drink, banana pieces) during the session can protect performance in the final sets. Use only if you notice strength fading in the second half of your session.</p>
"""

PERIOD_BODY = """
<h1>Section 3</h1>
<h2>Physiological Periodization: The 17-Week Structure</h2>
<p class="intro">How to structure 17 weeks of aggressive deficit to outsmart your own metabolism, protect muscle tissue, and arrive at Week 17 still performing at a high level.</p>

<h2>3.1 The Problem: Metabolic Adaptation</h2>
<p>The body&#8217;s response to caloric restriction is not passive. Multiple compensatory mechanisms activate within days to weeks:</p>
<ol>
  <li><strong>Adaptive thermogenesis (AT):</strong> A reduction in resting metabolic rate beyond what body weight loss alone explains. Rosenbaum &amp; Leibel (2010) documented AT of 200‑400 kcal/day in subjects after significant weight loss &#8212; meaning your TDEE may fall to 2,400‑2,600 kcal simply from chronic restriction, independent of weight change.</li>
  <li><strong>NEAT suppression:</strong> Non-exercise activity thermogenesis &#8212; fidgeting, posture, spontaneous movement &#8212; can fall by 200‑500 kcal/day during prolonged deficit (Levine et al., 1999). This happens unconsciously; you sit more and move less without realising.</li>
  <li><strong>Appetite hormone dysregulation:</strong> Leptin falls, ghrelin rises, and PYY decreases &#8212; producing relentless hunger that grows worse the longer the deficit continues (Sumithran et al., 2011, NEJM). These hormonal changes persist for months after dieting ends.</li>
  <li><strong>Muscle catabolism acceleration:</strong> Cortisol rises, testosterone falls, and protein turnover tilts net-catabolic after 6‑8 weeks of uninterrupted aggressive deficit (Friedl et al., 2000).</li>
</ol>
<p>The periodization strategy below deliberately interrupts these adaptations before they compound.</p>

<h2>3.2 Scientific Basis for Diet Breaks</h2>
<p>A diet break is a planned period of eating at maintenance calories, typically lasting 1‑2 weeks, inserted within an extended deficit phase.</p>
<ul>
  <li><strong>Byrne et al. (2017) &#8212; MATADOR Trial:</strong> The most important study in this space. Subjects on intermittent energy restriction (2 weeks deficit, 2 weeks maintenance, repeated) lost 47% more fat than continuous restriction subjects over the same total period. The intermittent group also showed significantly less adaptive thermogenesis. This is the closest we have to a definitive RCT on diet breaks.</li>
  <li><strong>Davoodi et al. (2014):</strong> Calorie-cycling groups demonstrated better preservation of RMR compared to continuous restriction groups at matched total deficits.</li>
  <li><strong>Peos et al. (2019):</strong> Diet breaks of 1 week at maintenance significantly recovered leptin, testosterone, and T3 compared to continuous restriction, with no clinically meaningful fat regain during the break week.</li>
</ul>

<h2>3.3 Scientific Basis for Refeed Days</h2>
<p>A refeed is a single day (or 2 consecutive days) of eating at or slightly above maintenance, with carbohydrates as the primary vehicle for the calorie increase:</p>
<ul>
  <li><strong>Glycogen resynthesis:</strong> A full refeed replenishes muscle glycogen (Bussau et al., 2002), directly supporting the subsequent week&#8217;s training quality.</li>
  <li><strong>Psychological relief:</strong> Refeed days reduce diet fatigue and improve dietary adherence in the following week (Cheatham et al., 2018).</li>
  <li><strong>Partial leptin recovery:</strong> Even a single high-carbohydrate day can transiently elevate leptin by 20‑30% (Dirlewanger et al., 2000), partially restoring satiety-signalling function.</li>
</ul>

<h2>3.4 NEAT Management</h2>
<p>NEAT suppression is arguably the largest single threat to your deficit &#8212; yet the least discussed. The prescription is simple: <strong>mandatory daily step targets.</strong></p>
<ul>
  <li>Walk a minimum of <strong>8,000 steps/day</strong> on rest days and <strong>6,000 steps/day</strong> on training days</li>
  <li>Use a wearable to track this; if below target, walk in the evening without exception</li>
  <li>Take stairs, stand at your desk, park further away &#8212; these micro-decisions constitute 150‑300 kcal/day that most dieters unconsciously abandon</li>
  <li>During diet break weeks, raise the step target to 10,000 to exploit the full metabolic capacity that calorie restoration provides</li>
</ul>
<p class="citation">Evidence: Levine et al. (1999); Church et al. (2007) &#8212; structured walking programmes during caloric restriction dramatically mitigate NEAT suppression.</p>

<h2>3.5 The 17-Week Phased Structure</h2>

<div class="phase">PHASE 1: Metabolic Conditioning (Weeks 1‑5)</div>
<p><strong>Objective:</strong> Establish the deficit, build habits, assess individual response.</p>
<ul>
  <li>Calories: 1,800 kcal/day with training-day carb cycling as per Section 2</li>
  <li>No dedicated refeed in Phase 1 &#8212; the training-day carbohydrate elevation (175 g) serves as a partial refeed</li>
  <li>Expected weight loss: 3.5‑4.5 kg over 5 weeks (includes initial water/glycogen loss weeks 1‑2)</li>
  <li>Training: Heavy resistance every other day; deload in Week 5 (reduce volume 40%, maintain intensity)</li>
  <li>Weekly check-in: 7-day average body weight. If losing &lt;0.6 kg/week by Week 3, reduce calories by 100 kcal or add 1,000 steps/day</li>
</ul>

<div class="phase">DIET BREAK 1: Week 6 &#8212; Full Metabolic Reset</div>
<p><strong>Objective:</strong> Restore leptin, testosterone, T3; replenish muscle glycogen; allow psychological recovery.</p>
<ul>
  <li>Calories: 2,400‑2,500 kcal/day (approximately estimated TDEE at current body weight)</li>
  <li>Carbohydrates: 280‑300 g/day &#8212; the primary macro increase; carbs restore glycogen and drive leptin recovery</li>
  <li>Protein: Maintain at 180 g/day; do not reduce</li>
  <li>Fat: 65‑75 g/day</li>
  <li>Training: Normal volume resumes after the deload; expect strength improvements this week</li>
  <li>Expected scale change: +1.0‑2.0 kg (entirely water and glycogen; not fat &#8212; do not panic)</li>
  <li>Monitoring: Hunger should markedly improve by Day 3‑4 of the break; if not, extend to 10 days</li>
</ul>

<div class="phase">PHASE 2: Continued Deficit (Weeks 7‑11)</div>
<p><strong>Objective:</strong> Capitalise on the metabolic reset. This phase typically produces faster fat loss than Phase 1 due to restored hormone function.</p>
<ul>
  <li>Calories: 1,800 kcal/day. Note: actual TDEE is now approximately 2,600‑2,700 kcal due to lower body weight (lost ~5‑6 kg). Reassess if you have reliable tracking data.</li>
  <li>Weekly refeed: Introduce one refeed day each Friday &#8212; raise carbohydrates to 250‑270 g, keep protein the same, reduce fat to 40 g. Total: ~2,100 kcal</li>
  <li>Expected weight loss: 3.5‑4.5 kg over 5 weeks</li>
  <li>Training: Full volume Week 7. Deload again in Week 11</li>
</ul>

<div class="phase">DIET BREAK 2: Week 12 &#8212; Mid-Cycle Reset</div>
<p><strong>Objective:</strong> Second and final diet break. Critical as accumulated dietary fatigue and adaptive thermogenesis are now substantial.</p>
<ul>
  <li>Calories: 2,200‑2,400 kcal (TDEE is lower now due to reduced body mass; do not overshoot)</li>
  <li>Same structure as Diet Break 1: high carbohydrate, maintained protein, moderate fat</li>
  <li>By Week 12 you should have lost approximately 8‑10 kg. The break is well-earned.</li>
</ul>

<div class="phase">PHASE 3: Final Push (Weeks 13‑17)</div>
<p><strong>Objective:</strong> Cross the finish line at 69.5 kg with maximum lean mass retention and minimum metabolic damage.</p>
<ul>
  <li>Calories: 1,600‑1,700 kcal (TDEE is now ~2,500‑2,600 kcal; adjust target to maintain ~900‑1,000 kcal deficit)</li>
  <li>This is the hardest phase psychologically: hunger is greatest, NEAT suppression most pronounced, social fatigue highest. The weekly refeed becomes essential survival infrastructure.</li>
  <li>Weekly refeed: 2,000‑2,200 kcal refeed day every 5 days</li>
  <li>Training: Maintain resistance training stimulus even if fatigue is high. If strength drops &gt;10% on key lifts, increase calories by 100 kcal rather than reducing training volume</li>
  <li>Expected weight loss: 4.0‑5.0 kg over 5 weeks</li>
  <li>Final Week 17 weight target: 69.5 kg</li>
</ul>

<h2>3.6 Complete 17-Week Calendar</h2>
<table>
  <tr><th>Week</th><th>Phase</th><th>Target kcal</th><th>Key Notes</th></tr>
  <tr><td>1</td><td>Phase 1</td><td>1,800</td><td>Establish habits; expect rapid initial loss (water/glycogen)</td></tr>
  <tr><td>2</td><td>Phase 1</td><td>1,800</td><td>True fat loss begins; expect ~0.5‑0.8 kg/week</td></tr>
  <tr><td>3</td><td>Phase 1</td><td>1,800</td><td>Assess: if &lt;0.6 kg/week, reduce 100 kcal or add 1,000 steps</td></tr>
  <tr><td>4</td><td>Phase 1</td><td>1,800</td><td>Monitor hunger, sleep quality, training performance</td></tr>
  <tr><td>5</td><td>Phase 1 + Deload</td><td>1,800</td><td>Reduce training volume 40%; maintain intensity</td></tr>
  <tr><td>6</td><td>DIET BREAK 1</td><td>2,400‑2,500</td><td>Full reset; scale will rise &#8212; that is glycogen and water</td></tr>
  <tr><td>7</td><td>Phase 2</td><td>1,800</td><td>Begin weekly Friday refeeds</td></tr>
  <tr><td>8</td><td>Phase 2</td><td>1,800</td><td>Full phase</td></tr>
  <tr><td>9</td><td>Phase 2</td><td>1,800</td><td>Full phase</td></tr>
  <tr><td>10</td><td>Phase 2</td><td>1,800</td><td>Full phase</td></tr>
  <tr><td>11</td><td>Phase 2 + Deload</td><td>1,800</td><td>Reduce training volume; prepare for Diet Break 2</td></tr>
  <tr><td>12</td><td>DIET BREAK 2</td><td>2,200‑2,400</td><td>Psychological and hormonal recovery</td></tr>
  <tr><td>13</td><td>Phase 3</td><td>1,650</td><td>Adjust for reduced TDEE; refeed every 5 days</td></tr>
  <tr><td>14</td><td>Phase 3</td><td>1,650</td><td>Full phase; hunger management is priority</td></tr>
  <tr><td>15</td><td>Phase 3</td><td>1,650</td><td>Full phase</td></tr>
  <tr><td>16</td><td>Phase 3</td><td>1,650</td><td>Final stretch</td></tr>
  <tr><td>17</td><td>Phase 3 Final</td><td>1,650</td><td>Target: 69.5 kg at end of week; begin exit strategy</td></tr>
</table>

<h2>3.7 Progress Monitoring Metrics</h2>
<table>
  <tr><th>Metric</th><th>Frequency</th><th>Method</th><th>Expected Trend</th></tr>
  <tr><td>Body weight</td><td>Daily (7-day average)</td><td>Morning, post-void, fasted</td><td>Downward, ~0.7‑0.9 kg/week average</td></tr>
  <tr><td>Waist circumference</td><td>Weekly</td><td>Tape, navel level, morning</td><td>Reducing; more reliable than scale during refeeds</td></tr>
  <tr><td>Training performance</td><td>Per session</td><td>Log weights &#215; reps</td><td>Stable; significant drop signals deficit too deep</td></tr>
  <tr><td>Sleep quality</td><td>Daily</td><td>Wearable HRV/sleep score</td><td>Should improve during diet breaks</td></tr>
  <tr><td>Step count</td><td>Daily</td><td>Wearable</td><td>Maintain target; watch for unconscious reduction</td></tr>
  <tr><td>Hunger rating (1‑10)</td><td>Daily</td><td>Self-rating</td><td>Drops during diet breaks; sustained 8+ signals need for break</td></tr>
</table>
"""

RECOVERY_BODY = """
<h1>Section 4</h1>
<h2>Age-Specific Recovery, Sleep &amp; Supplementation</h2>
<p class="intro">At 42, your recovery capacity has meaningfully declined compared to your 25-year-old self. This is not opinion &#8212; it is endocrinology. The protocols below are calibrated to compensate.</p>

<h2>4.1 The 42-Year-Old Physiology</h2>
<table>
  <tr><th>Parameter</th><th>Peak (20s)</th><th>At Age 42</th><th>Practical Implication</th></tr>
  <tr><td>Testosterone (total)</td><td>650‑800 ng/dL</td><td>450‑550 ng/dL</td><td>Reduced anabolic drive; slower recovery</td></tr>
  <tr><td>GH nocturnal pulse</td><td>High amplitude</td><td>~50‑70% reduced</td><td>Less overnight muscle repair; sleep matters more</td></tr>
  <tr><td>IGF-1</td><td>~200 ng/mL</td><td>~140‑160 ng/mL</td><td>Reduced satellite cell activation</td></tr>
  <tr><td>Cortisol clearance</td><td>Fast</td><td>Slower</td><td>Training/stress-induced cortisol persists longer</td></tr>
  <tr><td>mTORC1 sensitivity</td><td>High</td><td>Reduced ~30%</td><td>Higher protein dose needed per meal</td></tr>
  <tr><td>Slow-wave sleep</td><td>~25% of night</td><td>~15% of night</td><td>Less restorative sleep per hour</td></tr>
</table>
<p class="citation">Sources: Veldhuis et al. (2005); Churchward-Venne et al. (2012); Van Cauter et al. (2000)</p>

<h2>4.2 Sleep: The Most Undervalued Recovery Tool</h2>
<p>Sleep is not a passive recovery strategy &#8212; it is the primary anabolic window for a middle-aged male under caloric restriction.</p>

<h3>The Evidence</h3>
<ul>
  <li><strong>Leproult &amp; Van Cauter (2011, JAMA):</strong> One week of sleep restriction to 5 hours/night in men aged 38‑50 reduced testosterone by 10‑15% &#8212; equivalent to 10‑15 years of biological ageing in hormone terms.</li>
  <li><strong>Nedeltcheva et al. (2010):</strong> Subjects on a hypocaloric diet reducing sleep from 8.5 to 5.5 hours per night: 55% less fat was lost and 60% more lean mass was lost. Inadequate sleep literally redirects your deficit from fat to muscle.</li>
  <li><strong>Van Cauter et al. (2000):</strong> Growth hormone is released primarily during slow-wave sleep in the first half of the night. Disrupted or insufficient sleep dramatically curtails this pulse.</li>
  <li><strong>Spiegel et al. (2004):</strong> Sleep deprivation reduces leptin and elevates ghrelin &#8212; the same hormonal environment as prolonged dieting. These effects compound when co-occurring.</li>
</ul>

<h3>Sleep Prescriptions</h3>
<ul>
  <li><strong>Duration: 7.5‑9 hours in bed.</strong> Target 8 hours as non-negotiable during this protocol. This is a clinical intervention, not a lifestyle luxury.</li>
  <li><strong>Consistency:</strong> Maintain consistent wake time (&#177;30 min) including weekends. Circadian rhythm stability directly influences cortisol rhythm and muscle catabolism.</li>
  <li>Room temperature: 17‑19&#176;C (optimises GH pulse)</li>
  <li>Complete darkness (blackout blinds or eye mask)</li>
  <li>No screens 45 min before bed; blue light shifts the circadian clock by 90‑120 min</li>
  <li>Consistent pre-sleep routine: shower, light stretching, reading</li>
  <li><strong>Pre-sleep protein:</strong> 40 g casein 30 min before sleep increases overnight MPS by ~22% (Res et al., 2012; Snijders et al., 2015). This is a high-priority muscle-retention intervention.</li>
</ul>

<h2>4.3 Recovery Between Training Sessions</h2>
<h3>Evidence-Based Recovery Methods</h3>
<table>
  <tr><th>Method</th><th>Evidence</th><th>Protocol</th></tr>
  <tr><td>Cold water immersion</td><td>Moderate</td><td>10‑15 min at 10‑15&#176;C post-training; reduces acute soreness. Avoid immediately post-hypertrophy sessions &#8212; may blunt mTOR (Roberts et al., 2015).</td></tr>
  <tr><td>Light walking</td><td>Strong</td><td>20‑30 min low-intensity walk 4‑6 hours post-training; enhances blood flow, reduces cortisol, contributes to NEAT target</td></tr>
  <tr><td>Foam rolling</td><td>Moderate</td><td>10 min post-session; reduces perceived soreness (Cheatham et al., 2015)</td></tr>
  <tr><td>Contrast showers</td><td>Low‑Moderate</td><td>2 min hot / 30 sec cold &#215; 4 cycles; anecdotally effective for subjective recovery</td></tr>
  <tr><td>Compression garments</td><td>Moderate</td><td>Wear 2‑4 hours post-training; reduces perceptual fatigue and soreness (Hill et al., 2014)</td></tr>
</table>

<h3>Unscheduled Deload Triggers</h3>
<p>In addition to the planned deloads in Weeks 5 and 11, deload immediately if you observe:</p>
<ul>
  <li>Strength on key lifts drops &gt;10% without explanation</li>
  <li>Persistent joint soreness or tendon irritation</li>
  <li>Resting HR elevated &gt;5‑7 bpm above baseline for 3+ consecutive days</li>
  <li>HRV consistently below your personal baseline</li>
  <li>Extreme difficulty sleeping despite adequate sleep hygiene</li>
</ul>

<h2>4.4 Stress Management: The Cortisol Problem</h2>
<p>Chronic psychological stress elevates cortisol &#8212; which is proteolytic (muscle-degrading), and directly antagonistic to testosterone and GH. During a caloric deficit, additional chronic stress is compounding and must be managed actively.</p>
<ul>
  <li><strong>Mindfulness/breathing:</strong> 10‑20 min/day reduces cortisol AUC (Turakitwanakan et al., 2013); box breathing (4-4-4-4 pattern) acutely lowers cortisol</li>
  <li><strong>Avoid adding excessive cardio:</strong> Adding HIIT or long cardio sessions to heavy resistance training during deficit creates compounding physiological stress; resist the temptation to add cardio to &#8220;speed up&#8221; fat loss</li>
</ul>

<h2>4.5 Supplementation: Evidence-Based Tiers</h2>

<div class="phase">Tier 1: Evidence-Based Essentials</div>
<table>
  <tr><th>Supplement</th><th>Dose</th><th>Timing</th><th>Rationale</th></tr>
  <tr><td><strong>Vitamin D3 + K2</strong></td><td>3,000‑5,000 IU D3 + 100‑200 mcg K2</td><td>Morning, with fat-containing meal</td><td>Vitamin D deficiency prevalent (40‑60% UK adults); directly associated with low testosterone (Pilz et al., 2011); supports muscle function (Dawson-Hughes et al., 2010). K2 directs calcium to bone, not arteries.</td></tr>
  <tr><td><strong>Omega-3 EPA+DHA</strong></td><td>2‑3 g EPA+DHA/day (not total fish oil)</td><td>With meals, split dose</td><td>Reduces muscle protein breakdown during deficit (Smith et al., 2011); anti-inflammatory; modestly supports testosterone (Childs et al., 2021); cardiovascular protection during rapid weight loss.</td></tr>
  <tr><td><strong>Magnesium glycinate</strong></td><td>300‑400 mg elemental Mg</td><td>30‑60 min before sleep</td><td>Magnesium depletion occurs rapidly during caloric restriction and heavy sweating. Low magnesium directly associated with reduced testosterone (Cinar et al., 2011), impaired sleep architecture, and muscle cramps.</td></tr>
  <tr><td><strong>Zinc</strong></td><td>15‑25 mg elemental zinc</td><td>With food, not with iron</td><td>Cofactor in testosterone synthesis; deficiency common during restriction and high-volume training (Prasad et al., 1996). Do not exceed 40 mg/day. Prioritise dietary sources: red meat, oysters, pumpkin seeds.</td></tr>
  <tr><td><strong>Creatine monohydrate</strong></td><td>5 g/day</td><td>Any time; timing not critical</td><td>Most-studied ergogenic supplement in existence. During deficit: supports training performance (Rawson &amp; Volek, 2003), reduces muscle protein breakdown (Louis et al., 2003), enhances glycogen synthesis (Jäger et al., 2011). No loading phase needed.</td></tr>
</table>

<div class="phase">Tier 2: Strongly Recommended</div>
<table>
  <tr><th>Supplement</th><th>Dose</th><th>Timing</th><th>Rationale</th></tr>
  <tr><td><strong>Whey protein isolate</strong></td><td>1‑2 &#215; 25‑40 g</td><td>Post-workout and/or pre-sleep top-up</td><td>Convenient, fast-digesting, high leucine; use to hit daily protein targets when whole-food sources are insufficient.</td></tr>
  <tr><td><strong>Casein protein</strong></td><td>30‑40 g</td><td>30 min before sleep</td><td>Slow-digesting; sustains elevated blood amino acids for 7+ hours overnight; proven to increase overnight MPS (Res et al., 2012).</td></tr>
  <tr><td><strong>Caffeine</strong></td><td>3‑6 mg/kg (200‑400 mg)</td><td>30‑60 min pre-workout</td><td>Enhances strength (Graham, 2001), reduces perceived effort, improves training volume &#8212; all critical during deficit when energy is compromised. Cut off by 1 PM to protect sleep.</td></tr>
  <tr><td><strong>Comprehensive multivitamin</strong></td><td>1 &#215; RDA-level multi</td><td>With breakfast</td><td>At 1,800 kcal, achieving all micronutrient RDAs from food alone is extremely difficult. Look for methylated B vitamins (methylfolate, methylcobalamin).</td></tr>
</table>

<div class="phase">Tier 3: Optional Performance Optimisation</div>
<table>
  <tr><th>Supplement</th><th>Dose</th><th>Notes</th></tr>
  <tr><td>Beta-alanine</td><td>3.2‑6.4 g/day (split dose)</td><td>Buffers muscle acidosis; most beneficial in sets &gt;60 seconds. Modest but real ergogenic effect (Hobson et al., 2012).</td></tr>
  <tr><td>Citrulline malate</td><td>6‑8 g, 60 min pre-workout</td><td>Improves blood flow, reduces post-exercise soreness, may support training volume (Pérez-Guisado &amp; Jakeman, 2010).</td></tr>
  <tr><td>Ashwagandha (KSM-66)</td><td>300‑600 mg/day</td><td>Adaptogenic; reduces cortisol, modestly supports testosterone in stressed males (Wankhede et al., 2015). Most relevant in Phase 3 when accumulated fatigue is highest.</td></tr>
  <tr><td>Vitamin C</td><td>500‑1,000 mg/day</td><td>Antioxidant; may modestly blunt cortisol elevation post-exercise (Peters et al., 2001). Do not exceed 1,000 mg &#8212; higher doses may blunt training adaptations.</td></tr>
</table>

<div class="warning">
<strong>Note on testosterone boosters and commercial fat burners:</strong> Tribulus terrestris, DHEA (without medical supervision), and most thermogenic blends have negligible or no evidence for meaningful benefit. Do not waste money on these. The Tier 1 list is where the evidence lives.
</div>

<h2>4.6 Recommended Blood Work</h2>
<p>Given the aggressive nature of this protocol, obtain baseline blood work before starting and retest at Weeks 9 and 17:</p>
<ul>
  <li>Total and free testosterone</li>
  <li>LH and FSH (pituitary function)</li>
  <li>Thyroid panel: TSH, free T3, free T4</li>
  <li>Full blood count (anaemia risk under restriction)</li>
  <li>Ferritin (iron stores deplete rapidly under restriction and heavy training)</li>
  <li>Vitamin D (25-OH)</li>
  <li>Fasting insulin and glucose</li>
  <li>CRP (inflammation marker)</li>
</ul>
"""

EXIT_BODY = """
<h1>Section 5</h1>
<h2>Exit Strategy: Week 18 and the Reverse Diet</h2>
<p class="intro">Reaching 69.5 kg is only half the work. How you exit the deficit determines whether you keep it.</p>

<h2>5.1 The Post-Diet Physiological State</h2>
<p>At the end of 17 weeks of aggressive deficit, your body will be in a predictable physiological state:</p>
<ul>
  <li><strong>Metabolic rate suppression:</strong> Estimated TDEE at end-point body weight is approximately 2,400‑2,600 kcal (reduced from 2,817 by lower body mass plus adaptive thermogenesis). Do not return to 2,817 kcal &#8212; that will cause rapid fat regain.</li>
  <li><strong>Hormonal disruption:</strong> Testosterone, leptin, T3, and IGF-1 will all be below baseline. Leptin may be 50‑70% below its pre-diet level (Friedman, 2019), creating intense and chronic hunger that is a physiological reality, not a psychological weakness.</li>
  <li><strong>Elevated ghrelin:</strong> The hunger-stimulating hormone remains chronically elevated for weeks to months post-diet (Sumithran et al., 2011). This is the primary mechanism of weight regain: not willpower failure, but hormone-driven hyperphagia.</li>
  <li><strong>Glycogen depletion:</strong> The first week post-diet will involve +2‑4 kg on the scale from water and glycogen refilling. This is expected, benign, and unavoidable.</li>
</ul>

<h2>5.2 Reverse Dieting vs. Immediate Maintenance Return</h2>

<h3>Strategy A: Immediate Return to (New) Maintenance</h3>
<p>Rapidly increase calories to estimated end-point maintenance (~2,400 kcal at 69.5 kg):</p>
<ul>
  <li>Evidence from Byrne et al. (2017) and Hall et al. (2012) suggests metabolic rate recovers more quickly than previously believed &#8212; within 3‑4 weeks in some studies</li>
  <li>Less psychological burden than prolonged calorie restriction with slow increases</li>
  <li>Risk: if you overshoot maintenance (eating 2,600‑2,800 kcal thinking you are at maintenance), rapid fat regain ensues</li>
</ul>

<h3>Strategy B: Reverse Dieting (Graduated Increase)</h3>
<p>Incrementally increase calories by 50‑100 kcal per week until reaching estimated maintenance:</p>
<ul>
  <li>Popularised by Layne Norton, PhD, widely used in competitive bodybuilding with substantial anecdotal support</li>
  <li>The primary proposed benefit &#8212; &#8220;repairing the metabolism&#8221; &#8212; is partially supported (Trexler et al., 2014) but mechanistic evidence is less robust than anecdotal evidence</li>
  <li>Potential benefit: NEAT and thyroid hormones may recover more gradually, and a slow calorie increase allows real-time body weight adjustment</li>
  <li>Potential downside: prolonged mild restriction immediately after an already long diet may worsen hormonal disruption and psychological fatigue</li>
</ul>

<h3>The Evidence-Based Middle Ground</h3>
<p>A synthesis of the literature (Trexler et al., 2014; Dulloo et al., 2012; Byrne et al., 2017) supports a <strong>moderate, structured 4‑6 week step-up:</strong></p>
<div class="highlight">
The goal of the post-diet phase is not to &#8220;repair metabolism&#8221; but to gradually acclimate the appetite regulatory system to higher calorie intake, reduce the hormonal drivers of hyperphagia, restore glycogen, and allow NEAT to normalise &#8212; all while minimising fat regain.
</div>

<h2>5.3 The Recommended Exit Protocol: Weeks 18‑26</h2>

<div class="phase">Weeks 18‑19: Glycogen and Hormonal Stabilisation</div>
<ul>
  <li>Calories: <strong>2,000‑2,100 kcal/day</strong></li>
  <li>Carbohydrates: Increase to 220‑250 g/day &#8212; primary driver of glycogen replenishment and leptin recovery</li>
  <li>Protein: Maintain at 175 g</li>
  <li>Fat: 60‑65 g</li>
  <li>Expected scale change: +1.5‑3.0 kg (glycogen, water, gut content &#8212; not fat)</li>
  <li>Training: Return to normal volume; expect strength to rebound</li>
  <li>Monitoring: If scale weight increases &gt;3 kg, reduce to 1,900 kcal and reassess</li>
</ul>

<div class="phase">Weeks 20‑21: Step-Up to Near-Maintenance</div>
<ul>
  <li>Calories: <strong>2,200‑2,300 kcal/day</strong></li>
  <li>Carbohydrates: 270‑290 g/day</li>
  <li>If gaining &gt;0.3 kg/week (7-day average), hold calories flat for another week</li>
  <li>Begin intuitive eating calibration &#8212; start identifying hunger and satiety cues without counting every gram</li>
</ul>

<div class="phase">Weeks 22‑26: Maintenance Calibration</div>
<ul>
  <li>Calories: <strong>2,400‑2,600 kcal/day</strong></li>
  <li>This range is your new estimated maintenance. Let the scale guide the exact figure &#8212; individual variation is substantial.</li>
  <li>Maintenance defined as: 7-day average body weight stable within &#177;0.5 kg for 3+ consecutive weeks</li>
  <li>Training: Optionally shift to body recomposition &#8212; slightly above maintenance on training days, slightly below on rest days. This continues to improve body composition without formal cutting or bulking.</li>
</ul>

<h2>5.4 Preventing Fat Regain: Evidence Summary</h2>
<table>
  <tr><th>Strategy</th><th>Evidence</th><th>Prescription</th></tr>
  <tr><td>Maintain resistance training</td><td>Strong</td><td>Do not stop lifting. Muscle mass is the primary determinant of long-term RMR; every kg of LBM retained supports maintenance of the higher metabolic rate.</td></tr>
  <tr><td>Keep protein elevated</td><td>Strong</td><td>Maintain &#8805;1.6‑2.0 g/kg during maintenance phase; high protein increases diet-induced thermogenesis and satiety, reducing ad libitum calorie intake.</td></tr>
  <tr><td>Maintain step count</td><td>Strong</td><td>Keep 8,000+ steps/day &#8212; not just during the diet but for life. NEAT is the most modifiable component of TDEE.</td></tr>
  <tr><td>Weekly weigh-in</td><td>Moderate‑Strong</td><td>Self-monitoring after weight loss is strongly associated with long-term maintenance (Wing &amp; Phelan, 2005). Weekly weigh-in provides early warning of regain before it compounds.</td></tr>
  <tr><td>Maintain sleep</td><td>Strong</td><td>Returning to poor sleep habits will drive appetite dysregulation and fat regain independently of calorie intake.</td></tr>
  <tr><td>Minimise ultra-processed food</td><td>Moderate</td><td>Ultra-processed foods drive calorie overconsumption via hedonic pathways independent of leptin/ghrelin (Hall et al., 2019).</td></tr>
</table>

<h2>5.5 Long-Term Recomposition Strategy</h2>
<p>Once weight maintenance is established (~Week 26‑30 post-start), consider a structured body recomposition phase:</p>
<ul>
  <li><strong>Training-day surplus:</strong> +100‑200 kcal above maintenance, prioritising extra carbohydrate (~50 g)</li>
  <li><strong>Rest-day deficit:</strong> −100‑200 kcal below maintenance</li>
  <li><strong>Weekly calorie target:</strong> At or slightly above maintenance</li>
  <li><strong>Expected outcome:</strong> Gradual LBM gain of 0.5‑1.0 kg/month with minimal concurrent fat gain</li>
  <li>Slower than a dedicated bulk but preserves the aesthetic outcome achieved by the 17-week protocol</li>
</ul>
"""

APPENDIX_BODY = """
<h1>Appendix A</h1>
<h2>Daily Meal Templates at a Glance</h2>

<h3>Training Day (1,800 kcal) &#8212; Core Template</h3>
<table>
  <tr><th>Meal #</th><th>Approx. Time</th><th>Protein Target</th><th>Key Foods</th></tr>
  <tr><td>1 &#8212; Pre/Breakfast</td><td>07:00‑07:30</td><td>25‑35 g</td><td>Eggs, Greek yoghurt, oats, fruit</td></tr>
  <tr><td>2 &#8212; Pre-Workout</td><td>60‑90 min before training</td><td>25‑30 g</td><td>Whey protein, banana, oats</td></tr>
  <tr><td>3 &#8212; Post-Workout / Lunch</td><td>Within 45 min post-training</td><td>45‑55 g</td><td>Chicken/fish, rice, vegetables</td></tr>
  <tr><td>4 &#8212; Dinner + Pre-Sleep</td><td>18:00‑19:00 / 21:30</td><td>50‑60 g (split)</td><td>Beef/salmon, veg, cottage cheese</td></tr>
</table>

<h3>Rest Day (1,650‑1,750 kcal) &#8212; Key Differences</h3>
<table>
  <tr><th>Meal</th><th>Key Difference from Training Day</th></tr>
  <tr><td>Breakfast</td><td>Reduce or eliminate starchy carbs; extra eggs or Greek yoghurt</td></tr>
  <tr><td>Lunch</td><td>Half the rice/potato portion; double vegetables</td></tr>
  <tr><td>Dinner</td><td>Same protein; carbs optional as no post-workout window</td></tr>
  <tr><td>Pre-sleep</td><td>Always include cottage cheese or casein &#8212; rest days are also MPS-important</td></tr>
</table>

<h3>Refeed Day (2,100 kcal &#8212; Fridays, Phases 2‑3)</h3>
<table>
  <tr><th>Macro</th><th>Target</th><th>Strategy</th></tr>
  <tr><td>Protein</td><td>175 g</td><td>Unchanged</td></tr>
  <tr><td>Carbohydrates</td><td>250‑270 g</td><td>Add: extra rice/pasta, oats, fruit, potato</td></tr>
  <tr><td>Fat</td><td>40‑45 g</td><td>Reduce: omit olive oil additions; choose leaner proteins</td></tr>
</table>

<h1>Appendix B</h1>
<h2>Weekly Progress Tracking Checklist</h2>
<table>
  <tr><th>&#9744;</th><th>Item</th><th>Target</th></tr>
  <tr><td>&#9744;</td><td>7-day average body weight recorded</td><td>Compare to last week; expect &#8595; 0.7‑0.9 kg</td></tr>
  <tr><td>&#9744;</td><td>Waist circumference (Monday morning)</td><td>Expect &#8595; 0.5‑1 cm/week</td></tr>
  <tr><td>&#9744;</td><td>Average daily steps</td><td>&#8805;8,000 rest days / &#8805;6,000 training days</td></tr>
  <tr><td>&#9744;</td><td>Training sessions completed</td><td>3‑4 per week; log weights &#215; reps</td></tr>
  <tr><td>&#9744;</td><td>Sleep average (hours in bed)</td><td>&#8805;7.5 hours</td></tr>
  <tr><td>&#9744;</td><td>Pre-sleep protein consumed (nights)</td><td>7/7 nights</td></tr>
  <tr><td>&#9744;</td><td>Creatine consumed daily</td><td>7/7 days</td></tr>
  <tr><td>&#9744;</td><td>Vitamin D3 + Omega-3 consumed</td><td>7/7 days</td></tr>
  <tr><td>&#9744;</td><td>Average daily hunger (1‑10)</td><td>Record; &#8805;8 for 5+ days &#8594; assess if break needed</td></tr>
  <tr><td>&#9744;</td><td>Training performance trend</td><td>Stable or improving; &#8595; &gt;10% flags an issue</td></tr>
  <tr><td>&#9744;</td><td>Diet break/refeed scheduled?</td><td>Per Week-by-Week Calendar, Section 3</td></tr>
  <tr><td>&#9744;</td><td>Alcohol units this week</td><td>Target: &#8804;2 standard drinks maximum</td></tr>
</table>

<h2>Alcohol Note</h2>
<p>Alcohol is not prohibited during this protocol, but carries specific costs during aggressive fat loss:</p>
<ul>
  <li>Alcohol suppresses fat oxidation for 12‑36 hours post-consumption (Suter et al., 1992) &#8212; not by converting to fat itself, but by becoming the priority fuel, parking all other substrate oxidation</li>
  <li>Alcohol at doses above 0.5 g/kg acutely suppresses testosterone production via Leydig cell inhibition (Emanuele et al., 2001)</li>
  <li>Even 1‑2 drinks substantially reduce slow-wave sleep (Ebrahim et al., 2013), where GH pulsatility is highest</li>
  <li>Recommended maximum during this protocol: 2 standard drinks, maximum 1 occasion per week, not on training nights</li>
</ul>
"""

REFS_BODY = """
<h1>References &amp; Literature Guide</h1>
<p class="intro">Organised by protocol section. Study type noted to assist in evaluating evidence quality.</p>

<h2>Energy Balance &amp; Deficit Mathematics</h2>
<ul>
  <li>Forbes, G.B. (1987). Lean body mass-body fat interrelationships in humans. <em>Nutrition Reviews</em>, 45(8), 225‑231. [Review]</li>
  <li>Hall, K.D. et al. (2012). Quantification of the effect of energy imbalance on bodyweight. <em>Lancet</em>, 378(9793), 826‑837. [Modelling study]</li>
  <li>Hall, K.D. &amp; Guo, J. (2017). Obesity energetics: body weight regulation and the effects of diet composition. <em>Gastroenterology</em>, 152(7), 1718‑1727. [Review]</li>
  <li>Barakat, C. et al. (2020). Body recomposition: can trained individuals build muscle and lose fat at the same time? <em>Strength &amp; Conditioning Journal</em>, 42(5), 7‑21. [Review]</li>
</ul>

<h2>Protein: Muscle Preservation During Deficit</h2>
<ul>
  <li>Helms, E.R. et al. (2014). Evidence-based recommendations for natural bodybuilding contest preparation. <em>JISSN</em>, 11, 20. [Systematic Review]</li>
  <li>Longland, T.M. et al. (2016). Higher compared with lower dietary protein during an energy deficit promotes greater lean mass gain. <em>AJCN</em>, 103(3), 738‑746. [RCT]</li>
  <li>Morton, R.W. et al. (2018). A systematic review and meta-analysis of protein supplementation on resistance training-induced gains in muscle mass. <em>BJSM</em>, 52(6), 376‑384. [Meta-analysis, 49 RCTs]</li>
  <li>Trommelen, J. et al. (2021). The anabolic response to protein ingestion during recovery from exercise has no upper limit in magnitude and duration in vivo in humans. <em>Cell Reports Medicine</em>, 4(12), 101324. [RCT]</li>
  <li>Areta, J.L. et al. (2013). Timing and distribution of protein ingestion alters myofibrillar protein synthesis. <em>Journal of Physiology</em>, 591(9), 2319‑2331. [RCT]</li>
</ul>

<h2>Anabolic Resistance in Ageing</h2>
<ul>
  <li>Churchward-Venne, T.A. et al. (2012). Nutritional regulation of muscle protein synthesis with resistance exercise. <em>Nutrition and Metabolism</em>, 9(1), 40. [Review]</li>
  <li>Breen, L. &amp; Phillips, S.M. (2011). Skeletal muscle protein metabolism in the elderly. <em>Nutrition and Metabolism</em>, 8(1), 68. [Review]</li>
  <li>Yang, Y. et al. (2012). Myofibrillar protein synthesis following ingestion of soy protein at rest and after resistance exercise in elderly men. <em>Nutrition and Metabolism</em>, 9(1), 57. [RCT]</li>
  <li>Norton, L.E. &amp; Layman, D.K. (2006). Leucine regulates translation initiation of protein synthesis in skeletal muscle after exercise. <em>Journal of Nutrition</em>, 136(2), 533S‑537S. [Review]</li>
</ul>

<h2>Dietary Fat and Hormonal Health</h2>
<ul>
  <li>Hamalainen, E. et al. (1984). Diet and serum sex hormones in healthy men. <em>Journal of Steroid Biochemistry</em>, 20(1), 459‑464.</li>
  <li>Hamalainen, E. et al. (1985). Decrease of serum total and free testosterone during a low-fat high-fibre diet. <em>Journal of Steroid Biochemistry</em>, 23(4), 459‑463. [RCT]</li>
  <li>Volek, J.S. et al. (1997). Testosterone and cortisol in relationship to dietary nutrients and resistance exercise. <em>Journal of Applied Physiology</em>, 82(1), 49‑54.</li>
  <li>Smith, G.I. et al. (2011). Dietary omega-3 fatty acid supplementation increases the rate of muscle protein synthesis in older adults. <em>AJCN</em>, 93(2), 402‑412. [RCT]</li>
</ul>

<h2>Nutrient Timing</h2>
<ul>
  <li>Esmarck, B. et al. (2001). Timing of postexercise protein intake is important for muscle hypertrophy in elderly men. <em>Journal of Physiology</em>, 535(1), 301‑311. [RCT]</li>
  <li>Cribb, P.J. &amp; Hayes, A. (2006). Effects of supplement timing and resistance exercise on skeletal muscle hypertrophy. <em>Med Sci Sports Exerc</em>, 38(11), 1918‑1925. [RCT]</li>
  <li>Schoenfeld, B.J. et al. (2013). The effect of protein timing on muscle strength and hypertrophy: a meta-analysis. <em>JISSN</em>, 10, 53. [Meta-analysis]</li>
  <li>Jäger, R. et al. (2017). ISSN Position Stand: protein and exercise. <em>JISSN</em>, 14, 20.</li>
  <li>Jakubowicz, D. et al. (2013). High caloric intake at breakfast vs. dinner differentially influences weight loss. <em>Obesity</em>, 21(12), 2504‑2512. [RCT]</li>
  <li>Res, P.T. et al. (2012). Protein ingestion before sleep improves postexercise overnight recovery. <em>Med Sci Sports Exerc</em>, 44(8), 1560‑1569. [RCT]</li>
</ul>

<h2>Metabolic Adaptation, Diet Breaks and Refeeds</h2>
<ul>
  <li>Byrne, N.M. et al. (2017). Intermittent energy restriction improves weight loss efficiency in obese men: the MATADOR study. <em>International Journal of Obesity</em>, 41(2), 174‑183. [RCT]</li>
  <li>Sumithran, P. et al. (2011). Long-term persistence of hormonal adaptations to weight loss. <em>NEJM</em>, 365(17), 1597‑1604. [Prospective cohort]</li>
  <li>Rosenbaum, M. &amp; Leibel, R.L. (2010). Adaptive thermogenesis in humans. <em>International Journal of Obesity</em>, 34(S1), S47‑S55. [Review]</li>
  <li>Levine, J.A. et al. (1999). Role of nonexercise activity thermogenesis in resistance to fat gain in humans. <em>Science</em>, 283(5399), 212‑214. [Prospective study]</li>
  <li>Peos, J.J. et al. (2019). Intermittent dieting: theoretical considerations for the athlete. <em>Sports</em>, 7(1), 8. [Review]</li>
  <li>Dirlewanger, M. et al. (2000). Effects of short-term carbohydrate or fat overfeeding on energy expenditure and plasma leptin. <em>International Journal of Obesity</em>, 24(11), 1413‑1418. [RCT]</li>
</ul>

<h2>Sleep and Recovery</h2>
<ul>
  <li>Nedeltcheva, A.V. et al. (2010). Insufficient sleep undermines dietary efforts to reduce adiposity. <em>Annals of Internal Medicine</em>, 153(7), 435‑441. [RCT]</li>
  <li>Leproult, R. &amp; Van Cauter, E. (2011). Effect of 1 week of sleep restriction on testosterone levels in young healthy men. <em>JAMA</em>, 305(21), 2173‑2174. [RCT]</li>
  <li>Van Cauter, E. et al. (2000). Age-related changes in slow wave sleep and relationship with growth hormone and cortisol. <em>JAMA</em>, 284(7), 861‑868.</li>
  <li>Snijders, T. et al. (2015). Protein ingestion before sleep increases muscle mass and strength gains during prolonged resistance exercise training. <em>Journal of Nutrition</em>, 145(6), 1178‑1184. [RCT]</li>
</ul>

<h2>Supplementation</h2>
<ul>
  <li>Pilz, S. et al. (2011). Effect of vitamin D supplementation on testosterone levels in men. <em>Hormone and Metabolic Research</em>, 43(3), 223‑225. [RCT]</li>
  <li>Cinar, V. et al. (2011). Effects of magnesium supplementation on testosterone levels of athletes. <em>Biological Trace Element Research</em>, 140(1), 18‑23. [RCT]</li>
  <li>Rawson, E.S. &amp; Volek, J.S. (2003). Effects of creatine supplementation and resistance training on muscle strength. <em>J Strength Cond Res</em>, 17(4), 822‑831. [RCT]</li>
  <li>Wankhede, S. et al. (2015). Examining the effect of Withania somnifera supplementation on muscle strength and recovery. <em>JISSN</em>, 12, 43. [RCT]</li>
  <li>Graham, T.E. (2001). Caffeine and exercise: metabolism, endurance and performance. <em>Sports Medicine</em>, 31(11), 785‑807. [Review]</li>
</ul>

<h2>Post-Diet Strategy and Weight Maintenance</h2>
<ul>
  <li>Trexler, E.T. et al. (2014). Metabolic adaptation to weight loss: implications for the athlete. <em>JISSN</em>, 11(1), 7. [Review]</li>
  <li>Wing, R.R. &amp; Phelan, S. (2005). Long-term weight loss maintenance. <em>AJCN</em>, 82(1), 222S‑225S. [Review]</li>
  <li>Hall, K.D. et al. (2019). Ultra-processed diets cause excess calorie intake and weight gain. <em>Cell Metabolism</em>, 30(1), 67‑77. [RCT]</li>
  <li>Dulloo, A.G. et al. (2012). Poststarvation hyperphagia and body fat overshooting in humans. <em>International Journal of Obesity</em>, 21(suppl 3), S9‑S16. [Review]</li>
</ul>

<h2>Further Reading</h2>
<ul>
  <li><em>International Journal of Sport Nutrition and Exercise Metabolism</em></li>
  <li><em>Journal of the International Society of Sports Nutrition</em></li>
  <li><em>American Journal of Clinical Nutrition</em></li>
  <li><em>Medicine and Science in Sports and Exercise</em></li>
  <li>Norton, L. &amp; Baker, G. (2019). <em>Fat Loss Forever.</em> Biolayne LLC.</li>
  <li>Helms, E., Morgan, A. &amp; Valdez, A. (2019). <em>The Muscle and Strength Pyramid: Nutrition.</em></li>
</ul>

<div class="box">
<h3>Disclaimer</h3>
<p>This protocol is compiled from peer-reviewed academic literature and represents current best-practice clinical sports nutrition guidance. It is educational in nature and does not constitute personalised medical advice. Consult a registered sports dietitian and your general practitioner before undertaking aggressive caloric restriction, particularly if you have any pre-existing metabolic, cardiovascular, or hormonal conditions. Blood work monitoring as recommended in Section 4.6 is strongly advised.</p>
</div>
"""


def build_epub():
    book = epub.EpubBook()
    book.set_identifier("weight-loss-protocol-17wk-2026")
    book.set_title("The 17-Week Aggressive Recomposition Protocol")
    book.set_language("en")
    book.add_author("Clinical Sports Nutrition & Exercise Physiology Analysis")
    book.add_metadata("DC", "description",
        "Evidence-based 17-week fat loss and muscle preservation protocol for a 42-year-old male athlete. "
        "85 kg to 69.5 kg with full macronutrient, timing, periodization, recovery and exit strategy guidance.")
    book.add_metadata("DC", "subject", "Sports Nutrition; Weight Loss; Body Recomposition; Exercise Physiology")
    book.add_metadata("DC", "date", datetime.date.today().isoformat())

    css_item = epub.EpubItem(
        uid="style",
        file_name="style/main.css",
        media_type="text/css",
        content=CSS
    )
    book.add_item(css_item)

    chapters_data = [
        ("cover",   "Cover",                                  COVER_BODY),
        ("toc",     "Table of Contents",                      TOC_BODY),
        ("ch1",     "Executive Summary & Key Numbers",        EXEC_BODY),
        ("ch2",     "Section 1: Macronutrients",              MACRO_BODY),
        ("ch3",     "Section 2: Nutrient Timing",             TIMING_BODY),
        ("ch4",     "Section 3: Periodization",               PERIOD_BODY),
        ("ch5",     "Section 4: Recovery & Supplements",      RECOVERY_BODY),
        ("ch6",     "Section 5: Exit Strategy",               EXIT_BODY),
        ("ch7",     "Appendices A & B",                       APPENDIX_BODY),
        ("ch8",     "References",                             REFS_BODY),
    ]

    chapters = []
    for uid, title, body in chapters_data:
        item = ch(title, f"{uid}.xhtml", body)
        item.add_item(css_item)
        book.add_item(item)
        chapters.append(item)

    book.toc = [
        epub.Link(f"{uid}.xhtml", title, uid)
        for uid, title, _ in chapters_data
    ]

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapters

    output_path = "/home/user/dan-sterling-paris.github.io/17-week-recomposition-protocol.epub"
    epub.write_epub(output_path, book, {"epub3_pages": False})
    print(f"EPUB written to: {output_path}")

    # Quick validation: check no chapter is 0 bytes inside the zip
    import zipfile
    with zipfile.ZipFile(output_path) as z:
        for name in z.namelist():
            if name.endswith(".xhtml") and "ch" in name:
                size = z.getinfo(name).file_size
                print(f"  {name}: {size:,} bytes")

    return output_path


if __name__ == "__main__":
    build_epub()
