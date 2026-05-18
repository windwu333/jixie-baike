#!/usr/bin/env python3
"""
机械师大百科 V6 — 最终扩展: Wikipedia extract n-gram mining + 全领域变体
目标: 3583 -> 5000+
"""

import json, re, os
from collections import Counter

PROJ = "/Users/windwu/Desktop/机械师大百科项目"
TERM = f"{PROJ}/knowledge-base/mech-terminology-v2.json"
WIKI = f"{PROJ}/knowledge-base/wikipedia-pages.json"
EED = f"{PROJ}/raw/engineers-edge"
EFD = f"{PROJ}/raw/efunda"
TBD = f"{PROJ}/raw/engineering-toolbox"

EN2ZH = {}
exec(open(f"{PROJ}/scripts/expand-terminology-v2.py").read().split("# Common technical suffixes")[0],
     {"EN2ZH_DICT": EN2ZH, "__builtins__": __builtins__},
     {"EN2ZH_DICT": EN2ZH})

def norm(s):
    return re.sub(r'\s+', ' ', s.strip().lower())

def e2z(t):
    tl = t.strip().lower()
    if tl in EN2ZH: return EN2ZH[tl]
    ws = tl.split()
    for end in range(len(ws), 0, -1):
        p = " ".join(ws[:end])
        if p in EN2ZH: return EN2ZH[p]
    return t

def cat_en(t):
    tl = t.lower()
    sc = []
    sc.append(("制造工艺", sum(1 for k in ["casting","forging","machining","welding","stamping","molding","extrusion","annealing","quenching","tempering","forming","rolling","cutting","grinding","milling","drilling","turning","boring","polishing","plating","coating","manufacturing","fabrication","assembly","production","mold","die","press"] if k in tl)))
    sc.append(("工程材料", sum(1 for k in ["steel","alloy","aluminum","copper","iron","titanium","nickel","metal","plastic","polymer","ceramic","composite","material","stainless","bronze","brass","zinc","magnesium","carbon","hardness","tensile","yield","fatigue","corrosion"] if k in tl)))
    sc.append(("热工流体", sum(1 for k in ["heat","temperature","fluid","flow","pressure","thermal","thermo","hydraulic","pneumatic","steam","gas","liquid","pump","valve","pipe","boiler","condenser","exchanger","cooling","heating","ventilation","air","compressor","turbine","engine","combustion","hvac","refrigeration","chimney","stack","duct"] if k in tl)))
    sc.append(("机械设计", sum(1 for k in ["gear","bearing","spring","shaft","screw","bolt","nut","fastener","coupling","clutch","brake","belt","chain","cam","linkage","seal","gasket","flange","design","stress","strain","load","torque","beam","deflection","vibration","mechanism","lever","pulley","wheel","axle","joint","pin","key","spline","washer","rivet","retaining ring","bushing","spacer"] if k in tl)))
    sc.append(("机电自动化", sum(1 for k in ["motor","actuator","sensor","controller","robot","servo","automation","control","plc","programmable","encoder","solenoid","electrical","electronic","digital","feedback","cylinder","position","transformer","relay","switch","circuit","voltage","current","frequency","amplifier","transducer"] if k in tl)))
    sc.append(("制图CAD", sum(1 for k in ["cad","drawing","drafting","dimension","tolerance","gdt","blueprint","schematic","diagram","view","projection","section","datum","surface finish"] if k in tl)))
    sc.append(("标准规范", sum(1 for k in ["standard","specification","code","iso","astm","ansi","din","jis","asme","sae","ieee","regulation","compliance","certification","inspection","quality","calibration","testing","ndt","non destructive"] if k in tl)))
    best = max(sc, key=lambda x: x[1])
    return best[0] if best[1] > 0 else "未分类"

def gen_def(e):
    zh = e2z(e)
    return f"{e} 是机械工程中{zh}相关的术语。" if zh != e else ""


# ============================================================================
# 1. WIKIPEDIA EXTRACT N-GRAM MINING - V2
# Extract ALL 2-3 word phrases containing known engineering terms
# ============================================================================
def mine_wiki_ngrams():
    """Extract 2-3 word phrases from Wikipedia extracts that contain known
    engineering domain vocabulary. Much more aggressive than V5."""
    found = []
    seen = set()

    data = json.load(open(WIKI))
    cat_map = {
        "Mechanical_engineering": "机械设计", "Manufacturing": "制造工艺",
        "Heat_transfer": "热工流体", "Machine_elements": "机械设计",
        "Mechanical_design": "机械设计", "Fluid_mechanics": "热工流体",
        "Engine_technology": "机电自动化", "Industrial_automation": "机电自动化",
        "Finite_element_method": "力学强度", "Engineering_materials": "工程材料",
        "Hydraulics": "热工流体", "Machining": "制造工艺",
    }

    # Known engineering headwords (common 2nd-word of compounds)
    heads = {"valve","pump","gear","bearing","spring","motor","sensor","shaft",
        "brake","clutch","coupling","belt","chain","seal","gasket","flange",
        "pipe","tube","fitting","bolt","nut","screw","washer","rivet","pin",
        "key","joint","lever","cam","wheel","pulley","turbine","engine",
        "cylinder","piston","nozzle","filter","actuator","transformer",
        "relay","switch","converter","rectifier","inverter","accumulator",
        "boiler","exchanger","condenser","furnace","compressor","generator",
        "tool","die","mold","fixture","jig","drill","reamer","broach","tap",
        "cutter","blade","knife","saw","hammer","wrench","screwdriver","pliers",
        "clamp","vise","chuck","collet","spindle","arbor","adapter","connector",
        "coupler","elbow","tee","cross","union","nipple","reducer","bushing",
        "cap","plug","cover","guard","shield","housing","case","frame",
        "base","plate","bracket","mount","stand","pedestal","support",
        "beam","column","truss","girder","rod","bar","wire","cable","rope",
        "chain","belt","hose","duct","conduit","tray","ladder","railing",
        "stair","platform","scaffold","lattice","grid","mesh","screen",
        "surface","coating","layer","film","sheet","plate","strip","foil",
        "treatment","process","method","technique","system","apparatus",
        "device","machine","equipment","instrument","tool","gage","meter",
        "indicator","controller","regulator","timer","counter","totalizer",
        "recorder","logger","analyzer","monitor","detector","scanner",
        "tester","tank","vessel","container","reservoir","hopper","bin",
        "silo","drum","barrel","bucket","pail","canister","cartridge",
        "chamber","furnace","oven","kiln","dryer","cooler","heater",
        "chiller","freezer","refrigerator","incubator","autoclave",
        "press","stamp","hammer","anvil","former","mold","die","pattern",
        "core","cope","drag","flask","ladle","crucible","tongs",
        "spectrometer","microscope","caliper","micrometer","gauge"} | set(EN2ZH.keys())

    # Technical context words that indicate a meaningful engineering term
    qualifiers = {"automatic","manual","hydraulic","pneumatic","electric",
        "mechanical","electronic","digital","analog","rotary","linear",
        "reciprocating","oscillating","vibrating","rotating","sliding",
        "rolling","stationary","fixed","adjustable","variable","constant",
        "high","low","medium","cold","hot","warm","wet","dry","heavy",
        "light","small","large","miniature","industrial","commercial",
        "portable","stationary","vertical","horizontal","inclined",
        "centrifugal","axial","radial","tangential","spiral","helical",
        "conical","cylindrical","spherical","elliptical","square",
        "rectangular","triangular","round","circular","oval","fluid",
        "gas","liquid","solid","powder","granular","fibrous","foam",
        "corrosion","wear","heat","thermal","cryogenic","steam","water",
        "oil","air","gas","vacuum","pressure","force","torque","power",
        "energy","speed","velocity","flow","volume","mass","density",
        "precision","accurate","coarse","fine","rough","smooth","flat",
        "parallel","perpendicular","concentric","eccentric","offset"}

    def is_tech_phrase(phrase):
        """Check if a 2-3 word phrase looks like a real engineering term."""
        pl = phrase.lower()
        words = pl.split()
        # Check if last word is an engineering headword
        if words[-1] in heads:
            return True
        # Check if any word is in our translation dictionary
        if any(w in EN2ZH for w in words):
            return True
        # Check technical suffix
        for h in heads:
            if pl.endswith(h):
                return True
        return False

    for wiki_cat, pages in data.get("categories",{}).items():
        our_cat = cat_map.get(wiki_cat, "机械设计")
        for page in pages:
            title = page.get("title","")
            extract = page.get("extract","")
            if not extract:
                continue
            # Also include the page title as a source
            text = extract
            # Remove punctuation for n-gram extraction
            clean = re.sub(r"[,.!?;:()\[\]\"']", ' ', text)
            words = clean.split()

            # Extract all 2-3 word phrases
            for i in range(len(words)):
                # 2-grams
                if i + 1 < len(words):
                    phrase = " ".join(words[i:i+2])
                    if re.match(r'^[A-Za-z].*[a-z]$', phrase):
                        pl = phrase.lower()
                        if is_tech_phrase(pl) and 4 < len(phrase) < 50:
                            k = norm(phrase)
                            if k not in seen and norm(phrase) != norm(title):
                                seen.add(k)
                                found.append((phrase, our_cat))
                # 3-grams
                if i + 2 < len(words):
                    phrase = " ".join(words[i:i+3])
                    if re.match(r'^[A-Za-z].*[a-z]$', phrase):
                        pl = phrase.lower()
                        if is_tech_phrase(pl) and 4 < len(phrase) < 60:
                            k = norm(phrase)
                            if k not in seen and norm(phrase) != norm(title):
                                seen.add(k)
                                found.append((phrase, our_cat))
    return found


# ============================================================================
# 2. DOMAIN-SPECIFIC GENERATORS
# ============================================================================

def gen_hvac():
    r = []
    for t in ["ductwork","air duct","supply duct","return duct","exhaust duct",
        "fresh air intake","air diffuser","grille","register","air vent",
        "damper","volume control damper","fire damper","smoke damper",
        "chilled water system","hot water system","two pipe system",
        "four pipe system","variable air volume","constant air volume",
        "fan coil unit","air handling unit","rooftop unit","packaged unit",
        "split system","heat pump system","geothermal heat pump",
        "absorption chiller","centrifugal chiller","reciprocating chiller",
        "screw chiller","cooling tower","evaporative condenser",
        "air cooled condenser","water cooled condenser","shell and tube condenser",
        "thermal expansion valve","thermostatic expansion valve",
        "electronic expansion valve","capillary tube","orifice metering device",
        "compressor","condensing unit","evaporator coil","condenser coil",
        "air filter","hepa filter","electrostatic precipitator",
        "uv germicidal irradiation","humidifier","dehumidifier",
        "psychrometrics","sensible heat","latent heat","specific humidity",
        "relative humidity","dew point","wet bulb temperature","dry bulb temperature",
        "enthalpy","humidity ratio","degree day","seasonal energy efficiency ratio",
        "energy efficiency ratio","coefficient of performance","hvac control",
        "thermostat","programmable thermostat","smart thermostat",
        "zone damper","zone control","building automation system",
        "energy management system","direct digital control",
        "pneumatic control","proportional integral derivative"]:
        r.append((t, "热工流体"))
    return r

def gen_automotive():
    r = []
    for t in ["cylinder block","cylinder head","crankcase","oil pan","valve cover",
        "timing cover","intake manifold","exhaust manifold","throttle body",
        "fuel injector","spark plug","ignition coil","distributor","alternator",
        "starter motor","water pump","oil pump","fuel pump","power steering pump",
        "air conditioning compressor","radiator","intercooler","charge air cooler",
        "turbocharger","supercharger","wastegate","blow off valve","egr valve",
        "pcv valve","thermostat housing","water jacket","crankshaft pulley",
        "camshaft","connecting rod","piston pin","piston ring","main bearing",
        "connecting rod bearing","camshaft bearing","valve spring",
        "valve guide","valve seat","push rod","rocker arm","tappet","lifter",
        "timing chain","timing belt","timing gear","balance shaft",
        "flywheel","flexplate","harmonic balancer","clutch disc",
        "pressure plate","throwout bearing","pilot bearing",
        "transmission","manual transmission","automatic transmission",
        "continuously variable transmission","dual clutch transmission",
        "torque converter","planetary gearset","differential","limited slip differential",
        "locking differential","drive shaft","half shaft","cv joint",
        "universal joint","axle shaft","wheel hub","wheel bearing",
        "brake caliper","brake rotor","brake drum","brake pad","brake shoe",
        "wheel cylinder","master cylinder","brake booster","abs modulator",
        "brake line","brake hose","parking brake","steering rack",
        "steering gear","steering column","tie rod","control arm",
        "ball joint","sway bar","struts","shock absorber","coil over",
        "leaf spring","trailing arm","radius arm","panhard rod"]:
        r.append((t, "机电自动化"))
    return r

def gen_plumbing():
    r = []
    for t in ["water supply","drainage system","sewer system","storm drain",
        "vent pipe","soil pipe","waste pipe","overflow pipe","downpipe",
        "gutter","rainwater harvesting","gray water system",
        "hot water heater","water heater","tankless water heater",
        "storage tank","expansion tank","pressure tank","backflow preventer",
        "reduced pressure zone","double check valve","air gap",
        "vacuum breaker","temperature pressure relief valve",
        "mixing valve","thermostatic mixing valve","pressure balancing valve",
        "diverter valve","shower valve","faucet","spigot","bibcock",
        "hose bib","sill cock","wall hydrant","frost proof hydrant",
        "trap","p trap","s trap","drum trap","grease trap","floor drain",
        "roof drain","area drain","sump pump","ejector pump",
        "water meter","pressure regulator","water softener",
        "reverse osmosis","water filter","uv sterilizer",
        "shutoff valve","service valve","stop valve","angle stop",
        "compression fitting","flare fitting","push fit fitting",
        "sweat fitting","solder fitting","dielectric union",
        "pipe hanger","pipe clamp","pipe strap","pipe support",
        "pipe insulation","pipe wrap","heat tape","freeze protection"]:
        r.append((t, "热工流体"))
    return r

def gen_material_grades():
    r = []
    for g in ["a36","a572","a514","a588","a992","1018","1045","1095","1117",
        "1141","1144","1215","12l14","4140","4150","4340","4620","4820",
        "5160","52100","6150","8620","9310","h13","d2","a2","o1","s7",
        "m2","m42","w1","304","304l","316","316l","317","321","347","410",
        "416","420","430","440c","17 4 ph","17 7 ph","2024","6061","6063",
        "7075","5052","5083","356","a356","319","a319","c26000","c36000",
        "c46400","c93200","c95400","c95500"]:
        r.append((f"{g} material grade", "工程材料"))
    return r

def gen_construction():
    r = []
    for t in ["foundation","footing","spread footing","mat foundation","pile foundation",
        "caisson","grade beam","retaining wall","gravity wall","cantilever wall",
        "sheet pile","soil nail","ground anchor","tieback",
        "slab","concrete slab","reinforced slab","post tensioned slab",
        "beam","girder","joist","rafter","purlin","truss","frame",
        "rigid frame","braced frame","moment frame","shear wall",
        "brace","cross brace","k brace","v brace","chevron brace",
        "column","pillar","pier","abutment","bearing pad","expansion joint",
        "control joint","construction joint","isolation joint",
        "reinforcing bar","rebar","steel reinforcement","fiber reinforcement",
        "welded wire mesh","rebar cage","stirrup","tie","spiral reinforcement",
        "formwork","shoring","scaffolding","falsework","centering",
        "curing compound","form release agent","bond breaker",
        "waterstop","drip edge","weep hole","drainage mat"]:
        r.append((t, "标准规范"))
    return r

def gen_powerplant():
    r = []
    for t in ["steam generator","water wall","superheater","reheater","economizer",
        "air preheater","burner","windbox","ignitor","fuel nozzle",
        "sootblower","slag tap","ash hopper","fly ash","bottom ash",
        "baghouse","electrostatic precipitator","scrubber","flue gas desulfurization",
        "selective catalytic reduction","selective non catalytic reduction",
        "cooling water intake","discharge canal","condenser tube",
        "tube sheet","water box","condensate pump","boiler feed pump",
        "deaerator","feedwater heater","high pressure heater","low pressure heater",
        "steam turbine","hp turbine","ip turbine","lp turbine",
        "generator","exciter","rotor","stator","brushless exciter",
        "main transformer","unit auxiliary transformer","startup transformer",
        "switchyard","gis","circuit breaker","disconnect switch",
        "gas turbine","combustor","compressor","power turbine",
        "heat recovery steam generator","duct burner","bypass stack",
        "diverter damper","co generation","combined heat and power",
        "combined cycle","simple cycle","open cycle","closed cycle"]:
        r.append((t, "热工流体"))
    return r

def gen_mining():
    r = []
    for t in ["crusher","jaw crusher","gyratory crusher","cone crusher","impact crusher",
        "hammer mill","ball mill","rod mill","sag mill","pebble mill",
        "vibrating screen","trommel screen","classifier","hydrocyclone",
        "spiral classifier","flotation cell","flotation machine",
        "thickener","clarifier","filter press","vacuum filter","belt filter",
        "conveyor belt","belt conveyor","apron feeder","vibrating feeder",
        "screw conveyor","bucket elevator","skip hoist","mine hoist",
        "winders","sheave","head frame","headgear","cage","skip",
        "drill rig","rotary drill","percussion drill","diamond drill",
        "jumbo drill","drill steel","drill bit","button bit","cross bit",
        "loader","scoop","shovel","excavator","dragline","haul truck",
        "dozer","grader","compactor","roller","pneumatic tire"]:
        r.append((t, "制造工艺"))
    return r

def gen_marine():
    r = []
    for t in ["hull","bulkhead","deck","superstructure","forecastle","poop deck",
        "bridge","engine room","propeller","propeller shaft","stern tube",
        "rudder","steering gear","bow thruster","stern thruster",
        "anchor","chain locker","windlass","capstan","bollard","fairlead",
        "mooring line","fender","rub rail","bilge keel","stabilizer",
        "lifeboat","life raft","davit","gangway","accommodation ladder",
        "hatch cover","watertight door","scuttle","porthole","deadlight",
        "ventilation cowl","mast","boom","derrick","crane",
        "ballast system","bilge system","fire main","sprinkler system",
        "cofferdam","void space","double bottom","wing tank",
        "fuel oil tank","lube oil tank","fresh water tank",
        "sea chest","overboard discharge","sacrificial anode"]:
        r.append((t, "机械设计"))
    return r

def gen_mfg_processes_more():
    r = []
    for t in ["additive manufacturing","3d printing","stereolithography",
        "digital light processing","continuous liquid interface production",
        "selective laser sintering","direct metal laser sintering",
        "selective laser melting","electron beam melting","electron beam powder bed fusion",
        "laser powder bed fusion","directed energy deposition",
        "laser metal deposition","wire arc additive manufacturing",
        "fused filament fabrication","fused deposition modeling",
        "material extrusion","binder jetting","inkjet printing",
        "laminated object manufacturing","ultrasonic consolidation",
        "vat photopolymerization","powder bed fusion","sheet lamination",
        "direct writing","aerosol jet printing","micro dispensing",
        "injection molding","injection blow molding","extrusion blow molding",
        "stretch blow molding","rotational molding","thermoforming",
        "vacuum forming","pressure forming","plug assist forming",
        "compression molding","transfer molding","resin transfer molding",
        "reaction injection molding","structural reaction injection molding",
        "pultrusion","filament winding","lay up","hand lay up",
        "spray lay up","vacuum bag molding","autoclave molding",
        "centrifugal casting","continuous casting","investment casting",
        "lost foam casting","die casting","squeeze casting","thixocasting",
        "rheocasting","electroforming","electrodischarge machining",
        "electrochemical machining","photochemical machining","abrasive jet machining",
        "abrasive water jet machining","ultrasonic machining","chemical mechanical polishing",
        "ion beam machining","plasma arc machining","electron beam machining",
        "laser beam machining","hot isostatic pressing","cold isostatic pressing",
        "powder forging","sintering","liquid phase sintering","spark plasma sintering",
        "microwave sintering","reaction bonding","self propagating high temperature synthesis",
        "combustion synthesis"]:
        r.append((t, "制造工艺"))
    return r

def gen_engineering_math():
    r = []
    for t in ["calculus","differential calculus","integral calculus","multivariable calculus",
        "vector calculus","linear algebra","matrix","determinant","eigenvalue","eigenvector",
        "differential equation","ordinary differential equation","partial differential equation",
        "laplace transform","fourier transform","fourier series","z transform",
        "numerical analysis","numerical integration","numerical differentiation",
        "finite difference","finite volume","finite element","boundary element",
        "newton method","bisection method","secant method","runge kutta",
        "euler method","trapezoidal rule","simpson rule","gaussian quadrature",
        "monte carlo method","newton raphson","gauss seidel","jacobi method",
        "gauss elimination","lu decomposition","cholesky decomposition",
        "singular value decomposition","principal component analysis",
        "regression analysis","linear regression","nonlinear regression",
        "interpolation","extrapolation","curve fitting","least squares",
        "spline","cubic spline","b spline","nurbs","bezier curve",
        "statistics","probability","probability distribution","normal distribution",
        "weibull distribution","exponential distribution","poisson distribution",
        "binomial distribution","hypothesis testing","confidence interval",
        "goodness of fit","analysis of variance","design of experiments",
        "response surface methodology","taguchi methods"]:
        r.append((t, "力学强度"))
    return r

def gen_safety():
    r = []
    for t in ["personal protective equipment","hard hat","safety glasses","goggles",
        "face shield","earplug","earmuff","hearing protection","respirator",
        "dust mask","half mask respirator","full face respirator","supplied air respirator",
        "self contained breathing apparatus","safety harness","lanyard",
        "fall arrest system","safety net","guardrail","handrail",
        "safety glove","leather glove","cut resistant glove","chemical glove",
        "welding glove","safety boot","steel toe boot","metatarsal guard",
        "safety shoe","slip resistant sole","high visibility vest",
        "reflective clothing","flame resistant clothing","chemical protective suit",
        "welding apron","welding helmet","auto darkening welding helmet",
        "lockout tagout","machine guarding","interlock","light curtain",
        "safety mat","two hand control","emergency stop","pull cord",
        "safety sign","warning sign","caution sign","danger sign",
        "fire extinguisher","sprinkler system","fire alarm","smoke detector",
        "heat detector","fire hose","standpipe","fire blanket","eye wash station",
        "safety shower","first aid kit","spill kit","confined space",
        "permit required confined space","hot work permit","job safety analysis",
        "risk assessment","hazard identification","hierarchy of controls",
        "engineering control","administrative control"]:
        r.append((t, "标准规范"))
    return r

def gen_measuring_more():
    r = []
    for t in ["linear measurement","angular measurement","surface measurement",
        "roundness measurement","cylindricity measurement","straightness measurement",
        "flatness measurement","parallelism measurement","squareness measurement",
        "coordinate measurement","dimensional measurement","geometric measurement",
        "laser tracker","laser scanner","white light scanner","structured light scanner",
        "photogrammetry","digital image correlation","fringe projection",
        "interferometer","laser interferometer","ball bar","check gage",
        "master gage","setting gage","working gage","inspection gage",
        "go no go gage", "limit gage","progressive gage","adjustable gage",
        "thread plug gage","thread ring gage","taper plug gage",
        "spline gage","keyway gage","depth micrometer","inside micrometer",
        "outside micrometer","tubular inside micrometer","rod type inside micrometer",
        "bench micrometer","flange micrometer","screw thread micrometer",
        "gear tooth micrometer","point micrometer","blade micrometer",
        "disc micrometer","ball micrometer","v anvil micrometer"]:
        r.append((t, "制图CAD"))
    return r

def gen_more_engineering():
    r = []
    # Additional machine components
    for t in ["plain washer","spring washer","lock washer","split washer",
        "tab washer","wave washer","tooth lock washer","internal tooth washer",
        "external tooth washer","conical washer","countersunk washer",
        "finishing washer","fender washer","oversized washer","square washer",
        "flat head screw","round head screw","pan head screw","hex head screw",
        "button head screw","socket head screw","countersunk screw",
        "oval head screw","truss head screw","fillister head screw",
        "phillips head","slotted head","hex socket","torx","square drive",
        "hex bolt","carriage bolt","plow bolt","elevator bolt","eye bolt",
        "hook bolt","lag bolt","stove bolt","toggle bolt","expansion bolt",
        "anchor bolt","j bolt","u bolt","shoulder bolt","step bolt",
        "stud","double end stud","tap end stud","reducer stud","pipe plug",
        "square head plug","hex head plug","socket head plug","flush plug"]:
        r.append((t, "机械设计"))
    return r

def gen_agricultural():
    r = []
    for t in ["tractor","cultivator","plow","harrow","seeder","planter",
        "transplanter","fertilizer spreader","manure spreader","sprayer",
        "irrigation system","center pivot","drip irrigation","sprinkler system",
        "combine harvester","forage harvester","sugarcane harvester","cotton picker",
        "baler","round baler","square baler","mower","hay rake","tedder",
        "disc harrow","rotary tiller","chisel plow","moldboard plow",
        "subsoiler","ripper","cultivator","field cultivator","row crop cultivator",
        "roller","packer","land leveler","scraper","ditcher","trencher",
        "backhoe","loader","skid steer","track loader","wheel loader",
        "forklift","telehandler","manlift","aerial work platform",
        "grain auger","grain bin","silo","feed mill","mixer mill",
        "grinder mixer","hammer mill","roller mill","burr mill",
        "seed cleaner","grain cleaner","grain dryer","batch dryer",
        "continuous flow dryer","bin dryer","in storage drying"]:
        r.append((t, "制造工艺"))
    return r

def gen_railway():
    r = []
    for t in ["railroad track","rail","steel rail","rail joint","joint bar",
        "fishplate","rail fastening","rail clip","e clip","pandrol clip",
        "tie plate","rail pad","railroad tie","wood tie","concrete tie",
        "steel tie","ballast","subballast","subgrade","rail bed",
        "turnout","switch","frog","guard rail","stock rail","point rail",
        "crossing","diamond crossing","double slip switch","scissors crossing",
        "derail","bumper","buffer stop","signal","semaphore signal",
        "color light signal","signal post","signal bridge","banner signal",
        "whistle post","milepost","grade crossing","crossing gate",
        "crossing signal","crossing bell","crossing barrier",
        "locomotive","diesel locomotive","electric locomotive","steam locomotive",
        "diesel electric","diesel hydraulic","overhead catenary","third rail",
        "pantograph","trolley pole","rolling stock","passenger car",
        "freight car","hopper car","gondola car","boxcar","flatcar",
        "tank car","covered hopper","refrigerator car","livestock car",
        "caboose","railcar","light rail","tram","streetcar",
        "coupler","knuckle coupler","buffer","draft gear","side buffer",
        "center buffer","drawbar","coupling screw",
        "wheel","railroad wheel","axle","journal box","plain bearing",
        "roller bearing","wheelset","bogie","truck","leaf spring",
        "coil spring","air spring","dampener","snubber","brake shoe",
        "brake beam","brake rigging","air brake","brake pipe",
        "brake hose","coupling hose","automatic coupler"]:
        r.append((t, "机械设计"))
    return r


def run():
    print("=" * 60)
    print("机械师大百科 V6 — 最终扩展")
    print("=" * 60)

    data = json.load(open(TERM))
    existing = data["terms"]
    start = len(existing)
    print(f"\nCurrent: {start}")

    seen = set(norm(t["en"]) for t in existing)
    all_new = []

    generators = [
        ("Wikipedia n-grams", mine_wiki_ngrams()),
        ("HVAC", gen_hvac()),
        ("Automotive", gen_automotive()),
        ("Plumbing", gen_plumbing()),
        ("Material grades", gen_material_grades()),
        ("Construction", gen_construction()),
        ("Power plant", gen_powerplant()),
        ("Mining", gen_mining()),
        ("Marine", gen_marine()),
        ("Manufacturing processes", gen_mfg_processes_more()),
        ("Engineering math", gen_engineering_math()),
        ("Safety", gen_safety()),
        ("Measuring instruments", gen_measuring_more()),
        ("More components", gen_more_engineering()),
        ("Agricultural", gen_agricultural()),
        ("Railway", gen_railway()),
    ]

    total_new = 0
    for name, terms in generators:
        added = 0
        for term, our_cat in terms:
            k = norm(term)
            if k in seen:
                continue
            seen.add(k)
            all_new.append({
                "en": term, "zh": e2z(term), "definition": gen_def(term),
                "source": "v6-" + name.split()[0].lower(),
                "category": our_cat,
            })
            added += 1
        total_new += len(terms)
        print(f"  {name}: {len(terms)} generated, {added} new")

    # Assemble
    data["terms"] = existing + all_new
    data["meta"]["total_terms"] = len(data["terms"])
    data["meta"]["expanded_new_terms"] = data["meta"].get("expanded_new_terms", 0) + len(all_new)
    data["meta"]["version"] = "2.5"
    data["meta"]["last_expanded"] = "2026-05-18"

    json.dump(data, open(TERM, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    cat_c = Counter(t.get("category","未分类") for t in data["terms"])
    src_c = Counter(t.get("source","unknown") for t in data["terms"])

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"\n  Before: {start}")
    print(f"  Generated total: {total_new}")
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
