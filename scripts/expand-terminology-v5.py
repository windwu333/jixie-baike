#!/usr/bin/env python3
"""
机械师大百科 术语扩展 V5 — Wikipedia extract mining + 100+ niche variant categories
从 ~3200 条追至 5000+ 条
"""

import json, re, os
from collections import Counter

PROJECT = "/Users/windwu/Desktop/机械师大百科项目"
TERMFILE = f"{PROJECT}/knowledge-base/mech-terminology-v2.json"
WIKIFILE = f"{PROJECT}/knowledge-base/wikipedia-pages.json"
EEDIR = f"{PROJECT}/raw/engineers-edge"
EFUNDA = f"{PROJECT}/raw/efunda"
TBDIR = f"{PROJECT}/raw/engineering-toolbox"

EN2ZH_DICT = {}
exec(open(f"{PROJECT}/scripts/expand-terminology-v2.py").read().split("# Common technical suffixes")[0],
     {"EN2ZH_DICT": EN2ZH_DICT, "__builtins__": __builtins__},
     {"EN2ZH_DICT": EN2ZH_DICT})

def norm(s):
    return re.sub(r'\s+', ' ', s.strip().lower())

def en2zh(t):
    tl = t.strip().lower()
    if tl in EN2ZH_DICT:
        return EN2ZH_DICT[tl]
    ws = tl.split()
    for end in range(len(ws), 0, -1):
        p = " ".join(ws[:end])
        if p in EN2ZH_DICT:
            return EN2ZH_DICT[p]
    return t

def cat_en(t):
    tl = t.lower()
    scores = []
    mfg_k = ["casting","forging","machining","welding","stamping","molding","extrusion",
             "annealing","quenching","tempering","forming","rolling","cutting","grinding",
             "milling","drilling","turning","boring","polishing","plating","coating",
             "manufacturing","fabrication","assembly","production","mold","die","press"]
    scores.append(("制造工艺", sum(1 for k in mfg_k if k in tl)))
    mat_k = ["steel","alloy","aluminum","copper","iron","titanium","nickel","metal",
             "plastic","polymer","ceramic","composite","material","stainless","bronze",
             "brass","zinc","magnesium","carbon","hardness","tensile","yield","fatigue",
             "corrosion","ferrous","non ferrous","grade","temper"]
    scores.append(("工程材料", sum(1 for k in mat_k if k in tl)))
    th_k = ["heat","temperature","fluid","flow","pressure","thermal","thermo","hydraulic",
            "pneumatic","steam","gas","liquid","pump","valve","pipe","boiler","condenser",
            "exchanger","cooling","heating","ventilation","air","compressor","turbine",
            "engine","combustion","hvac","refrigeration","chimney","stack","duct"]
    scores.append(("热工流体", sum(1 for k in th_k if k in tl)))
    md_k = ["gear","bearing","spring","shaft","screw","bolt","nut","fastener","coupling",
            "clutch","brake","belt","chain","cam","linkage","seal","gasket","flange",
            "design","stress","strain","load","torque","beam","deflection","vibration",
            "mechanism","lever","pulley","wheel","axle","joint","pin","key","spline",
            "washer","rivet","retaining ring","bushing","spacer"]
    scores.append(("机械设计", sum(1 for k in md_k if k in tl)))
    auto_k = ["motor","actuator","sensor","controller","robot","servo","automation",
              "control","plc","programmable","encoder","solenoid","electrical","electronic",
              "digital","feedback","cylinder","position","transformer","relay","switch",
              "circuit","voltage","current","frequency","amplifier","transducer"]
    scores.append(("机电自动化", sum(1 for k in auto_k if k in tl)))
    cad_k = ["cad","drawing","drafting","dimension","tolerance","gdt","blueprint",
             "schematic","diagram","view","projection","section","datum","surface finish"]
    scores.append(("制图CAD", sum(1 for k in cad_k if k in tl)))
    std_k = ["standard","specification","code","iso","astm","ansi","din","jis","asme",
             "sae","ieee","regulation","compliance","certification","inspection",
             "quality","calibration","testing","ndt","non destructive"]
    scores.append(("标准规范", sum(1 for k in std_k if k in tl)))
    best = max(scores, key=lambda x: x[1])
    return best[0] if best[1] > 0 else "未分类"

def gen_def(e):
    zh = en2zh(e)
    return f"{e} 是机械工程中{zh}相关的术语。" if zh != e else ""


# =========================================================================
# STEP 1: Wikipedia extract mining for additional technical terms
# =========================================================================
def mine_wiki_extracts():
    """Scan Wikipedia extracts for capitalized engineering terms."""
    found = []
    seen = set()
    data = json.load(open(WIKIFILE))
    cats = data.get("categories", {})

    # Map Wikipedia categories to our categories
    cat_map = {
        "Mechanical_engineering": "机械设计", "Manufacturing": "制造工艺",
        "Heat_transfer": "热工流体", "Machine_elements": "机械设计",
        "Mechanical_design": "机械设计", "Fluid_mechanics": "热工流体",
        "Engine_technology": "机电自动化", "Industrial_automation": "机电自动化",
        "Finite_element_method": "力学强度", "Engineering_materials": "工程材料",
        "Hydraulics": "热工流体", "Machining": "制造工艺",
    }

    # Engineering suffix words - terms ending with these are likely valid
    eng_suffixes = {"machine","device","system","valve","pump","motor","engine",
        "sensor","actuator","controller","gear","bearing","spring","shaft",
        "screw","bolt","nut","washer","flange","gasket","seal","coupling",
        "clutch","brake","belt","chain","cam","lever","pulley","wheel",
        "joint","pin","key","rivet","weld","pipe","tube","fitting","tool",
        "cutter","drill","die","mold","fixture","jig","chuck","collet",
        "process","method","technique","analysis","design","testing",
        "inspection","calibration","standard","code","regulation",
        "material","alloy","steel","metal","plastic","ceramic","composite",
        "furnace","boiler","turbine","compressor","generator","transformer",
        "relay","switch","converter","rectifier","inverter","transducer",
        "calculator","formula","equation","theory","principle","law",
        "effect","phenomenon","parameter","variable","function","factor",
        "coefficient","modulus","ratio","index","number","constant",
        "element","compound","mixture","solution","reaction","chemistry",
        "physics","mechanics","dynamics","kinematics","thermodynamics",
        "fluid mechanics","strength","stiffness","hardness","toughness",
        "ductility","brittleness","elasticity","plasticity","creep",
        "fatigue","fracture","corrosion","wear","erosion","friction",
        "lubrication","stress","strain","force","torque","load","pressure",
        "temperature","flow","velocity","acceleration","energy","power",
        "work","heat","mass","weight","density","volume","area","length",
        "design","engineering","manufacturing","production","assembly",
        "fabrication","casting","forging","rolling","drawing","extrusion",
        "welding","brazing","soldering","machining","grinding","milling",
        "turning","drilling","boring","reaming","tapping","threading",
        "honing","lapping","polishing","plating","coating","painting",
        "annealing","quenching","tempering","normalizing","hardening",
        "treatment","surface","finishing","inspection","testing","quality",
        "control","automation","robot","hydraulic","pneumatic","electric",
        "electronic","control","sensor","actuator","programmable","servo",
        "stepper","linear","rotary","reciprocating","oscillating"}

    for wiki_cat, pages in cats.items():
        our_cat = cat_map.get(wiki_cat, "机械设计")
        for page in pages:
            extract = page.get("extract", "")
            title = page.get("title", "")
            if not extract:
                continue
            # Find capitalized multi-word terms in the extract
            # Pattern: consecutive capitalized words (potential engineering terms)
            for match in re.finditer(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', extract):
                term = match.group(0).strip()
                if len(term) < 5 or len(term) > 60:
                    continue
                k = norm(term)
                if k in seen:
                    continue
                # Skip if it's the same as the page title
                if norm(term) == norm(title):
                    continue
                # Check if it looks like a real engineering term
                tl = term.lower()
                has_suffix = any(tl.endswith(ss) or f" {ss}" in tl for ss in eng_suffixes)
                if not has_suffix:
                    # Check for other technical indicators
                    indicators = ["design","system","method","process","material",
                        "machine","device","tool","analysis","testing"]
                    if not any(ind in tl for ind in indicators):
                        continue
                seen.add(k)
                found.append((term, our_cat))
    return found


# =========================================================================
# STEP 2: Extract technical bigrams from ALL text content
# =========================================================================
def mine_all_content_bigrams():
    """Extract 2-3 word engineering terms from all source text content using
    known engineering qualifier+base patterns."""
    found = []
    seen = set()

    # Known engineering bases and their qualifiers
    all_patterns = {
        "joint": ("机械设计", ["universal","knuckle","ball","socket","slip","expansion",
            "flexible","rigid","welded","riveted","bolted","glued","adhesive",
            "mechanical","threaded","compression","flare","swivel","rotary",
            "pivot","hinge","gimbal","cardan","hooke","constant velocity",
            "double cardan","tripod","plunge","fixed","plumbing","pipe"]),
        "ring": ("机械设计", ["o","retaining","snap","circlip","piston","seal",
            "backup","wiper","scraper","wear","lantern","spacer","spacing",
            "shim","adjusting","locking","split","solid","open","closed",
            "dowel","spring","groove","gland","packing","lip","v"]),
        "key": ("机械设计", ["square","flat","woodruff","gib head","feather",
            "sunk","saddle","hollow","tang","round","taper","parallel",
            "prismatic","slide","sliding","driven"]),
        "spline": ("机械设计", ["parallel","involute","serration","straight",
            "helical","crowned","ball","tapered"]),
        "cam": ("机械设计", ["plate","cylindrical","linear","face","grooved",
            "positive motion","snail","heart shaped","constant acceleration",
            "constant velocity","simple harmonic","cycloidal","polynomial"]),
        "press": ("制造工艺", ["hydraulic","pneumatic","mechanical","hand","arber",
            "bench","floor","gap","open back inclinable","straight side",
            "knuckle joint","toggle","screw","crank","eccentric","friction",
            "power","flywheel","hot","cold","forming","stamping","drawing",
            "coining","embossing","blanking","piercing","bending","deep"]),
        "die": ("制造工艺", ["punch","blanking","piercing","bending","drawing",
            "forming","coining","embossing","extrusion","forging","casting",
            "trimming","shaving","lancing","cutoff","compound","combination",
            "progressive","transfer","single","simple","sectional","split",
            "adjustable","universal","master","sub","insert","holder"]),
        "lock": ("机械设计", ["combination","pad","cylinder","deadbolt","mortise",
            "rim","cam","warded","disc","pin tumbler","wafer","lever",
            "magnetic","electronic","biometric","keyless","smart"]),
        "lubricant": ("工程材料", ["oil","grease","synthetic","mineral","semi synthetic",
            "solid","dry","penetrating","extreme pressure","anti seize",
            "anti wear","rust preventive","cutting","hydraulic","gear",
            "engine","compressor","turbine","bearing","chain","food grade",
            "high temperature","low temperature","biodegradable"]),
        "lubrication": ("机械设计", ["oil","grease","mist","splash","forced",
            "circulating","centralized","automatic","manual","drip",
            "wick","bath","flood","jet","spray","air oil","minimum quantity"]),
        "coolant": ("热工流体", ["cutting","grinding","machining","water based",
            "oil based","synthetic","semi synthetic","soluble oil","emulsion",
            "mineral oil","straight oil","chemical","gas","refrigerant"]),
        "adhesive": ("工程材料", ["epoxy","cyanoacrylate","polyurethane","silicone",
            "acrylic","anaerobic","hot melt","pressure sensitive",
            "structural","conductive","thermoset","thermoplastic","two part",
            "single part","uv curing","water based","solvent based"]),
        "corrosion": ("力学强度", ["galvanic","uniform","pitting","crevice",
            "stress corrosion","intergranular","selective leaching",
            "erosion corrosion","cavitation","fretting","microbial",
            "atmospheric","underground","high temperature"]),
        "composite": ("工程材料", ["carbon fiber","glass fiber","aramid","polymer matrix",
            "metal matrix","ceramic matrix","continuous fiber","short fiber",
            "woven","unidirectional","bidirectional","quasi isotropic",
            "laminate","sandwich","hybrid","nanocomposite"]),
        "displacement": ("力学强度", ["positive","negative","angular","linear",
            "vertical","horizontal","lateral","axial","radial","piston",
            "volumetric","swept","clearance","pump","compressor"]),
        "instrument": ("制图CAD", ["measuring","testing","recording","indicating",
            "controlling","calibrating","laboratory","field","portable",
            "stationary","analog","digital","precision","industrial"]),
        "mount": ("机械设计", ["rigid","flexible","shock","vibration","engine",
            "motor","pump","compressor","pipe","wall","floor","ceiling",
            "spring","rubber","adjustable","fixed","swivel","hinged"]),
        "grade": ("工程材料", ["commercial","standard","premium","structural",
            "marine","aircraft","automotive","industrial","food",
            "pharmaceutical","nuclear","cryogenic","high temperature"]),
        "speed": ("机电自动化", ["high","low","medium","variable","constant",
            "fixed","adjustable","synchronous","asynchronous","rated",
            "maximum","minimum","operating","cutting","spindle","feed"]),
        "thread": ("机械设计", ["external","internal","left hand","right hand",
            "single start","multi start","fine","coarse","unified",
            "metric","british standard","american standard","acme",
            "buttress","square","knuckle","pipe","taper","straight"]),
        "taper": ("机械设计", ["morse","jarno","brown sharpe","jacobs","bridgeport",
            "r8","iso","metric","british standard","self holding",
            "self releasing","steep","slow","standard"]),
        "wrench": ("制图CAD", ["open end","box end","combination","socket",
            "ratchet","torque","adjustable","pipe","strap","chain",
            "crowfoot","flare nut","hex","allen","torx","spanner"]),
        "cabinet": ("机电自动化", ["control","electrical","instrument","junction",
            "distribution","terminal","enclosure","panel","switchgear",
            "weatherproof","explosion proof","stainless steel"]),
        "panel": ("机电自动化", ["control","electrical","instrument","distribution",
            "solar","switch","junction","terminal","operator","display",
            "touch","front","rear","access","door mounted"]),
        "brazing": ("制造工艺", ["torch","furnace","induction","resistance","dip",
            "salt bath","vacuum","flux","silver","copper","aluminum",
            "nickel","gold","stainless steel","carbide"]),
        "soldering": ("制造工艺", ["soft","hard","wave","reflow","hand","dip",
            "furnace","induction","resistance","ultrasonic","infrared",
            "laser","hot air","solder iron"]),
        "hose": ("热工流体", ["hydraulic","pneumatic","water","steam","chemical",
            "oil","fuel","air","braided","reinforced","rubber","ptfe",
            "nylon","polyurethane","stainless steel","flexible",
            "high pressure","low pressure","suction","discharge"]),
        "coupler": ("机械设计", ["quick","hydraulic","pneumatic","air","water",
            "hydrant","camlock","threaded","flush face","flat face",
            "high pressure","low pressure","dry break","non spill"]),
        "pulley": ("机械设计", ["flat belt","v belt","timing","crowned","stepped",
            "idler","tensioner","driven","drive","driver","driven",
            "tightener","snubber","deflector","grooved","flanged",
            "cast iron","steel","aluminum","nylon","delrin"]),
        "lever": ("机械设计", ["first class","second class","third class","bell crank",
            "hand","foot","treadle","toggle","angle","bent","straight",
            "compound","locking","disconnect","shifting","control"]),
        "grip": ("机械设计", ["hand","tool","ergonomic","rubber","plastic",
            "pistol","straight","power","precision","pinch","finger"]),
        # add more standard/manufacturing terms
        "inspection": ("标准规范", ["visual","dimensional","surface","ultrasonic",
            "magnetic particle","liquid penetrant","radiographic",
            "eddy current","acoustic emission","leak","pressure",
            "hydrostatic","pneumatic","proof","functional",
            "first article","in process","final","receiving"]),
        "allowance": ("机械设计", ["clearance","interference","transition",
            "basic","shaft basis","hole basis","standard","special"]),
        "fit": ("机械设计", ["clearance","interference","transition","press",
            "shrink","drive","running","sliding","locational",
            "force","tight","wringing","push","easy","loose"]),
        "stress": ("力学强度", ["tensile","compressive","shear","torsional",
            "bending","thermal","residual","contact","bearing",
            "principal","von mises","allowable","working",
            "design","yield","ultimate","proof","endurance",
            "fatigue","impact","burst","hoop","longitudinal",
            "radial","tangential","normal","direct"]),
    }

    # Scan all text sources
    sources = []

    # Engineers Edge
    for fn in os.listdir(EEDIR):
        if fn.endswith('.json'):
            try:
                sources.extend(json.load(open(f"{EEDIR}/{fn}")))
            except: pass

    # Also scan extract content
    data = json.load(open(WIKIFILE))
    for pages in data.get("categories", {}).values():
        for p in pages:
            sources.append({"title": p["title"], "text": p.get("extract","")})

    # Efunda content
    for fn in os.listdir(EFUNDA):
        if fn.endswith('.json'):
            try:
                for r in json.load(open(f"{EFUNDA}/{fn}")):
                    sources.append({"title": r.get("title",""), "text": r.get("content","")})
            except: pass

    for rec in sources:
        title = rec.get("title","")
        text = rec.get("text","")
        content = (title + " " + text).lower()
        for base, (cat, qualifiers) in all_patterns.items():
            for qual in qualifiers:
                compound = f"{qual} {base}"
                k = norm(compound)
                if k in seen:
                    continue
                if compound.lower() in content:
                    seen.add(k)
                    found.append((compound, cat))
    return found


# =========================================================================
# STEP 3: More niche variant categories
# =========================================================================
def gen_niche_variants():
    r = []

    # Mechanical design - seals
    for s in ["mechanical","lip","oil","radial shaft","face","labyrinth","v ring",
        "o ring","wipers","scraper","piston","rod","rotary","stationary",
        "dynamic","clearance","floating","magneto","abradable","gas","dry",
        "wet","contact","non contact","hydrodynamic","hydrostatic","magnetic"]:
        r.append((f"{s} seal", "机械设计"))

    # Engineering standards
    for std in ["astm","iso","ansi","din","jis","asme","sae","ieee","api",
        "nema","ul","ce", "bs","gb","en","iec","nace","iso 9000","iso 14000",
        "iso 9001","iso 14001","ohsas 18001","six sigma","lean manufacturing",
        "total quality management","statistical process control",
        "statistical quality control","acceptance sampling","zero defect",
        "continuous improvement","kaizen","poka yoke","kanban","just in time",
        "5s","value stream mapping","failure mode","cause and effect",
        "control chart","pareto analysis","process capability",
        "measurement system analysis","gauge repeatability",
        "gauge reproducibility","gauge r and r","calibration procedure",
        "quality assurance","quality control","quality management",
        "quality system","quality audit","quality plan","quality policy"]:
        r.append((f"{std}", "标准规范"))

    # GD&T
    for gdt in ["straightness","flatness","circularity","cylindricity",
        "profile of a line","profile of a surface","angularity","perpendicularity",
        "parallelism","position","concentricity","symmetry","circular runout",
        "total runout","maximum material condition","least material condition",
        "regardless of feature size","datum feature","datum target",
        "feature control frame","basic dimension","reference dimension",
        "tolerance zone","projected tolerance zone","bonus tolerance",
        "virtual condition","resultant condition","inner boundary",
        "outer boundary","actual mating envelope","minimum material envelope"]:
        r.append((gdt, "制图CAD"))

    # More heat transfer
    for ht in ["conduction","convection","radiation","thermal conduction",
        "thermal convection","thermal radiation","natural convection",
        "forced convection","boiling heat transfer","condensation heat transfer",
        "film coefficient","heat transfer coefficient","overall heat transfer coefficient",
        "fouling factor","log mean temperature difference","number of transfer units",
        "effectiveness ntu method","laminar flow","turbulent flow",
        "transition flow","reynolds number","prandtl number","nusselt number",
        "grashof number","peclet number","stefan boltzmann constant",
        "black body","gray body","emissivity","absorptivity","reflectivity",
        "transmissivity","view factor","radiation shield","fin efficiency",
        "fin effectiveness","biot number","fourier number"]:
        r.append((ht, "热工流体"))

    # Fluid mechanics
    for fm in ["bernoulli equation","continuity equation","navier stokes equation",
        "euler equation","darcy weisbach equation","hagen poiseuille equation",
        "manning equation","darcy friction factor","fanning friction factor",
        "moody chart","relative roughness","hydraulic diameter",
        "hydraulic radius","hydraulic gradient","energy grade line",
        "hydraulic grade line","major loss","minor loss","head loss",
        "friction loss","entrance loss","exit loss","bend loss",
        "valve loss","fitting loss","equivalent length","flow coefficient",
        "discharge coefficient","contraction coefficient","velocity coefficient",
        "vena contracta","orifice meter","venturi meter","flow nozzle",
        "pitot tube","annubar","turbine meter","positive displacement meter",
        "ultrasonic flow meter","magnetic flow meter","vortex flow meter",
        "coriolis flow meter","thermal mass flow meter"]:
        r.append((fm, "热工流体"))

    # Thermodynamics
    for td in ["ideal gas law","boyle law","charles law","gay lussac law",
        "combined gas law","specific heat","specific heat capacity",
        "internal energy","enthalpy","entropy","gibbs free energy",
        "helmholtz free energy","carnot cycle","otto cycle","diesel cycle",
        "brayton cycle","rankine cycle","stirling cycle","erricsson cycle",
        "lenoir cycle","atkinson cycle","miller cycle","dual cycle",
        "carnot efficiency","thermal efficiency","isentropic efficiency",
        "volumetric efficiency","mechanical efficiency","overall efficiency",
        "compression ratio","cutoff ratio","pressure ratio","specific fuel consumption",
        "heat rate","brake specific fuel consumption","indicated specific fuel consumption"]:
        r.append((td, "热工流体"))

    # Strength of materials - additional
    for sm in ["hooke law","stress strain curve","elastic region","plastic region",
        "yield point","upper yield point","lower yield point","strain hardening",
        "necking","ultimate strength","fracture point","true stress",
        "true strain","engineering stress","engineering strain",
        "nominal stress","nominal strain","offset yield method",
        "0.2 percent offset","proof stress","elastic limit",
        "proportional limit","modulus of elasticity","elastic modulus",
        "young modulus","shear modulus","bulk modulus","poisson ratio",
        "axial deformation","torsional deformation","bending deformation",
        "shear deformation","thermal deformation","creep deformation",
        "elastic deformation","plastic deformation","viscoelastic deformation"]:
        r.append((sm, "力学强度"))

    # Manufacturing - more processes
    for p in [
        "abrasive water jet machining","abrasive flow machining","electrochemical machining",
        "electrochemical grinding","electrical discharge machining","die sinking edm",
        "wire edm","electron beam machining","laser beam machining","ion beam machining",
        "plasma arc machining","ultrasonic machining","chemical machining",
        "photochemical machining","electropolishing","magnetic abrasive finishing",
        "magnetorheological finishing","abrasive jet machining","water jet machining",
        "cryogenic machining","hot machining","high speed machining",
        "micro machining","nano machining","precision machining",
        "roll bonding","explosive welding","friction welding","inertia welding",
        "continuous drive friction welding","linear friction welding",
        "friction stir welding","friction stir processing","ultrasonic welding",
        "diffusion welding","hot isostatic pressing","cold isostatic pressing",
        "powder metallurgy","metal injection molding","ceramic injection molding",
        "additive manufacturing","3d printing","stereolithography",
        "selective laser sintering","selective laser melting","electron beam melting",
        "fused deposition modeling","direct metal laser sintering",
        "laminated object manufacturing","digital light processing",
        "binder jetting","direct energy deposition","laser metal deposition",
        "wire arc additive manufacturing","cold spray"]:
        r.append((p, "制造工艺"))

    return r


def run():
    print("=" * 60)
    print("机械师大百科 术语扩展 V5 (extract mining + 100+ niche variants)")
    print("=" * 60)

    data = json.load(open(TERMFILE))
    existing = data["terms"]
    start_count = len(existing)
    print(f"\nCurrent: {start_count}")

    seen = set()
    for t in existing:
        seen.add(norm(t["en"]))

    all_new = []

    # Step 1: Wikipedia extract mining
    print("\n[1/3] Mining Wikipedia extracts...")
    wiki_terms = mine_wiki_extracts()
    w_add = 0
    for term, our_cat in wiki_terms:
        k = norm(term)
        if k in seen:
            continue
        seen.add(k)
        all_new.append({
            "en": term, "zh": en2zh(term), "definition": gen_def(term),
            "source": "wiki-extract", "category": our_cat,
        })
        w_add += 1
    print(f"  Found: {len(wiki_terms)}, New: {w_add}")

    # Step 2: Bigram mining from all content
    print("\n[2/3] Mining bigrams from all text content...")
    bigrams = mine_all_content_bigrams()
    b_add = 0
    for term, our_cat in bigrams:
        k = norm(term)
        if k in seen:
            continue
        seen.add(k)
        all_new.append({
            "en": term, "zh": en2zh(term), "definition": gen_def(term),
            "source": "bigram-mine", "category": our_cat,
        })
        b_add += 1
    print(f"  Found: {len(bigrams)}, New: {b_add}")

    # Step 3: Niche variant generation
    print("\n[3/3] Generating niche variant categories...")
    variants = gen_niche_variants()
    v_add = 0
    for term, our_cat in variants:
        k = norm(term)
        if k in seen:
            continue
        seen.add(k)
        all_new.append({
            "en": term, "zh": en2zh(term), "definition": gen_def(term),
            "source": "variant-v5", "category": our_cat,
        })
        v_add += 1
    print(f"  Generated: {len(variants)}, New: {v_add}")

    # Assemble
    data["terms"] = existing + all_new
    data["meta"]["total_terms"] = len(data["terms"])
    data["meta"]["expanded_new_terms"] = data["meta"].get("expanded_new_terms", 0) + len(all_new)
    data["meta"]["version"] = "2.4"
    data["meta"]["last_expanded"] = "2026-05-18"

    # Save
    json.dump(data, open(TERMFILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    cat_c = Counter(t.get("category","未分类") for t in data["terms"])
    src_c = Counter(t.get("source","unknown") for t in data["terms"])

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"\n  Before: {start_count}")
    print(f"  New added: {len(all_new)}")
    print(f"  Final total: {len(data['terms'])}")
    print(f"\n  Category Distribution:")
    for cat, cnt in sorted(cat_c.items(), key=lambda x: -x[1]):
        print(f"    {cat}: {cnt:5d} ({cnt/len(data['terms'])*100:5.1f}%)")
    print(f"\n  Source Distribution:")
    for src, cnt in sorted(src_c.items(), key=lambda x: -x[1]):
        print(f"    {src}: {cnt}")
    zh_n = sum(1 for t in data["terms"] if not t.get("zh"))
    df_n = sum(1 for t in data["terms"] if not t.get("definition"))
    print(f"\n  No Chinese: {zh_n}")
    print(f"  No definition: {df_n}")

if __name__ == "__main__":
    run()
